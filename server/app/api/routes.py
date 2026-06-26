from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_teacher, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.check_in_record import CheckInRecord
from app.models.database import get_db
from app.models.face_profile import FaceProfile
from app.models.user import User
from app.schemas import (
    AbsentStudent,
    CheckInRecordResponse,
    CheckInResponse,
    LoginRequest,
    MessageResponse,
    RegisterResponse,
    TeacherOverviewResponse,
    TokenResponse,
)
from app.services.face_service import face_service

router = APIRouter()


def _parse_date(date_str: str | None) -> datetime.date:
    if not date_str:
        return datetime.now().date()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD") from exc


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/auth/register", response_model=RegisterResponse)
async def register(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    student_no: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()
    name = name.strip()
    student_no = student_no.strip()

    if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    if (await db.execute(select(User).where(User.student_no == student_no))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="学号已注册")

    if (await db.execute(select(FaceProfile).where(FaceProfile.student_no == student_no))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="学号已注册")

    content = await photo.read()
    upload_dir = Path(settings.upload_dir) / "faces"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{student_no}_{uuid4().hex[:8]}.jpg"
    photo_path = upload_dir / filename
    photo_path.write_bytes(content)

    user = User(
        username=username,
        password_hash=hash_password(password),
        name=name,
        student_no=student_no,
        role="student",
    )
    db.add(user)
    await db.flush()

    profile = FaceProfile(
        user_id=user.id,
        name=name,
        student_no=student_no,
        photo_path=str(photo_path),
    )
    db.add(profile)
    await db.flush()

    try:
        face_result = await face_service.add_face(profile.id, content)
        profile.frs_face_id = face_result.get("face_id")
    except (ValueError, RuntimeError) as exc:
        await db.rollback()
        photo_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()

    return RegisterResponse(
        message="注册成功",
        username=user.username,
        name=user.name,
        student_no=user.student_no,
        access_token=create_access_token(user.username),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(
        access_token=create_access_token(user.username),
        username=user.username,
        name=user.name,
        role=user.role,
    )


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(_: User = Depends(get_current_user)):
    return MessageResponse(message="已注销，请清除客户端 Token")


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(photo: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    content = await photo.read()
    try:
        search_result = await face_service.search(content)
        profile_id_raw = search_result.get("external_image_id") or search_result.get("face_id")
        score = float(search_result.get("similarity") or 0.0)
    except (ValueError, RuntimeError) as exc:
        return CheckInResponse(success=False, message=str(exc))

    if profile_id_raw is None:
        return CheckInResponse(success=False, message="未识别到匹配的人脸，请重试")

    try:
        profile_id = int(profile_id_raw)
    except (TypeError, ValueError):
        return CheckInResponse(success=False, message="人脸匹配结果无效")

    result = await db.execute(
        select(FaceProfile).where(FaceProfile.id == profile_id, FaceProfile.is_active.is_(True))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return CheckInResponse(success=False, message="匹配用户已失效")

    upload_dir = Path(settings.upload_dir) / "checkins"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{profile.student_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
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
        student_no=profile.student_no,
        message=f"签到成功，欢迎 {profile.name}！",
    )


@router.get("/check-in/records", response_model=list[CheckInRecordResponse])
async def list_check_in_records(
    date: str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_result = await db.execute(select(FaceProfile).where(FaceProfile.user_id == current_user.id))
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        return []

    stmt = (
        select(CheckInRecord)
        .where(CheckInRecord.face_profile_id == profile.id)
        .order_by(CheckInRecord.check_in_time.desc())
    )
    if date:
        day = _parse_date(date)
        next_day = day + timedelta(days=1)
        stmt = stmt.where(
            CheckInRecord.check_in_time >= day,
            CheckInRecord.check_in_time < next_day,
        )

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        CheckInRecordResponse(
            id=record.id,
            face_profile_id=record.face_profile_id,
            name=profile.name,
            student_no=profile.student_no,
            check_in_time=record.check_in_time,
            similarity_score=record.similarity_score,
        )
        for record in records
    ]


@router.get("/teacher/overview", response_model=TeacherOverviewResponse)
async def teacher_overview(
    date: str | None = Query(None, description="YYYY-MM-DD，默认今天"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_teacher),
):
    day = _parse_date(date)
    next_day = day + timedelta(days=1)

    profiles_result = await db.execute(
        select(FaceProfile).where(FaceProfile.is_active.is_(True)).order_by(FaceProfile.student_no)
    )
    profiles = profiles_result.scalars().all()
    profile_map = {p.id: p for p in profiles}

    records_result = await db.execute(
        select(CheckInRecord)
        .where(CheckInRecord.check_in_time >= day, CheckInRecord.check_in_time < next_day)
        .order_by(CheckInRecord.check_in_time.desc())
    )
    records = records_result.scalars().all()

    checked_in_ids: set[int] = set()
    record_responses: list[CheckInRecordResponse] = []
    for record in records:
        profile = profile_map.get(record.face_profile_id)
        if profile is None:
            continue
        checked_in_ids.add(profile.id)
        record_responses.append(
            CheckInRecordResponse(
                id=record.id,
                face_profile_id=record.face_profile_id,
                name=profile.name,
                student_no=profile.student_no,
                check_in_time=record.check_in_time,
                similarity_score=record.similarity_score,
            )
        )

    absent = [
        AbsentStudent(name=p.name, student_no=p.student_no)
        for p in profiles
        if p.id not in checked_in_ids
    ]

    return TeacherOverviewResponse(
        date=day.isoformat(),
        total_registered=len(profiles),
        checked_in_count=len(checked_in_ids),
        absent_count=len(absent),
        records=record_responses,
        absent_students=absent,
    )
