"""
Ordering Agent.
Converts demand forecasts minus current stock into recommended purchase/cooking quantities,
incorporating safety stock, shelf life constraints, and kitchen lead times.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.db.models import OrderRecommendation, InventoryItem, DailyForecast, AgentLog
from app.core.config import calibration_data


class OrderingAgent:
    def __init__(self):
        self.agent_name = "OrderingAgent"

    def compute_order_recommendation(
        self,
        food_class: str,
        forecast_portions: float,
        current_stock: float,
        lead_time_hours: float = 2.0,
        safety_stock_factor: float = 0.08
    ) -> Dict[str, Any]:
        """
        Calculates recommended order/prep portions.
        Safety stock covers demand spikes during lead time.
        """
        # Safety stock buffer
        safety_stock = round(forecast_portions * safety_stock_factor, 0)
        
        # Net requirement
        net_required = (forecast_portions + safety_stock) - current_stock
        
        # Batch rounding (canteen cooks in minimum pots/batches of 5 portions)
        if net_required <= 2.0:
            recommended = 0.0
        else:
            recommended = max(5.0, round(net_required / 5.0) * 5.0)

        rationale = (
            f"Recommended {int(recommended)} portions of {food_class}. "
            f"Forecast: {int(forecast_portions)}, Safety Stock: {int(safety_stock)} "
            f"({int(safety_stock_factor*100)}%), Usable Stock on hand: {int(current_stock)}. "
            f"Net demand: {net_required:.1f} rounded to 5-portion kitchen pot batches."
        )

        return {
            "food_class": food_class,
            "forecast_portions": forecast_portions,
            "current_stock": current_stock,
            "safety_stock": safety_stock,
            "recommended_portions": recommended,
            "lead_time_hours": lead_time_hours,
            "rationale": rationale
        }

    def run(
        self,
        db: Session,
        target_date: Optional[date] = None,
        meal_period: str = "lunch"
    ) -> List[Dict[str, Any]]:
        """
        Executes ordering cycle for all food items for the given meal period.
        """
        curr_date = target_date or date.today()
        date_str = curr_date.isoformat()
        food_classes = list(calibration_data.get("classes", {}).keys())
        results = []
        log_summaries = []

        for fc in food_classes:
            # Get latest forecast
            fcst = db.query(DailyForecast).filter(
                DailyForecast.forecast_date == date_str,
                DailyForecast.meal_period == meal_period,
                DailyForecast.food_class == fc
            ).first()

            forecast_val = fcst.forecast_portions if fcst else 100.0

            # Calculate current fresh stock on hand
            items = db.query(InventoryItem).filter(
                InventoryItem.food_class == fc,
                InventoryItem.status.in_(["fresh", "discounted"])
            ).all()
            usable_stock = sum(it.current_stock_portions for it in items)

            rec = self.compute_order_recommendation(
                food_class=fc,
                forecast_portions=forecast_val,
                current_stock=usable_stock
            )
            results.append(rec)

            if rec["recommended_portions"] > 0:
                log_summaries.append(f"{fc}: {int(rec['recommended_portions'])} portions")

            # Persist OrderRecommendation
            order_rec = OrderRecommendation(
                date=date_str,
                meal_period=meal_period,
                food_class=fc,
                recommended_portions=rec["recommended_portions"],
                safety_stock=rec["safety_stock"],
                current_stock=rec["current_stock"],
                lead_time_hours=rec["lead_time_hours"],
                status="pending"
            )
            db.add(order_rec)

        # Audit log
        summary_text = (
            f"Generated kitchen prep orders for {meal_period.title()} [{date_str}]. "
            + (", ".join(log_summaries[:4]) if log_summaries else "All items adequately stocked.")
        )
        audit_entry = AgentLog(
            agent_name=self.agent_name,
            action="GENERATE_ORDER_RECOMMENDATIONS",
            rationale=summary_text
        )
        db.add(audit_entry)
        db.commit()

        return results


ordering_agent = OrderingAgent()

