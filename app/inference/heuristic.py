"""
Lightweight Plate-State Classifier & Pixel-Coverage Heuristic.
Used when the object detection model only detects food classes without explicit
plate-state annotations, or as a secondary verification layer.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image


class PlateCoverageHeuristic:
    """
    Computes food coverage ratio on the plate surface using color segmentation
    and morphological boundary analysis.
    """
    def __init__(
        self, 
        empty_threshold: float = 0.06, 
        partial_threshold: float = 0.60
    ):
        self.empty_threshold = empty_threshold
        self.partial_threshold = partial_threshold

    def analyze_frame_coverage(
        self, 
        image: Image.Image,
        plate_box: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates food pixel coverage ratio inside the plate mask.
        plate_box: (x1, y1, x2, y2) normalized [0, 1]
        """
        img_np = np.array(image.convert("RGB"))
        h, w, _ = img_np.shape

        if plate_box:
            x1 = int(max(0, plate_box[0] * w))
            y1 = int(max(0, plate_box[1] * h))
            x2 = int(min(w, plate_box[2] * w))
            y2 = int(min(h, plate_box[3] * h))
            roi = img_np[y1:y2, x1:x2]
        else:
            # Center circular region assumption (occupies center 75%)
            cx, cy = w // 2, h // 2
            radius = int(min(w, h) * 0.38)
            y1 = max(0, cy - radius)
            y2 = min(h, cy + radius)
            x1 = max(0, cx - radius)
            x2 = min(w, cx + radius)
            roi = img_np[y1:y2, x1:x2]

        if roi.size == 0:
            return {
                "plate_state": "empty_plate",
                "coverage_ratio": 0.0,
                "food_pixels": 0,
                "plate_pixels": 1
            }

        rh, rw, _ = roi.shape
        # Create circular mask for ROI
        y_coords, x_coords = np.ogrid[:rh, :rw]
        center_y, center_x = rh / 2.0, rw / 2.0
        r_sq = (min(rh, rw) / 2.0) ** 2
        circle_mask = ((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2) <= r_sq

        # Typical canteen plate surface: high brightness, low saturation (white/steel/cream melamine)
        # Convert RGB to HSV-like approximation without requiring heavy cv2
        r = roi[:, :, 0].astype(np.float32)
        g = roi[:, :, 1].astype(np.float32)
        b = roi[:, :, 2].astype(np.float32)

        max_val = np.maximum(np.maximum(r, g), b)
        min_val = np.minimum(np.minimum(r, g), b)
        delta = max_val - min_val

        # Saturation: delta / max_val
        sat = np.zeros_like(max_val)
        nonzero = max_val > 10
        sat[nonzero] = delta[nonzero] / max_val[nonzero]

        # Brightness / value
        val = max_val

        # Food pixels typically have distinct color saturation (curry turmeric, red chili, greens)
        # OR dark spices / gravies (val < 65)
        # Clean plate is either bright & low sat (val > 175 and sat < 0.20) or stainless steel reflection
        is_clean_surface = (val > 170) & (sat < 0.22)
        is_food_pixel = ~is_clean_surface & (val > 25)

        plate_pixels = int(np.sum(circle_mask))
        food_pixels = int(np.sum(circle_mask & is_food_pixel))

        coverage_ratio = food_pixels / max(plate_pixels, 1)

        if coverage_ratio < self.empty_threshold:
            state = "empty_plate"
        elif coverage_ratio < self.partial_threshold:
            state = "partial_leftover"
        else:
            state = "full_plate"

        return {
            "plate_state": state,
            "coverage_ratio": round(float(coverage_ratio), 3),
            "food_pixels": food_pixels,
            "plate_pixels": plate_pixels
        }


heuristic_classifier = PlateCoverageHeuristic()

