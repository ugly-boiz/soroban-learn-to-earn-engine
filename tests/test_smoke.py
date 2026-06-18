import torch
from consparse.models import ConsSparseModel
from consparse.data import SyntheticSparseDataset, collate_sparse


def test_forward():
    ds = SyntheticSparseDataset(input_dim=1024, size=4, nnz_per_row=8)
    xb, yb = collate_sparse([ds[i] for i in range(4)])
    model = ConsSparseModel(1024, {"task_a": 1})
    out = model(xb)
    assert "task_a" in out
    assert out["task_a"].shape[0] == 4
