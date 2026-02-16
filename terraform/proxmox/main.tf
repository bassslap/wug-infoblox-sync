terraform {
  required_version = ">= 1.6.0"
  required_providers {
    infoblox = {
      source  = "infobloxopen/infoblox"
      version = "~> 2.11"
    }
  }
}

provider "infoblox" {
  server   = var.infoblox_server
  username = var.infoblox_username
  password = var.infoblox_password
}

resource "infoblox_ip_allocation" "example" {
  network_view = var.network_view
  cidr         = var.cidr
  fqdn         = var.fqdn
}

output "allocated_ip" {
  value = infoblox_ip_allocation.example.allocated_ipv4_addr
}
