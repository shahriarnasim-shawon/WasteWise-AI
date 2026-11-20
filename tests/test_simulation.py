"""
Unit tests asserting the >= 30% Food Waste Reduction Target.
Tests single-run and multi-seed Monte Carlo evaluation across random seeds.
Fails loudly if reduction is under 30%.
"""

import pytest
from app.sim.engine import SimulationEngine


def test_simulation_reproducible_single_run():
    """Verify that same seed produces identical reproducible results."""
    eng1 = SimulationEngine(days=30, seed=42)
    res1 = eng1.run_single_simulation(seed=42)

    eng2 = SimulationEngine(days=30, seed=42)
    res2 = eng2.run_single_simulation(seed=42)

    assert res1["baseline"]["waste_kg"] == res2["baseline"]["waste_kg"]
    assert res1["wastewise_ai"]["waste_kg"] == res2["wastewise_ai"]["waste_kg"]
    assert res1["impact"]["waste_reduction_pct"] == res2["impact"]["waste_reduction_pct"]


def test_simulation_achieves_at_least_30_percent_reduction():
    """Assert strictly that WasteWiseAI achieves at least 30% waste reduction."""
    eng = SimulationEngine(days=30, seed=42)
    res = eng.run_single_simulation(seed=42)

    reduction = res["impact"]["waste_reduction_pct"]
    assert reduction >= 30.0, f"Expected >= 30% reduction, got {reduction}%"
    assert res["impact"]["waste_saved_kg"] > 0
    assert res["impact"]["cost_saved_bdt"] > 0


def test_simulation_service_level_maintained():
    """Verify customer service level (fill rate) remains >= 94%."""
    eng = SimulationEngine(days=30, seed=42)
    res = eng.run_single_simulation(seed=42)

    assert res["wastewise_ai"]["service_level_pct"] >= 94.0
    assert res["baseline"]["service_level_pct"] >= 90.0


def test_simulation_multi_seed_mean_reduction_target():
    """Assert multi-seed mean across 20 distinct seeds exceeds 30% reduction."""
    eng = SimulationEngine(days=30, seed=101)
    report = eng.run_multi_seed(num_seeds=20)

    assert report["headline_reduction_pct"] >= 30.0
    assert report["target_achieved"] is True
    assert report["confidence_interval_95"][0] >= 28.0

