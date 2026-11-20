"""
Unit tests for WasteWiseAI Inference & Quantity Estimation.
Verifies Mock Mode fallback, bounding area to grams conversion, and plate state assessment.
"""

import pytest
import io
from PIL import Image, ImageDraw

from pathlib import Path
from app.inference.detector import FoodDetector
from app.inference.quantity_estimator import QuantityEstimator
from app.inference.heuristic import PlateCoverageHeuristic


@pytest.fixture
def mock_detector():
    return FoodDetector()


@pytest.fixture
def missing_detector():
    return FoodDetector(model_path=Path("models/nonexistent_model.onnx"))


@pytest.fixture
def sample_plate_image():
    """Generates a synthetic plate image with white plate and food-colored patches."""
    img = Image.new("RGB", (640, 640), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    # Draw white round plate
    draw.ellipse([80, 80, 560, 560], fill=(245, 245, 245), outline=(200, 200, 200), width=4)
    # Draw food patch (curry/rice)
    draw.ellipse([200, 200, 440, 440], fill=(180, 110, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def clean_empty_plate_image():
    """Generates an empty plate image."""
    img = Image.new("RGB", (640, 640), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 80, 560, 560], fill=(250, 250, 250), outline=(210, 210, 210), width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_detector_mock_mode_active_when_model_missing(missing_detector):
    """Ensure detector falls back gracefully to Mock Mode when best.onnx is absent."""
    status = missing_detector.get_status()
    assert status["is_mock"] is True
    assert "Mock Mode" in status["mock_reason"] or "not found" in status["mock_reason"]


def test_quantity_estimator_rice_conversion():
    """Verify that detected area correctly converts to grams using portion_calibration.yaml."""
    estimator = QuantityEstimator()
    # 640x640 image, plate occupies center ~70%
    plate_px = estimator.estimate_plate_pixel_area((640, 640))
    # Food box covering 25% of plate
    box = [0.3, 0.3, 0.6, 0.6]  # 0.3 x 0.3 = 0.09 frame area
    res = estimator.estimate_food_item("rice", box, (640, 640), plate_px)

    assert res["food_class"] == "rice"
    assert res["estimated_grams"] > 0.0
    assert res["cost_value_bdt"] > 0.0
    assert res["sales_value_bdt"] >= res["cost_value_bdt"]
    assert res["waste_category"] == "animal_feed"


def test_plate_state_empty_assessment():
    """Verify that small food quantities are classified as empty_plate."""
    estimator = QuantityEstimator()
    state, ratio = estimator.assess_plate_state(total_leftover_grams=8.0, total_food_area_cm2=10.0)
    assert state == "empty_plate"
    assert ratio < 0.06


def test_plate_state_leftover_assessment():
    """Verify that medium food quantities are classified as partial_leftover."""
    estimator = QuantityEstimator()
    state, ratio = estimator.assess_plate_state(total_leftover_grams=120.0, total_food_area_cm2=150.0)
    assert state == "partial_leftover"
    assert 0.06 <= ratio <= 0.60


def test_plate_coverage_heuristic_empty():
    """Verify plate coverage heuristic on synthetic clean plate."""
    heuristic = PlateCoverageHeuristic()
    img = Image.new("RGB", (300, 300), (245, 245, 245))
    res = heuristic.analyze_frame_coverage(img)
    assert res["plate_state"] == "empty_plate"
    assert res["coverage_ratio"] < 0.10


def test_detector_inference_output_contract(mock_detector, sample_plate_image):
    """Verify the detector returns all required contract fields for the ingestion layer."""
    res = mock_detector.detect(sample_plate_image, image_name="test_plate_1.jpg")
    assert res["success"] is True
    assert "boxes" in res
    assert "plate_state" in res
    assert res["plate_state"] in ["empty_plate", "partial_leftover", "full_plate"]
    assert "total_leftover_grams" in res
    assert "total_cost_bdt" in res
    assert "inference_time_ms" in res
    assert "is_mock" in res

