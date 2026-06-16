from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.routes import router
from app.config import settings
from app.core.security import hash_password
from app.models.database import Base, async_session, engine
from app.models.user import User


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            session.add(User(username="admin", password_hash=hash_password("admin123")))
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


_candidates = [
    Path(__file__).resolve().parent.parent.parent / "mobile",
    Path(__file__).resolve().parent.parent / "mobile",
]
mobile_dir = next((p for p in _candidates if p.exists()), None)
if mobile_dir:
    app.mount("/", StaticFiles(directory=str(mobile_dir), html=True), name="mobile")
