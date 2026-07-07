"""Tests for consparse core components: models, data utilities, and training loop."""

import torch

from consparse.data import SyntheticSparseDataset, collate_sparse
from consparse.models import (
    ConsSparseModel,
    MultiTaskHead,
    SparseEncoder,
    SparseLinear,
)
from consparse.train import train

# ── SparseLinear ────────────────────────────────────────────────────────────


class TestSparseLinear:
    def test_dense_input(self):
        layer = SparseLinear(10, 4)
        x = torch.randn(3, 10)
        out = layer(x)
        assert out.shape == (3, 4)
        assert not out.is_sparse

    def test_sparse_input(self):
        layer = SparseLinear(10, 4)
        x = torch.sparse_coo_tensor(
            torch.tensor([[0, 0, 1], [1, 3, 7]]),
            torch.tensor([1.0, 2.0, 3.0]),
            size=(2, 10),
        ).coalesce()
        out = layer(x)
        assert out.shape == (2, 4)
        assert not out.is_sparse

    def test_no_bias(self):
        layer = SparseLinear(10, 4, bias=False)
        assert layer.bias is None
        x = torch.randn(3, 10)
        out = layer(x)
        assert out.shape == (3, 4)

    def test_sparse_and_dense_equivalent(self):
        """Sparse and dense inputs should produce identical results."""
        layer = SparseLinear(8, 3)
        dense = torch.randn(2, 8)
        # Build equivalent sparse tensor with no zeros
        indices = torch.stack(
            [torch.arange(2).repeat_interleave(8), torch.arange(8).repeat(2)],
        )
        sparse = torch.sparse_coo_tensor(indices, dense.flatten(), size=(2, 8)).coalesce()
        out_dense = layer(dense)
        out_sparse = layer(sparse)
        assert torch.allclose(out_dense, out_sparse, atol=1e-5)

    def test_gradient_flow(self):
        layer = SparseLinear(10, 4)
        x = torch.randn(3, 10, requires_grad=False)
        out = layer(x)
        loss = out.sum()
        loss.backward()
        assert layer.weight.grad is not None
        assert layer.bias.grad is not None


# ── SparseEncoder ───────────────────────────────────────────────────────────


class TestSparseEncoder:
    def test_output_shape(self):
        enc = SparseEncoder(1024, hidden_dims=(512, 256))
        x = torch.randn(8, 1024)
        out = enc(x)
        assert out.shape == (8, 256)
        assert enc.out_dim == 256

    def test_custom_hidden_dims(self):
        enc = SparseEncoder(512, hidden_dims=(128,))
        x = torch.randn(4, 512)
        out = enc(x)
        assert out.shape == (4, 128)
        assert enc.out_dim == 128

    def test_sparse_input(self):
        enc = SparseEncoder(1000, hidden_dims=(200,))
        idx = torch.tensor([[0, 0, 1], [5, 9, 42]])
        val = torch.tensor([1.0, 2.0, 3.0])
        x = torch.sparse_coo_tensor(idx, val, size=(2, 1000)).coalesce()
        out = enc(x)
        assert out.shape == (2, 200)

    def test_eval_mode_no_dropout_change(self):
        """Dropout should not change outputs in eval mode."""
        enc = SparseEncoder(64, hidden_dims=(32,), dropout=0.5)
        enc.eval()
        x = torch.randn(4, 64)
        out1 = enc(x)
        out2 = enc(x)
        assert torch.allclose(out1, out2)

    def test_gradient_flow(self):
        enc = SparseEncoder(64, hidden_dims=(32,))
        x = torch.randn(4, 64)
        out = enc(x)
        loss = out.sum()
        loss.backward()
        for name, p in enc.named_parameters():
            assert p.grad is not None, f"{name} has no gradient"


# ── MultiTaskHead ───────────────────────────────────────────────────────────


