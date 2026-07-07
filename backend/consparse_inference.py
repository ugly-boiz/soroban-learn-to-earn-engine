"""Lightweight inference helper for backend.

This module intentionally keeps imports local to avoid requiring heavy deps
on import time during dev (e.g., torch). The backend uses the module functions
at runtime when the environment is prepared.
"""

MODEL = None


def load_local_model(input_dim: int, task_dims: dict[str, int]):
    global MODEL
    from consparse.models import ConsSparseModel

    MODEL = ConsSparseModel(input_dim, task_dims)
    MODEL.eval()


def predict_from_sparse_batch(xb):
    """Run a forward pass on a batched sparse tensor.

    xb: torch.sparse_coo_tensor
    """
    import torch

    global MODEL
    if MODEL is None:
        raise RuntimeError("Model not loaded")
    with torch.no_grad():
        out = MODEL(xb)
    return {k: v.cpu().numpy() for k, v in out.items()}
