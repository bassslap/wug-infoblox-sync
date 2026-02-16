# wug-infoblox-sync

Minimal bridge service for syncing WhatsUp Gold devices into Infoblox IPAM host records, plus OpenTofu starter config for Infoblox IP allocation.

## What this includes

- Flask endpoints:
  - `GET /status`
  - `POST /dry-run` (no write)
  - `POST /sync` (writes to Infoblox)
- WUG API client with token auth and retry/backoff
- Infoblox WAPI client with host record upsert
- Mapping layer with extensible attributes for source parity (`WUG Device ID`, `WUG Status`)
- OpenTofu starter under `tofu/`

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m wug_infoblox_sync.app
```

## Example API usage

```bash
curl -s http://localhost:8080/status
curl -s -X POST http://localhost:8080/dry-run -H 'Content-Type: application/json' -d '{"limit": 25}'
curl -s -X POST http://localhost:8080/sync -H 'Content-Type: application/json' -d '{"limit": 25}'
```

## OpenTofu usage

```bash
cd tofu
cp terraform.tfvars.example terraform.tfvars
# edit values

tofu init
tofu plan
tofu apply
```

## Notes

- This service is intentionally minimal and stateless.
- Add a database/checkpoint store later if you want full reconciliation and delete handling.
- If your WUG schema differs, update parsing in `src/wug_infoblox_sync/wug_client.py`.
