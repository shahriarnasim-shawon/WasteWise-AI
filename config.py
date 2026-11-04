from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "wastewise.db"

# Default pretrained weights; in Step 2 we will drop Kaggle-trained 'best.pt' into models/
CUSTOM_MODEL_PATH = BASE_DIR / "models" / "best.pt"
DEFAULT_MODEL_NAME = "yolo11n-seg.pt"

# Confidence threshold for detections; below LOW_CONF_THRESHOLD triggers human review flag
CONF_THRESHOLD = 0.35
LOW_CONF_THRESHOLD = 0.50

# Reference ROI (Tray Return Zone) as fraction of frame [x1, y1, x2, y2]
TRAY_ROI_FRAC = (0.10, 0.10, 0.90, 0.90)

# Pretrained COCO classes relevant for immediate baseline testing before Step 2 Kaggle training
# COCO IDs: 45=bowl, 46=banana, 47=apple, 48=sandwich, 49=orange, 50=broccoli, 51=carrot, 52=hot dog, 53=pizza, 54=donut, 55=cake
COCO_FOOD_CLASSES = {
    46: "banana", 47: "apple", 48: "sandwich", 49: "orange",
    50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza",
    54: "donut", 55: "cake"
}
COCO_CONTAINER_CLASSES = {45: "bowl", 60: "dining table"}

# Stage 2 Reference Mass Calibration Table (grams for 100% reference tray coverage)
# Can be toggled on/off in the UI. Uncalibrated items default to None (Visual Ratio Only).
DEFAULT_MASS_CALIBRATION_GRAMS = {
    "rice": 250.0,
    "dal": 150.0,
    "curry": 180.0,
    "vegetables": 140.0,
    "meat_fish": 160.0,
    "banana": 120.0,
    "apple": 150.0,
    "sandwich": 180.0,
    "pizza": 220.0,
    "broccoli": 130.0,
    "carrot": 110.0,
    "cake": 140.0,
}
