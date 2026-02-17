from __future__ import annotations

import logging
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

from .config import load_settings
from .sync_service import SyncService
from .wug_client import WUGClient


def create_app() -> Flask:
    load_dotenv()
    settings = load_settings()

    logging.basicConfig(level=getattr(logging, settings.sync_log_level.upper(), logging.INFO))

    app = Flask(__name__)
    service = SyncService(settings)
    wug_client = WUGClient(settings)

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
                "POST /add-test-device": "Add test device to WUG (payload: {display_name, ip_address, hostname?})"
            }
        }), 200

    @app.get("/status")
    def status() -> tuple:
        return jsonify({"service": "wug-infoblox-sync", "status": "ok"}), 200

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
