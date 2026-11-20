"""
WasteWiseAI Database Seeding Script.
Generates 3 weeks of realistic historical canteen waste events, inventory batches,
demand forecasts, dynamic discount offers, waste manifests, and agent audit logs.
"""

from datetime import datetime, timedelta, date
import random
from app.db.session import SessionLocal, init_db
from app.db.models import (
    WasteEvent, InventoryItem, DailyForecast, OrderRecommendation,
    DiscountOffer, WasteBinState, WasteCollectionManifest, AgentLog
)
from app.core.config import calibration_data

FOODS = ["rice", "dal", "bhuna_khichuri", "chicken_curry", "fish_curry", "vegetable", "egg_curry", "bhorta"]
MEALS = ["breakfast", "lunch", "snacks"]


def seed_database():
    print("[INFO] Initializing database schema...")
    init_db()
    db = SessionLocal()

    print("[INFO] Seeding waste bin categories...")
    for cat, cfg in calibration_data.get("waste_bins", {}).items():
        existing = db.query(WasteBinState).filter(WasteBinState.category == cat).first()
        if not existing:
            wb = WasteBinState(
                category=cat,
                name_en=cfg.get("name_en", cat),
                name_bn=cfg.get("name_bn", cat),
                capacity_kg=cfg.get("capacity_kg", 40.0),
                current_weight_kg=round(random.uniform(12.0, 32.0), 1),
                fill_percentage=0.0,
                destination=cfg.get("destination", "Recycling"),
                status="normal"
            )
            wb.fill_percentage = round((wb.current_weight_kg / wb.capacity_kg) * 100.0, 1)
            if wb.fill_percentage >= 80.0:
                wb.status = "pickup_scheduled"
            db.add(wb)
    db.commit()

    print("[INFO] Seeding 21 days of historical waste events & forecasts...")
    now = datetime.utcnow()
    for day_offset in range(21, 0, -1):
        hist_date = (now - timedelta(days=day_offset)).date()
        date_str = hist_date.isoformat()
        day_name = hist_date.strftime("%A")

        is_rain = random.random() < 0.25
        is_friday = day_name == "Friday"
        weather_flag = "rain" if is_rain else "normal"
        event_flag = "friday_prayer" if is_friday else "regular_day"

        # Forecasts
        for meal in MEALS:
            for f in FOODS:
                base = 120.0 if meal == "lunch" else 50.0
                if f in ["rice", "dal"] and meal == "lunch":
                    base = 350.0
                elif f == "bhuna_khichuri" and is_rain:
                    base = 220.0

                df = DailyForecast(
                    forecast_date=date_str,
                    meal_period=meal,
                    food_class=f,
                    forecast_portions=round(base * (1.1 if is_friday and f == "chicken_curry" else 1.0), 0),
                    lower_bound=round(base * 0.85, 0),
                    upper_bound=round(base * 1.15, 0),
                    actual_consumed=round(base * random.uniform(0.90, 1.05), 0),
                    day_of_week=day_name,
                    weather_flag=weather_flag,
                    event_flag=event_flag,
                    created_at=now - timedelta(days=day_offset)
                )
                db.add(df)

        # Waste Events (dish return scans)
        for _ in range(random.randint(15, 25)):
            dish = random.choice(FOODS)
            is_clean = random.random() < 0.72  # 72% clean plate rate
            if is_clean:
                p_state = "empty_plate"
                grams = 0.0
                cost = 0.0
            else:
                p_state = "partial_leftover"
                grams = round(random.uniform(25.0, 140.0), 1)
                cost = round(grams * 0.15, 1)

            we = WasteEvent(
                timestamp=now - timedelta(days=day_offset, hours=random.randint(1, 10)),
                station_id="station-dish-return-1",
                meal_period=random.choice(MEALS),
                food_class=dish if not is_clean else "none",
                estimated_grams=grams,
                cost_value_bdt=cost,
                sales_value_bdt=cost * 1.6,
                plate_state=p_state,
                coverage_ratio=0.0 if is_clean else round(random.uniform(0.10, 0.45), 2),
                confidence=round(random.uniform(0.82, 0.95), 2),
                waste_category="animal_feed" if dish in ["rice", "bhuna_khichuri"] else "compost",
                is_mock=True
            )
            db.add(we)

    db.commit()

    print("[INFO] Seeding active hot-counter batches & dynamic discounts...")
    batches = [
        ("BATCH-KC-204", "bhuna_khichuri", "lunch", 60.0, 32.0, 40.0, 80.0, 0.8, 3, 35.0, "discounted"),
        ("BATCH-RC-108", "rice", "lunch", 120.0, 65.0, 20.0, 35.0, 1.4, 2, 20.0, "discounted"),
        ("BATCH-CC-302", "chicken_curry", "lunch", 80.0, 45.0, 70.0, 130.0, 2.1, 0, 0.0, "fresh"),
        ("BATCH-FC-401", "fish_curry", "lunch", 50.0, 28.0, 60.0, 110.0, 2.3, 0, 0.0, "fresh"),
        ("BATCH-VG-505", "vegetable", "lunch", 70.0, 50.0, 18.0, 30.0, 3.6, 0, 0.0, "fresh"),
    ]

    for b_id, fc, meal, init_stk, curr_stk, cost, price, hrs_left, tier, disc_pct, stat in batches:
        existing_item = db.query(InventoryItem).filter(InventoryItem.batch_id == b_id).first()
        if existing_item:
            continue

        item = InventoryItem(
            batch_id=b_id,
            food_class=fc,
            meal_period=meal,
            initial_stock_portions=init_stk,
            current_stock_portions=curr_stk,
            unit_cost_bdt=cost,
            selling_price_bdt=price,
            prepared_at=now - timedelta(hours=4.0 - hrs_left),
            expiry_at=now + timedelta(hours=hrs_left),
            discount_tier=tier,
            discount_percent=disc_pct,
            status=stat
        )
        db.add(item)
        db.flush()

        if tier > 0:
            disc_price = max(cost * 1.05, round(price * (1.0 - disc_pct / 100.0), 1))
            offer = DiscountOffer(
                inventory_item_id=item.id,
                food_class=fc,
                discount_tier=tier,
                discount_percent=disc_pct,
                original_price_bdt=price,
                discounted_price_bdt=disc_price,
                reason=f"Near expiry: {hrs_left}h remaining with {int(curr_stk)} portions unsold.",
                active_until=item.expiry_at,
                is_active=True
            )
            db.add(offer)

    print("[INFO] Seeding collection manifests and agent audit logs...")
    manifests_seed = [
        ("WW-EDIB-20261115-001", "edible_surplus", 18.5, "Mirpur Community Food Bank", "scheduled", "Untouched trays sealed in insulated cambros."),
        ("WW-COMP-20261115-002", "compost", 30.0, "Campus Organic Compost Unit", "completed", "Vegetable prep peelings & lentil residue."),
        ("WW-ANIM-20261114-004", "animal_feed", 34.2, "Savar Poultry Cooperative", "completed", "Clean plate scrape rice & grain feed."),
    ]
    for code, cat, wt, dest, stat, notes in manifests_seed:
        existing_m = db.query(WasteCollectionManifest).filter(WasteCollectionManifest.manifest_code == code).first()
        if existing_m:
            continue

        m = WasteCollectionManifest(
            manifest_code=code,
            timestamp=now - timedelta(hours=random.randint(2, 28)),
            category=cat,
            total_kg=wt,
            destination=dest,
            status=stat,
            notes=notes
        )
        db.add(m)

    audit_logs_seed = [
        ("DynamicDiscountAgent", "PUBLISH_DYNAMIC_DISCOUNT", "Applied Tier 3 (35% off) to Bhuna Khichuri [Batch BATCH-KC-204]. Original: 80.0 BDT, New: 52.0 BDT. Rationale: 0.8h remaining before lunch service closure."),
        ("AgentOrchestrator", "RESOLVE_ORDER_SURPLUS_CONFLICT", "Downscaled kitchen orders by 32 portions of Khichuri to prioritize clearance of existing discounted surplus."),
        ("WasteCollectionAgent", "SCHEDULE_WASTE_PICKUP", "Dispatched manifest WW-COMP-20261115-002 for Organic Compost. Bin fill reached 85.7%."),
        ("DemandForecastAgent", "GENERATE_DAILY_FORECAST", "Forecasted 165 portions of Bhuna Khichuri for Lunch on Friday. Applied weather (rain) modifier +35% and Friday prayer shift."),
    ]
    for agent, action, rat in audit_logs_seed:
        al = AgentLog(
            timestamp=now - timedelta(minutes=random.randint(5, 120)),
            agent_name=agent,
            action=action,
            rationale=rat
        )
        db.add(al)

    db.commit()
    db.close()
    print("[SUCCESS] Historical database successfully seeded!")


if __name__ == "__main__":
    seed_database()
