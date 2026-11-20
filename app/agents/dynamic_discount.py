"""
Dynamic Discount Agent.
Calculates dynamic discount tiers (10%, 20%, 35%, 50%) for near-expiry prepared canteen dishes
based on remaining shelf life, unsold batch stock, and current sell-through velocity.
Enforces strict unit-cost floor price guardrails and auto-publishes to Today's Offers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db.models import InventoryItem, DiscountOffer, AgentLog
from app.api.event_bus import event_bus
from app.core.config import calibration_data

DISCOUNT_TIERS = {
    0: {"percent": 0.0, "name": "Standard"},
    1: {"percent": 10.0, "name": "Early Bird / Gentle Clearance"},
    2: {"percent": 20.0, "name": "Afternoon Rush Clearance"},
    3: {"percent": 35.0, "name": "Urgent Pre-Expiry Flash Offer"},
    4: {"percent": 50.0, "name": "Final Call Flash Sale"}
}


class DynamicDiscountAgent:
    def __init__(self):
        self.agent_name = "DynamicDiscountAgent"

    def evaluate_item_discount(
        self,
        item: InventoryItem,
        current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a single inventory item batch and computes appropriate discount tier.
        """
        now = current_time or datetime.utcnow()
        if item.status in ["expired", "depleted"] or item.current_stock_portions <= 0:
            return None

        # Remaining shelf life
        time_left = item.expiry_at - now
        hours_left = time_left.total_seconds() / 3600.0

        if hours_left <= 0:
            # Batch has expired
            item.status = "expired"
            return None

        class_cfg = calibration_data.get("classes", {}).get(item.food_class, {})
        original_price = item.selling_price_bdt
        floor_price = class_cfg.get("floor_price_bdt", item.unit_cost_bdt * 1.05)

        # Determine discount tier based on remaining time and stock pressure
        tier = 0
        reason = ""

        if hours_left < 0.75:  # Under 45 minutes remaining
            tier = 4
            reason = f"Critical expiry alert: only {int(hours_left*60)}m shelf life remaining with {int(item.current_stock_portions)} portions unsold."
        elif hours_left < 1.5:  # Under 90 minutes
            tier = 3
            reason = f"Near expiry: {hours_left:.1f}h remaining. High leftover risk for batch {item.batch_id}."
        elif hours_left < 2.5 and item.current_stock_portions >= 20.0:
            tier = 2
            reason = f"Surplus clearance: {int(item.current_stock_portions)} portions remaining with {hours_left:.1f}h before expiry."
        elif hours_left < 3.0 and item.current_stock_portions >= 35.0:
            tier = 1
            reason = f"Mild velocity lag: stock ({int(item.current_stock_portions)}) exceeds consumption rate."

        if tier == 0:
            return None

        discount_percent = DISCOUNT_TIERS[tier]["percent"]
        raw_discounted_price = original_price * (1.0 - discount_percent / 100.0)

        # Enforce floor price guardrail
        final_discounted_price = round(max(floor_price, raw_discounted_price), 2)
        effective_discount_pct = round(((original_price - final_discounted_price) / original_price) * 100.0, 1)

        rationale = (
            f"Applied Tier {tier} ({effective_discount_pct}% off) to {class_cfg.get('name_en', item.food_class)} "
            f"[Batch {item.batch_id}]. Original: {original_price:.1f} BDT, New: {final_discounted_price:.1f} BDT "
            f"(Floor Guardrail: {floor_price:.1f} BDT). Rationale: {reason}"
        )

        return {
            "inventory_item_id": item.id,
            "food_class": item.food_class,
            "batch_id": item.batch_id,
            "discount_tier": tier,
            "discount_percent": effective_discount_pct,
            "original_price_bdt": original_price,
            "discounted_price_bdt": final_discounted_price,
            "floor_price_bdt": floor_price,
            "reason": reason,
            "active_until": item.expiry_at,
            "rationale": rationale
        }

    def run(
        self,
        db: Session,
        current_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans all active inventory items and updates Today's Offers.
        """
        now = current_time or datetime.utcnow()
        items = db.query(InventoryItem).filter(
            InventoryItem.status.in_(["fresh", "discounted"])
        ).all()

        offers_created = []

        for item in items:
            eval_res = self.evaluate_item_discount(item, now)
            if eval_res:
                # Update item state
                item.discount_tier = eval_res["discount_tier"]
                item.discount_percent = eval_res["discount_percent"]
                item.status = "discounted"

                # Check existing offer
                offer = db.query(DiscountOffer).filter(
                    DiscountOffer.inventory_item_id == item.id,
                    DiscountOffer.is_active == True
                ).first()

                if offer:
                    offer.discount_tier = eval_res["discount_tier"]
                    offer.discount_percent = eval_res["discount_percent"]
                    offer.discounted_price_bdt = eval_res["discounted_price_bdt"]
                    offer.reason = eval_res["reason"]
                    offer.active_until = eval_res["active_until"]
                else:
                    offer = DiscountOffer(
                        inventory_item_id=item.id,
                        food_class=item.food_class,
                        discount_tier=eval_res["discount_tier"],
                        discount_percent=eval_res["discount_percent"],
                        original_price_bdt=eval_res["original_price_bdt"],
                        discounted_price_bdt=eval_res["discounted_price_bdt"],
                        reason=eval_res["reason"],
                        active_until=eval_res["active_until"],
                        is_active=True
                    )
                    db.add(offer)

                # Log explainable action
                audit = AgentLog(
                    agent_name=self.agent_name,
                    action="PUBLISH_DYNAMIC_DISCOUNT",
                    rationale=eval_res["rationale"]
                )
                db.add(audit)
                offers_created.append(eval_res)

        db.commit()

        # Publish discount event over event bus if any discounts were applied
        if offers_created:
            event_bus.publish_sync("discount_offers_updated", {"count": len(offers_created), "offers": offers_created})

        return offers_created


discount_agent = DynamicDiscountAgent()

