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
        """
        Get devices from WUG by iterating through device groups.
        Uses /device-groups/- endpoint followed by /device-groups/{groupId}/devices
        """
        token = self._token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        
        # First get all device groups
        base_url = self.settings.wug_base_url.rstrip('/')
        groups_endpoint = f"{base_url}/api/v1/device-groups/-"
        
        groups_response = self.session.get(
            groups_endpoint,
            headers=headers,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        groups_response.raise_for_status()
        groups_data = groups_response.json()
        
        if not isinstance(groups_data, dict) or 'data' not in groups_data:
            return []
        
        groups = groups_data['data'].get('groups', [])
        
        # Get devices from each group
        all_devices: list[WUGDevice] = []
        seen_device_ids = set()
        
        for group in groups:
            group_id = group.get('id')
            group_name = group.get('name', 'Unknown')
            
            if not group_id:
                continue
            
            try:
                devices_endpoint = f"{base_url}/api/v1/device-groups/{group_id}/devices"
                devices_response = self.session.get(
                    devices_endpoint,
                    headers=headers,
                    timeout=self.settings.sync_timeout_seconds,
                    verify=self.settings.sync_verify_ssl,
                )
                devices_response.raise_for_status()
                devices_data = devices_response.json()
                
                if isinstance(devices_data, dict) and 'data' in devices_data:
                    devices = devices_data['data'].get('devices', [])
                    
                    for item in devices:
                        if not isinstance(item, dict):
                            continue
                        
                        device_id = str(item.get("id") or item.get("deviceId") or "")
                        
                        # Skip duplicates
                        if device_id in seen_device_ids:
                            continue
                        
                        hostname = str(item.get("displayName") or item.get("hostName") or item.get("name") or "")
                        ip = str(
                            item.get("networkAddress")
                            or item.get("ipAddress")
                            or item.get("primaryAddress")
                            or ""
                        )
                        status = str(item.get("bestState") or item.get("state") or item.get("status") or "unknown")
                        
                        if not device_id or not ip:
                            continue
                        
                        # Add group information to raw data
                        item['group_id'] = group_id
                        item['group_name'] = group_name
                        
                        all_devices.append(
                            WUGDevice(
                                source_id=device_id,
                                hostname=hostname or f"wug-{device_id}",
                                ip_address=ip,
                                status=status,
                                raw=item,
                            )
                        )
                        seen_device_ids.add(device_id)
                        
                        if limit and len(all_devices) >= limit:
                            return all_devices
            
            except Exception as e:
                # Log warning but continue with other groups
                print(f"Warning: Failed to get devices from group {group_name}: {e}")
                continue
        
        return all_devices

    def device_exists(self, ip_address: str) -> bool:
        """
        Check if a device with the given IP address already exists in WUG.
        """
        devices = self.get_devices()
        return any(d.ip_address == ip_address for d in devices)

    def create_device(
        self,
        display_name: str,
        ip_address: str,
        hostname: str | None = None,
        device_type: str = "Network Device",
        primary_role: str = "Device",
        poll_interval: int = 60,
    ) -> dict[str, Any]:
        """
        Create a new device in WhatsUp Gold using the device template endpoint.
        Based on the working implementation from netbox-wug-sync.
        
        Args:
            display_name: Display name for the device
            ip_address: IP address of the device
            hostname: Hostname (optional, defaults to display_name)
            device_type: Device type (optional)
            primary_role: Primary role (optional)
            poll_interval: Polling interval in seconds (optional)
            
        Returns:
            Dictionary with creation result including device ID
        """
        token = self._token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if hostname is None:
            hostname = display_name
        
        # Build device template payload based on WUG API schema
        device_template = {
            "displayName": display_name,
            "deviceType": device_type,
            "primaryRole": primary_role,
            "pollIntervalSeconds": poll_interval,
            "interfaces": [
                {
                    "defaultInterface": True,
                    "pollUsingNetworkName": False,
                    "networkAddress": ip_address,
                    "networkName": hostname,
                }
            ],
            "attributes": [],
            "customLinks": [],
            "activeMonitors": [{"classId": "", "Name": "Ping"}],
            "performanceMonitors": [],
            "passiveMonitors": [],
            "dependencies": [],
            "ncmTasks": [],
            "applicationProfiles": [],
            "layer2Data": "",
            "groups": [],
        }
        
        body = {"options": ["all"], "templates": [device_template]}
        
        base_url = self.settings.wug_base_url.rstrip('/')
        endpoint = f"{base_url}/api/v1/devices/-/config/template"
        
        response = self.session.patch(
            endpoint,
            json=body,
            headers=headers,
            timeout=self.settings.sync_timeout_seconds,
            verify=self.settings.sync_verify_ssl,
        )
        response.raise_for_status()
        data = response.json()
        
        if data and "data" in data:
            result_data = data["data"]
            
            # Check for errors
            if "errors" in result_data and result_data["errors"]:
                errors = result_data["errors"]
                return {
                    "success": False,
                    "message": f"Device creation had errors: {errors}",
                    "errors": errors,
                }
            
            # Get device ID from response
            if "idMap" in result_data and result_data["idMap"]:
                device_id = result_data["idMap"][0].get("resultId")
                return {
                    "success": True,
                    "device_id": device_id,
                    "display_name": display_name,
                    "ip_address": ip_address,
                    "hostname": hostname,
                }
            else:
                return {
                    "success": False,
                    "message": "Device creation response missing device ID",
                    "response_data": result_data,
                }
        else:
            return {"success": False, "message": "Invalid API response format"}
