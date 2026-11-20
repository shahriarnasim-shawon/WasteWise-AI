"""
Database session and connection management for WasteWiseAI.
Supports SQLite (default) and PostgreSQL via DATABASE_URL.
Safely handles container paths and provides resilient fallbacks for cloud deployments (Render, Railway, Fly).
"""

from pathlib import Path
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


def get_effective_database_url(url: str) -> str:
    """
    Ensures parent directories exist for SQLite files.
    Falls back gracefully to a writable location if the target directory is missing or read-only.
    """
    if not url.startswith("sqlite"):
        return url

    if ":memory:" in url:
        return url

    # Extract path from sqlite:///...
    match = re.match(r"^sqlite:///(.*)$", url)
    if not match:
        return url

    raw_path = match.group(1)
    target_path = Path(raw_path if raw_path.startswith("/") else f"/{raw_path}" if url.startswith("sqlite:////") else raw_path)

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Test write permission in parent directory
        test_file = target_path.parent / ".ww_test"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
        return url
    except Exception as err:
        print(f"[WasteWise-AI] Warning: Cannot write SQLite database to {target_path} ({err}).")
        
        # Try local fallback in current working directory
        try:
            local_fallback = Path("./wastewise.db").resolve()
            local_fallback.parent.mkdir(parents=True, exist_ok=True)
            print(f"[WasteWise-AI] Using local directory fallback: {local_fallback}")
            return f"sqlite:///{local_fallback}"
        except Exception:
            # Fallback to /tmp which is always writable in Linux containers
            tmp_fallback = Path("/tmp/wastewise.db")
            tmp_fallback.parent.mkdir(parents=True, exist_ok=True)
            print(f"[WasteWise-AI] Using /tmp fallback: {tmp_fallback}")
            return f"sqlite:///{tmp_fallback}"


db_url = get_effective_database_url(settings.DATABASE_URL)

engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all tables in the database with failover protection."""
    global engine, SessionLocal, db_url
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[WasteWise-AI] Database init failed with {db_url} ({e}). Retrying with /tmp fallback...")
        tmp_url = "sqlite:////tmp/wastewise.db"
        Path("/tmp").mkdir(parents=True, exist_ok=True)
        engine = create_engine(tmp_url, connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("[WasteWise-AI] Resilient database initialized at /tmp/wastewise.db successfully.")
