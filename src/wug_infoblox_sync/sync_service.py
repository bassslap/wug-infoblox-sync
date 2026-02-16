from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .config import Settings
from .infoblox_client import InfobloxClient
from .mapper import device_to_infoblox_record
from .models import SyncResult
from .wug_client import WUGClient


class SyncService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.wug_client = WUGClient(settings)
        self.infoblox_client = InfobloxClient(settings)

    def run_sync(self, dry_run: bool, limit: int | None = None) -> SyncResult:
        devices = self.wug_client.get_devices(limit=limit)
        details: list[dict[str, Any]] = []

        processed = 0
        changed = 0
        skipped = 0
        errors = 0

        for device in devices:
            processed += 1
            try:
                record = device_to_infoblox_record(device, self.settings)
                result = self.infoblox_client.upsert_host_record(record, dry_run=dry_run)
                changed += 1 if result.get("changed") else 0
                details.append(
                    {
                        "device_id": device.source_id,
                        "hostname": device.hostname,
                        "ip_address": device.ip_address,
                        "result": result,
                    }
                )
            except Exception as exc:
                errors += 1
                details.append(
                    {
                        "device_id": device.source_id,
                        "hostname": device.hostname,
                        "ip_address": device.ip_address,
                        "error": str(exc),
                    }
                )

        return SyncResult(
            discovered=len(devices),
            processed=processed,
            created_or_updated=changed,
            skipped=skipped,
            errors=errors,
            dry_run=dry_run,
            details=details,
        )

    @staticmethod
    def result_dict(result: SyncResult) -> dict[str, Any]:
        return asdict(result)
