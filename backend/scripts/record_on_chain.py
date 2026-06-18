"""Placeholder script to interact with a Soroban (Stellar) contract.

This script is a scaffolding helper. For deployment and secure signing you should
use `soroban` CLI or the official SDK with a securely stored key. Replace the
`CONTRACT_ID` with your deployed contract ID and update invocation accordingly.
"""
import os
import subprocess
import sys

CONTRACT_ID = os.environ.get("CONS_CONTRACT_ID", "REPLACE_WITH_CONTRACT_ID")
SOROBAN_RPC = os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")


def record(value: str) -> str:
    """Invoke `soroban` CLI to call `store_result` on the contract.

    This function falls back to printing a message if the `soroban` CLI is not
    available. In production use a secure signing method and avoid shelling out.
    """
    # build the soroban CLI invocation
    cmd = [
        "soroban",
        "contract",
        "invoke",
        "--network",
        SOROBAN_RPC,
        "--wasm",  # placeholder; real invocation may differ depending on deployment
        CONTRACT_ID,
        "store_result",
        value,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except FileNotFoundError:
        return f"soroban CLI not found; would record {value} to {CONTRACT_ID} on {SOROBAN_RPC}"
    except subprocess.CalledProcessError as e:
        return f"error invoking soroban: {e.stderr}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: record_on_chain.py <value>")
        sys.exit(2)
    value = sys.argv[1]
    print(record(value))
