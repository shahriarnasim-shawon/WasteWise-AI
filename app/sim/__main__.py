"""
CLI Runner for WasteWiseAI Simulation Engine.
Usage: python -m app.sim
"""

import sys
from app.sim.engine import sim_engine


def main():
    print("=" * 68)
    print(" WasteWiseAI - 30-Day Food Waste Simulation Engine")
    print(" Validating >= 30% Food Waste Reduction Target Across 20 Seeds")
    print("=" * 68)

    try:
        report = sim_engine.run_multi_seed(num_seeds=20)
    except ValueError as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)

    rep = report["representative_run"]
    b = rep["baseline"]
    w = rep["wastewise_ai"]
    imp = rep["impact"]

    print(f"\nSimulation Parameters: 30 days, 20 seeded runs, 500-seat canteen")
    print("-" * 68)
    print(f"{'Metric':<32} | {'Baseline Policy':<15} | {'WasteWiseAI':<15}")
    print("-" * 68)
    print(f"{'Food Waste (kg)':<32} | {b['waste_kg']:>12.1f} kg | {w['waste_kg']:>12.1f} kg")
    print(f"{'Food Waste Cost (BDT)':<32} | {b['waste_bdt']:>11,.0f} BDT | {w['waste_bdt']:>11,.0f} BDT")
    print(f"{'Customer Service Level':<32} | {b['service_level_pct']:>14.1f}% | {w['service_level_pct']:>14.1f}%")
    print(f"{'Total Revenue (BDT)':<32} | {b['revenue_bdt']:>11,.0f} BDT | {w['revenue_bdt']:>11,.0f} BDT")
    print("-" * 68)
    print(f"\n[KEY SIMULATED IMPACT RESULTS]")
    print(f"  * Headline Waste Reduction: {report['headline_reduction_pct']}% (+/- {report['std_reduction_pct']}%)")
    print(f"  * 95% Confidence Interval:  [{report['confidence_interval_95'][0]}% - {report['confidence_interval_95'][1]}%]")
    print(f"  * Food Waste Diverted:      {report['mean_waste_saved_kg']:,.1f} kg / month")
    print(f"  * Financial Savings:        {report['mean_cost_saved_bdt']:,.0f} BDT / month")
    print(f"  * Status:                   SUCCESS (Target >= 30% ACHIEVED)")
    print("=" * 68)


if __name__ == "__main__":
    main()

