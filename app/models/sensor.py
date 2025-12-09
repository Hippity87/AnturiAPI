from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator
from app.core.utils import normalize_and_validate_mac

# --- ENUMS ---

class SensorStatus(str, Enum):
    NORMAL = "NORMAL"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

# --- BASE MODELS (Business Data) ---
# Näissä on vain kentät, jotka käyttäjä voi syöttää luodessa.

class SensorBase(SQLModel):
    mac_id: str = Field(
        index=True, 
        unique=True, 
        description="MAC-osoite (XX:XX:XX:XX:XX:XX)"
    )
    block: str = Field(
        index=True, 
        min_length=1, 
        max_length=50, 
        description="Fyysinen lohko"
    )
    status: SensorStatus = Field(default=SensorStatus.NORMAL)

    class Config:
        json_schema_extra = {
            "example": {"mac_id": "AA:BB:CC:11:22:33", "block": "Lohko A", "status": "NORMAL"}
        }

    @field_validator("mac_id")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        return normalize_and_validate_mac(v)

class MeasurementBase(SQLModel):
    temperature: float = Field(ge=-273.15, le=1000.0, description="Lämpötila (°C)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Aikaleima"
    )

class SensorEventBase(SQLModel):
    status: SensorStatus
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- DATABASE TABLES (ORM) ---
# Nämä sisältävät ID:t ja relaatiot, joita ei näytetä suoraan API:ssa näin.

class Sensor(SensorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    measurements: List["Measurement"] = Relationship(back_populates="sensor")
    events: List["SensorEvent"] = Relationship(back_populates="sensor")

class Measurement(MeasurementBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    sensor: Optional[Sensor] = Relationship(back_populates="measurements")

class SensorEvent(SensorEventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    sensor: Optional[Sensor] = Relationship(back_populates="events")

# --- API MODELS (DTOs) ---

# Create: Sama kuin Base
SensorCreate = SensorBase
MeasurementCreate = MeasurementBase

# Update: Kaikki kentät valinnaisia
class SensorUpdate(SQLModel):
    block: Optional[str] = Field(default=None, min_length=1, max_length=50)
    status: Optional[SensorStatus] = Field(default=None)

# Read: Base + ID
class SensorRead(SensorBase):
    id: int

class MeasurementRead(MeasurementBase):
    id: int
    sensor_id: int

class SensorEventRead(SensorEventBase):
    id: int
    sensor_id: int

# Special Read Models: Erikoistapaukset UI:ta varten

class SensorBlockRead(SQLModel):
    """
    Optimoitu kevyt malli lohkonäkymää varten.
    Sisältää sekä ID:n että MACin helpottamaan kommunikaatiota.
    """
    mac_id: str
    status: SensorStatus
    last_temperature: Optional[float]
    last_timestamp: Optional[datetime]
    id: int


class SensorDetailRead(SensorRead):
    """
    Yksittäisen anturin tarkastelu: Tähän haluamme mukaan listan mittauksia.
    """
    measurements: List[MeasurementRead]