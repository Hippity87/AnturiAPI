from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.core.database import get_session
from app.models.sensor import Sensor, SensorCreate, SensorRead, SensorUpdate, Measurement, MeasurementCreate, MeasurementRead, SensorEventRead, SensorBlockRead, SensorDetailRead
from app.crud import sensor as sensor_crud
from app.crud import measurement as measurement_crud

router = APIRouter(prefix="/sensors", tags=["sensors"])

# ---  LUO UUSI ANTURI ---
@router.post("/", response_model=SensorRead, status_code=status.HTTP_201_CREATED, 
             summary="Luo uusi anturi",
             description="Rekisteröi uuden anturin järjestelmään. Tarkistaa, onko MAC-osoite uniikki. **Huom:** Luonnin yhteydessä luodaan automaattisesti ensimmäinen historiatieto tilaan, joka annetaan syötteessä.")
async def create_sensor(
    sensor_in: SensorCreate, 
    session: AsyncSession = Depends(get_session)
):
    existing_sensor = await sensor_crud.get_sensor_by_mac(session, sensor_in.mac_id)
    if existing_sensor:
        raise HTTPException(
            status_code=400, 
            detail="Sensor with this MAC ID already exists"
        )
    return await sensor_crud.create_sensor(session, sensor_in)

# ---  LÄHETÄ MITTAUSDATA ---
@router.post("/{sensor_id}/measurements", response_model=MeasurementRead, status_code=status.HTTP_201_CREATED,
             summary="Lisää mittausdataa",
             description="Tallentaa uuden lämpötilamittauksen tietylle anturille. Aikaleima luodaan automaattisesti, jos sitä ei anneta.")
async def create_measurement_for_sensor(
    sensor_id: int,
    measurement_in: MeasurementCreate,
    session: AsyncSession = Depends(get_session)
):
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    return await measurement_crud.create_measurement(session, measurement_in, sensor_id)

# ---  HAE ANTURIT (Status-suodatus) ---
@router.get("/", response_model=List[SensorRead],
            summary="Listaa kaikki anturit",
            description="Hakee listan kaikista antureista. Voit suodattaa listaa anturin tilan perusteella (esim. `status=ERROR`).")
async def read_sensors(
    status: Optional[str] = Query(None, description="Suodata tilan mukaan (NORMAL, ERROR, MAINTENANCE)"),
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_sensors(session, status=status)

# --- UUSI: HAE LOHKON ANTURIT ---
@router.get("/block/{block_name}", response_model=List[SensorBlockRead],
            summary="Hae lohkon anturit ja uusin data",
            description="Optimioitu näkymä, joka listaa tietyn lohkon anturit ja niiden **viimeisimmän** mittaustuloksen. Käytä tätä, kun haluat nopean katsauksen lohkon tilanteeseen.")
async def read_sensors_by_block(
    block_name: str,
    session: AsyncSession = Depends(get_session)
):
    # Palauttaa listan dict-objekteja, jotka mäppäytyvät SensorBlockRead-malliin
    sensors_data = await sensor_crud.get_sensors_by_block_with_stats(session, block=block_name)
    return sensors_data

# ---  HAE YKSI ANTURI + MITTAUSHISTORIA ---
@router.get("/{sensor_id}", response_model=SensorDetailRead,
            summary="Hae yksittäinen anturi",
            description="Palauttaa anturin perustiedot ja listan mittauksista. Oletuksena näytetään 10 uusinta mittausta, mutta voit hakea dataa myös aikaväliltä `start_time` - `end_time`.")
async def read_sensor(
    sensor_id: int,
    limit: int = Query(10, description="Montako mittausta haetaan (jos aikaväliä ei annettu)"),
    start_time: Optional[datetime] = Query(None, description="Alkamisaika (esim. 2023-01-01T12:00:00)"),
    end_time: Optional[datetime] = Query(None, description="Päättymisaika"),
    session: AsyncSession = Depends(get_session)
):
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    statement = (
        select(Measurement)
        .where(Measurement.sensor_id == sensor_id)
        .order_by(desc(Measurement.timestamp), desc(Measurement.id))
    )
    
    if start_time:
        statement = statement.where(Measurement.timestamp >= start_time)
    if end_time:
        statement = statement.where(Measurement.timestamp <= end_time)
        
    if not start_time and not end_time:
        statement = statement.limit(limit)
    
    result = await session.exec(statement)
    measurements = result.all()

    return SensorDetailRead(
        **sensor.model_dump(), 
        measurements=measurements
    )

# ---  PÄIVITÄ ANTURI ---
@router.patch("/{sensor_id}", response_model=SensorRead,
              summary="Päivitä anturin tietoja",
              description="Muuta anturin lohkoa tai tilaa. Jos tila muuttuu (esim. ERROR -> NORMAL), muutoksesta luodaan automaattisesti merkintä tapahtumalokiin.")
async def update_sensor(
    sensor_id: int,
    sensor_update: SensorUpdate,
    session: AsyncSession = Depends(get_session)
):
    db_sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    return await sensor_crud.update_sensor(session, db_sensor, sensor_update)

# ---  HAE ANTURIN HISTORIA  ---
@router.get("/{sensor_id}/history", response_model=List[SensorEventRead],
            summary="Hae anturin tapahtumaloki",
            description="Listaa kaikki anturin tilamuutokset (milloin luoto, milloin anturi on mennyt vikatilaan ja milloin se on palautettu normaaliksi).")
async def read_sensor_history(
    sensor_id: int,
    session: AsyncSession = Depends(get_session)
):
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    return await sensor_crud.get_events(session, sensor_id=sensor_id)

# ---  HAE GLOBAALI HISTORIA ---
@router.get("/events/all", response_model=List[SensorEventRead],
            summary="Hae koko tehtaan tapahtumat",
            description="Listaa tapahtumia kaikilta antureilta. Käytä `status`-suodatinta (esim. `status=ERROR`) saadaksesi datan virhegraafia varten.")
async def read_all_events(
    status: Optional[str] = Query(None, description="Suodata tilan mukaan"),
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_events(session, status=status)