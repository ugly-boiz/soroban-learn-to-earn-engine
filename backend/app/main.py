from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from consparse.data import SyntheticSparseDataset, collate_sparse
from consparse.models import ConsSparseModel
from ..soroban_client import record_result, CONTRACT_ID, RPC
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

app = FastAPI(title="ConsSparse Backend")

# Allow dev frontend origins (Vite/CRA). Extend as needed for production.
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = None


class PredictRequest(BaseModel):
    batch_size: Optional[int] = 8


class RecordRequest(BaseModel):
    value: float


class SetContractRequest(BaseModel):
    contract_id: str
    admin_token: Optional[str] = None


@app.on_event("startup")
def load_model():
    global MODEL
    # Optionally skip model loading for quick dev checks or smoke tests.
    if os.environ.get("SKIP_MODEL_LOAD", "").lower() in ("1", "true", "yes"):
        MODEL = None
        return

    # Load a lightweight model for inference. In production, load a trained checkpoint.
    input_dim = int(os.environ.get("INPUT_DIM", "100000"))
    MODEL = ConsSparseModel(input_dim, {"task_a": 1})


def _check_rpc(url: str, timeout: int = 3) -> dict:
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            return {"reachable": True, "status": getattr(resp, "status", None)}
    except HTTPError as e:
        return {"reachable": False, "error": f"HTTPError {e.code}"}
    except URLError as e:
        return {"reachable": False, "error": str(e.reason)}
    except Exception as e:
        return {"reachable": False, "error": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(req: PredictRequest):
    # If the model wasn't loaded (dev / SKIP_MODEL_LOAD), return a lightweight
    # synthetic prediction so tests and smoke checks can run without heavy deps.
    if MODEL is None:
        # return a simple zeroed prediction for each requested batch entry
        preds = {"task_a": [[0.0] for _ in range(req.batch_size)]}
        return {"predictions": preds}

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
async def record_on_chain(req: RecordRequest):
    """Record a numeric result on Stellar (Soroban).

    Accepts JSON payload: {"value": <number>} and invokes the backend helper.
    """
    value = req.value
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


@app.get("/status")
async def status():
    """Return service status including Soroban RPC reachability and contract config."""
    rpc_info = _check_rpc(RPC)
    contract_configured = bool(CONTRACT_ID and CONTRACT_ID != "REPLACE_WITH_CONTRACT_ID")
    return {
        "status": "ok",
        "rpc": {"url": RPC, **rpc_info},
        "contract_configured": contract_configured,
        "contract_id": CONTRACT_ID if contract_configured else None,
    }


@app.post("/admin/set_contract")
async def set_contract(req: SetContractRequest):
    """Set the contract id at runtime (dev-only).

    Protected by `ADMIN_TOKEN` environment variable if set. This endpoint is
    intended for development convenience only.
    """
    admin_token = os.environ.get("ADMIN_TOKEN")
    if admin_token and req.admin_token != admin_token:
        return {"status": "error", "detail": "invalid_admin_token"}
    # import module and set CONTRACT_ID in the soroban client module
    import importlib

    try:
        sc = importlib.import_module("backend.soroban_client")
        sc.CONTRACT_ID = req.contract_id
        return {"status": "ok", "contract_id": sc.CONTRACT_ID}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
