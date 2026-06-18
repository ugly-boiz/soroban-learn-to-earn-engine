"""Helper to build and deploy the Soroban contract using `soroban` CLI.

This is a convenience wrapper; ensure you have `soroban` and the Rust toolchain installed.
Set `CONS_SOROBAN_NETWORK` to the RPC URL or network name and `CONS_CONTRACT_WASM`
if you have a prebuilt wasm file. See contracts/README.md for details.
"""
import os
import subprocess
import sys

NETWORK = os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")
WASM = os.environ.get("CONS_CONTRACT_WASM", "./contracts/target/wasm32-unknown-unknown/release/consparse_contract.wasm")


def build_and_deploy():
    # Build using soroban CLI if available
    try:
        subprocess.run(["soroban", "contract", "build"], check=True)
    except FileNotFoundError:
        print("soroban CLI not found; run `cargo build --target wasm32-unknown-unknown --release` in contracts/ instead")
    # Deploy
    try:
        res = subprocess.run(["soroban", "contract", "deploy", "--wasm", WASM, "--network", NETWORK], capture_output=True, text=True, check=True)
        print(res.stdout)
    except Exception as e:
        print("deploy failed:", e)


if __name__ == "__main__":
    build_and_deploy()
