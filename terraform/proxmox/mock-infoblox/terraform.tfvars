# Proxmox connection
proxmox_host     = "10.100.0.10"
api_user         = "terraform@pve"
api_token_name   = "chef"
api_token_value  = "c20e70d5-a5cf-4040-8c77-5fc5811a5692"

# VM configuration
vm_id        = 414
node_name    = "pve"
template_id  = 9001
vm_cores     = 1
vm_memory    = 1024
disk_size_gb = 32
storage_pool = "local-4tb"

# Network configuration
network_bridge     = "vmbr0"
vlan_tag           = 0
vm_ip_address      = "10.100.0.14"
subnet_bits        = 14
gateway            = "10.100.0.1"
ssh_public_key_file = "~/.ssh/id_rsa.pub"

# Tags
tags = ["mock", "infoblox", "testing"]
