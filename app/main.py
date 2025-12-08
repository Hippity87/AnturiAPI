from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db, get_session
from app.routers import sensors, measurements

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: Initializing the database...")
    await init_db()
    print("Database initialized.")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Sensor API",
    version="1.0.0",
    description="API for Raspberry PI sensor data collection",
    lifespan=lifespan,
    swagger_ui_parameters={"operationsSorter": "method"})

@app.get("/")
async def root():
    return {"message": "Sensor API is running!", "status": "OK"}


app.include_router(sensors.router)
app.include_router(measurements.router)