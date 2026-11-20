"""
Quantity Estimator Module.
Converts detected plate and food bounding areas into physical cm² and estimated leftover grams,
using the portion calibration configuration.
"""

from typing import Dict, Any, Optional, Tuple, List
import math
from app.core.config import calibration_data


class QuantityEstimator:
    def __init__(self, calibration: Optional[Dict[str, Any]] = None):
        self.calib = calibration or calibration_data
        self.plate_ref = self.calib.get("plate_reference", {})
        self.ref_diameter_cm = float(self.plate_ref.get("standard_diameter_cm", 26.0))
        self.ref_area_cm2 = float(self.plate_ref.get("area_cm2", 530.93))
        self.empty_thresh = float(self.plate_ref.get("empty_threshold_ratio", 0.06))
        self.partial_thresh = float(self.plate_ref.get("partial_threshold_ratio", 0.60))
        self.classes_calib = self.calib.get("classes", {})

    def estimate_plate_pixel_area(
        self, 
        image_shape: Tuple[int, int], 
        plate_box: Optional[List[float]] = None
    ) -> float:
        """
        Calculates or estimates the plate area in pixels.
        plate_box is [x1, y1, x2, y2] normalized (0 to 1) or absolute.
        """
        img_h, img_w = image_shape
        if plate_box:
            # normalize if absolute
            x1, y1, x2, y2 = plate_box
            if x1 > 1.0 or y1 > 1.0 or x2 > 1.0 or y2 > 1.0:
                bw = (x2 - x1)
                bh = (y2 - y1)
            else:
                bw = (x2 - x1) * img_w
                bh = (y2 - y1) * img_h
            # Elliptical / circular plate assumption inside bounding box
            return (math.pi / 4.0) * bw * bh
        else:
            # Default assumption: plate occupies ~68% of the frame's minimum dimension
            diameter_px = min(img_w, img_h) * 0.72
            return math.pi * ((diameter_px / 2.0) ** 2)

    def estimate_food_item(
        self,
        food_class: str,
        box: List[float],
        image_shape: Tuple[int, int],
        plate_pixel_area: float,
        shape_fill_factor: float = 0.78
    ) -> Dict[str, Any]:
        """
        Estimates leftover grams for a single food detection box.
        box: [x1, y1, x2, y2]
        """
        img_h, img_w = image_shape
        x1, y1, x2, y2 = box
        if x1 > 1.0 or y1 > 1.0 or x2 > 1.0 or y2 > 1.0:
            bw = max(0.0, x2 - x1)
            bh = max(0.0, y2 - y1)
        else:
            bw = max(0.0, (x2 - x1) * img_w)
            bh = max(0.0, (y2 - y1) * img_h)

        raw_box_area_px = bw * bh
        # Irregular food pile fill factor
        effective_food_px = raw_box_area_px * shape_fill_factor

        # Pixel to physical cm² ratio based on reference plate
        cm2_per_px = self.ref_area_cm2 / max(plate_pixel_area, 1.0)
        area_cm2 = effective_food_px * cm2_per_px

        class_info = self.classes_calib.get(food_class, {})
        grams_per_cm2 = class_info.get("grams_per_cm2", 0.80)
        std_portion = class_info.get("standard_portion_grams", 200.0)
        unit_cost = class_info.get("unit_cost_bdt", 25.0)
        selling_price = class_info.get("selling_price_bdt", 45.0)

        estimated_grams = round(area_cm2 * grams_per_cm2, 1)
        # Cap to realistic maximum of 1.4x standard portion for safety
        estimated_grams = min(estimated_grams, round(std_portion * 1.4, 1))

        # Financial value of wasted food
        cost_value_bdt = round((estimated_grams / max(std_portion, 1.0)) * unit_cost, 2)
        sales_value_bdt = round((estimated_grams / max(std_portion, 1.0)) * selling_price, 2)

        return {
            "food_class": food_class,
            "name_en": class_info.get("name_en", food_class),
            "name_bn": class_info.get("name_bn", food_class),
            "area_cm2": round(area_cm2, 2),
            "estimated_grams": estimated_grams,
            "cost_value_bdt": cost_value_bdt,
            "sales_value_bdt": sales_value_bdt,
            "waste_category": class_info.get("waste_category", "general"),
            "standard_portion_grams": std_portion
        }

    def assess_plate_state(
        self,
        total_leftover_grams: float,
        total_food_area_cm2: float,
        explicit_plate_state: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Determines overall plate state and coverage ratio.
        Returns (plate_state, coverage_ratio).
        """
        if explicit_plate_state in ["empty_plate", "partial_leftover", "full_plate"]:
            ratio = total_food_area_cm2 / self.ref_area_cm2
            return explicit_plate_state, min(1.0, round(ratio, 3))

        coverage_ratio = min(1.0, total_food_area_cm2 / self.ref_area_cm2)
        if coverage_ratio < self.empty_thresh or total_leftover_grams < 15.0:
            return "empty_plate", round(coverage_ratio, 3)
        elif coverage_ratio < self.partial_thresh or total_leftover_grams < 180.0:
            return "partial_leftover", round(coverage_ratio, 3)
        else:
            return "full_plate", round(coverage_ratio, 3)


estimator = QuantityEstimator()

