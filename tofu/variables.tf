variable "infoblox_server" {
  type = string
}

variable "infoblox_username" {
  type      = string
  sensitive = true
}

variable "infoblox_password" {
  type      = string
  sensitive = true
}

variable "network_view" {
  type    = string
  default = "default"
}

variable "cidr" {
  type = string
}

variable "fqdn" {
  type = string
}
