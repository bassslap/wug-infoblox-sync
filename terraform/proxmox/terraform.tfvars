# Proxmox connection - Individual variables for BPG provider
proxmox_host     = "10.100.0.10"
api_user         = "terraform@pve"
api_token_name   = "chef"
api_token_value  = "c20e70d5-a5cf-4040-8c77-5fc5811a5692"

# VM configuration
vm_id        = 402
node_name    = "pve"
template_id  = 9001
vm_cores     = 2
vm_memory    = 2048
disk_size_gb = 32
storage_pool = "local-4tb"

# Network configuration
network_bridge  = "vmbr0"
vlan_tag        = 0
vm_ip_address   = "10.100.0.14"
subnet_bits     = 14
gateway         = "10.100.0.1"
dns_servers     = ["8.8.8.8", "8.8.4.4"]
dns_zone        = "lab.local"

# VM credentials
vm_user             = "ubuntu"
vm_password         = "ubuntu123!"
ssh_public_key_file = "~/.ssh/id_rsa.pub"

# Tags
tags = ["wug-sync", "automation", "infoblox"]

# WUG API credentials
wug_base_url  = "https://wug.local:9644"
wug_username  = "api_user"
wug_password  = "apiuser123!"

# Infoblox API credentials
infoblox_base_url  = "https://infoblox.local"
infoblox_username  = "admin"
infoblox_password  = "admin123!"
