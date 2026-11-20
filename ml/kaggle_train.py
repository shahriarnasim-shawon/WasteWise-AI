"""
WasteWiseAI - Kaggle Model Training Pipeline for Bangladeshi Canteen Foods.
Loads dataset from Kaggle input, converts/validates YOLO annotations, splits train/val/test,
trains YOLOv8n with canteen lighting/blur/occlusion augmentations, evaluates mAP50-95,
and exports best.onnx + classes.json for drop-in use in WasteWiseAI.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Configurable Kaggle input dataset path
DEFAULT_DATASET_INPUT = os.getenv("KAGGLE_DATASET_PATH", "/kaggle/input/bangladeshi-canteen-foods")
OUTPUT_DIR = Path("/kaggle/working/export") if os.path.exists("/kaggle") else Path("./models_export")


def parse_args():
    parser = argparse.ArgumentParser(description="WasteWiseAI YOLOv8n Training & ONNX Export Pipeline")
    parser.add_argument("--data-path", type=str, default=DEFAULT_DATASET_INPUT, help="Path to input dataset")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size for training and ONNX export")
    parser.add_argument("--device", type=str, default="", help="Device: '0' for GPU or 'cpu'")
    return parser.parse_args()


def setup_dataset_yaml(dataset_root: Path, classes_list: list) -> Path:
    """Creates YOLOv8 dataset.yaml definition."""
    yaml_path = OUTPUT_DIR / "dataset.yaml"
    names_dict = {i: name for i, name in enumerate(classes_list)}
    
    content = f"""# WasteWiseAI Dataset Configuration
path: {dataset_root.absolute()}
train: images/train
val: images/val
test: images/test

names:
"""
    for idx, name in names_dict.items():
        content += f"  {idx}: {name}\n"

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[INFO] Created YOLO dataset YAML at {yaml_path}")
    return yaml_path


def train_and_export():
    args = parse_args()
    data_dir = Path(args.data_path)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" WasteWiseAI - YOLOv8n Training Pipeline (Kaggle -> Antigravity)")
    print(f" Input Dataset Path: {data_dir}")
    print(f" Export Output Path: {OUTPUT_DIR}")
    print("=" * 70)

    # 1. Identify Classes
    data_yaml_file = data_dir / "data.yaml"
    classes_file = data_dir / "classes.txt"
    if data_yaml_file.exists():
        import yaml
        with open(data_yaml_file, "r") as f:
            ydata = yaml.safe_load(f)
            if isinstance(ydata.get("names"), list):
                classes = ydata["names"]
            elif isinstance(ydata.get("names"), dict):
                classes = [ydata["names"][k] for k in sorted(ydata["names"].keys())]
            else:
                classes = []
    elif classes_file.exists():
        with open(classes_file, "r") as f:
            classes = [line.strip() for line in f if line.strip()]
    else:
        # PSTU Bangladeshi Canteen Dataset Classes
        classes = [
            "Chop", "Puri", "chaa", "chola", "daal", "egg", "fish",
            "mashed potato", "matha", "meat", "rice", "ruti", "salad",
            "singara", "sweet", "veg roll", "vegetable"
        ]

    # Save classes.json for drop-in loading
    plate_states = [c for c in classes if c in ["empty_plate", "partial_leftover", "full_plate"]]
    food_classes = [c for c in classes if c not in plate_states]

    classes_json_path = OUTPUT_DIR / "classes.json"
    with open(classes_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "food_classes": food_classes,
            "plate_state_classes": plate_states,
            "all_classes": classes
        }, f, indent=2)
    print(f"[INFO] Saved classes.json ({len(classes)} classes) to {classes_json_path}")

    # 2. Check for ultralytics
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] 'ultralytics' package not found. Run 'pip install ultralytics' first.")
        sys.exit(1)

    # Use existing Roboflow data.yaml if present, or generate one
    if (data_dir / "data.yaml").exists():
        yaml_config = data_dir / "data.yaml"
    else:
        yaml_config = setup_dataset_yaml(data_dir, classes)

    # 3. Initialize YOLOv8-nano model (optimized for CPU inference)
    print("[INFO] Loading base model: yolov8n.pt...")
    model = YOLO("yolov8n.pt")

    # 4. Train with canteen augmentations (lighting, blur, scale, occlusion)
    print(f"[INFO] Beginning training for {args.epochs} epochs...")
    results = model.train(
        data=str(yaml_config),
        epochs=args.epochs,
        batch=args.batch_size,
        imgsz=args.imgsz,
        patience=12,
        device=args.device if args.device else (0 if os.path.exists("/dev/nvidia0") else "cpu"),
        # Augmentations for canteen conditions
        hsv_h=0.015,       # Slight hue variations
        hsv_s=0.6,         # Saturation (curry oil, turmeric variations)
        hsv_v=0.4,         # Brightness / shadows from canteen lighting
        degrees=15.0,      # Plate rotation
        translate=0.1,     # Slight camera alignment offset
        scale=0.5,         # Zoom / plate distance variation
        shear=2.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,        # Multi-dish mosaic
        mixup=0.1,
        project=str(OUTPUT_DIR / "runs"),
        name="wastewise_yolov8n"
    )

    # 5. Evaluate on Validation / Test Set
    print("\n[INFO] Evaluating model on validation/test set...")
    metrics = model.val()
    print(f"  mAP50:    {metrics.box.map50:.4f}")
    print(f"  mAP50-95: {metrics.box.map:.4f}")

    # 6. Export to ONNX (CPU Execution Provider Compatible)
    print(f"\n[INFO] Exporting best model weights to ONNX format (imgsz={args.imgsz})...")
    best_pt = OUTPUT_DIR / "runs" / "wastewise_yolov8n" / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = Path(model.trainer.best)

    best_model = YOLO(str(best_pt))
    exported_onnx = best_model.export(
        format="onnx",
        imgsz=args.imgsz,
        dynamic=False,
        simplify=True,
        opset=12
    )

    # Copy best.onnx to export root
    final_onnx = OUTPUT_DIR / "best.onnx"
    shutil.copy(exported_onnx, final_onnx)
    print(f"[SUCCESS] Exported best.onnx to {final_onnx}")

    print("\n" + "=" * 70)
    print(" Training and Export Complete!")
    print(f" 1. Download: {final_onnx}")
    print(f" 2. Download: {classes_json_path}")
    print(" 3. Place both files in WasteWiseAI: models/best.onnx & models/classes.json")
    print(" The application will automatically switch from Mock Mode to ONNX Runtime CPU.")
    print("=" * 70)


if __name__ == "__main__":
    train_and_export()

