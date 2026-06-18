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
    # TODO: Implement SDK-based invocation using secure key management.
    return _invoke_cli(value, contract_id, rpc_url)
