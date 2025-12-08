from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.core.database import get_session
from app.models.sensor import Sensor, SensorCreate, SensorRead, SensorUpdate, Measurement, MeasurementCreate, MeasurementRead, SensorEventRead
from app.crud import sensor as sensor_crud
from app.crud import measurement as measurement_crud

router = APIRouter(prefix="/sensors", tags=["sensors"])

# --- 1. LUO UUSI ANTURI ---
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

# --- 2. HAE ANTURIT (Lohko / Status -suodatus) ---
@router.get("/", response_model=List[SensorRead])
async def read_sensors(
    block: Optional[str] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_sensors(session, block=block, status=status)

# --- 3. HAE YKSI ANTURI + MITTAUSHISTORIA ---
# Tämä toteuttaa vaatimuksen: "Näytä anturi ja oletuksena 10 uusinta mittausta"
# Luomme lennosta yhdistelmä-mallin vastaukselle.
from pydantic import BaseModel

class SensorDetailRead(SensorRead):
    measurements: List[MeasurementRead]

# app/routers/sensors.py

@router.get("/{sensor_id}", response_model=SensorDetailRead)
async def read_sensor(
    sensor_id: int,
    limit: int = Query(10, description="Montako mittausta haetaan"),
    session: AsyncSession = Depends(get_session)
):
    # 1. Haetaan anturi
    sensor = await sensor_crud.get_sensor_by_id(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # 2. Haetaan mittaukset manuaalisesti (jotta saadaan limit toimimaan)

    statement = (
        select(Measurement)
        .where(Measurement.sensor_id == sensor_id)
        # 1. Ensisijaisesti ajan mukaan
        # 2. Jos ajat ovat tasan, uusin ID ensin
        .order_by(desc(Measurement.timestamp), desc(Measurement.id))
        .limit(limit)
    )
    result = await session.exec(statement)
    measurements = result.all()

    # --- KORJAUS ALKAA TÄSTÄ ---
    
    # ÄLÄ TEE NÄIN (Tämä aiheuttaa MissingGreenlet-virheen):
    # sensor.measurements = measurements 
    # return sensor

    # TEE NÄIN:
    # Luomme uuden SensorDetailRead-objektin yhdistämällä anturin tiedot ja mittaukset.
    # **sensor.model_dump() purkaa anturin kentät (mac_id, block, jne.)
    return SensorDetailRead(
        **sensor.model_dump(), 
        measurements=measurements
    )

# --- 4. PÄIVITÄ ANTURI (Status / Lohko) ---
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

# --- 5. LÄHETÄ MITTAUSDATA (Anturi kutsuu tätä) ---
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



# --- 6. HAE ANTURIN HISTORIA  ---
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

# --- 7. HAE GLOBAALI HISTORIA ---
# Query-parametrilla ?status=ERROR saadaan lista graafia varten.
@router.get("/events/all", response_model=List[SensorEventRead])
async def read_all_events(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await sensor_crud.get_events(session, status=status)