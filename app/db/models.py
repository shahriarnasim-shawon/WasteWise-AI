"""
SQLAlchemy ORM models for WasteWiseAI.
Includes waste events, inventory items, forecasts, order recommendations,
discount offers, waste manifests, and agent rationale logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class WasteEvent(Base):
    """Recorded food waste detection event from dishes or trays."""
    __tablename__ = "waste_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    station_id = Column(String(64), default="station-dish-return-1", index=True)
    meal_period = Column(String(32), default="lunch", index=True)  # breakfast, lunch, snacks, dinner
    food_class = Column(String(64), index=True)
    estimated_grams = Column(Float, nullable=False, default=0.0)
    cost_value_bdt = Column(Float, nullable=False, default=0.0)
    sales_value_bdt = Column(Float, nullable=False, default=0.0)
    plate_state = Column(String(32), default="partial_leftover", index=True)  # empty_plate, partial_leftover, full_plate
    coverage_ratio = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    waste_category = Column(String(32), default="general")  # edible_surplus, animal_feed, compost, general
    image_ref = Column(String(255), nullable=True)
    is_mock = Column(Boolean, default=True)


class InventoryItem(Base):
    """Current prepared canteen dishes and batch shelf-life tracking."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    food_class = Column(String(64), index=True, nullable=False)
    batch_id = Column(String(64), unique=True, index=True, nullable=False)
    meal_period = Column(String(32), default="lunch")
    initial_stock_portions = Column(Float, nullable=False)
    current_stock_portions = Column(Float, nullable=False)
    unit_cost_bdt = Column(Float, nullable=False)
    selling_price_bdt = Column(Float, nullable=False)
    prepared_at = Column(DateTime, default=datetime.utcnow)
    expiry_at = Column(DateTime, nullable=False, index=True)
    discount_tier = Column(Integer, default=0)       # 0=0%, 1=10%, 2=20%, 3=35%, 4=50%
    discount_percent = Column(Float, default=0.0)
    status = Column(String(32), default="fresh")     # fresh, discounted, expired, depleted


class DailyForecast(Base):
    """Predictive demand forecasts generated per meal period and food dish."""
    __tablename__ = "daily_forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    meal_period = Column(String(32), index=True, nullable=False)
    food_class = Column(String(64), index=True, nullable=False)
    forecast_portions = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    actual_consumed = Column(Float, nullable=True)
    day_of_week = Column(String(16))
    weather_flag = Column(String(32), default="normal")     # normal, rain, heavy_rain, heatwave
    event_flag = Column(String(32), default="regular_day")  # regular_day, exam_day, friday_prayer, holiday
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderRecommendation(Base):
    """Agent purchase/prep recommendations based on forecast minus stock."""
    __tablename__ = "order_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(10), index=True, nullable=False)
    meal_period = Column(String(32), index=True, nullable=False)
    food_class = Column(String(64), index=True, nullable=False)
    recommended_portions = Column(Float, nullable=False)
    safety_stock = Column(Float, default=0.0)
    current_stock = Column(Float, default=0.0)
    lead_time_hours = Column(Float, default=2.0)
    status = Column(String(32), default="pending")  # pending, accepted, overridden
    override_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DiscountOffer(Base):
    """Automated dynamic discounts published to Today's Offers board."""
    __tablename__ = "discount_offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    food_class = Column(String(64), index=True, nullable=False)
    discount_tier = Column(Integer, default=1)
    discount_percent = Column(Float, nullable=False)
    original_price_bdt = Column(Float, nullable=False)
    discounted_price_bdt = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    active_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WasteBinState(Base):
    """Real-time tracking of waste bin fill levels (derived from detected grams)."""
    __tablename__ = "waste_bin_states"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(32), unique=True, index=True, nullable=False)  # edible_surplus, animal_feed, compost, general
    name_en = Column(String(64))
    name_bn = Column(String(64))
    capacity_kg = Column(Float, nullable=False)
    current_weight_kg = Column(Float, default=0.0)
    fill_percentage = Column(Float, default=0.0)
    destination = Column(String(128))
    last_pickup_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="normal")  # normal, nearing_capacity, pickup_scheduled


class WasteCollectionManifest(Base):
    """Collection manifests for scheduled pickups / surplus donations."""
    __tablename__ = "waste_collection_manifests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    manifest_code = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    category = Column(String(32), index=True, nullable=False)
    total_kg = Column(Float, nullable=False)
    destination = Column(String(128), nullable=False)
    status = Column(String(32), default="scheduled")  # scheduled, in_transit, completed
    notes = Column(Text, nullable=True)


class AgentLog(Base):
    """Agent explainability audit log showing inputs, outputs, and reasoning."""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_name = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False)
    rationale = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

