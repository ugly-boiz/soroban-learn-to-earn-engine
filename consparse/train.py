"""Training CLI for the consSparse model.

Provides a minimal train loop for smoke testing.
"""

import argparse

import torch
import yaml
from torch.utils.data import DataLoader

from .data import SyntheticSparseDataset, collate_sparse
from .models import ConsSparseModel


def train(config):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = SyntheticSparseDataset(
        input_dim=config["input_dim"],
        size=config.get("size", 256),
        nnz_per_row=config.get("nnz_per_row", 16),
        task_dims=config.get("task_dims", {"task_a": 1}),
    )
    loader = DataLoader(dataset, batch_size=config.get("batch_size", 8), collate_fn=collate_sparse)
    model = ConsSparseModel(config["input_dim"], config.get("task_dims", {"task_a": 1})).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=config.get("lr", 1e-3))
    model.train()
    for epoch in range(config.get("epochs", 1)):
        for xb, yb in loader:
            xb = xb.to(device)
            out = model(xb)
            loss = 0.0
            for k in yb:
                pred = out[k]
                target = yb[k].to(device).float()
                loss = loss + ((pred.squeeze(-1) - target.squeeze(-1)) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        print(f"Epoch {epoch} loss={loss.item():.4f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/dev.yaml")
    args = parser.parse_args()
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    train(cfg)


if __name__ == "__main__":
    main()
