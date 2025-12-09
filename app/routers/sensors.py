from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.core.database import get_session
from app.models.sensor import Sensor, SensorCreate, SensorRead, SensorUpdate, Measurement, MeasurementCreate, MeasurementRead, SensorEventRead, SensorBlockRead
from app.crud import sensor as sensor_crud
from app.crud import measurement as measurement_crud

router = APIRouter(prefix="/sensors", tags=["sensors"])

# ---  LUO UUSI ANTURI ---
@router.post("/", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
async def create_sensor(
    sensor_in: SensorCreate, 
    session: AsyncSession = Depends(get_session)
):
    # Tarkistetaan, onko MAC-osoite jo olemassa
    existing_sensor = await sensor_crud.get_sensor_by_mac(session, sensor_in.mac_id)
    if existing_sensor:
        raise HTTPException(
            status_code=400, 
            detail="Sensor with this MAC ID already exists"
        )
    return await sensor_crud.create_sensor(session, sensor_in)



# ---  LÄHETÄ MITTAUSDATA (Anturi kutsuu tätä) ---
@router.post("/{sensor_id}/measurements", response_model=MeasurementRead, status_code=status.HTTP_201_CREATED)
async def create_measurement_for_sensor(
    sensor_id: int,
    measurement_in: MeasurementCreate,
    session: AsyncSession = Depends(get_session)
):
    # Varmistetaan että anturi on olemassa
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    # Luodaan mittaus
    return await measurement_crud.create_measurement(session, measurement_in, sensor_id)



# ---  HAE ANTURIT (Lohko / Status -suodatus) ---
@router.get("/", response_model=List[SensorRead])
async def read_sensors(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_sensors(session, status=status)

# ---  HAE YKSI ANTURI + MITTAUSHISTORIA ---
# Tämä toteuttaa vaatimuksen: "Näytä anturi ja oletuksena 10 uusinta mittausta"
# Luomme lennosta yhdistelmä-mallin vastaukselle.
from pydantic import BaseModel

class SensorDetailRead(SensorRead):
    measurements: List[MeasurementRead]


@router.get("/{sensor_id}", response_model=SensorDetailRead)
async def read_sensor(
    sensor_id: int,
    limit: int = Query(10, description="Montako mittausta haetaan (jos aikaväliä ei annettu)"),
    start_time: Optional[datetime] = Query(None, description="Hae mittaukset tästä ajankohdasta eteenpäin"),
    end_time: Optional[datetime] = Query(None, description="Hae mittaukset tähän ajankohtaan asti"),
    session: AsyncSession = Depends(get_session)
):
    # 1. Haetaan anturi
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # 2. Rakennetaan mittausten kysely dynaamisesti
    statement = (
        select(Measurement)
        .where(Measurement.sensor_id == sensor_id)
        .order_by(desc(Measurement.timestamp), desc(Measurement.id)) # Uusimmat ensin + tie-breaker
    )
    
    # --- AIKASUODATUS ---
    if start_time:
        statement = statement.where(Measurement.timestamp >= start_time)
    
    if end_time:
        statement = statement.where(Measurement.timestamp <= end_time)
        
    # Sovelletaan limit vain jos aikaväliä EI ole määritelty tiukaksi
    # (Tai voimme päättää, että limit on aina voimassa. Yleensä aikavälihaussa halutaan kaikki data.)
    if not start_time and not end_time:
        statement = statement.limit(limit)
    
    # Jos käyttäjä antoi aikavälin, emme ehkä halua katkaista listaa 10 kappaleeseen,
    # mutta turvallisuuden vuoksi voisi olla joku maksimi (esim 1000). 
    # Tässä esimerkissä poistamme limitin kokonaan jos aikaväli on käytössä.
    
    result = await session.exec(statement)
    measurements = result.all()

    # 3. Palautetaan yhdistelmäobjekti
    return SensorDetailRead(
        **sensor.model_dump(), 
        measurements=measurements
    )

# ---  PÄIVITÄ ANTURI (Status / Lohko) ---
@router.patch("/{sensor_id}", response_model=SensorRead)
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
@router.get("/{sensor_id}/history", response_model=List[SensorEventRead])
async def read_sensor_history(
    sensor_id: int,
    session: AsyncSession = Depends(get_session)
):
    # Varmistetaan ensin, että anturi on olemassa
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
        
    return await sensor_crud.get_events(session, sensor_id=sensor_id)

# ---  HAE GLOBAALI HISTORIA ---
# Query-parametrilla ?status=ERROR saadaan lista graafia varten.
@router.get("/events/all", response_model=List[SensorEventRead])
async def read_all_events(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_events(session, status=status)



# ---  HAE LOHKON ANTURIT (Spec: mac, status, last_temp, last_time) ---
@router.get("/block/{block_name}", response_model=List[SensorBlockRead])
async def read_sensors_by_block(
    block_name: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Listaa tietyn lohkon anturit ja niiden viimeisimmän mittaustuloksen.
    Ei palauta anturin ID:tä tai lohkon nimeä vastauksessa.
    """
    sensors_data = await sensor_crud.get_sensors_by_block_with_stats(session, block=block_name)
    return sensors_data