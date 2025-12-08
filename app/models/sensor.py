from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship



class SensorBase(SQLModel):
    mac_id: str = Field(index=True, unique=True, description="Anturin uniikki laitetunniste")
    block: str = Field(index=True, description="Fyysinen lohko, johon anturi kuuluu")
    status: str = Field(default="NORMAL", description="Anturin tila: NORMAL tai ERROR")

class MeasurementBase(SQLModel):
    temperature: float = Field(description="Lämpötila Celsius-asteina")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Mittauksen aikaleima")




class Sensor(SensorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relaatio: Yhdellä anturilla voi olla monta mittausta
    measurements: List["Measurement"] = Relationship(back_populates="sensor")

class Measurement(MeasurementBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key: Linkittää mittauksen tiettyyn anturiin
    sensor_id: int = Field(foreign_key="sensor.id")
    
    # Relaatio: Linkki takaisin anturi-objektiin
    sensor: Optional[Sensor] = Relationship(back_populates="measurements")



class SensorCreate(SensorBase):
    pass

class SensorUpdate(SQLModel):
    block: Optional[str] = None
    status: Optional[str] = None

class SensorRead(SensorBase):
    id: int
        
class MeasurementCreate(MeasurementBase):
    pass

class MeasurementRead(MeasurementBase):
    id: int
    sensor_id: int


# --- EVENT LOG MODEL ---

class SensorEventBase(SQLModel):
    status: str = Field(description="Tila johon siirryttiin (esim. ERROR)")
    description: Optional[str] = Field(default=None, description="Lisätieto tapahtumasta")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SensorEvent(SensorEventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    
    # Valinnainen: Relaatio takaisin anturiin
    sensor: Optional[Sensor] = Relationship()

# Schema lukemista varten
class SensorEventRead(SensorEventBase):
    id: int
    sensor_id: int