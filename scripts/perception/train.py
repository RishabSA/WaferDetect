from ultralytics import YOLO
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        type=str,
        default="data/yolo/data.yaml",
        help="Path to the YOLO data direcotry with the data.yaml file (default: data/yolo/data.yaml).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="stage1_baseline",
        help="Name to use for YOLO training (default: stage1_baseline).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=200,
        help="Number of epochs to train for (default: 200).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use for model training, e.g., mps, 0 (cuda), cpu (default: cpu).",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="yolo26m-seg.pt",
        help="YOLO segmentation model name *.pt to load (default: yolo26m-seg.pt).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (defualt: 42).",
    )

    args = parser.parse_args()

    train_args = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": 640,
        "patience": 50,
        "mosaic": 0.0,
        "degrees": 180.0,
        "flipud": 0.5,
        "fliplr": 0.5,
        "scale": 0.1,
        # Color augmentation
        "hsv_h": 0.0,
        "hsv_s": 0.0,
        "hsv_v": 0.0,
        "seed": args.seed,
        "project": "runs/train",
        "name": args.name,
        "device": args.device,
    }

    model = YOLO(args.model_name)
    model.train(resume=args.resume, **train_args)
