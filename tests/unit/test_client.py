from __future__ import annotations

from pathlib import Path

import pytest
from nqct import Client, NQCTClient, Runtime, __version__
from nqct.auth.credentials import load_profile
from nqct.client import NQCTClient as ClientClass
from nqct.exceptions import AuthenticationError


def test_public_aliases() -> None:
    assert Client is NQCTClient
    assert Runtime is NQCTClient
    assert __version__ == "0.2.0"


def test_missing_credentials_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_FILE", tmp_path / "credentials.json")
    monkeypatch.delenv("NQCT_API_KEY", raising=False)
    monkeypatch.delenv("NQCT_TOKEN", raising=False)
    monkeypatch.delenv("NQCT_URL", raising=False)
    with pytest.raises(AuthenticationError, match="No credentials"):
        NQCTClient()


def test_default_api_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_FILE", tmp_path / "credentials.json")
    monkeypatch.delenv("NQCT_URL", raising=False)
    monkeypatch.delenv("NQCT_API_KEY", raising=False)
    client = NQCTClient(api_key="nqct_test")
    assert client.url == "https://api.nqct.org/api/v1"
    client.close()


def test_explicit_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NQCT_API_KEY", raising=False)
    client = NQCTClient(url="http://localhost:8000/api/v1", api_key="nqct_test")
    assert client.api_key == "nqct_test"
    client.close()


def test_env_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NQCT_URL", "http://example:8000/api/v1")
    monkeypatch.setenv("NQCT_API_KEY", "nqct_from_env")
    client = NQCTClient()
    assert client.url == "http://example:8000/api/v1"
    assert client.api_key == "nqct_from_env"
    client.close()


def test_save_and_load_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    creds_file = tmp_path / "credentials.json"
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_FILE", creds_file)

    ClientClass.save_account(
        url="http://localhost:8000/api/v1",
        api_key="nqct_saved",
        name="default",
    )
    assert creds_file.exists()
    assert oct(creds_file.stat().st_mode & 0o777) == oct(0o600)

    profile = load_profile("default")
    assert profile["url"] == "http://localhost:8000/api/v1"
    assert profile["api_key"] == "nqct_saved"

    client = NQCTClient()
    assert client.api_key == "nqct_saved"
    client.close()


def test_save_account_defaults_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    creds_file = tmp_path / "credentials.json"
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_FILE", creds_file)
    monkeypatch.delenv("NQCT_URL", raising=False)

    ClientClass.save_account(api_key="nqct_saved")
    profile = load_profile("default")
    assert profile["url"] == "https://api.nqct.org/api/v1"
    assert profile["api_key"] == "nqct_saved"


def test_delete_account(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    creds_file = tmp_path / "credentials.json"
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_DIR", tmp_path)
    monkeypatch.setattr("nqct.auth.credentials.CREDENTIALS_FILE", creds_file)

    ClientClass.save_account(url="http://localhost:8000/api/v1", api_key="nqct_x")
    ClientClass.delete_account()
    assert not creds_file.exists()
