from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    incus_url: str = ""
    # TLS client cert auth
    incus_client_cert: str = ""
    incus_client_key: str = ""
    # OIDC auth (Authentik app_password)
    incus_oidc_issuer: str = ""
    incus_oidc_client_id: str = ""
    incus_username: str = ""
    incus_password: str = ""
    # TLS verification
    incus_ca_cert: str = ""
    incus_verify_ssl: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _reset_settings() -> None:
    global _settings
    _settings = None
