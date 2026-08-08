import os
import csv
import random
from typing import List, Dict, Tuple

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
import torchvision
from torchvision import transforms
from PIL import Image


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def read_csv(csv_path: str) -> List[Tuple[str, List[str]]]:
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            path = r["path"].strip()
            labels = r["labels"].strip().split() if r["labels"].strip() else []
            rows.append((path, labels))
    return rows


def build_label_map(rows: List[Tuple[str, List[str]]]) -> Dict[str, int]:
    vocab = sorted({lab for _, labs in rows for lab in labs})
    return {lab: i for i, lab in enumerate(vocab)}


class MultiLabelDataset(Dataset):
    def __init__(self, rows, label2idx, transform=None):
        self.rows = rows
        self.label2idx = label2idx
        self.num_labels = len(label2idx)
        self.transform = transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        path, labels = self.rows[idx]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing file: {path}")

        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)

        y = torch.zeros(self.num_labels, dtype=torch.float32)
        for lab in labels:
            y[self.label2idx[lab]] = 1.0

        return img, y, path


def main():
    set_seed(42)

    CSV_PATH = "model/data/train/train.csv"  # change if needed
    BATCH_SIZE = 8
    EPOCHS = 15
    LR = 1e-3
    VAL_FRAC = 0.2
    NUM_WORKERS = 2

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    rows = read_csv(CSV_PATH)
    label2idx = build_label_map(rows)
    print(f"Num samples: {len(rows)}")
    print(f"Num labels: {len(label2idx)}")
    print("Labels:", list(label2idx.keys()))

    # ResNet50 expects ImageNet normalization
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    full_ds = MultiLabelDataset(rows, label2idx, transform=train_tf)

    n_val = max(1, int(len(full_ds) * VAL_FRAC))
    n_train = len(full_ds) - n_val
    train_ds, val_ds = random_split(full_ds, [n_train, n_val])

    # ensure val uses val transforms
    val_ds.dataset.transform = val_tf

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=True
    )
    val_loader = DataLoader(
        val_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True
    )

    # Model: pretrained ResNet50 with new head
    model = torchvision.models.resnet50(
        weights=torchvision.models.ResNet50_Weights.DEFAULT
    )
    in_feats = model.fc.in_features
    model.fc = nn.Linear(in_feats, len(label2idx))

    # Freeze backbone, train only head
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("fc.")

    model = model.to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.fc.parameters(), lr=LR, weight_decay=1e-4)

    def evaluate():
        model.eval()
        total_loss = 0.0
        total_items = 0

        correct = 0
        denom = 0

        with torch.no_grad():
            for x, y, _ in val_loader:
                x = x.to(device, non_blocking=True)
                y = y.to(device, non_blocking=True)

                logits = model(x)
                loss = criterion(logits, y)

                bs = x.size(0)
                total_loss += loss.item() * bs
                total_items += bs

                probs = torch.sigmoid(logits)
                preds = (probs >= 0.5).float()
                correct += (preds == y).sum().item()
                denom += y.numel()

        return total_loss / max(1, total_items), correct / max(1, denom)

    best_val = float("inf")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running = 0.0

        for x, y, _ in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            running += loss.item() * x.size(0)

        train_loss = running / max(1, n_train)
        val_loss, val_micro_acc = evaluate()

        print(f"Epoch {epoch:02d} | train_loss={train_loss:.4f} | "
              f"val_loss={val_loss:.4f} | val_micro_acc={val_micro_acc:.4f}")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(
                {"model_state": model.state_dict(), "label2idx": label2idx},
                "best_head_resnet50.pt"
            )
            print("  saved -> best_head_resnet50.pt")

    print("Done.")


if __name__ == "__main__":
    main()
