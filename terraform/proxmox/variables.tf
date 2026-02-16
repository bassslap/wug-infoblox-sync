# Proxmox connection - BPG provider individual variables
variable "proxmox_host" {
  description = "Proxmox host IP or hostname"
  type        = string
}

variable "api_user" {
  description = "Proxmox API user (e.g., terraform@pve)"
  type        = string
}

variable "api_token_name" {
  description = "Proxmox API token name"
  type        = string
}

variable "api_token_value" {
  description = "Proxmox API token value (UUID)"
  type        = string
  sensitive   = true
}

variable "proxmox_insecure" {
  description = "Skip TLS verification for Proxmox API"
  type        = bool
  default     = true
}

variable "proxmox_ssh_user" {
  description = "SSH user for Proxmox host (for snippet upload)"
  type        = string
  default     = "root"
}

# VM configuration
variable "vm_id" {
  description = "VM ID number in Proxmox"
  type        = number
}

variable "node_name" {
  description = "Proxmox node name where VM will be created"
  type        = string
}

variable "template_id" {
  description = "Template VM ID to clone from (Ubuntu cloud image)"
  type        = number
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_memory" {
  description = "Memory in MB"
  type        = number
  default     = 2048
}

variable "disk_size_gb" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

variable "storage_pool" {
  description = "Storage pool name (e.g., local-lvm)"
  type        = string
}

# Network configuration
variable "network_bridge" {
  description = "Network bridge name (e.g., vmbr0)"
  type        = string
  default     = "vmbr0"
}

variable "vlan_tag" {
  description = "VLAN tag (0 = no VLAN)"
  type        = number
  default     = 0
}

variable "vm_ip_address" {
  description = "Static IP address for the VM"
  type        = string
}

variable "subnet_bits" {
  description = "Subnet mask bits (e.g., 24 for /24)"
  type        = number
  default     = 24
}

variable "gateway" {
  description = "Default gateway IP"
  type        = string
}

variable "dns_servers" {
  description = "List of DNS servers"
  type        = list(string)
  default     = ["8.8.8.8", "8.8.4.4"]
}

variable "dns_zone" {
  description = "DNS zone/domain for FQDN"
  type        = string
}

# VM credentials
variable "vm_user" {
  description = "Default VM user"
  type        = string
  default     = "ubuntu"
}

variable "vm_password" {
  description = "Password for VM user"
  type        = string
  sensitive   = true
  default     = "ubuntu123!"
}

variable "ssh_public_key_file" {
  description = "Path to SSH public key file"
  type        = string
}

# VM tags
variable "tags" {
  description = "List of tags for the VM"
  type        = list(string)
  default     = ["wug-sync", "automation"]
}

# WUG API credentials
variable "wug_base_url" {
  description = "WhatsUp Gold API base URL (e.g., https://wug.example.com:9644)"
  type        = string
}

variable "wug_username" {
  description = "WhatsUp Gold API username"
  type        = string
  sensitive   = true
}

variable "wug_password" {
  description = "WhatsUp Gold API password"
  type        = string
  sensitive   = true
}

# Infoblox API credentials
variable "infoblox_base_url" {
  description = "Infoblox WAPI base URL (e.g., https://infoblox.example.com)"
  type        = string
}

variable "infoblox_username" {
  description = "Infoblox API username"
  type        = string
  sensitive   = true
}

variable "infoblox_password" {
  description = "Infoblox API password"
  type        = string
  sensitive   = true
}
