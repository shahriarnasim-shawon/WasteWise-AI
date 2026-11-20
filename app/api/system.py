"""
System, Health, Model Status, and Configuration Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db, init_db, Base, engine
from app.inference.detector import detector
from app.core.config import settings, calibration_data
import app.db.models as db_models

router = APIRouter(tags=["System & Health"])


@router.get("/healthz")
def health_check():
    """Health check endpoint for Docker container and Render platform health probes."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "model_status": "mock" if detector.is_mock else "onnx_active"
    }


@router.get("/api/model/status")
def model_status():
    """Returns inference engine status, classes list, and mock mode indicators."""
    status = detector.get_status()
    status["calibration_loaded"] = bool(calibration_data)
    status["timestamp"] = datetime.utcnow().isoformat()
    return status


@router.get("/api/config/calibration")
def get_calibration():
    """Returns the current portion calibration, plate diameter reference, and bin configs."""
    return calibration_data


@router.post("/api/system/reset")
def reset_database(db: Session = Depends(get_db)):
    """Clears and re-creates database tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "reset_successful", "timestamp": datetime.utcnow().isoformat()}

