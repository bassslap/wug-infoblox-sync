# Proxmox Deployment for WUG-Infoblox Sync

Deploy the sync service as an Ubuntu VM on Proxmox using Terraform/OpenTofu.

## Prerequisites

- Proxmox VE cluster with API access
- Ubuntu Cloud Image template created in Proxmox (e.g., VM ID 9000)
- SSH key pair for VM access
- SSH control socket directory: `mkdir -p ~/.ssh/control`

## Quick Start

```bash
cd terraform/proxmox

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Required Configuration

Edit `terraform.tfvars` with your values:

```hcl
# Proxmox
proxmox_host       = "10.100.0.10"
api_user           = "terraform@pve"
api_token_name     = "chef"
api_token_value    = "your-token-uuid"

# VM settings
vm_id              = 402
vm_ip_address      = "10.0.0.50"
gateway            = "10.0.0.1"
dns_zone           = "lab.local"
ssh_public_key_file = "~/.ssh/id_rsa.pub"

# WUG API credentials
wug_base_url       = "https://wug.example.com:9644"
wug_username       = "api_user"
wug_password       = "your-wug-password"

# Infoblox API credentials
infoblox_base_url  = "https://infoblox.example.com"
infoblox_username  = "admin"
infoblox_password  = "your-infoblox-password"
```

## Post-Deployment

The VM automatically:
- Clones the GitHub repo to `/opt/wug-infoblox-sync`
- Sets up Python venv and installs dependencies
- Creates `.env` with your credentials
- Starts the sync service

**Test the service (wait ~2 minutes for cloud-init):**

```bash
# Check service health
curl http://<vm-ip>:8080/status

# Dry-run test (no writes)
curl -X POST http://<vm-ip>:8080/dry-run \
  -H 'Content-Type: application/json' \
  -d '{"limit": 10}'

# Perform actual sync
curl -X POST http://<vm-ip>:8080/sync \
  -H 'Content-Type: application/json' \
  -d '{"limit": 10}'
```

## SSH Access

```bash
ssh ubuntu@<vm-ip>
# Password: ubuntu123!

# View logs
sudo journalctl -u wug-infoblox-sync -f

# Restart service
sudo systemctl restart wug-infoblox-sync
```

## Files

- `main.tf` - VM provisioning with bpg/proxmox provider
- `variables.tf` - Variable definitions including WUG/Infoblox credentials
- `cloud-init.yml` - Ubuntu cloud-init template (auto-installs service with credentials)
- `terraform.tfvars.example` - Example configuration values

## Service Management

```bash
# View logs
sudo journalctl -u wug-infoblox-sync -f

# Check status
sudo systemctl status wug-infoblox-sync

# Restart service
sudo systemctl restart wug-infoblox-sync

# Stop service
sudo systemctl stop wug-infoblox-sync

# Edit credentials (requires restart)
sudo vim /opt/wug-infoblox-sync/.env
sudo systemctl restart wug-infoblox-sync
```

## Notes

- Credentials are passed via Terraform and automatically configured in `.env`
- The service auto-starts on boot
- Cloud-init sets up Python venv, installs dependencies, and creates systemd service
- Default VM credentials: `ubuntu` / `ubuntu123!`
- Service listens on `0.0.0.0:8080` inside the VM
- Credentials are marked `sensitive = true` in Terraform (not shown in plan output)

