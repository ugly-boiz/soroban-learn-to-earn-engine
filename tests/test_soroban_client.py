from backend.soroban_client import _invoke_cli, record_result


def test_fallback_when_cli_missing(monkeypatch):
    monkeypatch.setenv("CONS_CONTRACT_ID", "TEST_CONTRACT")
    # ensure soroban is not on PATH for the test
    monkeypatch.delenv("PATH", raising=False)
    res = _invoke_cli("123")
    assert res["status"] == "fallback"


def test_record_result_returns_dict():
    res = record_result("1.23")
    assert isinstance(res, dict)
