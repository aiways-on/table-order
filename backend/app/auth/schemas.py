"""Auth/session request & response schemas (Pydantic validation).  [SEC-05]"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    store_code: str = Field(min_length=1, max_length=64)
    admin_username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)


class AdminLoginResponse(BaseModel):
    store_id: str
    role: str = "admin"


class TableSetupRequest(BaseModel):
    table_no: int = Field(ge=1)
    table_password: str = Field(min_length=4, max_length=200)


class TableSetupResponse(BaseModel):
    table_id: str
    table_no: int


class SessionStartRequest(BaseModel):
    store_code: str = Field(min_length=1, max_length=64)
    table_no: int = Field(ge=1)
    table_password: str = Field(min_length=4, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    session_token: str
    store_id: str
    table_id: str


class MessageResponse(BaseModel):
    message: str
