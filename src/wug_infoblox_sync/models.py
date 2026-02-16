from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WUGDevice:
    source_id: str
    hostname: str
    ip_address: str
    status: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class InfobloxHostRecord:
    fqdn: str
    ip_address: str
    network_view: str
    extattrs: dict[str, dict[str, str]]


@dataclass(frozen=True)
class SyncResult:
    discovered: int
    processed: int
    created_or_updated: int
    skipped: int
    errors: int
    dry_run: bool
    details: list[dict[str, Any]]
