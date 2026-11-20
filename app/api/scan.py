"""
Real-time Ingestion Layer API.
Handles camera frame uploads, webcam streams, demo plate replay,
WasteEvent persistence, bin fill-level updates, and live event broadcasting.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel
import base64
import time

from app.db.session import get_db
from app.db.models import WasteEvent, WasteBinState
from app.inference.detector import detector
from app.api.event_bus import event_bus
from app.core.config import calibration_data

router = APIRouter(prefix="/scan", tags=["Live Scan & Ingestion"])

SAMPLE_PLATES_DIR = Path(__file__).resolve().parent.parent.parent / "demo" / "sample_plates"


class Base64ScanRequest(BaseModel):
    image_base64: str
    station_id: Optional[str] = "station-dish-return-1"
    meal_period: Optional[str] = "lunch"
    image_name: Optional[str] = None
    persist: Optional[bool] = True


def _update_waste_bins(db: Session, waste_category: str, grams: float):
    """Accumulates detected waste grams into the corresponding bin state."""
    bin_state = db.query(WasteBinState).filter(WasteBinState.category == waste_category).first()
    if not bin_state:
        # Check if already staged in current session
        for obj in db.new:
            if isinstance(obj, WasteBinState) and obj.category == waste_category:
                bin_state = obj
                break

    if not bin_state:
        # initialize from calibration
        bin_cfg = calibration_data.get("waste_bins", {}).get(waste_category, {})
        bin_state = WasteBinState(
            category=waste_category,
            name_en=bin_cfg.get("name_en", waste_category),
            name_bn=bin_cfg.get("name_bn", waste_category),
            capacity_kg=bin_cfg.get("capacity_kg", 40.0),
            current_weight_kg=0.0,
            fill_percentage=0.0,
            destination=bin_cfg.get("destination", "Municipal Recycling"),
            status="normal"
        )
        db.add(bin_state)
        db.flush()

    kg_added = grams / 1000.0
    bin_state.current_weight_kg = round(bin_state.current_weight_kg + kg_added, 2)
    bin_state.fill_percentage = round(min(100.0, (bin_state.current_weight_kg / max(bin_state.capacity_kg, 1.0)) * 100.0), 1)
    
    thresh = calibration_data.get("waste_bins", {}).get(waste_category, {}).get("pickup_threshold_ratio", 0.80) * 100.0
    if bin_state.fill_percentage >= thresh:
        bin_state.status = "pickup_scheduled"
    elif bin_state.fill_percentage >= 65.0:
        bin_state.status = "nearing_capacity"
    else:
        bin_state.status = "normal"


@router.post("/frame")
async def scan_frame(
    file: Optional[UploadFile] = File(None),
    station_id: str = Form("station-dish-return-1"),
    meal_period: str = Form("lunch"),
    db: Session = Depends(get_db)
):
    """
    Ingest a raw dish/tray image frame from webcam or uploaded file.
    Runs ONNX/Mock detector, calculates leftover grams, updates database & bins,
    and broadcasts WasteEvent over live event bus.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="No image file provided")

    image_bytes = await file.read()
    detection_res = detector.detect(image_bytes, image_name=file.filename)

    if not detection_res.get("success"):
        raise HTTPException(status_code=400, detail=detection_res.get("error", "Detection failed"))

    # Record WasteEvents in DB
    boxes = detection_res.get("boxes", [])
    plate_state = detection_res.get("plate_state", "empty_plate")

    if len(boxes) == 0:
        # Record empty plate scan event
        evt = WasteEvent(
            station_id=station_id,
            meal_period=meal_period,
            food_class="none",
            estimated_grams=0.0,
            cost_value_bdt=0.0,
            sales_value_bdt=0.0,
            plate_state=plate_state,
            coverage_ratio=detection_res.get("coverage_ratio", 0.0),
            confidence=1.0,
            waste_category="none",
            is_mock=detection_res.get("is_mock", True)
        )
        db.add(evt)
    else:
        for b in boxes:
            evt = WasteEvent(
                station_id=station_id,
                meal_period=meal_period,
                food_class=b["food_class"],
                estimated_grams=b["estimated_grams"],
                cost_value_bdt=b["cost_value_bdt"],
                sales_value_bdt=b["sales_value_bdt"],
                plate_state=plate_state,
                coverage_ratio=detection_res.get("coverage_ratio", 0.0),
                confidence=b["confidence"],
                waste_category=b["waste_category"],
                is_mock=detection_res.get("is_mock", True)
            )
            db.add(evt)
            _update_waste_bins(db, b["waste_category"], b["estimated_grams"])

    db.commit()

    # Broadcast to live UI
    payload = {
        "station_id": station_id,
        "meal_period": meal_period,
        "plate_state": plate_state,
        "total_leftover_grams": detection_res["total_leftover_grams"],
        "total_cost_bdt": detection_res["total_cost_bdt"],
        "coverage_ratio": detection_res["coverage_ratio"],
        "boxes": boxes,
        "inference_time_ms": detection_res["inference_time_ms"],
        "is_mock": detection_res["is_mock"]
    }
    await event_bus.publish("new_scan", payload)

    return detection_res


