from .config import Settings
from .models import InfobloxHostRecord, WUGDevice


def device_to_infoblox_record(device: WUGDevice, settings: Settings) -> InfobloxHostRecord:
    normalized_host = device.hostname.strip().lower().replace(" ", "-")
    if "." not in normalized_host:
        normalized_host = f"{normalized_host}.local"

    extattrs = {
        "Source": {"value": "WhatsUpGold"},
        "WUG Device ID": {"value": device.source_id},
        "WUG Status": {"value": device.status},
    }

    return InfobloxHostRecord(
        fqdn=normalized_host,
        ip_address=device.ip_address,
        network_view=settings.infoblox_network_view,
        extattrs=extattrs,
    )
