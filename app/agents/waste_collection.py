"""
Waste Collection & Routing Agent.
Routes unavoidable food waste and surplus by category:
- Edible Surplus -> Local Food Banks / Charity Donation
- Animal Feed -> Poultry & Dairy Farms
- Organic Compost -> Campus Fertilizer Unit
- General Waste -> Municipal Waste Processing
Schedules automated pickups when bin fill levels cross thresholds and creates collection manifests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.db.models import WasteBinState, WasteCollectionManifest, AgentLog
from app.api.event_bus import event_bus
from app.core.config import calibration_data


class WasteCollectionAgent:
    def __init__(self):
        self.agent_name = "WasteCollectionAgent"

    def check_bins_and_schedule(
        self,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Inspects all 4 waste categories. When a bin fill level reaches threshold,
        generates a formal WasteCollectionManifest and dispatches collection.
        """
        bins = db.query(WasteBinState).all()
        if not bins:
            # Seed bins from calibration
            for cat, cfg in calibration_data.get("waste_bins", {}).items():
                b = WasteBinState(
                    category=cat,
                    name_en=cfg.get("name_en", cat),
                    name_bn=cfg.get("name_bn", cat),
                    capacity_kg=cfg.get("capacity_kg", 40.0),
                    current_weight_kg=0.0,
                    fill_percentage=0.0,
                    destination=cfg.get("destination", "Recycling"),
                    status="normal"
                )
                db.add(b)
            db.commit()
            bins = db.query(WasteBinState).all()

        manifests_generated = []

        for b in bins:
            cat_cfg = calibration_data.get("waste_bins", {}).get(b.category, {})
            threshold_ratio = cat_cfg.get("pickup_threshold_ratio", 0.80)
            threshold_pct = threshold_ratio * 100.0

            if b.fill_percentage >= threshold_pct or b.status == "pickup_scheduled":
                # Generate unique manifest code
                date_prefix = datetime.utcnow().strftime("%Y%m%d")
                short_code = str(uuid.uuid4())[:6].upper()
                manifest_code = f"WW-{b.category.upper()[:4]}-{date_prefix}-{short_code}"

                manifest = WasteCollectionManifest(
                    manifest_code=manifest_code,
                    timestamp=datetime.utcnow(),
                    category=b.category,
                    total_kg=b.current_weight_kg,
                    destination=b.destination,
                    status="scheduled",
                    notes=f"Auto-scheduled by {self.agent_name}. Fill reached {b.fill_percentage}% of {b.capacity_kg}kg capacity."
                )
                db.add(manifest)

                rationale = (
                    f"Scheduled collection manifest {manifest_code} for {b.name_en}. "
                    f"Bin load: {b.current_weight_kg:.1f} kg ({b.fill_percentage}% of {b.capacity_kg} kg). "
                    f"Dispatched pickup route to: {b.destination}."
                )
                audit = AgentLog(
                    agent_name=self.agent_name,
                    action="SCHEDULE_WASTE_PICKUP",
                    rationale=rationale
                )
                db.add(audit)

                manifests_generated.append({
                    "manifest_code": manifest_code,
                    "category": b.category,
                    "name_en": b.name_en,
                    "total_kg": b.current_weight_kg,
                    "destination": b.destination,
                    "rationale": rationale
                })

                # Reset bin state after pickup generation
                b.current_weight_kg = 0.0
                b.fill_percentage = 0.0
                b.status = "normal"
                b.last_pickup_at = datetime.utcnow()

        db.commit()

        if manifests_generated:
            event_bus.publish_sync("manifests_generated", {"count": len(manifests_generated), "manifests": manifests_generated})

        return manifests_generated

    def generate_manifest_csv(self, db: Session) -> str:
        """Exports all recorded collection manifests to CSV format."""
        manifests = db.query(WasteCollectionManifest).order_by(WasteCollectionManifest.timestamp.desc()).all()
        lines = ["Manifest Code,Timestamp,Category,Weight (kg),Destination,Status,Notes"]
        for m in manifests:
            t_str = m.timestamp.isoformat() if m.timestamp else ""
            lines.append(f'"{m.manifest_code}","{t_str}","{m.category}",{m.total_kg:.2f},"{m.destination}","{m.status}","{m.notes or ""}"')
        return "\n".join(lines)


waste_collection_agent = WasteCollectionAgent()