class TestMultiTaskHead:
    def test_single_task(self):
        head = MultiTaskHead(256, {"regression": 1})
        x = torch.randn(8, 256)
        out = head(x)
        assert set(out.keys()) == {"regression"}
        assert out["regression"].shape == (8, 1)

    def test_multiple_tasks(self):
        head = MultiTaskHead(256, {"task_a": 1, "task_b": 3, "task_c": 10})
        x = torch.randn(8, 256)
        out = head(x)
        assert set(out.keys()) == {"task_a", "task_b", "task_c"}
        assert out["task_a"].shape == (8, 1)
        assert out["task_b"].shape == (8, 3)
        assert out["task_c"].shape == (8, 10)

    def test_gradient_flow(self):
        head = MultiTaskHead(256, {"a": 1, "b": 2})
        x = torch.randn(8, 256)
        out = head(x)
        loss = out["a"].sum() + out["b"].sum()
        loss.backward()
        for k, layer in head.heads.items():
            assert layer.weight.grad is not None, f"head {k} weight has no gradient"


# ── ConsSparseModel ─────────────────────────────────────────────────────────


class TestConsSparseModel:
    def test_single_task_output(self):
        model = ConsSparseModel(1024, {"task_a": 1})
        x = torch.randn(4, 1024)
        out = model(x)
        assert "task_a" in out
        assert out["task_a"].shape == (4, 1)

    def test_multi_task_output(self):
        model = ConsSparseModel(512, {"cls": 3, "reg": 1, "aux": 5})
        x = torch.randn(2, 512)
        out = model(x)
        assert out["cls"].shape == (2, 3)
        assert out["reg"].shape == (2, 1)
        assert out["aux"].shape == (2, 5)

    def test_sparse_input(self):
        model = ConsSparseModel(1000, {"task_a": 1})
        idx = torch.tensor([[0, 1], [10, 20]])
        val = torch.tensor([1.0, -1.0])
        x = torch.sparse_coo_tensor(idx, val, size=(2, 1000)).coalesce()
        out = model(x)
        assert out["task_a"].shape == (2, 1)

    def test_model_parameters_trainable(self):
        model = ConsSparseModel(256, {"task_a": 1})
        params = sum(p.numel() for p in model.parameters())
        assert params > 0
        # All parameters should require gradients
        for p in model.parameters():
            assert p.requires_grad

    def test_backward_through_full_model(self):
        model = ConsSparseModel(256, {"a": 1, "b": 2})
        x = torch.randn(4, 256)
        out = model(x)
        loss = out["a"].mean() + out["b"].mean()
        loss.backward()
        for name, p in model.named_parameters():
            assert p.grad is not None, f"{name} has no gradient"


# ── SyntheticSparseDataset ──────────────────────────────────────────────────


class TestSyntheticSparseDataset:
    def test_length(self):
        ds = SyntheticSparseDataset(input_dim=100, size=10, nnz_per_row=5)
        assert len(ds) == 10

    def test_item_shape(self):
        ds = SyntheticSparseDataset(input_dim=200, size=8, nnz_per_row=4, task_dims={"a": 1})
        x, y = ds[0]
        assert x.is_sparse
        assert x.shape == (1, 200)
        assert x._nnz() == 4
        assert set(y.keys()) == {"a"}
        assert y["a"].shape == (1,)

    def test_multi_task_targets(self):
        ds = SyntheticSparseDataset(input_dim=100, size=4, nnz_per_row=3, task_dims={"x": 2, "y": 2})
        _, y = ds[0]
        assert y["x"].shape == (2,)
        assert y["y"].shape == (2,)
        # Targets from different tasks should differ (different linear projections)
        assert not torch.allclose(y["x"], y["y"])

    def test_deterministic_seed(self):
        ds1 = SyntheticSparseDataset(input_dim=100, size=5, nnz_per_row=3, seed=42)
        ds2 = SyntheticSparseDataset(input_dim=100, size=5, nnz_per_row=3, seed=42)
        x1, y1 = ds1[0]
        x2, y2 = ds2[0]
        assert torch.equal(x1.to_dense(), x2.to_dense())
        assert torch.allclose(y1["task_a"], y2["task_a"])

    def test_different_seeds_different_data(self):
        ds1 = SyntheticSparseDataset(input_dim=100, size=5, nnz_per_row=3, seed=42)
        ds2 = SyntheticSparseDataset(input_dim=100, size=5, nnz_per_row=3, seed=99)
        x1, _ = ds1[0]
        x2, _ = ds2[0]
        # Extremely unlikely to be identical
        assert not torch.equal(x1.to_dense(), x2.to_dense())

    def test_default_task_dims(self):
        ds = SyntheticSparseDataset(input_dim=50, size=3, nnz_per_row=2)
        _, y = ds[0]
        assert "task_a" in y
        assert y["task_a"].shape == (1,)


