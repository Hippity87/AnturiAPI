import re
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator


class SensorStatus(str, Enum):
    NORMAL = "NORMAL"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class SensorBase(SQLModel):
    mac_id: str = Field(
        index=True, 
        unique=True, 
        description="Anturin MAC-osoite (tallennetaan muodossa XX:XX:XX:XX:XX:XX)"
    )
    # Lohkon nimi ei saa olla tyhjä
    block: str = Field(
        index=True, 
        min_length=1, 
        max_length=50, 
        description="Fyysinen lohko, johon anturi kuuluu"
    )
    status: SensorStatus = Field(default=SensorStatus.NORMAL, description="Anturin tila")

    class Config:
        json_schema_extra = {
            "example": {
                "mac_id": "AA:BB:CC:11:22:33",
                "block": "Lohko A1",
                "status": "NORMAL"
            }
        }

    @field_validator("mac_id")
    @classmethod
    def validate_and_normalize_mac(cls, v: str) -> str:
        # 1. Siivous: Poista tyhjät ja muuta isoksi
        v = v.strip().upper()
        
        # 2. Normalisointi: Vaihda viivat kaksoispisteiksi
        # Esim. "AA-BB-CC..." -> "AA:BB:CC..."
        v = v.replace("-", ":")
        
        # 3. Validointi: Tarkista että muoto on nyt tasan XX:XX:XX:XX:XX:XX
        # Regex: 2 heksamerkkiä, kaksoispiste, toista 5 kertaa, lopussa 2 heksamerkkiä
        regex = r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"
        
        if not re.match(regex, v):
            raise ValueError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX")
            
        return v

class SensorEventBase(SQLModel):
    # Myös historiassa kannattaa käyttää Enumia
    status: SensorStatus = Field(description="Tila johon siirryttiin")
    description: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MeasurementBase(SQLModel):
    # rajat lämpötilalle (ettei tule virhesyöttöjä)
    temperature: float = Field(
        description="Lämpötila Celsius-asteina", 
        ge=-273.15, # Absolute zero
        le=1000.0   # Joku järkevä yläraja
    )
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
    block: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=50,
        schema_extra={"example": "Lohko B"}
    )
    
    status: Optional[SensorStatus] = Field(
        default=None,
        description="Uusi tila (NORMAL, ERROR, MAINTENANCE)",
        schema_extra={"example": "ERROR"} 
    )

class SensorRead(SensorBase):
    id: int
        
class MeasurementCreate(MeasurementBase):
    pass

class MeasurementRead(MeasurementBase):
    id: int
    sensor_id: int


# --- EVENT LOG MODEL ---

class SensorEvent(SensorEventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    
    # Valinnainen: Relaatio takaisin anturiin
    sensor: Optional[Sensor] = Relationship()

# Schema lukemista varten
class SensorEventRead(SensorEventBase):
    id: int
    sensor_id: int