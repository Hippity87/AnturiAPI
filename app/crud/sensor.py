from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.sensor import Sensor, SensorCreate, SensorUpdate, SensorEvent

# 1. HAE YKSI (ID:n perusteella)
async def get_sensor_by_id(session: AsyncSession, sensor_id: int) -> Optional[Sensor]:
    return await session.get(Sensor, sensor_id)

# 2. HAE YKSI (MAC-osoitteen perusteella - estetään duplikaatit)
async def get_sensor_by_mac(session: AsyncSession, mac_id: str) -> Optional[Sensor]:
    statement = select(Sensor).where(Sensor.mac_id == mac_id)
    result = await session.exec(statement)
    return result.first()

# 3. HAE KAIKKI (Tukee suodatusta lohkon ja statuksen mukaan)
async def get_sensors(
    session: AsyncSession, 
    block: Optional[str] = None, 
    status: Optional[str] = None
) -> List[Sensor]:
    statement = select(Sensor)
    
    if block:
        statement = statement.where(Sensor.block == block)
    if status:
        statement = statement.where(Sensor.status == status)
        
    result = await session.exec(statement)
    return result.all()

# 4. LUO UUSI ANTURI
async def create_sensor(session: AsyncSession, sensor_in: SensorCreate) -> Sensor:
    # Muutetaan Pydantic-malli tietokantamalliksi
    db_sensor = Sensor.model_validate(sensor_in)
    session.add(db_sensor)
    await session.commit()
    await session.refresh(db_sensor)
    return db_sensor

# 5. PÄIVITÄ ANTURI (vaihda status ERROR -> NORMAL)

async def update_sensor(
    session: AsyncSession, 
    db_sensor: Sensor, 
    sensor_update: SensorUpdate
) -> Sensor:
    
    # 1. Otetaan talteen vanha status vertailua varten
    old_status = db_sensor.status
    
    # 2. Päivitetään anturin tiedot
    sensor_data = sensor_update.model_dump(exclude_unset=True)
    for key, value in sensor_data.items():
        setattr(db_sensor, key, value)
    
    session.add(db_sensor)
    
    # 3. LOKITUS: Jos status muuttui, luodaan tapahtuma
    if sensor_update.status and sensor_update.status != old_status:
        event = SensorEvent(
            sensor_id=db_sensor.id,
            status=sensor_update.status,
            description=f"Status changed from {old_status} to {sensor_update.status}"
        )
        session.add(event)
        
    # 4. Tallennetaan kaikki kerralla (Transaktio)
    await session.commit()
    await session.refresh(db_sensor)
    return db_sensor