from datetime import datetime

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    name: str
    role: str = "student"


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    message: str
    username: str
    name: str
    student_no: str
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class CheckInResponse(BaseModel):
    success: bool
    name: str | None = None
    student_no: str | None = None
    message: str


class CheckInRecordResponse(BaseModel):
    id: int
    face_profile_id: int
    name: str
    student_no: str
    check_in_time: datetime
    similarity_score: float

    model_config = {"from_attributes": True}


class AbsentStudent(BaseModel):
    name: str
    student_no: str


class TeacherOverviewResponse(BaseModel):
    date: str
    total_registered: int
    checked_in_count: int
    absent_count: int
    records: list[CheckInRecordResponse]
    absent_students: list[AbsentStudent]
