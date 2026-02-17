variable "proxmox_host" {
  description = "Proxmox host IP address"
  type        = string
}

variable "api_user" {
  description = "Proxmox API user"
  type        = string
}

variable "api_token_name" {
  description = "Proxmox API token name"
  type        = string
}

variable "api_token_value" {
  description = "Proxmox API token value"
  type        = string
  sensitive   = true
}

variable "vm_id" {
  description = "VM ID for the mock Infoblox server"
  type        = number
}

variable "node_name" {
  description = "Proxmox node name"
  type        = string
}

variable "template_id" {
  description = "Template VM ID to clone from"
  type        = number
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 1
}

variable "vm_memory" {
  description = "Memory in MB"
  type        = number
  default     = 1024
}

variable "disk_size_gb" {
  description = "Disk size in GB"
  type        = number
  default     = 32
}

variable "storage_pool" {
  description = "Proxmox storage pool"
  type        = string
}

variable "network_bridge" {
  description = "Network bridge"
  type        = string
}

variable "vlan_tag" {
  description = "VLAN tag (0 for no VLAN)"
  type        = number
  default     = 0
}

variable "vm_ip_address" {
  description = "Static IP address for the VM"
  type        = string
}

variable "subnet_bits" {
  description = "Subnet bits (e.g., 24 for /24)"
  type        = number
}

variable "gateway" {
  description = "Default gateway"
  type        = string
}

variable "ssh_public_key_file" {
  description = "Path to SSH public key file"
  type        = string
}

variable "tags" {
  description = "Tags for the VM"
  type        = list(string)
  default     = []
}
