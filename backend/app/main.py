from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import os

from consparse.data import SyntheticSparseDataset, collate_sparse
from consparse.models import ConsSparseModel
from ..soroban_client import record_result

app = FastAPI(title="ConsSparse Backend")

MODEL = None


class PredictRequest(BaseModel):
    batch_size: Optional[int] = 8


@app.on_event("startup")
def load_model():
    global MODEL
    # Load a lightweight model for inference. In production, load a trained checkpoint.
    input_dim = int(os.environ.get("INPUT_DIM", "100000"))
    MODEL = ConsSparseModel(input_dim, {"task_a": 1})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(req: PredictRequest):
    # For the scaffold, generate synthetic data and run the model.
    ds = SyntheticSparseDataset(input_dim=MODEL.encoder.net[0].weight.shape[1] if hasattr(MODEL.encoder.net[0], 'weight') else 1024, size=req.batch_size, nnz_per_row=16)
    xb, yb = collate_sparse([ds[i] for i in range(req.batch_size)])
    MODEL.eval()
    with __import__('torch').no_grad():
        out = MODEL(xb)
    # convert tensors to python lists
    result = {k: v.detach().cpu().tolist() for k, v in out.items()}
    return {"predictions": result}


@app.post("/record_on_chain")
async def record_on_chain(value: float):
    """Placeholder endpoint: record a numeric result on Stellar (Soroban).

    This scaffold calls an external script (`backend/scripts/record_on_chain.py`) or
    the `soroban` CLI. Fill in `CONTRACT_ID` and proper invocation for your deployment.
    """
    # Try to call the helper script's `record` function directly; fallback to subprocess
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "record_on_chain.py"))
    # try using the soroban_client wrapper
    try:
        res = record_result(value)
        return res
    except Exception:
        # fallback to subprocess call to the script
        try:
            import subprocess

            env = os.environ.copy()
            proc = subprocess.run(["python", script_path, str(value)], capture_output=True, text=True, env=env, check=True)
            return {"status": "submitted", "output": proc.stdout}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
