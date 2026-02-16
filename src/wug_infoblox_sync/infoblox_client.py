from __future__ import annotations

from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Settings
from .models import InfobloxHostRecord


class InfobloxClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.infoblox_username, settings.infoblox_password)
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

    def _wapi_base(self) -> str:
        return f"{self.settings.infoblox_base_url.rstrip('/')}/wapi/{self.settings.infoblox_wapi_version}"

    def upsert_host_record(self, record: InfobloxHostRecord, dry_run: bool) -> dict[str, Any]:
        if dry_run:
            return {
                "changed": True,
                "action": "dry-run-upsert",
                "fqdn": record.fqdn,
                "ip_address": record.ip_address,
            }

        query_url = f"{self._wapi_base()}/record:host"
        query_params = {
            "name": record.fqdn,
            "_return_fields": "_ref,name,ipv4addrs,extattrs",
        }
        query_response = self.session.get(
            query_url,
            params=query_params,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        query_response.raise_for_status()
        existing = query_response.json()

        payload = {
            "name": record.fqdn,
            "ipv4addrs": [{"ipv4addr": record.ip_address}],
            "extattrs": record.extattrs,
            "view": record.network_view,
        }

        if isinstance(existing, list) and existing:
            ref = existing[0].get("_ref")
            if not ref:
                raise RuntimeError(f"Infoblox returned existing record without _ref for {record.fqdn}")
            update_url = f"{self._wapi_base()}/{ref}"
            update_response = self.session.put(
                update_url,
                json=payload,
                timeout=self.settings.sync_timeout_seconds,
                verify=self.settings.sync_verify_ssl,
            )
            update_response.raise_for_status()
            return {
                "changed": True,
                "action": "updated",
                "fqdn": record.fqdn,
                "ip_address": record.ip_address,
            }

        create_response = self.session.post(
            query_url,
            json=payload,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        create_response.raise_for_status()
        return {
            "changed": True,
            "action": "created",
            "fqdn": record.fqdn,
            "ip_address": record.ip_address,
            "ref": create_response.json(),
        }
