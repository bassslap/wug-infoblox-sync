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
proxmox_endpoint   = "https://your-proxmox:8006"
proxmox_api_token  = "root@pam!terraform=your-token-secret"
proxmox_host       = "your-proxmox-hostname"
vm_id              = 500
node_name          = "pve"
template_id        = 9000  # Your Ubuntu cloud image template
vm_ip_address      = "10.0.0.50"
gateway            = "10.0.0.1"
dns_zone           = "lab.local"
ssh_public_key_file = "~/.ssh/id_rsa.pub"
```

## Post-Deployment

SSH into the VM and configure WUG/Infoblox credentials:

```bash
ssh ubuntu@<vm-ip>
# Password: ubuntu123!

# Edit credentials
sudo vim /opt/wug-infoblox-sync/.env
# Update WUG_BASE_URL, WUG_USERNAME, WUG_PASSWORD
# Update INFOBLOX_BASE_URL, INFOBLOX_USERNAME, INFOBLOX_PASSWORD

# Start the service
sudo systemctl start wug-infoblox-sync
sudo systemctl status wug-infoblox-sync
```

## Test the Service

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

## Files

- `main.tf` - VM provisioning with bpg/proxmox provider
- `variables.tf` - Variable definitions
- `cloud-init.yml` - Ubuntu cloud-init template (auto-installs service)
- `terraform.tfvars.example` - Example configuration values

## Service Management

```bash
# View logs
sudo journalctl -u wug-infoblox-sync -f

# Restart service
sudo systemctl restart wug-infoblox-sync

# Stop service
sudo systemctl stop wug-infoblox-sync
```

## Notes

- The service auto-starts on boot after initial `.env` configuration
- Cloud-init sets up Python venv, installs dependencies, and creates systemd service
- Default VM credentials: `ubuntu` / `ubuntu123!`
- Service listens on `0.0.0.0:8080` inside the VM

