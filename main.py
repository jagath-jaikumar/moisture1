from fastapi import FastAPI, status, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
import os
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import datetime


class StatusMessage(BaseModel):
    status: Literal["ok", "fail"] = "ok"
    message: Optional[str]


class RegisterDevice(BaseModel):
    mac: str
    nickname: Optional[str]
    dangerThreshold: Optional[float]


class RegisterReading(BaseModel):
    mac: str
    reading: float


class SelectReadings(BaseModel):
    mac: str = ""


class Reading(BaseModel):
    created_at: datetime
    reading: float


class SensorReadings(BaseModel):
    mac: str
    readings: List[Reading]


class ReadingsResponse(BaseModel):
    result: List[SensorReadings]


app = FastAPI()

url = os.getenv("SUPABASE_URL", default="")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", default="")

supabase: Client = create_client(url, key)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.post("/register/device", response_model=StatusMessage)
async def register_device(request: RegisterDevice):
    device = (
        supabase.table("moistureSensor").select("*").eq("mac", request.mac).execute()
    )
    message = "found"
    if not device.data:
        device = (
            supabase.table("moistureSensor")
            .insert(
                [
                    {
                        "nickname": request.nickname,
                        "dangerThreshold": request.dangerThreshold,
                        "mac": request.mac,
                    }
                ]
            )
            .execute()
        )
        message = "created"

    return StatusMessage(message=message)


@app.post("/register/reading", response_model=StatusMessage)
async def register_reading(request: RegisterReading):
    device = (
        supabase.table("moistureSensor").select("*").eq("mac", request.mac).execute()
    )
    if not device.data:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"device {request.mac} not found",
        )

    supabase.table("moistureReading").insert(
        [
            {
                "sensor": device.data[0]["id"],
                "reading": request.reading,
            }
        ]
    ).execute()

    return StatusMessage()


@app.post("/select/readings", response_model=ReadingsResponse)
async def select_readings(request: SelectReadings):
    device = (
        supabase.table("moistureSensor").select("*").eq("mac", request.mac).execute()
    )
    if not device.data:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"device {request.mac} not found",
        )
    readings = (
        supabase.table("moistureReading")
        .select("*")
        .eq("sensor", device.data[0]["id"])
        .execute()
        .data
    )
    result = [
        SensorReadings(mac=request.mac, readings=[Reading(**r) for r in readings])
    ]

    return ReadingsResponse(result=result)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", default="5000")),
        log_level="info",
        workers=4,
    )
