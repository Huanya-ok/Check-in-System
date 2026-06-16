from datetime import datetime

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class FaceProfileResponse(BaseModel):
    id: int
    name: str
    employee_no: str
    photo_path: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckInResponse(BaseModel):
    success: bool
    name: str | None = None
    employee_no: str | None = None
    message: str


class CheckInRecordResponse(BaseModel):
    id: int
    face_profile_id: int
    name: str
    employee_no: str
    check_in_time: datetime
    similarity_score: float

    model_config = {"from_attributes": True}
