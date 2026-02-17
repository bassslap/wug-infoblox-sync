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

    def run_reverse_sync(self, dry_run: bool, limit: int | None = None) -> SyncResult:
        """
        Reverse sync: Import devices from Infoblox into WhatsUp Gold.
        
        Args:
            dry_run: If True, don't actually create devices in WUG
            limit: Optional limit on number of records to process
            
        Returns:
            SyncResult with details of import operation
        """
        # Get all host records from Infoblox
        infoblox_records = self.infoblox_client.get_all_host_records(limit=limit)
        details: list[dict[str, Any]] = []

        processed = 0
        created = 0
        skipped = 0
        errors = 0

        for record in infoblox_records:
            processed += 1
            hostname = record.get("hostname", "")
            ip_address = record.get("ip_address", "")
            
            if not hostname or not ip_address:
                skipped += 1
                details.append({
                    "hostname": hostname or "unknown",
                    "ip_address": ip_address or "unknown",
                    "action": "skipped",
                    "reason": "Missing hostname or IP address",
                })
                continue
            
            try:
                # Check if device already exists in WUG
                if self.wug_client.device_exists(ip_address):
                    skipped += 1
                    details.append({
                        "hostname": hostname,
                        "ip_address": ip_address,
                        "action": "skipped",
                        "reason": "Device already exists in WUG",
                    })
                    continue
                
                if dry_run:
                    created += 1
                    details.append({
                        "hostname": hostname,
                        "ip_address": ip_address,
                        "action": "dry-run-create",
                        "message": "Would create device in WUG",
                    })
                else:
                    # Create device in WUG
                    result = self.wug_client.create_device(
                        display_name=hostname,
                        ip_address=ip_address,
                        hostname=hostname,
                    )
                    
                    if result.get("success"):
                        created += 1
                        details.append({
                            "hostname": hostname,
                            "ip_address": ip_address,
                            "action": "created",
                            "device_id": result.get("device_id"),
                            "message": "Successfully created in WUG",
                        })
                    else:
                        errors += 1
                        details.append({
                            "hostname": hostname,
                            "ip_address": ip_address,
                            "action": "failed",
                            "error": result.get("message", "Unknown error"),
                        })
                        
            except Exception as exc:
                errors += 1
                details.append({
                    "hostname": hostname,
                    "ip_address": ip_address,
                    "action": "failed",
                    "error": str(exc),
                })

        return SyncResult(
            discovered=len(infoblox_records),
            processed=processed,
            created_or_updated=created,
            skipped=skipped,
            errors=errors,
            dry_run=dry_run,
            details=details,
        )

    @staticmethod
    def result_dict(result: SyncResult) -> dict[str, Any]:
        return asdict(result)
