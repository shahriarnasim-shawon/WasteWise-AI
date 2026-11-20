"""
Core application configuration for WasteWiseAI.
Loads environment variables, yaml calibration, and provides typed settings.
"""

from pathlib import Path
from typing import List, Optional
import os
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PlateReference(BaseModel):
    standard_diameter_cm: float = 26.0
    area_cm2: float = 530.93
    empty_threshold_ratio: float = 0.06
    partial_threshold_ratio: float = 0.60


class FoodClassConfig(BaseModel):
    name_en: str
    name_bn: str
    grams_per_cm2: float
    standard_portion_grams: float
    unit_cost_bdt: float
    selling_price_bdt: float
    floor_price_bdt: float
    shelf_life_hours: float
    waste_category: str


class WasteBinConfig(BaseModel):
    name_en: str
    name_bn: str
    capacity_kg: float
    pickup_threshold_ratio: float
    destination: str


class Settings(BaseSettings):
    PROJECT_NAME: str = "WasteWiseAI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database: SQLite default, Postgres supported via DATABASE_URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'wastewise.db'}"
    )
    
    # Model configuration
    MODEL_PATH: Path = BASE_DIR / "models" / "best.onnx"
    CLASSES_PATH: Path = BASE_DIR / "models" / "classes.json"
    CALIBRATION_PATH: Path = BASE_DIR / "config" / "portion_calibration.yaml"
    
    # Frame rate / Rate limit / Privacy
    MAX_FPS_INFERENCE: float = 2.5
    STORE_IMAGES_DEFAULT: bool = False  # Privacy: discard raw images by default
    IMAGE_RETENTION_HOURS: int = 24
    
    # Station configuration
    STATION_IDS: List[str] = ["station-dish-return-1", "station-dish-return-2", "station-kitchen-prep"]

    model_config = SettingsConfigDict(case_sensitive=True, extra="allow")


settings = Settings()


def load_calibration():
    """Loads calibration YAML into memory."""
    if not settings.CALIBRATION_PATH.exists():
        raise FileNotFoundError(f"Calibration file missing at {settings.CALIBRATION_PATH}")
    with open(settings.CALIBRATION_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


calibration_data = load_calibration()
