from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PeerRegistration(BaseModel):
    hostname: str
    ip: str


class PeerRecord(BaseModel):
    hostname: str
    ip: str
    last_seen: datetime


class PeerResponse(BaseModel):
    hostname: str
    ip: str


class ErrorResponse(BaseModel):
    error: str


class StatusResponse(BaseModel):
    status: str
    message: str
