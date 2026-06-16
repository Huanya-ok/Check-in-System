from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.check_in_record import CheckInRecord
from app.models.database import get_db
from app.models.face_profile import FaceProfile
from app.models.user import User
from app.schemas import (
    CheckInRecordResponse,
    CheckInResponse,
    FaceProfileResponse,
    LoginRequest,
    TokenResponse,
)
from app.services.face_service import face_service

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(access_token=create_access_token(user.username))


@router.post("/faces", response_model=FaceProfileResponse)
async def create_face(
    name: str = Form(...),
    employee_no: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    existing = await db.execute(select(FaceProfile).where(FaceProfile.employee_no == employee_no))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="工号已存在")

    content = await photo.read()
    upload_dir = Path(settings.upload_dir) / "faces"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{employee_no}_{uuid4().hex[:8]}.jpg"
    photo_path = upload_dir / filename
    photo_path.write_bytes(content)

    profile = FaceProfile(name=name, employee_no=employee_no, photo_path=str(photo_path))
    db.add(profile)
    await db.flush()

    try:
        embedding_index = face_service.add_face(profile.id, content)
        profile.embedding_index = embedding_index
    except ValueError as exc:
        await db.rollback()
        photo_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/faces", response_model=list[FaceProfileResponse])
async def list_faces(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(FaceProfile).where(FaceProfile.is_active.is_(True)).order_by(FaceProfile.id))
    return result.scalars().all()


@router.delete("/faces/{face_id}")
async def delete_face(
    face_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(FaceProfile).where(FaceProfile.id == face_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="人脸记录不存在")

    profile.is_active = False
    face_service.remove_face(profile.id)
    await db.commit()
    return {"message": "已删除"}


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(photo: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await photo.read()
    try:
        profile_id, score = face_service.search(content)
    except ValueError as exc:
        return CheckInResponse(success=False, message=str(exc))

    if profile_id is None:
        return CheckInResponse(success=False, message="未识别到匹配的人脸，请重试")

    result = await db.execute(
        select(FaceProfile).where(FaceProfile.id == profile_id, FaceProfile.is_active.is_(True))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return CheckInResponse(success=False, message="匹配用户已失效")

    upload_dir = Path(settings.upload_dir) / "checkins"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{profile.employee_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    photo_path = upload_dir / filename
    photo_path.write_bytes(content)

    record = CheckInRecord(
        face_profile_id=profile.id,
        similarity_score=score,
        photo_path=str(photo_path),
    )
    db.add(record)
    await db.commit()

    return CheckInResponse(
        success=True,
        name=profile.name,
        employee_no=profile.employee_no,
        message=f"签到成功，欢迎 {profile.name}！",
    )


@router.get("/check-in/records", response_model=list[CheckInRecordResponse])
async def list_check_in_records(
    date: str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = (
        select(CheckInRecord, FaceProfile)
        .join(FaceProfile, CheckInRecord.face_profile_id == FaceProfile.id)
        .order_by(CheckInRecord.check_in_time.desc())
    )
    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD") from exc
        stmt = stmt.where(CheckInRecord.check_in_time >= day)

    result = await db.execute(stmt)
    rows = result.all()
    return [
        CheckInRecordResponse(
            id=record.id,
            face_profile_id=record.face_profile_id,
            name=profile.name,
            employee_no=profile.employee_no,
            check_in_time=record.check_in_time,
            similarity_score=record.similarity_score,
        )
        for record, profile in rows
    ]