# ── collate_sparse ──────────────────────────────────────────────────────────


class TestCollateSparse:
    def test_batch_shape(self):
        ds = SyntheticSparseDataset(input_dim=128, size=8, nnz_per_row=6)
        batch = [ds[i] for i in range(4)]
        xb, yb = collate_sparse(batch)
        assert xb.is_sparse
        assert xb.shape == (4, 128)
        assert yb["task_a"].shape == (4,)

    def test_single_item_batch(self):
        ds = SyntheticSparseDataset(input_dim=64, size=4, nnz_per_row=4)
        batch = [ds[0]]
        xb, yb = collate_sparse(batch)
        assert xb.shape == (1, 64)
        assert yb["task_a"].shape == (1,)

    def test_multi_task_collate(self):
        ds = SyntheticSparseDataset(input_dim=64, size=8, nnz_per_row=4, task_dims={"a": 1, "b": 2})
        batch = [ds[i] for i in range(4)]
        xb, yb = collate_sparse(batch)
        assert xb.shape == (4, 64)
        assert yb["a"].shape == (4,)
        assert yb["b"].shape == (4, 2)

    def test_collate_preserves_values(self):
        """Values from individual items should map correctly into the batch tensor."""
        ds = SyntheticSparseDataset(input_dim=200, size=4, nnz_per_row=5, seed=123)
        x0, _ = ds[0]
        x1, _ = ds[1]
        xb, _ = collate_sparse([ds[0], ds[1]])
        # Row 0 of the batch should match x0.to_dense()
        assert torch.allclose(xb[0].to_dense(), x0.to_dense(), atol=1e-6)
        assert torch.allclose(xb[1].to_dense(), x1.to_dense(), atol=1e-6)


# ── Training loop ───────────────────────────────────────────────────────────


class TestTrainLoop:
    def test_train_runs(self):
        """The training loop should run to completion without error."""
        config = {
            "input_dim": 64,
            "size": 32,
            "nnz_per_row": 8,
            "batch_size": 8,
            "epochs": 2,
            "lr": 1e-3,
            "task_dims": {"task_a": 1},
        }
        train(config)

    def test_train_multi_task(self):
        """Training with multiple task heads should run without error."""
        config = {
            "input_dim": 128,
            "size": 32,
            "nnz_per_row": 8,
            "batch_size": 8,
            "epochs": 2,
            "lr": 1e-3,
            "task_dims": {"a": 1, "b": 2},
        }
        train(config)

    def test_train_reduces_loss(self, monkeypatch):
        """Loss should decrease from first to last epoch."""
        torch.manual_seed(0)
        losses = []

        def capture_print(s):
            # Parse "Epoch N loss=..." lines
            if "loss=" in str(s):
                losses.append(float(s.split("loss=")[1]))

        monkeypatch.setattr("builtins.print", capture_print)

        config = {
            "input_dim": 256,
            "size": 64,
            "nnz_per_row": 16,
            "batch_size": 16,
            "epochs": 4,
            "lr": 5e-3,
            "task_dims": {"task_a": 1},
        }
        train(config)

        assert len(losses) == 4
        # Loss in the first epoch should be higher than the last
        assert losses[0] > losses[-1], f"Expected loss to decrease: {losses}"

    def test_train_with_defaults(self):
        """Training with minimal config (only required fields) uses defaults."""
        config = {
            "input_dim": 64,
            "task_dims": {"task_a": 1},
        }
        train(config)
