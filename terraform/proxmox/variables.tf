# Proxmox connection
variable "proxmox_endpoint" {
  description = "Proxmox API endpoint (e.g., https://proxmox.example.com:8006)"
  type        = string
}

variable "proxmox_api_token" {
  description = "Proxmox API token (format: user@realm!tokenid=secret)"
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

variable "proxmox_host" {
  description = "Proxmox host IP or hostname for SCP operations"
  type        = string
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
