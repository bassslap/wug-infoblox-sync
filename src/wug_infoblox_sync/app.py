from __future__ import annotations

import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv

from .config import load_settings
from .sync_service import SyncService


def create_app() -> Flask:
    load_dotenv()
    settings = load_settings()

    logging.basicConfig(level=getattr(logging, settings.sync_log_level.upper(), logging.INFO))

    app = Flask(__name__)
    service = SyncService(settings)

    @app.get("/status")
    def status() -> tuple:
        return jsonify({"service": "wug-infoblox-sync", "status": "ok"}), 200

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

    return app


def main() -> None:
    app = create_app()
    settings = load_settings()
    app.run(host=settings.flask_host, port=settings.flask_port)


if __name__ == "__main__":
    main()
