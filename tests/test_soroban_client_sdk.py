import backend.soroban_client_sdk as sdk
from backend.soroban_client import record_result


def test_record_result_uses_sdk(monkeypatch):
    # stub the SDK helper to simulate a successful submission
    def fake_sdk(value, signer_secret=None, contract_id=None, rpc_url=None):
        return {"status": "submitted", "output": "sdk_ok"}

    monkeypatch.setattr(sdk, "record_result_sdk", fake_sdk)
    res = record_result("123", signer_secret="SOMESECRET", contract_id="C1", rpc_url="R1")
    assert isinstance(res, dict)
    assert res.get("status") == "submitted"
    assert res.get("output") == "sdk_ok"


def test_record_result_falls_back_to_cli(monkeypatch):
    # make the SDK helper return None to force CLI fallback; monkeypatch _invoke_cli to return sentinel
    import backend.soroban_client as sc

    monkeypatch.setattr(sc, "_try_sdk_record", lambda *a, **k: None)
    monkeypatch.setattr(
        sc,
        "_invoke_cli",
        lambda value, contract_id=None, rpc_url=None: {"status": "fallback", "detail": "soroban_cli_not_available"},
    )
    res = record_result("456")
    assert isinstance(res, dict)
    assert res.get("status") in ("fallback", "error")
