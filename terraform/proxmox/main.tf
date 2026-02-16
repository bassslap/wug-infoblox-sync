terraform {
  required_version = ">= 1.6.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.50"
    }
  }
}

provider "proxmox" {
  endpoint = var.proxmox_endpoint
  api_token = var.proxmox_api_token
  insecure  = var.proxmox_insecure
  
  ssh {
    agent    = true
    username = var.proxmox_ssh_user
  }
}

locals {
  basename = "wug-sync"
}

# Render cloud-init template to local file
resource "local_file" "wug_sync_userdata" {
  content = templatefile("${path.module}/cloud-init.yml", {
    hostname        = local.basename
    dns_zone        = var.dns_zone
    ip_address      = var.vm_ip_address
    gateway         = var.gateway
    subnet_bits     = var.subnet_bits
    dns_servers     = join(",", var.dns_servers)
    ssh_public_key  = trimspace(file(var.ssh_public_key_file))
  })
  filename = "${path.root}/tmp/wug-sync-userdata.yml"
}

# Copy cloud-init snippet to Proxmox
resource "null_resource" "copy_snippet_to_proxmox" {
  depends_on = [local_file.wug_sync_userdata]
  
  triggers = {
    src_hash = sha256(local_file.wug_sync_userdata.content)
  }

  provisioner "local-exec" {
    command = "scp -o ControlMaster=auto -o ControlPath=~/.ssh/control/%r@%h:%p -o ControlPersist=300 ${local_file.wug_sync_userdata.filename} root@${var.proxmox_host}:/var/lib/vz/snippets/"
  }
}

# Create VM from Ubuntu cloud image template
resource "proxmox_virtual_environment_vm" "wug_sync" {
  depends_on = [null_resource.copy_snippet_to_proxmox]
  
  vm_id       = var.vm_id
  node_name   = var.node_name
  name        = local.basename
  description = "WhatsUp Gold to Infoblox IPAM Sync Service"
  tags        = var.tags

  agent {
    enabled = true
    trim    = true
  }

  cpu {
    cores = var.vm_cores
    type  = "x86-64-v2-AES"
  }

  memory {
    dedicated = var.vm_memory
  }

  network_device {
    bridge  = var.network_bridge
    model   = "virtio"
    vlan_id = var.vlan_tag != 0 ? var.vlan_tag : null
  }
  
  # Disk
  disk {
    datastore_id = var.storage_pool
    interface    = "scsi0"
    iothread     = true
    size         = var.disk_size_gb
    file_format  = "raw"
  }
  
  # Clone from Ubuntu cloud image template
  clone {
    vm_id = var.template_id
    full  = true
  }

  initialization {
    ip_config {
      ipv4 {
        address = "${var.vm_ip_address}/${var.subnet_bits}"
        gateway = var.gateway
      }
    }
    
    user_account {
      keys     = [trimspace(file(var.ssh_public_key_file))]
      username = var.vm_user
      password = var.vm_password
    }
    
    dns {
      domain  = var.dns_zone
      servers = var.dns_servers
    }
    
    user_data_file_id = "local:snippets/wug-sync-userdata.yml"
  }

  operating_system {
    type = "l26"
  }

  started         = true
  template        = false
  stop_on_destroy = true
  on_boot         = true
}

output "vm_ip" {
  value       = var.vm_ip_address
  description = "Static IP address of the WUG-Infoblox sync VM"
}

output "vm_name" {
  value       = proxmox_virtual_environment_vm.wug_sync.name
  description = "Name of the VM"
}

output "ssh_command" {
  value       = "ssh ${var.vm_user}@${var.vm_ip_address}"
  description = "SSH command to connect to the VM (password: ${var.vm_password})"
}
