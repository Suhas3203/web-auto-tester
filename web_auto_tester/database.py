"""
Async database layer for persisting test run history.

Drivers:
  - SQLite  (default, local dev): sqlite+aiosqlite:///./web-auto-tester.db
  - Supabase PostgreSQL (Render): set DATABASE_URL env var to the
    "Transaction pooler" connection string from your Supabase project
    (Settings → Database → Connection string → URI, port 6543).
    Both postgres:// and postgresql:// prefixes are normalised automatically.

Usage:
    from web_auto_tester.database import init_db, save_run, list_runs, get_run
"""

from __future__ import annotations

import json
import os

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, Text


# ── Connection URL ────────────────────────────────────────────────────────────
_raw_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./web-auto-tester.db")

_is_postgres = "postgres" in _raw_url and "sqlite" not in _raw_url

# Normalise Supabase / generic Postgres URLs → asyncpg driver
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_url.startswith("postgresql://") and "+asyncpg" not in _raw_url:
    _raw_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Strip ?sslmode=... from URL — asyncpg handles SSL via connect_args
if "?sslmode=" in _raw_url:
    _raw_url = _raw_url.split("?sslmode=")[0]

DATABASE_URL = _raw_url

# Supabase requires SSL; SQLite needs check_same_thread=False
if "sqlite" in DATABASE_URL:
    _connect_args: dict = {"check_same_thread": False}
else:
    import ssl as _ssl
    _ssl_ctx = _ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl.CERT_NONE
    _connect_args = {"ssl": _ssl_ctx}

_engine_kwargs: dict = {"echo": False, "connect_args": _connect_args}
if "sqlite" not in DATABASE_URL:
    # Supabase transaction pooler drops idle connections — keep pool small
    _engine_kwargs.update({"pool_size": 2, "max_overflow": 3, "pool_recycle": 300, "pool_pre_ping": True})

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ── ORM Model ─────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048))
    mode: Mapped[str] = mapped_column(String(16), default="lite")
    status: Mapped[str] = mapped_column(String(16), default="completed")

    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    framework_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    started_at: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0)

    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Lifecycle ──────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create tables if they don't exist. Called at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── CRUD ──────────────────────────────────────────────────────────────────────
async def save_run(
    *,
    run_id: str,
    url: str,
    mode: str,
    status: str,
    framework: str | None,
    framework_version: str | None,
    started_at: float,
    duration_seconds: float,
    total_pages: int,
    total_tests: int,
    passed: int,
    failed: int,
    warnings: int,
    pass_rate: float,
    error_msg: str | None = None,
    report_json: str | None = None,
) -> None:
    """Insert or replace a test run record."""
    async with SessionLocal() as session:
        run = TestRun(
            id=run_id,
            url=url,
            mode=mode,
            status=status,
            framework=framework,
            framework_version=framework_version,
            started_at=started_at,
            duration_seconds=duration_seconds,
            total_pages=total_pages,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            warnings=warnings,
            pass_rate=pass_rate,
            error_msg=error_msg,
            report_json=report_json,
        )
        await session.merge(run)   # upsert
        await session.commit()


async def list_runs(limit: int = 50) -> list[dict]:
    """Return recent runs, newest first, without the heavy report_json blob."""
    async with SessionLocal() as session:
        rows = await session.execute(
            select(TestRun)
            .order_by(desc(TestRun.started_at))
            .limit(limit)
        )
        runs = rows.scalars().all()
        return [
            {
                "id": r.id,
                "url": r.url,
                "mode": r.mode,
                "status": r.status,
                "framework": r.framework,
                "framework_version": r.framework_version,
                "started_at": r.started_at,
                "duration_seconds": r.duration_seconds,
                "total_pages": r.total_pages,
                "total_tests": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "warnings": r.warnings,
                "pass_rate": r.pass_rate,
                "error_msg": r.error_msg,
            }
            for r in runs
        ]


async def get_run(run_id: str) -> dict | None:
    """Return a single run including its full report_json."""
    async with SessionLocal() as session:
        run = await session.get(TestRun, run_id)
        if not run:
            return None
        return {
            "id": run.id,
            "url": run.url,
            "mode": run.mode,
            "status": run.status,
            "framework": run.framework,
            "framework_version": run.framework_version,
            "started_at": run.started_at,
            "duration_seconds": run.duration_seconds,
            "total_pages": run.total_pages,
            "total_tests": run.total_tests,
            "passed": run.passed,
            "failed": run.failed,
            "warnings": run.warnings,
            "pass_rate": run.pass_rate,
            "error_msg": run.error_msg,
            "report_json": json.loads(run.report_json) if run.report_json else None,
        }
