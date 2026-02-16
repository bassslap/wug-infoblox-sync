# Azure Infrastructure

Placeholder for Azure resources that integrate with Infoblox IPAM.

## Suggested structure

```
main.tf               # Azure provider + core resources
variables.tf          # Variable definitions
outputs.tf            # Outputs (IPs, DNS names, etc.)
terraform.tfvars      # Your values (gitignored)
```

## Example use cases

- Azure VMs with Infoblox DDI integration
- Azure Functions for IPAM automation
- VNet/subnet allocation synced to Infoblox
