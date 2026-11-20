"""
API Router for Predictive Agents & Orchestration.
Exposes forecasts, kitchen order recommendations, Today's Offers,
waste collection manifests, and explainable agent logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime

from app.db.session import get_db
from app.db.models import (
    DailyForecast, OrderRecommendation, DiscountOffer, 
    WasteBinState, WasteCollectionManifest, AgentLog, InventoryItem
)
from app.agents.orchestrator import orchestrator
from app.agents.waste_collection import waste_collection_agent

router = APIRouter(prefix="/agents", tags=["Predictive Agents"])


class OrderOverrideRequest(BaseModel):
    new_portions: float
    override_reason: str


class CycleTriggerRequest(BaseModel):
    meal_period: Optional[str] = "lunch"
    weather_flag: Optional[str] = "normal"
    event_flag: Optional[str] = "regular_day"


@router.get("/forecasts")
def get_forecasts(
    target_date: Optional[str] = None,
    meal_period: Optional[str] = "lunch",
    db: Session = Depends(get_db)
):
    """Retrieve demand forecasts for the specified date and meal period."""
    curr_date = target_date or date.today().isoformat()
    q = db.query(DailyForecast).filter(DailyForecast.forecast_date == curr_date)
    if meal_period:
        q = q.filter(DailyForecast.meal_period == meal_period)
    forecasts = q.all()
    return {"forecast_date": curr_date, "meal_period": meal_period, "forecasts": forecasts}


@router.get("/orders")
def get_orders(
    target_date: Optional[str] = None,
    meal_period: Optional[str] = "lunch",
    db: Session = Depends(get_db)
):
    """Retrieve kitchen order / prep recommendations."""
    curr_date = target_date or date.today().isoformat()
    orders = db.query(OrderRecommendation).filter(
        OrderRecommendation.date == curr_date,
        OrderRecommendation.meal_period == meal_period
    ).all()
    return {"date": curr_date, "orders": orders}


@router.post("/orders/{order_id}/accept")
def accept_order(order_id: int, db: Session = Depends(get_db)):
    """Approve a pending kitchen order recommendation."""
    order = db.query(OrderRecommendation).filter(OrderRecommendation.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order recommendation not found")
    order.status = "accepted"
    db.commit()
    return {"status": "accepted", "order_id": order_id}


@router.post("/orders/{order_id}/override")
def override_order(
    order_id: int, 
    payload: OrderOverrideRequest,
    db: Session = Depends(get_db)
):
    """Override an order recommendation with custom quantity and reason."""
    order = db.query(OrderRecommendation).filter(OrderRecommendation.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order recommendation not found")
    order.recommended_portions = payload.new_portions
    order.status = "overridden"
    order.override_reason = payload.override_reason
    db.commit()
    return {"status": "overridden", "order_id": order_id, "new_portions": payload.new_portions}


@router.get("/discounts")
def get_discounts(db: Session = Depends(get_db)):
    """Retrieve active dynamic discount offers for 'Today's Offers' board."""
    offers = db.query(DiscountOffer).filter(DiscountOffer.is_active == True).all()
    return {"offers": offers}


@router.get("/collection")
def get_collection_status(db: Session = Depends(get_db)):
    """Retrieve waste bin fill levels and recent pickup manifests."""
    bins = db.query(WasteBinState).all()
    manifests = db.query(WasteCollectionManifest).order_by(WasteCollectionManifest.timestamp.desc()).limit(15).all()
    return {"bins": bins, "recent_manifests": manifests}


@router.get("/collection/manifests/export_csv")
def export_manifests_csv(db: Session = Depends(get_db)):
    """Download collection manifests as CSV."""
    csv_content = waste_collection_agent.generate_manifest_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wastewise_collection_manifests.csv"}
    )


@router.get("/logs")
def get_agent_logs(
    limit: int = Query(30, ge=1, le=100),
    agent_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve recent explainable agent reasoning audit logs."""
    q = db.query(AgentLog).order_by(AgentLog.timestamp.desc())
    if agent_name:
        q = q.filter(AgentLog.agent_name == agent_name)
    logs = q.limit(limit).all()
    return {"logs": logs}


@router.post("/run_cycle")
def run_agent_cycle(
    payload: Optional[CycleTriggerRequest] = None,
    db: Session = Depends(get_db)
):
    """Triggers an end-to-end agent cycle via the Orchestrator."""
    p = payload or CycleTriggerRequest()
    summary = orchestrator.run_full_cycle(
        db,
        meal_period=p.meal_period or "lunch",
        weather_flag=p.weather_flag or "normal",
        event_flag=p.event_flag or "regular_day"
    )
    return summary

