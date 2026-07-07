"""Simple Soroban client wrapper for the backend.

This wrapper prefers the `soroban` CLI fallback. Replace the `_invoke_cli` call
with an SDK-based implementation using secure key management when ready.
"""

import os
import shutil
import subprocess

CONTRACT_ID = os.environ.get("CONS_CONTRACT_ID", "REPLACE_WITH_CONTRACT_ID")
RPC = os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")
SIGNER_SECRET = os.environ.get("CONS_SIGNER_SECRET")  # optional


def _try_sdk_record(value: str, signer_secret: str | None, contract_id: str | None, rpc_url: str | None) -> dict | None:
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


def _invoke_cli(value: str, contract_id: str | None = None, signer_secret: str | None = None) -> dict:
    c = contract_id or CONTRACT_ID
    if shutil.which("soroban") is None:
        return {"status": "fallback", "detail": "soroban_cli_not_available"}
    secret = signer_secret or SIGNER_SECRET
    if not secret:
        return {"status": "error", "detail": "signer_secret_required"}
    # Use zero key as a simple demo storage key (BytesN<32>)
    # Network name "testnet" is resolved from the stellar CLI v27 config
    cmd = [
        "soroban",
        "contract",
        "invoke",
        "--id",
        c,
        "--source-account",
        secret,
        "--network",
        "testnet",
        "--",
        "store_result",
        "--key",
        "0000000000000000000000000000000000000000000000000000000000000000",
        "--value",
        str(int(value)),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "submitted", "output": res.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "detail": e.stderr}


def record_result(
    value, signer_secret: str | None = None, contract_id: str | None = None, rpc_url: str | None = None
) -> dict:
    """High-level helper to record a numeric result to the Soroban contract.

    Current implementation prefers the `soroban` CLI. Replace with SDK-based
    transaction construction and signing if you want direct Python integration.
    """
    # try SDK path first when signer_secret is provided
    sdk_res = _try_sdk_record(str(value), signer_secret or SIGNER_SECRET, contract_id or CONTRACT_ID, rpc_url or RPC)
    if isinstance(sdk_res, dict) and sdk_res.get("status") == "submitted":
        return sdk_res

    # fallback to CLI invocation (existing behavior)
    return _invoke_cli(value, contract_id, signer_secret)
