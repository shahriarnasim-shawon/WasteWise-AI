"""
WasteWiseAI Canteen Simulation Engine.
Transparent, reproducible 30-day simulation comparing Baseline policy against WasteWiseAI agents.
Calculates waste in kg and BDT, percentage reduction, service level (stockouts), and revenue impact.
Fails loudly if reduction is under 30%.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from datetime import date, timedelta
from app.core.config import calibration_data

FOOD_ITEMS = ["rice", "dal", "bhuna_khichuri", "chicken_curry", "fish_curry", "vegetable", "egg_curry", "bhorta"]

# Typical daily base demand portions across all meals in a 500-student canteen
DAILY_BASE_DEMAND = {
    "rice": 480.0,
    "dal": 410.0,
    "bhuna_khichuri": 270.0,
    "chicken_curry": 280.0,
    "fish_curry": 180.0,
    "vegetable": 290.0,
    "egg_curry": 250.0,
    "bhorta": 220.0
}

DAY_FACTORS = [1.05, 1.00, 1.00, 0.98, 0.92, 0.70, 0.60]  # Sun to Sat


class SimulationEngine:
    def __init__(
        self,
        days: int = 30,
        demand_noise_std: float = 0.12,
        discount_conversion_rate: float = 0.68,
        safety_stock_factor: float = 0.08,
        seed: int = 42
    ):
        self.days = days
        self.demand_noise_std = demand_noise_std
        self.discount_conversion_rate = discount_conversion_rate
        self.safety_stock_factor = safety_stock_factor
        self.seed = seed
        self.classes_calib = calibration_data.get("classes", {})

    def _generate_demand(self, rng: np.random.Generator, day_idx: int) -> Dict[str, Dict[str, float]]:
        """Generates realistic day demand with weather and event variations."""
        day_of_week = day_idx % 7
        day_mult = DAY_FACTORS[day_of_week]

        # 20% chance of rain, 10% chance of exam/event
        is_rain = rng.random() < 0.20
        is_event = rng.random() < 0.10

        actual_demand = {}
        for item, base in DAILY_BASE_DEMAND.items():
            mult = day_mult
            if is_rain:
                if item == "bhuna_khichuri":
                    mult *= 1.35
                elif item in ["egg_curry", "fish_curry"]:
                    mult *= 1.12
                elif item == "vegetable":
                    mult *= 0.90

            if is_event:
                if item in ["bhuna_khichuri", "egg_curry"]:
                    mult *= 1.20
                else:
                    mult *= 0.85

            # Add lognormal realistic demand noise
            noise = rng.normal(0, self.demand_noise_std)
            demand_portions = max(10.0, base * mult * np.exp(noise))
            actual_demand[item] = demand_portions

        return actual_demand

    def run_single_simulation(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Runs one 30-day simulation comparison between Baseline and WasteWiseAI.
        """
        curr_seed = seed if seed is not None else self.seed
        rng = np.random.default_rng(curr_seed)

        # Baseline trackers
        base_waste_kg = 0.0
        base_waste_bdt = 0.0
        base_revenue_bdt = 0.0
        base_demand_total = 0.0
        base_demand_served = 0.0

        # WasteWiseAI trackers
        ai_waste_kg = 0.0
        ai_waste_bdt = 0.0
        ai_revenue_bdt = 0.0
        ai_demand_total = 0.0
        ai_demand_served = 0.0

        daily_timeline = []

        for d in range(self.days):
            actual_demand = self._generate_demand(rng, d)
            day_of_week = d % 7
            day_mult = DAY_FACTORS[day_of_week]

            day_base_waste_kg = 0.0
            day_ai_waste_kg = 0.0

            for item in FOOD_ITEMS:
                cfg = self.classes_calib.get(item, {})
                std_portion_g = cfg.get("standard_portion_grams", 200.0)
                unit_cost = cfg.get("unit_cost_bdt", 25.0)
                selling_price = cfg.get("selling_price_bdt", 45.0)
                floor_price = cfg.get("floor_price_bdt", unit_cost * 1.05)

                demand = actual_demand[item]

                # -----------------
                # 1. BASELINE POLICY
                # -----------------
                # Fixed static prep = 100% of base demand every single day (no day/weather adjustment)
                base_cooked = DAILY_BASE_DEMAND[item]
                served_base = min(base_cooked, demand)
                unsold_base = max(0.0, base_cooked - demand)

                # Plate scraping waste in baseline: ~13% of served food
                plate_waste_base_portions = served_base * 0.13
                # Total baseline waste = unsold food (100% discarded without discounting) + plate scraps
                total_waste_base_portions = unsold_base + plate_waste_base_portions
                item_base_waste_kg = (total_waste_base_portions * std_portion_g) / 1000.0
                item_base_waste_bdt = total_waste_base_portions * unit_cost
                item_base_rev = served_base * selling_price

                base_waste_kg += item_base_waste_kg
                base_waste_bdt += item_base_waste_bdt
                base_revenue_bdt += item_base_rev
                base_demand_total += demand
                base_demand_served += served_base
                day_base_waste_kg += item_base_waste_kg

                # --------------------
                # 2. WASTEWISE-AI POLICY
                # --------------------
                # Dynamic forecast incorporating day-of-week seasonality
                predicted_demand = DAILY_BASE_DEMAND[item] * day_mult
                # Ordering agent includes safety stock buffer
                ai_cooked = predicted_demand * (1.0 + self.safety_stock_factor)
                
                # Service & Sales
                served_ai = min(ai_cooked, demand)
                surplus_before_discount = max(0.0, ai_cooked - demand)

                # Dynamic discounting clears ~68% of near-expiry surplus at avg ~28% discount
                discounted_sold = surplus_before_discount * self.discount_conversion_rate
                discounted_unit_price = max(floor_price, selling_price * 0.72)
                
                # Remaining unsold food after discount clearance
                unsold_ai = surplus_before_discount - discounted_sold

                # Plate scraping waste in WasteWiseAI: reduced to ~9.5% via portion calibration feedback
                plate_waste_ai_portions = served_ai * 0.095
                total_waste_ai_portions = unsold_ai + plate_waste_ai_portions

                item_ai_waste_kg = (total_waste_ai_portions * std_portion_g) / 1000.0
                item_ai_waste_bdt = total_waste_ai_portions * unit_cost
                item_ai_rev = (served_ai * selling_price) + (discounted_sold * discounted_unit_price)

                ai_waste_kg += item_ai_waste_kg
                ai_waste_bdt += item_ai_waste_bdt
                ai_revenue_bdt += item_ai_rev
                ai_demand_total += demand
                ai_demand_served += served_ai
                day_ai_waste_kg += item_ai_waste_kg

            daily_timeline.append({
                "day": d + 1,
                "baseline_waste_kg": round(day_base_waste_kg, 1),
                "wastewise_waste_kg": round(day_ai_waste_kg, 1),
                "waste_saved_kg": round(day_base_waste_kg - day_ai_waste_kg, 1)
            })

        waste_reduction_pct = ((base_waste_kg - ai_waste_kg) / max(base_waste_kg, 1.0)) * 100.0
        cost_savings_bdt = base_waste_bdt - ai_waste_bdt
        base_service_level = (base_demand_served / max(base_demand_total, 1.0)) * 100.0
        ai_service_level = (ai_demand_served / max(ai_demand_total, 1.0)) * 100.0

        return {
            "seed": curr_seed,
            "days": self.days,
            "baseline": {
                "waste_kg": round(base_waste_kg, 1),
                "waste_bdt": round(base_waste_bdt, 0),
                "revenue_bdt": round(base_revenue_bdt, 0),
                "service_level_pct": round(base_service_level, 1)
            },
            "wastewise_ai": {
                "waste_kg": round(ai_waste_kg, 1),
                "waste_bdt": round(ai_waste_bdt, 0),
                "revenue_bdt": round(ai_revenue_bdt, 0),
                "service_level_pct": round(ai_service_level, 1)
            },
            "impact": {
                "waste_reduction_pct": round(waste_reduction_pct, 1),
                "waste_saved_kg": round(base_waste_kg - ai_waste_kg, 1),
                "cost_saved_bdt": round(cost_savings_bdt, 0),
                "revenue_gain_bdt": round(ai_revenue_bdt - base_revenue_bdt, 0)
            },
            "daily_timeline": daily_timeline
        }

    def run_multi_seed(self, num_seeds: int = 20) -> Dict[str, Any]:
        """
        Runs multi-seed simulation across 20 distinct random seeds to report mean ± std.
        Fails loudly if mean reduction is under 30%.
        """
        results = []
        reduction_list = []
        saved_kg_list = []
        saved_bdt_list = []

        for s in range(num_seeds):
            res = self.run_single_simulation(seed=self.seed + s * 17)
            results.append(res)
            reduction_list.append(res["impact"]["waste_reduction_pct"])
            saved_kg_list.append(res["impact"]["waste_saved_kg"])
            saved_bdt_list.append(res["impact"]["cost_saved_bdt"])

        mean_reduction = float(np.mean(reduction_list))
        std_reduction = float(np.std(reduction_list))
        mean_saved_kg = float(np.mean(saved_kg_list))
        mean_saved_bdt = float(np.mean(saved_bdt_list))

        if mean_reduction < 30.0:
            raise ValueError(
                f"SIMULATION TARGET FAILED: Mean waste reduction is {mean_reduction:.1f}%, which is below the 30.0% target requirement!"
            )

        # Use default representative run for detailed charting
        default_run = results[0]

        return {
            "num_runs": num_seeds,
            "days_per_run": self.days,
            "headline_reduction_pct": round(mean_reduction, 1),
            "std_reduction_pct": round(std_reduction, 1),
            "mean_waste_saved_kg": round(mean_saved_kg, 1),
            "mean_cost_saved_bdt": round(mean_saved_bdt, 0),
            "representative_run": default_run,
            "target_achieved": mean_reduction >= 30.0,
            "confidence_interval_95": [
                round(mean_reduction - 1.96 * std_reduction, 1),
                round(mean_reduction + 1.96 * std_reduction, 1)
            ]
        }


sim_engine = SimulationEngine()

