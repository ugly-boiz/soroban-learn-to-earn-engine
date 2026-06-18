"""Core sparse-aware model modules (PyTorch).

This file provides a minimal, extensible model scaffold with a sparse input encoder
and multi-task heads.
"""
from typing import Dict

import torch
import torch.nn as nn


class SparseLinear(nn.Module):
    """A thin wrapper that accepts dense or sparse input tensors and applies a linear layer.

    For sparse input (torch.sparse_coo_tensor), it performs the equivalent of
    x @ W.T + b using sparse-dense multiplication.
    """

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(out_features, in_features) * 0.02)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.is_sparse:
            out = torch.sparse.mm(x, self.weight.t())
        else:
            out = x @ self.weight.t()
        if self.bias is not None:
            out = out + self.bias
        return out


class SparseEncoder(nn.Module):
    """Encodes extremely high-dimensional sparse inputs into dense embeddings.

    The encoder uses a stack of sparse-aware linear layers with optional
    normalization and activation.
    """

    def __init__(self, input_dim: int, hidden_dims=(1024, 512), dropout: float = 0.1):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(SparseLinear(prev, h))
            layers.append(nn.LayerNorm(h))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(dropout))
            prev = h
        self.net = nn.Sequential(*layers)
        self.out_dim = prev

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MultiTaskHead(nn.Module):
    """Collection of per-task output heads.

    Heads are simple linear layers by default but can be replaced with more
    sophisticated components (calibration layers, uncertainty heads, etc.).
    """

    def __init__(self, in_dim: int, task_dims: Dict[str, int]):
        super().__init__()
        self.heads = nn.ModuleDict({k: nn.Linear(in_dim, v) for k, v in task_dims.items()})

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        return {k: head(x) for k, head in self.heads.items()}


class ConsSparseModel(nn.Module):
    """End-to-end model: sparse encoder + multi-task heads.

    Args:
        input_dim: dimensionality of the sparse input vectors.
        task_dims: mapping from task name to output dim (1 for regression/binary).
    """

    def __init__(self, input_dim: int, task_dims: Dict[str, int]):
        super().__init__()
        self.encoder = SparseEncoder(input_dim)
        self.heads = MultiTaskHead(self.encoder.out_dim, task_dims)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        emb = self.encoder(x)
        return self.heads(emb)
