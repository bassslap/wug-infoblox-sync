terraform {
  required_version = ">= 1.6.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.50"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://${var.proxmox_host}:8006"
  api_token = "${var.api_user}!${var.api_token_name}=${var.api_token_value}"
  insecure  = true
  ssh {
    agent = true
  }
}

locals {
  basename = "mock-infoblox"
}

# Read the mock app content
data "local_file" "app_py" {
  filename = "${path.module}/app.py"
}

# Render cloud-init with app content embedded
resource "local_file" "mock_infoblox_userdata" {
  content = templatefile("${path.module}/cloud-init.yml", {
    hostname       = local.basename
    ip_address     = var.vm_ip_address
    subnet_bits    = var.subnet_bits
    gateway        = var.gateway
    ssh_public_key = file(pathexpand(var.ssh_public_key_file))
    app_content    = indent(6, data.local_file.app_py.content)
  })
  filename        = "${path.module}/tmp/${local.basename}-userdata.yml"
  file_permission = "0600"
}

# Copy snippet to Proxmox
resource "null_resource" "copy_snippet_to_proxmox" {
  triggers = {
    src_hash = local_file.mock_infoblox_userdata.content_sha1
  }

  provisioner "local-exec" {
    command = "scp -o ControlMaster=auto -o ControlPath=~/.ssh/control/%r@%h:%p -o ControlPersist=300 ${local_file.mock_infoblox_userdata.filename} root@${var.proxmox_host}:/var/lib/vz/snippets/"
  }

  depends_on = [local_file.mock_infoblox_userdata]
}

# Deploy the VM
resource "proxmox_virtual_environment_vm" "mock_infoblox" {
  name        = local.basename
  description = "Mock Infoblox WAPI Server for Testing"
  node_name   = var.node_name
  vm_id       = var.vm_id
  tags        = var.tags
  on_boot     = true

  clone {
    vm_id   = var.template_id
    full    = true
    retries = 1
  }

  agent {
    enabled = true
    timeout = "15m"
    trim    = true
    type    = "virtio"
  }

  cpu {
    cores   = var.vm_cores
    sockets = 1
    type    = "x86-64-v2-AES"
  }

  memory {
    dedicated = var.vm_memory
  }

  disk {
    interface    = "scsi0"
    datastore_id = var.storage_pool
    size         = var.disk_size_gb
    file_format  = "raw"
    aio          = "io_uring"
  }

  network_device {
    bridge  = var.network_bridge
    vlan_id = var.vlan_tag != 0 ? var.vlan_tag : null
  }

  initialization {
    datastore_id = var.storage_pool
    user_data_file_id = "local:snippets/${local.basename}-userdata.yml"
  }

  depends_on = [null_resource.copy_snippet_to_proxmox]
}

output "vm_ip" {
  value = var.vm_ip_address
}

output "vm_name" {
  value = local.basename
}

output "wapi_url" {
  value = "https://${var.vm_ip_address}/wapi/v2.12.3/"
}

output "ssh_command" {
  value = "ssh ubuntu@${var.vm_ip_address}"
}
