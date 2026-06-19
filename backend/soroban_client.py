"""Simple Soroban client wrapper for the backend.

This wrapper prefers the `soroban` CLI fallback. Replace the `_invoke_cli` call
with an SDK-based implementation using secure key management when ready.
"""
import os
import shutil
import subprocess
from typing import Optional, Dict

CONTRACT_ID = os.environ.get("CONS_CONTRACT_ID", "REPLACE_WITH_CONTRACT_ID")
RPC = os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")
SIGNER_SECRET = os.environ.get("CONS_SIGNER_SECRET")  # optional


def _try_sdk_record(value: str, signer_secret: Optional[str], contract_id: Optional[str], rpc_url: Optional[str]) -> Optional[Dict]:
    """Try an SDK-based invocation using a local helper module.

    This function imports `backend.soroban_client_sdk` and delegates the
    attempt there. It never raises; on failure it returns None so callers
    can fallback to the CLI path.
    """
    if signer_secret is None:
        return None
    try:
        from . import soroban_client_sdk

        return soroban_client_sdk.record_result_sdk(value, signer_secret, contract_id, rpc_url)
    except Exception:
        return None


def _invoke_cli(value: str, contract_id: Optional[str] = None, rpc_url: Optional[str] = None) -> Dict:
    c = contract_id or CONTRACT_ID
    r = rpc_url or RPC
    if shutil.which("soroban") is None:
        return {"status": "fallback", "detail": "soroban_cli_not_available"}
    cmd = ["soroban", "contract", "invoke", "--network", r, c, "store_result", str(value)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "submitted", "output": res.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "detail": e.stderr}


def record_result(value, signer_secret: Optional[str] = None, contract_id: Optional[str] = None, rpc_url: Optional[str] = None) -> Dict:
    """High-level helper to record a numeric result to the Soroban contract.

    Current implementation prefers the `soroban` CLI. Replace with SDK-based
    transaction construction and signing if you want direct Python integration.
    """
    # try SDK path first when signer_secret is provided
    sdk_res = _try_sdk_record(str(value), signer_secret or SIGNER_SECRET, contract_id or CONTRACT_ID, rpc_url or RPC)
    if isinstance(sdk_res, dict):
        return sdk_res

    # fallback to CLI invocation (existing behavior)
    return _invoke_cli(value, contract_id, rpc_url)
