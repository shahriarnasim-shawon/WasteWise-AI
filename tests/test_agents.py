"""
Unit tests for WasteWiseAI Predictive Agents.
Verifies demand forecasting, safety stock ordering, dynamic discounting guardrails,
waste collection routing, and orchestrator conflict resolution.
"""

import pytest
from datetime import datetime, timedelta, date
from app.db.session import SessionLocal, init_db
from app.db.models import InventoryItem, WasteBinState
from app.agents.demand_forecast import demand_agent
from app.agents.ordering import ordering_agent
from app.agents.dynamic_discount import discount_agent
from app.agents.waste_collection import waste_collection_agent
from app.agents.orchestrator import orchestrator


@pytest.fixture
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_demand_forecast_agent_rain_modifier():
    """Verify DemandForecastAgent adjusts khichuri demand during rain."""
    res_normal = demand_agent.forecast_item("bhuna_khichuri", "lunch", weather_flag="normal")
    res_rain = demand_agent.forecast_item("bhuna_khichuri", "lunch", weather_flag="rain")
    assert res_rain["forecast_portions"] > res_normal["forecast_portions"]
    assert res_rain["lower_bound"] < res_rain["forecast_portions"] < res_rain["upper_bound"]
    assert "Weather (rain)" in res_rain["rationale"]


def test_ordering_agent_calculation():
    """Verify OrderingAgent correctly subtracts stock on hand and adds safety stock."""
    # Forecast 200, current stock 50, safety stock ~16 (8%)
    res = ordering_agent.compute_order_recommendation(
        food_class="rice",
        forecast_portions=200.0,
        current_stock=50.0,
        safety_stock_factor=0.08
    )
    # Net demand = (200 + 16) - 50 = 166 -> rounded to 5-portion batch = 165
    assert res["recommended_portions"] >= 160.0
    assert res["safety_stock"] == 16.0
    assert res["food_class"] == "rice"


import uuid

def test_dynamic_discount_floor_price_guardrail(db):
    """Verify DynamicDiscountAgent enforces floor price and prevents selling below cost."""
    now = datetime.utcnow()
    item = InventoryItem(
        food_class="chicken_curry",
        batch_id=f"TEST-CC-{uuid.uuid4().hex[:6]}",
        meal_period="lunch",
        initial_stock_portions=40.0,
        current_stock_portions=30.0,
        unit_cost_bdt=70.0,
        selling_price_bdt=130.0,
        prepared_at=now - timedelta(hours=3),
        expiry_at=now + timedelta(minutes=30),  # Under 45m -> Tier 4 (50% off)
        status="fresh"
    )
    db.add(item)
    db.commit()

    eval_res = discount_agent.evaluate_item_discount(item, current_time=now)
    assert eval_res is not None
    assert eval_res["discount_tier"] == 4
    # 50% of 130 is 65, but floor price is 75.0 (cost + 5BDT)
    # The agent MUST enforce floor price 75.0!
    assert eval_res["discounted_price_bdt"] >= 75.0


def test_waste_collection_manifest_generation(db):
    """Verify WasteCollectionAgent triggers manifest when bin fill reaches threshold."""
    # Force a bin past 80% threshold
    bin_state = db.query(WasteBinState).filter(WasteBinState.category == "compost").first()
    if not bin_state:
        bin_state = WasteBinState(
            category="compost",
            name_en="Organic Compost",
            capacity_kg=35.0,
            current_weight_kg=30.0,
            fill_percentage=85.7,
            destination="Campus Compost Unit",
            status="normal"
        )
        db.add(bin_state)
    else:
        bin_state.current_weight_kg = 30.0
        bin_state.fill_percentage = 85.7
    db.commit()

    manifests = waste_collection_agent.check_bins_and_schedule(db)
    assert len(manifests) >= 1
    assert any(m["category"] == "compost" for m in manifests)
    # Check that bin was reset
    db.refresh(bin_state)
    assert bin_state.fill_percentage == 0.0


def test_orchestrator_full_cycle(db):
    """Verify orchestrator runs all 4 agents in sequence without error."""
    summary = orchestrator.run_full_cycle(db, meal_period="lunch", weather_flag="normal")
    assert summary["forecasts_count"] > 0
    assert summary["orders_count"] > 0
    assert "duration_seconds" in summary
