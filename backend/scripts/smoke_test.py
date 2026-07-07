"""Simple smoke test script for local backends.

Usage:
  CONS_SOROBAN_RPC=https://soroban-testnet.stellar.org python backend/scripts/smoke_test.py

This script attempts to call /status and (optionally) /record_on_chain if a
contract id is configured.
"""

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = os.environ.get("BASE_URL", "http://localhost:8000")


def get_status():
    try:
        req = Request(f"{BASE}/status")
        with urlopen(req, timeout=5) as resp:
            text = resp.read().decode()
            print("/status ->", text)
            return json.loads(text)
    except Exception as e:
        print("/status error:", e)
        return None


def record_value(v):
    try:
        data = json.dumps({"value": v}).encode()
        req = Request(f"{BASE}/record_on_chain", data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            text = resp.read().decode()
            print("/record_on_chain ->", text)
            return json.loads(text)
    except HTTPError as e:
        print("/record_on_chain HTTPError:", e.read().decode())
        return None
    except Exception as e:
        print("/record_on_chain error:", e)
        return None


if __name__ == "__main__":
    st = get_status()
    if st and st.get("contract_configured"):
        print("Contract configured, attempting record")
        record_value(123)
    else:
        print("No contract configured — skip record step")
        sys.exit(0)
