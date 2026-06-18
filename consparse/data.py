"""Data utilities: sparse biochemical inputs and synthetic dataset for tests.

This provides a Dataset that yields sparse fingerprints or feature matrices as
`torch.sparse_coo_tensor` along with per-task targets.
"""
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset


class SyntheticSparseDataset(Dataset):
    """Generates random sparse data for quick experiments.

    Each example is a sparse vector of length `input_dim` with `nnz_per_row`
    nonzeros chosen uniformly and values sampled from N(0,1). Targets are
    linear functions of the dense projection with noise.
    """

    def __init__(
        self,
        input_dim: int = 100_000,
        size: int = 1024,
        nnz_per_row: int = 32,
        task_dims: Dict[str, int] = None,
        seed: int = 42,
    ):
        self.input_dim = input_dim
        self.size = size
        self.nnz_per_row = nnz_per_row
        self.task_dims = task_dims or {"task_a": 1}
        rng = np.random.RandomState(seed)
        self.rows = []
        self.values = []
        self.cols = []
        for i in range(size):
            cols = rng.choice(input_dim, size=nnz_per_row, replace=False)
            vals = rng.randn(nnz_per_row).astype(np.float32)
            rows = np.full_like(cols, i, dtype=np.int64)
            self.rows.append(rows)
            self.cols.append(cols)
            self.values.append(vals)
        # create a random linear projection used to generate targets
        self.proj = rng.randn(input_dim, sum(self.task_dims.values())).astype(np.float32)

    def __len__(self):
        return self.size

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        rows = self.rows[idx]
        cols = self.cols[idx]
        vals = self.values[idx]
        indices = np.stack([np.zeros_like(cols), cols], axis=0).astype(np.int64)
        # Create a 1 x input_dim sparse tensor
        i = torch.LongTensor(indices)
        v = torch.from_numpy(vals)
        x = torch.sparse_coo_tensor(i, v, size=(1, self.input_dim)).coalesce()
        # dense projection for targets
        dense = np.zeros((self.input_dim,), dtype=np.float32)
        dense[cols] = vals
        y = dense @ self.proj + 0.1 * rng.randn(sum(self.task_dims.values())).astype(np.float32)
        # split into task dict
        out = {}
        offset = 0
        for k, dim in self.task_dims.items():
            out[k] = torch.from_numpy(y[offset : offset + dim]).float()
            offset += dim
        return x, out


# Small collate fn to stack sparse rows into a batch sparse tensor

def collate_sparse(batch):
    xs, ys = zip(*batch)
    # xs: list of 1 x input_dim sparse tensors
    indices = []
    values = []
    cols = None
    for i, x in enumerate(xs):
        x = x.coalesce()
        idx = x.indices()  # 2 x nnz
        vals = x.values()
        # convert row idx to batch row
        batch_row = torch.zeros_like(idx[0]) + i
        batch_idx = torch.stack([batch_row, idx[1]], dim=0)
        indices.append(batch_idx)
        values.append(vals)
    indices = torch.cat(indices, dim=1)
    values = torch.cat(values, dim=0)
    input_dim = xs[0].size(1)
    xb = torch.sparse_coo_tensor(indices, values, size=(len(xs), input_dim)).coalesce()
    # stack ys
    yb = {}
    for k in ys[0].keys():
        yb[k] = torch.stack([y[k].squeeze(0) if y[k].dim()>0 else y[k] for y in ys])
    return xb, yb