@router.post("/frame_base64")
async def scan_frame_base64(
    payload: Base64ScanRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a base64-encoded webcam frame. Throttled from frontend.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        image_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {str(e)}")

    detection_res = detector.detect(image_bytes, image_name=payload.image_name)

    if not detection_res.get("success"):
        raise HTTPException(status_code=400, detail=detection_res.get("error", "Detection failed"))

    boxes = detection_res.get("boxes", [])
    plate_state = detection_res.get("plate_state", "empty_plate")

    if payload.persist:
        if len(boxes) == 0:
            evt = WasteEvent(
                station_id=payload.station_id,
                meal_period=payload.meal_period,
                food_class="none",
                estimated_grams=0.0,
                cost_value_bdt=0.0,
                sales_value_bdt=0.0,
                plate_state=plate_state,
                coverage_ratio=detection_res.get("coverage_ratio", 0.0),
                confidence=1.0,
                waste_category="none",
                is_mock=detection_res.get("is_mock", True)
            )
            db.add(evt)
        else:
            for b in boxes:
                evt = WasteEvent(
                    station_id=payload.station_id,
                    meal_period=payload.meal_period,
                    food_class=b["food_class"],
                    estimated_grams=b["estimated_grams"],
                    cost_value_bdt=b["cost_value_bdt"],
                    sales_value_bdt=b["sales_value_bdt"],
                    plate_state=plate_state,
                    coverage_ratio=detection_res.get("coverage_ratio", 0.0),
                    confidence=b["confidence"],
                    waste_category=b["waste_category"],
                    is_mock=detection_res.get("is_mock", True)
                )
                db.add(evt)
                _update_waste_bins(db, b["waste_category"], b["estimated_grams"])

        db.commit()

        broadcast_data = {
            "station_id": payload.station_id,
            "meal_period": payload.meal_period,
            "plate_state": plate_state,
            "total_leftover_grams": detection_res["total_leftover_grams"],
            "total_cost_bdt": detection_res["total_cost_bdt"],
            "coverage_ratio": detection_res["coverage_ratio"],
            "boxes": boxes,
            "inference_time_ms": detection_res["inference_time_ms"],
            "is_mock": detection_res["is_mock"]
        }
        await event_bus.publish("new_scan", broadcast_data)

    return detection_res


@router.get("/replay/frames")
def list_replay_frames():
    """Returns the list of generated sample plate images available for demo replay."""
    frames = []
    if SAMPLE_PLATES_DIR.exists():
        files = sorted(list(SAMPLE_PLATES_DIR.glob("*.jpg")))
        for idx, f in enumerate(files):
            frames.append({
                "index": idx,
                "filename": f.name,
                "title": f.stem.replace("_", " ").title()
            })
    return {"frames": frames}


@router.post("/replay/step")
async def replay_step(
    frame_index: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Replay a specific demo frame by index (0-4), run detection, persist,
    and broadcast live event to the dashboard.
    """
    if not SAMPLE_PLATES_DIR.exists():
        raise HTTPException(status_code=404, detail="Sample plates directory missing")

    files = sorted(list(SAMPLE_PLATES_DIR.glob("*.jpg")))
    if not files:
        raise HTTPException(status_code=404, detail="No sample plate images found")

    target_file = files[frame_index % len(files)]
    image_bytes = target_file.read_bytes()
    detection_res = detector.detect(image_bytes, image_name=target_file.name)

    boxes = detection_res.get("boxes", [])
    plate_state = detection_res.get("plate_state", "empty_plate")

    for b in boxes:
        evt = WasteEvent(
            station_id="station-demo-replay",
            meal_period="lunch",
            food_class=b["food_class"],
            estimated_grams=b["estimated_grams"],
            cost_value_bdt=b["cost_value_bdt"],
            sales_value_bdt=b["sales_value_bdt"],
            plate_state=plate_state,
            coverage_ratio=detection_res.get("coverage_ratio", 0.0),
            confidence=b["confidence"],
            waste_category=b["waste_category"],
            is_mock=detection_res.get("is_mock", True)
        )
        db.add(evt)
        _update_waste_bins(db, b["waste_category"], b["estimated_grams"])

    db.commit()

    # Read base64 to allow frontend demo rendering
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    detection_res["image_base64"] = f"data:image/jpeg;base64,{b64_img}"
    detection_res["frame_filename"] = target_file.name

    broadcast_data = {
        "station_id": "station-demo-replay",
        "meal_period": "lunch",
        "plate_state": plate_state,
        "total_leftover_grams": detection_res["total_leftover_grams"],
        "total_cost_bdt": detection_res["total_cost_bdt"],
        "coverage_ratio": detection_res["coverage_ratio"],
        "boxes": boxes,
        "inference_time_ms": detection_res["inference_time_ms"],
        "is_mock": detection_res["is_mock"],
        "frame_index": frame_index
    }
    await event_bus.publish("new_scan", broadcast_data)

    return detection_res
