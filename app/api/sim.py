"""
API Router for Food Waste Simulation Engine.
Exposes parameterized simulation runs comparing Baseline against WasteWiseAI.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.sim.engine import SimulationEngine, sim_engine

router = APIRouter(prefix="/sim", tags=["Simulation Engine"])


class SimulationParams(BaseModel):
    days: int = Field(30, ge=7, le=90)
    demand_noise_std: float = Field(0.12, ge=0.01, le=0.40)
    discount_conversion_rate: float = Field(0.68, ge=0.20, le=0.95)
    safety_stock_factor: float = Field(0.08, ge=0.0, le=0.25)
    num_seeds: int = Field(15, ge=1, le=50)


@router.post("/run")
def run_simulation(params: SimulationParams) -> Dict[str, Any]:
    """Runs a fresh multi-seed simulation with customized parameters."""
    engine = SimulationEngine(
        days=params.days,
        demand_noise_std=params.demand_noise_std,
        discount_conversion_rate=params.discount_conversion_rate,
        safety_stock_factor=params.safety_stock_factor
    )
    result = engine.run_multi_seed(num_seeds=params.num_seeds)
    return result


@router.get("/latest")
def get_latest_simulation() -> Dict[str, Any]:
    """Returns the default reproducible 30-day simulation benchmark."""
    return sim_engine.run_multi_seed(num_seeds=15)

