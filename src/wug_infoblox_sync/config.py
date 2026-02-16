from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    flask_host: str
    flask_port: int
    sync_timeout_seconds: int
    sync_verify_ssl: bool
    sync_log_level: str
    wug_base_url: str
    wug_username: str
    wug_password: str
    wug_token_endpoint: str
    wug_devices_endpoint: str
    wug_page_size: int
    infoblox_base_url: str
    infoblox_wapi_version: str
    infoblox_username: str
    infoblox_password: str
    infoblox_network_view: str
    infoblox_dry_run: bool


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
        flask_port=int(os.getenv("FLASK_PORT", "8080")),
        sync_timeout_seconds=int(os.getenv("SYNC_TIMEOUT_SECONDS", "30")),
        sync_verify_ssl=_as_bool(os.getenv("SYNC_VERIFY_SSL", "false"), False),
        sync_log_level=os.getenv("SYNC_LOG_LEVEL", "INFO"),
        wug_base_url=os.getenv("WUG_BASE_URL", ""),
        wug_username=os.getenv("WUG_USERNAME", ""),
        wug_password=os.getenv("WUG_PASSWORD", ""),
        wug_token_endpoint=os.getenv("WUG_TOKEN_ENDPOINT", "/api/v1/token"),
        wug_devices_endpoint=os.getenv("WUG_DEVICES_ENDPOINT", "/api/v1/devices/-"),
        wug_page_size=int(os.getenv("WUG_PAGE_SIZE", "500")),
        infoblox_base_url=os.getenv("INFOBLOX_BASE_URL", ""),
        infoblox_wapi_version=os.getenv("INFOBLOX_WAPI_VERSION", "v2.12.3"),
        infoblox_username=os.getenv("INFOBLOX_USERNAME", ""),
        infoblox_password=os.getenv("INFOBLOX_PASSWORD", ""),
        infoblox_network_view=os.getenv("INFOBLOX_NETWORK_VIEW", "default"),
        infoblox_dry_run=_as_bool(os.getenv("INFOBLOX_DRY_RUN", "true"), True),
    )
