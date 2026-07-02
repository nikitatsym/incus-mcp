"""Unit-test scaffolding for incus-mcp.

No docker-compose. Every non-integration test uses `stub_client` +
`respx_mock` to run against fake HTTP; no real Incus, no real cert files,
no OIDC discovery.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import incus_mcp.tools.helpers as helpers
from incus_mcp.client import IncusClient
from incus_mcp.config import _reset_settings

TEST_BASE_URL = "https://incus.test:8443"


@pytest.fixture(autouse=True)
def _reset_state():
    """Drop settings + client singletons before every test.

    Prevents any earlier test's env / mocked client from leaking into the
    next case's setup.
    """
    _reset_settings()
    helpers._client = None
    yield
    _reset_settings()
    helpers._client = None


@pytest.fixture
def client_env(monkeypatch):
    """Set INCUS_URL to the fake base URL and reset the settings cache.

    Use in tests that walk the settings/config path directly.
    """
    monkeypatch.setenv("INCUS_URL", TEST_BASE_URL)
    _reset_settings()
    return TEST_BASE_URL


@pytest.fixture
def respx_mock():
    """respx router scoped to the fake Incus base URL.

    `assert_all_called=False`: tests may register routes they don't hit
    (e.g. a fallback that only fires on the failure branch).
    """
    with respx.mock(base_url=TEST_BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def stub_client(respx_mock, monkeypatch):
    """`IncusClient` wired to the respx mock, installed as the tools singleton.

    Tests interact via `incus_mcp.tools.*` ops; the client under the hood
    is this stub, so no real network hits and no auth setup.
    """
    http = httpx.Client(
        base_url=TEST_BASE_URL,
        transport=httpx.MockTransport(respx_mock.handler),
    )
    client = IncusClient._for_tests(http)
    monkeypatch.setattr(helpers, "_client", client)
    return client


@pytest.fixture
def oidc_env(monkeypatch):
    """Env + respx routes for the OIDC discovery + token flow.

    Only the dedicated OIDC test cases use this; the rest use `stub_client`.
    """
    monkeypatch.setenv("INCUS_URL", TEST_BASE_URL)
    monkeypatch.setenv("INCUS_OIDC_ISSUER", "https://auth.test")
    monkeypatch.setenv("INCUS_OIDC_CLIENT_ID", "test-client")
    monkeypatch.setenv("INCUS_USERNAME", "tester")
    monkeypatch.setenv("INCUS_PASSWORD", "s3cret")
    _reset_settings()
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://auth.test/.well-known/openid-configuration").respond(
            200, json={"token_endpoint": "https://auth.test/token"},
        )
        mock.post("https://auth.test/token").respond(
            200,
            json={
                "access_token": "test-access",
                "refresh_token": "test-refresh",
                "expires_in": 3600,
            },
        )
        yield mock
