from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.sensor import Measurement, MeasurementCreate

# 1. LUO UUSI MITTAUS
async def create_measurement(
    session: AsyncSession, 
    measurement_in: MeasurementCreate, 
    sensor_id: int
) -> Measurement:
    # Luodaan tietokantaobjekti ja lisätään siihen sensor_id manuaalisesti
    db_measurement = Measurement(**measurement_in.model_dump(), sensor_id=sensor_id)
    
    session.add(db_measurement)
    await session.commit()
    await session.refresh(db_measurement)
    return db_measurement

# 2. POISTA MITTAUS (Yksittäinen virheellinen tulos)
async def delete_measurement(session: AsyncSession, measurement_id: int) -> bool:
    measurement = await session.get(Measurement, measurement_id)
    if not measurement:
        return False
        
    await session.delete(measurement)
    await session.commit()
    return True