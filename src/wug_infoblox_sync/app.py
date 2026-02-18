from __future__ import annotations

import logging
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

from .config import load_settings
from .sync_service import SyncService
from .wug_client import WUGClient
from .infoblox_client import InfobloxClient
from .models import InfobloxHostRecord


def create_app() -> Flask:
    load_dotenv()
    settings = load_settings()

    logging.basicConfig(level=getattr(logging, settings.sync_log_level.upper(), logging.INFO))

    app = Flask(__name__)
    service = SyncService(settings)
    wug_client = WUGClient(settings)
    infoblox_client = InfobloxClient(settings)

    @app.get("/")
    def index():
        """Dashboard UI"""
        return render_template("index.html")

    @app.get("/api")
    def api_info() -> tuple:
        return jsonify({
            "service": "wug-infoblox-sync",
            "version": "1.0.0",
            "endpoints": {
                "GET /status": "Health check",
                "POST /sync": "Sync WUG devices to Infoblox (payload: {limit?: number})",
                "POST /dry-run": "Dry run WUG to Infoblox sync (payload: {limit?: number})",
                "POST /reverse-sync": "Sync Infoblox host records to WUG (payload: {limit?: number})",
                "POST /reverse-dry-run": "Dry run Infoblox to WUG sync (payload: {limit?: number})",
                "POST /add-test-device": "Add test device to WUG (payload: {display_name, ip_address, hostname?})",
                "POST /add-test-host": "Add test host record to Infoblox (payload: {hostname, ip_address, comment?})",
                "GET /wug-devices": "Get all devices from WUG",
                "GET /infoblox-hosts": "Get all host records from Infoblox"
            }
        }), 200

    @app.get("/status")
    def status() -> tuple:
        return jsonify({"service": "wug-infoblox-sync", "status": "ok"}), 200

    @app.get("/wug-devices")
    def get_wug_devices() -> tuple:
        """Get all devices from WUG"""
        try:
            limit = request.args.get("limit", type=int)
            devices = wug_client.get_devices(limit=limit)
            
            # Format devices for display
            device_list = []
            for device in devices:
                device_list.append({
                    "id": device.get("id"),
                    "name": device.get("displayName", device.get("name", "Unknown")),
                    "ip_address": device.get("primaryAddress", device.get("ipAddress", "N/A")),
                    "hostname": device.get("networkName", device.get("hostname", "N/A")),
                    "device_type": device.get("deviceType", "Unknown"),
                    "status": device.get("isUp", "Unknown")
                })
            
            return jsonify({
                "success": True,
                "count": len(device_list),
                "devices": device_list
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching WUG devices")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch devices from WUG"
            }), 500

    @app.get("/infoblox-hosts")
    def get_infoblox_hosts() -> tuple:
        """Get all host records from Infoblox"""
        try:
            limit = request.args.get("limit", type=int, default=1000)
            hosts = infoblox_client.get_all_host_records(limit=limit)
            
            # Format hosts for display
            # Note: get_all_host_records() transforms the API response:
            # - "name" becomes "hostname"  
            # - "ipv4addrs" becomes "ip_address"
            host_list = []
            for host in hosts:
                host_list.append({
                    "name": host.get("hostname", "Unknown"),
                    "ip_address": host.get("ip_address", "N/A"),
                    "comment": host.get("comment", ""),
                    "extattrs": host.get("extattrs", {})
                })
            
            return jsonify({
                "success": True,
                "count": len(host_list),
                "hosts": host_list
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching Infoblox hosts")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch host records from Infoblox"
            }), 500

    @app.delete("/infoblox-hosts/<hostname>")
    def delete_infoblox_host(hostname: str) -> tuple:
        """Delete a host record from Infoblox"""
        try:
            result = infoblox_client.delete_host_record(hostname)
            
            if result.get("success"):
                return jsonify({
                    "success": True,
                    "message": result.get("message"),
                    "hostname": hostname
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result.get("message"),
                    "hostname": hostname
                }), 404
                
        except Exception as e:
            logging.exception(f"Error deleting host {hostname}")
            return jsonify({
                "success": False,
                "error": str(e),
                "message": f"Failed to delete host record '{hostname}'"
            }), 500

    @app.post("/add-test-device")
    def add_test_device() -> tuple:
        """Add a test device to WUG"""
        payload = request.get_json(silent=True) or {}
        display_name = payload.get("display_name")
        ip_address = payload.get("ip_address")
        hostname = payload.get("hostname", ip_address)

        if not display_name or not ip_address:
            return jsonify({"error": "display_name and ip_address are required"}), 400

        try:
            # Check if device already exists
            if wug_client.device_exists(ip_address):
                return jsonify({
                    "error": f"Device with IP {ip_address} already exists in WUG",
                    "ip_address": ip_address
                }), 409

            # Add device to WUG
            result = wug_client.create_device(
                display_name=display_name,
                ip_address=ip_address,
                hostname=hostname,
                device_type="Windows",
                primary_role="Server",
                poll_interval=300
            )
            
            return jsonify({
                "success": True,
                "message": f"Device '{display_name}' added to WUG",
                "device": {
                    "display_name": display_name,
                    "ip_address": ip_address,
                    "hostname": hostname
                },
                "wug_response": result
            }), 201

        except Exception as e:
            logging.exception("Error adding test device")
            return jsonify({
                "error": str(e),
                "message": "Failed to add device to WUG"
            }), 500

    @app.post("/add-test-host")
    def add_test_host() -> tuple:
        """Add a test host record to Infoblox and device to WUG"""
        payload = request.get_json(silent=True) or {}
        hostname = payload.get("hostname")
        ip_address = payload.get("ip_address")
        comment = payload.get("comment", "")
        enable_monitoring = payload.get("enable_monitoring", True)

        if not hostname or not ip_address:
            return jsonify({"error": "hostname and ip_address are required"}), 400

        infoblox_result = None
        wug_result = None
        
        try:
            # Create InfobloxHostRecord object
            extattrs = {
                "Source": {"value": "Manual"},
                "Created": {"value": "Dashboard"}
            }
            if comment:
                extattrs["Comment"] = {"value": comment}
            
            host_record = InfobloxHostRecord(
                fqdn=hostname,
                ip_address=ip_address,
                network_view="default",
                extattrs=extattrs
            )
            
            # Add host record to Infoblox
            infoblox_result = infoblox_client.upsert_host_record(
                record=host_record,
                dry_run=False
            )
            
        except Exception as e:
            logging.exception("Error adding host to Infoblox")
            return jsonify({
                "error": str(e),
                "message": "Failed to add host record to Infoblox"
            }), 500
        
        # Try to add device to WUG (don't fail if this times out)
        try:
            if wug_client.device_exists(ip_address):
                wug_result = {
                    "success": False,
                    "message": f"Device with IP {ip_address} already exists in WUG",
                    "skipped": True
                }
            else:
                wug_result = wug_client.create_device(
                    display_name=hostname,
                    ip_address=ip_address,
                    hostname=hostname,
                    device_type="Server",
                    primary_role="Server",
                    poll_interval=300,
                    enable_monitoring=enable_monitoring
                )
        except Exception as e:
            logging.exception("Error adding device to WUG")
            wug_result = {
                "success": False,
                "message": f"WUG operation failed or timed out: {str(e)}",
                "error": True
            }
        
        # Build response
        message = f"Host '{hostname}' added to Infoblox"
        warning = None
        
        if wug_result and wug_result.get("success"):
            message += " and WUG"
        elif wug_result and wug_result.get("skipped"):
            message += " (device already in WUG)"
        elif wug_result and wug_result.get("error"):
            message += " (WUG operation failed)"
        elif wug_result and not wug_result.get("success"):
            # Check for license error
            wug_msg = wug_result.get("message", "")
            if "License" in wug_msg or "maximum devices" in wug_msg:
                warning = "⚠️ WUG License Limit: Cannot add more devices. Please remove unused devices or upgrade license."
                message += " (WUG license limit reached)"
            elif wug_result.get("errors"):
                error_msgs = wug_result.get("errors", [])
                if error_msgs:
                    first_error = error_msgs[0].get("messages", ["Unknown error"])[0] if isinstance(error_msgs, list) else str(error_msgs)
                    warning = f"⚠️ WUG Error: {first_error}"
                message += " (WUG error - see details)"
            else:
                message += " (WUG operation failed)"
            
        return jsonify({
            "success": True,
            "message": message,
            "warning": warning,
            "host": {
                "hostname": hostname,
                "ip_address": ip_address,
                "comment": comment,
                "monitoring_enabled": enable_monitoring
            },
            "infoblox_response": infoblox_result,
            "wug_response": wug_result
        }), 201

    @app.post("/sync")
    def sync() -> tuple:
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_sync(dry_run=False, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/dry-run")
    def dry_run() -> tuple:
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_sync(dry_run=True, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/reverse-sync")
    def reverse_sync() -> tuple:
        """Import devices from Infoblox into WhatsUp Gold"""
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_reverse_sync(dry_run=False, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/reverse-dry-run")
    def reverse_dry_run() -> tuple:
        """Dry run of importing devices from Infoblox into WhatsUp Gold"""
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_reverse_sync(dry_run=True, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    return app


def main() -> None:
    app = create_app()
    settings = load_settings()
    app.run(host=settings.flask_host, port=settings.flask_port)


if __name__ == "__main__":
    main()
