"""Attempt multiple Soroban SDK patterns and submit an invocation.

This helper is best-effort: Soroban support in `stellar_sdk` has varied
APIs across releases. The function below tries several known shapes and
returns informative diagnostics when a required feature is missing.

If a compatible SDK is not available, the caller should fall back to the
`soroban` CLI (already implemented elsewhere in the repo).
"""

import importlib
import os


def _int_or_fail(v: str) -> int:
    try:
        return int(float(v))
    except Exception:
        raise ValueError("value must be numeric") from None


def record_result_sdk(
    value: str, signer_secret: str | None = None, contract_id: str | None = None, rpc_url: str | None = None
) -> dict:
    """Try to invoke `store_result` on the deployed contract using SDK.

    Returns a dict with keys `status` and additional diagnostics. On
    success returns `{"status": "submitted", "detail": <something>}`.
    On failure returns an explanatory `status` and `detail`.
    """
    contract = contract_id or os.environ.get("CONS_CONTRACT_ID")
    rpc = rpc_url or os.environ.get("CONS_SOROBAN_RPC", "https://soroban-testnet.stellar.org")

    if not contract or contract == "REPLACE_WITH_CONTRACT_ID":
        return {"status": "error", "detail": "contract_id_not_configured"}
    if signer_secret is None:
        return {"status": "error", "detail": "signer_secret_required_for_sdk"}

    # numeric value expected for contract's i128 parameter
    try:
        numeric_value = _int_or_fail(value)
    except ValueError as e:
        return {"status": "error", "detail": str(e)}

    # Import stellar_sdk and check for soroban support
    try:
        stellar_sdk = importlib.import_module("stellar_sdk")
    except Exception:
        return {"status": "unavailable", "detail": "stellar_sdk_not_installed"}

    # Try common Soroban submodule locations
    soroban_mod = None
    for candidate in ("stellar_sdk.soroban", "stellar_sdk.soroban.soroban_rpc_client", "sorobanpy"):
        try:
            soroban_mod = importlib.import_module(candidate)
            break
        except Exception:
            soroban_mod = None

    if soroban_mod is None:
        return {"status": "unavailable", "detail": "stellar_sdk_soroban_support_missing"}

    # Try multiple SDK shapes. These branches attempt to use the SDK when
    # available; if any branch succeeds we return the result. All exceptions
    # are captured and returned as diagnostic info.
    errors = []

    # Branch A: modern `stellar_sdk.soroban.SorobanServer`-style API
    try:
        SorobanServer = getattr(soroban_mod, "SorobanServer", None) or getattr(soroban_mod, "SorobanClient", None)
        ScVal = getattr(soroban_mod, "ScVal", None)
        HostFunction = getattr(soroban_mod, "HostFunction", None)
        ScVec = getattr(soroban_mod, "ScVec", None)

        if SorobanServer and ScVal and HostFunction and ScVec:
            server = SorobanServer(rpc)
            # Zero key (BytesN<32>) used as a simple per-demo key
            key_bytes = bytes([0] * 32)
            # Build ScVal arguments if the SDK exposes constructors
            try:
                key_arg = ScVal.from_bytes(key_bytes) if hasattr(ScVal, "from_bytes") else ScVal.bytes(key_bytes)
                val_arg = ScVal.from_i128(numeric_value) if hasattr(ScVal, "from_i128") else ScVal.i128(numeric_value)
                args = ScVec([key_arg, val_arg])
            except Exception:
                # best-effort alternate construction
                args = None

            # Construct host function call
            hf = None
            if hasattr(HostFunction, "invoke_contract"):
                hf = HostFunction.invoke_contract(contract, "store_result", args)
            elif hasattr(HostFunction, "new"):
                hf = HostFunction.new(contract, "store_result", args)

            if hf is None:
                raise RuntimeError("HostFunction construction not supported by SDK variant")

            # Try to prepare and submit a transaction using server helpers
            if hasattr(server, "prepare_transaction"):
                tx = server.prepare_transaction(source_key=None, host_function=hf)
                # sign and send if tx object supports it
                if hasattr(tx, "sign"):
                    from stellar_sdk import Keypair

                    kp = Keypair.from_secret(signer_secret)
                    tx.sign(kp)
                    if hasattr(server, "send_transaction"):
                        submit_res = server.send_transaction(tx)
                        return {"status": "submitted", "output": submit_res}
            # If we reach here we couldn't finish with this branch
            errors.append("sdk_branch_A_incomplete")
    except Exception as e:
        errors.append(f"branch_A_error:{e}")

    # Branch B: try to use stellar_sdk core + InvokeHostFunction op (older shapes)
    try:
        # dynamic imports to avoid hard dependency at module import time
        Keypair = getattr(stellar_sdk, "Keypair", None) or getattr(
            importlib.import_module("stellar_sdk.keypair"), "Keypair", None
        )
        TransactionBuilder = getattr(stellar_sdk, "TransactionBuilder", None)
        Network = getattr(stellar_sdk, "Network", None)
        Server = getattr(stellar_sdk, "Server", None)

        # check for operation class in soroban_mod or stellar_sdk
        InvokeHostFunction = getattr(soroban_mod, "InvokeHostFunction", None) or getattr(
            stellar_sdk, "InvokeHostFunction", None
        )

        if Keypair and TransactionBuilder and Network and Server and InvokeHostFunction:
            server = Server(rpc)
            kp = Keypair.from_secret(signer_secret)
            # load account for sequence number
            try:
                source_acct = server.load_account(kp.public_key)
            except Exception:
                source_acct = None

            # zero key bytes
            key_bytes = bytes([0] * 32)
            # build operation arguments if SDK exposes ScVal/ScVec
            ScVal = getattr(soroban_mod, "ScVal", None)
            ScVec = getattr(soroban_mod, "ScVec", None)
            if ScVal and ScVec:
                try:
                    key_arg = ScVal.from_bytes(key_bytes) if hasattr(ScVal, "from_bytes") else ScVal.bytes(key_bytes)
                    val_arg = (
                        ScVal.from_i128(numeric_value) if hasattr(ScVal, "from_i128") else ScVal.i128(numeric_value)
                    )
                    args = ScVec([key_arg, val_arg])
                except Exception:
                    args = None
            else:
                args = None

            op = InvokeHostFunction(contract, "store_result", args)

            # Build transaction (best-effort). If source_acct is None try a minimal build.
            txb = TransactionBuilder(
                source_account=source_acct or object(),
                network_passphrase=(
                    Network.TESTNET_NETWORK_PASSPHRASE
                    if hasattr(Network, "TESTNET_NETWORK_PASSPHRASE")
                    else Network.PUBLIC_NETWORK_PASSPHRASE
                ),
                base_fee=100,
            )
            txb.append_operation(op)
            tx = txb.build()
            tx.sign(kp)
            # Submit using server
            submit_res = server.submit_transaction(tx)
            return {"status": "submitted", "output": submit_res}
    except Exception as e:
        errors.append(f"branch_B_error:{e}")

    # Nothing succeeded — return collected diagnostics
    return {"status": "unavailable", "detail": "no_supported_sdk_flow", "errors": errors}
