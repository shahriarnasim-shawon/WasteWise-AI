"""
Demand Forecast Agent.
Forecasts per-item portion demand per meal period (breakfast, lunch, snacks)
using historical consumption, day-of-week seasonality, weather flags, and event flags.
Generates point forecasts, 90% confidence intervals, and explainable rationale logs.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import math
from sqlalchemy.orm import Session

from app.db.models import DailyForecast, AgentLog
from app.core.config import calibration_data

# Base typical portions per meal period for a standard 500-seat university/office canteen
BASE_CONSUMPTION = {
    "breakfast": {
        "rice": 80.0,
        "dal": 70.0,
        "bhuna_khichuri": 140.0,
        "chicken_curry": 0.0,
        "fish_curry": 0.0,
        "vegetable": 90.0,
        "egg_curry": 120.0,
        "bhorta": 60.0
    },
    "lunch": {
        "rice": 380.0,
        "dal": 320.0,
        "bhuna_khichuri": 90.0,
        "chicken_curry": 220.0,
        "fish_curry": 160.0,
        "vegetable": 190.0,
        "egg_curry": 110.0,
        "bhorta": 150.0
    },
    "snacks": {
        "rice": 40.0,
        "dal": 30.0,
        "bhuna_khichuri": 160.0,
        "chicken_curry": 60.0,
        "fish_curry": 20.0,
        "vegetable": 50.0,
        "egg_curry": 80.0,
        "bhorta": 40.0
    }
}

# Bangladeshi canteen day-of-week factors (Sun-Thu normal, Fri prayer shift, Sat weekend/half-day)
DAY_FACTORS = {
    "Sunday": 1.05,     # Start of work week in Bangladesh
    "Monday": 1.00,
    "Tuesday": 1.00,
    "Wednesday": 0.98,
    "Thursday": 0.92,   # Pre-weekend tapering
    "Friday": 0.70,     # Juma prayer: reduced total attendance, but high demand for Khichuri & Chicken
    "Saturday": 0.60    # Half day / lighter traffic
}

# Weather impact modifiers
WEATHER_MODIFIERS = {
    "normal": {"all": 1.0},
    "rain": {"bhuna_khichuri": 1.35, "egg_curry": 1.15, "fish_curry": 1.10, "vegetable": 0.90},
    "heavy_rain": {"bhuna_khichuri": 1.50, "egg_curry": 1.25, "all": 0.85},
    "heatwave": {"rice": 0.90, "dal": 1.15, "vegetable": 1.10, "chicken_curry": 0.85}
}

# Institutional calendar events in Bangladesh
EVENT_MODIFIERS = {
    "regular_day": {"all": 1.0},
    "exam_day": {"all": 0.75, "snacks": 1.30},       # Quick snacks surge, sit-down lunch drops
    "friday_prayer": {"bhuna_khichuri": 1.40, "chicken_curry": 1.30, "lunch": 0.85},
    "holiday": {"all": 0.20}                          # University/office closed, only dorm skeleton
}


class DemandForecastAgent:
    def __init__(self):
        self.agent_name = "DemandForecastAgent"

    def forecast_item(
        self,
        food_class: str,
        meal_period: str = "lunch",
        target_date: Optional[date] = None,
        weather_flag: str = "normal",
        event_flag: str = "regular_day"
    ) -> Dict[str, Any]:
        """
        Calculates explainable point forecast and confidence interval for a single food item.
        """
        curr_date = target_date or date.today()
        day_name = curr_date.strftime("%A")

        base = BASE_CONSUMPTION.get(meal_period, {}).get(food_class, 100.0)
        day_factor = DAY_FACTORS.get(day_name, 1.00)

        # Weather multiplier
        weather_dict = WEATHER_MODIFIERS.get(weather_flag, {})
        weather_mult = weather_dict.get(food_class, weather_dict.get("all", 1.0))

        # Event multiplier
        event_dict = EVENT_MODIFIERS.get(event_flag, {})
        event_mult = event_dict.get(food_class, event_dict.get(meal_period, event_dict.get("all", 1.0)))

        # Point forecast with natural variability bounds
        point_forecast = round(base * day_factor * weather_mult * event_mult, 0)
        
        # Standard error / 90% confidence interval (approx +/- 12%)
        std_error = max(4.0, point_forecast * 0.12)
        lower_bound = max(0.0, round(point_forecast - 1.645 * std_error, 0))
        upper_bound = round(point_forecast + 1.645 * std_error, 0)

        rationale = (
            f"Forecasted {int(point_forecast)} portions of {food_class} for {meal_period.title()} on {day_name} "
            f"[{curr_date.isoformat()}]. Base: {int(base)}, Day factor ({day_name}): {day_factor:.2f}, "
            f"Weather ({weather_flag}): {weather_mult:.2f}x, Event ({event_flag}): {event_mult:.2f}x. "
            f"90% CI: [{int(lower_bound)}, {int(upper_bound)}]."
        )

        return {
            "forecast_date": curr_date.isoformat(),
            "meal_period": meal_period,
            "food_class": food_class,
            "forecast_portions": point_forecast,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "day_of_week": day_name,
            "weather_flag": weather_flag,
            "event_flag": event_flag,
            "rationale": rationale
        }

    def run(
        self,
        db: Session,
        target_date: Optional[date] = None,
        meal_period: str = "lunch",
        weather_flag: str = "normal",
        event_flag: str = "regular_day"
    ) -> List[Dict[str, Any]]:
        """
        Executes daily demand forecast across all active food classes and persists to DB.
        """
        food_classes = list(calibration_data.get("classes", {}).keys())
        results = []
        rationales = []

        for fc in food_classes:
            res = self.forecast_item(fc, meal_period, target_date, weather_flag, event_flag)
            results.append(res)
            rationales.append(f"{fc}: {int(res['forecast_portions'])} portions")

            # Persist or update DailyForecast
            existing = db.query(DailyForecast).filter(
                DailyForecast.forecast_date == res["forecast_date"],
                DailyForecast.meal_period == res["meal_period"],
                DailyForecast.food_class == res["food_class"]
            ).first()

            if existing:
                existing.forecast_portions = res["forecast_portions"]
                existing.lower_bound = res["lower_bound"]
                existing.upper_bound = res["upper_bound"]
                existing.weather_flag = res["weather_flag"]
                existing.event_flag = res["event_flag"]
            else:
                df = DailyForecast(
                    forecast_date=res["forecast_date"],
                    meal_period=res["meal_period"],
                    food_class=res["food_class"],
                    forecast_portions=res["forecast_portions"],
                    lower_bound=res["lower_bound"],
                    upper_bound=res["upper_bound"],
                    day_of_week=res["day_of_week"],
                    weather_flag=res["weather_flag"],
                    event_flag=res["event_flag"]
                )
                db.add(df)

        # Log to agent audit trail
        audit_entry = AgentLog(
            agent_name=self.agent_name,
            action="GENERATE_DAILY_FORECAST",
            rationale=f"Generated demand forecasts for {meal_period.title()} ({target_date or date.today()}): " + "; ".join(rationales[:4]) + "..."
        )
        db.add(audit_entry)
        db.commit()

        return results


demand_agent = DemandForecastAgent()

