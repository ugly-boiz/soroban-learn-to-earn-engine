"""Simple RPC reachability checker for Soroban RPC URL.

Usage:
  CONS_SOROBAN_RPC=https://soroban-testnet.stellar.org python backend/scripts/check_rpc.py
"""

import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RPC = os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")


def check_rpc(url: str, timeout: int = 5) -> int:
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None)
            print(f"reachable: True status={code}")
            return 0
    except HTTPError as e:
        print(f"reachable: False http_error={e.code}")
        return 2
    except URLError as e:
        print(f"reachable: False url_error={e.reason}")
        return 3
    except Exception as e:
        print(f"reachable: False error={e}")
        return 4


if __name__ == "__main__":
    sys.exit(check_rpc(RPC))
