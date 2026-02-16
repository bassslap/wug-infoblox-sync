from __future__ import annotations

from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Settings
from .models import WUGDevice


class WUGClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "PATCH", "DELETE"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _token(self) -> str:
        payload = {
            "grant_type": "password",
            "username": self.settings.wug_username,
            "password": self.settings.wug_password,
        }
        token_url = f"{self.settings.wug_base_url.rstrip('/')}{self.settings.wug_token_endpoint}"
        response = self.session.post(
            token_url,
            data=payload,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("WUG authentication succeeded but no access_token returned")
        return token

    def get_devices(self, limit: int | None = None) -> list[WUGDevice]:
        token = self._token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        endpoint = f"{self.settings.wug_base_url.rstrip('/')}{self.settings.wug_devices_endpoint}"
        params: dict[str, Any] = {"pageSize": self.settings.wug_page_size}
        if limit:
            params["pageSize"] = min(limit, self.settings.wug_page_size)

        response = self.session.get(
            endpoint,
            headers=headers,
            params=params,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        response.raise_for_status()
        payload = response.json()

        items = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []

        devices: list[WUGDevice] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            device_id = str(item.get("id") or item.get("deviceId") or "")
            hostname = str(item.get("displayName") or item.get("name") or "")
            ip = str(
                item.get("networkAddress")
                or item.get("ipAddress")
                or item.get("primaryAddress")
                or ""
            )
            status = str(item.get("state") or item.get("status") or "unknown")
            if not device_id or not ip:
                continue
            devices.append(
                WUGDevice(
                    source_id=device_id,
                    hostname=hostname or f"wug-{device_id}",
                    ip_address=ip,
                    status=status,
                    raw=item,
                )
            )
            if limit and len(devices) >= limit:
                break
        return devices
