"""
Agent Orchestrator.
Coordinates the predictive agent suite, executes schedules & event triggers,
resolves policy conflicts, and logs centralized decision rationale.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.agents.demand_forecast import demand_agent
from app.agents.ordering import ordering_agent
from app.agents.dynamic_discount import discount_agent
from app.agents.waste_collection import waste_collection_agent
from app.db.models import AgentLog, OrderRecommendation, InventoryItem
from app.api.event_bus import event_bus


class AgentOrchestrator:
    def __init__(self):
        self.orchestrator_name = "AgentOrchestrator"

    def run_full_cycle(
        self,
        db: Session,
        target_date: Optional[date] = None,
        meal_period: str = "lunch",
        weather_flag: str = "normal",
        event_flag: str = "regular_day"
    ) -> Dict[str, Any]:
        """
        Executes a complete coordinated agent cycle:
        1. Demand Forecasting
        2. Order Recommendations
        3. Conflict Resolution (prevents cooking new batches if near-expiry stock exists)
        4. Dynamic Discounting for near-expiry batches
        5. Waste Collection & Routing
        """
        curr_date = target_date or date.today()
        start_time = datetime.utcnow()

        # Step 1: Demand Forecast
        forecasts = demand_agent.run(
            db, 
            target_date=curr_date, 
            meal_period=meal_period, 
            weather_flag=weather_flag, 
            event_flag=event_flag
        )

        # Step 2: Kitchen Ordering
        orders = ordering_agent.run(
            db, 
            target_date=curr_date, 
            meal_period=meal_period
        )

        # Step 3: Conflict Resolution
        # If an item currently has discounted surplus expiring soon, reduce/suppress new order recommendations
        discounted_items = db.query(InventoryItem).filter(
            InventoryItem.status == "discounted",
            InventoryItem.current_stock_portions > 15.0
        ).all()
        discounted_classes = {it.food_class: it.current_stock_portions for it in discounted_items}

        conflicts_resolved = 0
        if discounted_classes:
            pending_orders = db.query(OrderRecommendation).filter(
                OrderRecommendation.date == curr_date.isoformat(),
                OrderRecommendation.meal_period == meal_period,
                OrderRecommendation.status == "pending"
            ).all()

            for order in pending_orders:
                if order.food_class in discounted_classes:
                    surplus_qty = discounted_classes[order.food_class]
                    old_qty = order.recommended_portions
                    new_qty = max(0.0, round(old_qty - surplus_qty, 0))
                    if new_qty != old_qty:
                        order.recommended_portions = new_qty
                        order.override_reason = (
                            f"Orchestrator conflict resolution: reduced order by {int(surplus_qty)} portions "
                            f"to prioritize clearance of existing discounted surplus."
                        )
                        conflicts_resolved += 1

            if conflicts_resolved > 0:
                audit = AgentLog(
                    agent_name=self.orchestrator_name,
                    action="RESOLVE_ORDER_SURPLUS_CONFLICT",
                    rationale=f"Resolved {conflicts_resolved} kitchen prep conflicts: downscaled orders to prevent cannibalizing near-expiry discounted stock."
                )
                db.add(audit)
                db.commit()

        # Step 4: Dynamic Discounting
        discounts = discount_agent.run(db)

        # Step 5: Waste Collection & Routing
        manifests = waste_collection_agent.check_bins_and_schedule(db)

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        cycle_summary = {
            "cycle_timestamp": start_time.isoformat(),
            "meal_period": meal_period,
            "target_date": curr_date.isoformat(),
            "forecasts_count": len(forecasts),
            "orders_count": len(orders),
            "conflicts_resolved": conflicts_resolved,
            "discounts_applied": len(discounts),
            "manifests_scheduled": len(manifests),
            "duration_seconds": round(elapsed, 2)
        }

        # Broadcast orchestrator cycle completion
        event_bus.publish_sync("orchestrator_cycle_completed", cycle_summary)

        return cycle_summary


orchestrator = AgentOrchestrator()

