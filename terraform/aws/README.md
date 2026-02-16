# AWS Infrastructure

Placeholder for AWS resources that integrate with Infoblox IPAM.

## Suggested structure

```
main.tf               # AWS provider + core resources
variables.tf          # Variable definitions
outputs.tf            # Outputs (IPs, DNS names, etc.)
terraform.tfvars      # Your values (gitignored)
```

## Example use cases

- EC2 instances with Infoblox DDI integration
- Lambda functions for IPAM automation
- VPC/subnet allocation synced to Infoblox
