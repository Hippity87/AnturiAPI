from enum import Enum
from typing import List, Optional
from sqlmodel import select, desc, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.sensor import Sensor, SensorCreate, SensorUpdate, SensorEvent, Measurement


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

# 4. LUO UUSI ANTURI + ALKUTAPAHTUMA
async def create_sensor(session: AsyncSession, sensor_in: SensorCreate) -> Sensor:
    # 1. Luodaan anturi-objekti
    db_sensor = Sensor.model_validate(sensor_in)
    session.add(db_sensor)
    
    # 2. Ajetaan flush(), jotta saamme db_sensor.id:n käyttöön heti 
    # (mutta ei vielä commitoida transaktiota)
    await session.flush()

    # 3. Luodaan ensimmäinen historiatieto
    # Varmistetaan, että tallennamme status-arvon stringinä, jos se on Enum
    initial_status = sensor_in.status.value if hasattr(sensor_in.status, "value") else sensor_in.status

    event = SensorEvent(
        sensor_id=db_sensor.id,
        status=initial_status,
        description="Sensor created"
    )
    session.add(event)

    # 4. Tallennetaan molemmat kantaan (Commit)
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
    old_status = db_sensor.status.value if isinstance(db_sensor.status, Enum) else db_sensor.status
    
    # 2. Päivitetään anturin tiedot
    sensor_data = sensor_update.model_dump(exclude_unset=True)
    for key, value in sensor_data.items():
        if isinstance(value, Enum):
            value = value.value  # Tallenna enum-arvo tietokantaan

        setattr(db_sensor, key, value)
    
    session.add(db_sensor)
    
    # 3. LOKITUS: Jos status muuttui, luodaan tapahtuma
    new_status = sensor_update.status
    if isinstance(new_status, Enum):
        new_status = new_status.value

    if new_status and new_status != old_status:
        event = SensorEvent(
            sensor_id=db_sensor.id,
            status=new_status, # Tähän menee nyt varmasti string
            description=f"Status changed from {old_status} to {new_status}"
        )
        session.add(event)
    
        
    # 4. Tallennetaan kaikki kerralla (Transaktio)
    await session.commit()
    await session.refresh(db_sensor)
    return db_sensor


# 6. HAE TAPAHTUMALOKI

async def get_events(
    session: AsyncSession, 
    sensor_id: Optional[int] = None, 
    status: Optional[str] = None
) -> List[SensorEvent]:
    statement = select(SensorEvent)
    
    # Filtteri 1: Jos halutaan tietyn anturin historia
    if sensor_id:
        statement = statement.where(SensorEvent.sensor_id == sensor_id)
        
    # Filtteri 2: Jos halutaan esim. vain virhetilanteet (graafia varten)
    if status:
        statement = statement.where(SensorEvent.status == status)
        
    # Järjestys: Uusin tapahtuma ensin
    statement = statement.order_by(desc(SensorEvent.timestamp))
    
    result = await session.exec(statement)
    return result.all()


# 7. HAE LOHKON ANTURIT + VIIMEISIN DATA
async def get_sensors_by_block_with_stats(
    session: AsyncSession, 
    block: str
) -> List[dict]:
    """
    Hakee tietyn lohkon anturit ja liittää mukaan uusimman mittauksen tiedot.
    Toteutetaan ns. "Greatest-N-per-group" -kysely.
    """
    
    # 1. Alikysely: Etsi uusin aikaleima jokaiselle anturille
    subq = (
        select(
            Measurement.sensor_id, 
            func.max(Measurement.timestamp).label("max_ts")
        )
        .group_by(Measurement.sensor_id)
        .subquery()
    )

    # 2. Pääkysely: Anturi + Mittaus (joka matchaa uusimpaan aikaleimaan)
    # Käytämme outerjoinia, jotta saamme anturin listalle vaikka sillä ei olisi yhtään mittausta.
    statement = (
        select(Sensor, Measurement)
        .where(Sensor.block == block)
        .outerjoin(subq, Sensor.id == subq.c.sensor_id)
        .outerjoin(
            Measurement, 
            and_(
                Measurement.sensor_id == Sensor.id, 
                Measurement.timestamp == subq.c.max_ts
            )
        )
    )

    result = await session.exec(statement)
    
    # 3. Muotoillaan vastaus haluttuun muotoon
    response_data = []
    for sensor, measurement in result.all():
        response_data.append({
            "mac_id": sensor.mac_id,
            "status": sensor.status,
            "last_temperature": measurement.temperature if measurement else None,
            "last_timestamp": measurement.timestamp if measurement else None
        })
        
    return response_data