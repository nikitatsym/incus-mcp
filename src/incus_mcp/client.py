from __future__ import annotations

import time

import httpx

from .config import get_settings


class APIError(Exception):
    def __init__(self, status: int, method: str, path: str, body):
        self.status = status
        self.method = method
        self.path = path
        self.body = body
        super().__init__(f"{method} {path} → {status}: {body}")


class IncusClient:
    def __init__(self):
        s = get_settings()
        if not s.incus_url:
            raise ValueError("INCUS_URL is required")

        verify = s.incus_ca_cert if s.incus_ca_cert else s.incus_verify_ssl
        kwargs: dict = {"base_url": s.incus_url, "verify": verify, "timeout": 30.0}

        if s.incus_client_cert and s.incus_client_key:
            kwargs["cert"] = (s.incus_client_cert, s.incus_client_key)
            self._auth_mode = "tls"
            self._access_token = None
        elif s.incus_username and s.incus_password:
            self._auth_mode = "oidc"
            self._oidc_issuer = s.incus_oidc_issuer
            self._oidc_client_id = s.incus_oidc_client_id
            self._username = s.incus_username
            self._password = s.incus_password
            self._access_token: str | None = None
            self._refresh_token: str | None = None
            self._token_expiry: float = 0
            self._token_endpoint: str | None = None
            self._authenticate()
            kwargs["headers"] = {"Authorization": f"Bearer {self._access_token}"}
        else:
            raise ValueError(
                "Auth required: set INCUS_CLIENT_CERT+INCUS_CLIENT_KEY "
                "or INCUS_USERNAME+INCUS_PASSWORD"
            )

        self._http = httpx.Client(**kwargs)

    def _discover_token_endpoint(self) -> str:
        if self._token_endpoint:
            return self._token_endpoint
        url = self._oidc_issuer.rstrip("/") + "/.well-known/openid-configuration"
        r = httpx.get(url, timeout=10.0)
        r.raise_for_status()
        self._token_endpoint = r.json()["token_endpoint"]
        return self._token_endpoint

    def _authenticate(self) -> None:
        endpoint = self._discover_token_endpoint()
        r = httpx.post(
            endpoint,
            data={
                "grant_type": "password",
                "client_id": self._oidc_client_id,
                "username": self._username,
                "password": self._password,
                "scope": "openid",
            },
            timeout=10.0,
        )
        if r.status_code != 200:
            raise APIError(r.status_code, "POST", endpoint, r.text)
        data = r.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token")
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60

    def _refresh(self) -> None:
        if not self._refresh_token:
            self._authenticate()
            return
        endpoint = self._discover_token_endpoint()
        r = httpx.post(
            endpoint,
            data={
                "grant_type": "refresh_token",
                "client_id": self._oidc_client_id,
                "refresh_token": self._refresh_token,
            },
            timeout=10.0,
        )
        if r.status_code != 200:
            self._authenticate()
            return
        data = r.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60

    def _ensure_token(self) -> None:
        if self._auth_mode != "oidc":
            return
        if time.time() >= self._token_expiry:
            self._refresh()
            self._http.headers["Authorization"] = f"Bearer {self._access_token}"

    def _handle(self, r: httpx.Response):
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = r.text
            raise APIError(r.status_code, r.request.method, str(r.request.url), body)
        if r.status_code == 204 or not r.content:
            return None
        ct = r.headers.get("content-type", "")
        if "json" not in ct:
            return r.text
        data = r.json()
        # Incus wraps responses in envelope
        if isinstance(data, dict) and "metadata" in data:
            if data.get("type") == "error":
                raise APIError(
                    data.get("error_code", 400),
                    r.request.method,
                    str(r.request.url),
                    data.get("error", "Unknown error"),
                )
            return data["metadata"]
        return data

    def get(self, path: str, **kwargs):
        self._ensure_token()
        return self._handle(self._http.get(path, **kwargs))

    def post(self, path: str, **kwargs):
        self._ensure_token()
        return self._handle(self._http.post(path, **kwargs))

    def put(self, path: str, **kwargs):
        self._ensure_token()
        return self._handle(self._http.put(path, **kwargs))

    def patch(self, path: str, **kwargs):
        self._ensure_token()
        return self._handle(self._http.patch(path, **kwargs))

    def delete(self, path: str, **kwargs):
        self._ensure_token()
        return self._handle(self._http.delete(path, **kwargs))
