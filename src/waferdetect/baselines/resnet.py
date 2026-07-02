import argparse
import json
import os
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import ResNet18_Weights, resnet18
from tqdm import tqdm

from waferdetect.perception.annotations import load_class_names, load_label_file
from waferdetect.perception.dataset import stem_category

classes_file = Path("data/raw/classes.txt")
yolo_dir = Path("data/yolo")
out_dir = Path("runs/baselines/resnet")

input_size = 224


def multi_hot(label_path: Path, n_classes: int) -> torch.Tensor:
    target = torch.zeros(n_classes)

    for instance in load_label_file(label_path):
        target[instance.class_id] = 1.0

    return target


class WaferDataset(Dataset):
    def __init__(self, images_dir: Path, labels_dir: Path, n_classes: int):
        self.paths = sorted(images_dir.glob("*.jpg"))
        self.labels_dir = labels_dir
        self.n_classes = n_classes

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        path = self.paths[index]
        image = Image.open(path).convert("L").resize((input_size, input_size))

        tensor = (
            torch.from_numpy(np.asarray(image).copy()).float().unsqueeze(dim=0) / 255.0
        )
        tensor = tensor.repeat(3, 1, 1)

        return tensor, multi_hot(self.labels_dir / f"{path.stem}.txt", self.n_classes)


def evaluate(
    model: nn.Module, loader: DataLoader, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    model.eval()
    all_predictions = []
    all_targets = []

    with torch.inference_mode():
        for images, targets in loader:
            logits = model(images.to(device))  # shape: (batch, 21)
            all_predictions.append((torch.sigmoid(logits) > 0.5).float().cpu())
            all_targets.append(targets)

    return torch.cat(all_predictions), torch.cat(all_targets)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Training epochs (default: 20).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="AdamW learning rate (default: 1e-4).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device, e.g. mps, cuda, cpu (default: cpu).",
    )

    args = parser.parse_args()

    device = torch.device(args.device)

    class_names = load_class_names(classes_file)
    n_classes = len(class_names)

    train_set = WaferDataset(
        yolo_dir / "images" / "train", yolo_dir / "labels" / "train", n_classes
    )
    test_set = WaferDataset(
        yolo_dir / "images" / "test", yolo_dir / "labels" / "test", n_classes
    )
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=args.batch_size)

    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(in_features=model.fc.in_features, out_features=n_classes)
    model = model.to(device)
    optimizer = torch.optim.AdamW(params=model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        model.train()
        progress_bar = tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")

        for images, targets in progress_bar:
            optimizer.zero_grad()

            logits = model(images.to(device))  # shape: (batch_size, 21)

            loss = F.binary_cross_entropy_with_logits(logits, targets.to(device))

            loss.backward()
            optimizer.step()

            progress_bar.set_postfix(loss=f"{loss.item():.6f}")

    predictions, targets = evaluate(model, test_loader, device)
    exact = (predictions == targets).all(dim=1).float()
    combo_mask = torch.tensor(
        [stem_category(path.stem) == "combo" for path in test_set.paths]
    )

    per_class_f1 = {}
    for index, name in enumerate(class_names):
        tp = ((predictions[:, index] == 1) & (targets[:, index] == 1)).sum()
        fp = ((predictions[:, index] == 1) & (targets[:, index] == 0)).sum()
        fn = ((predictions[:, index] == 0) & (targets[:, index] == 1)).sum()

        denominator = (2 * tp + fp + fn).item()
        per_class_f1[name] = float(2 * tp / denominator) if denominator else 0.0

    metrics = {
        "exact_match_all": float(exact.mean()),
        "exact_match_singles": float(exact[~combo_mask].mean()),
        "exact_match_combo": float(exact[combo_mask].mean()),
        "macro_f1": float(sum(per_class_f1.values()) / n_classes),
        "per_class_f1": per_class_f1,
    }

    os.makedirs(out_dir, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    torch.save(model.state_dict(), out_dir / "model.pt")

    print(
        json.dumps(
            {key: value for key, value in metrics.items() if key != "per_class_f1"},
            indent=2,
        )
    )
