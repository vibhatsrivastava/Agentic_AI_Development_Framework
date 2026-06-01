# Terraform Best Practices

## Resource Naming Conventions

All AWS resources should follow the naming pattern: `{service}-{environment}-{function}-{instance_number}`

**Examples:**
- `web-prod-api-01` — Production web API server instance 1
- `db-staging-mysql-01` — Staging MySQL database instance 1
- `cache-dev-redis-01` — Development Redis cache instance 1

**Benefits:**
- Clear identification of resource purpose and environment
- Easy cost allocation and filtering
- Consistent naming for automation scripts

## Tagging Strategy

### Mandatory Tags (All Environments)

| Tag | Purpose | Format | Example |
|---|---|---|---|
| Environment | Identifies deployment environment | prod, staging, dev | prod |
| Owner | Team responsible for resource | team-{name} | team-platform |
| CostCenter | Billing allocation | {department}-{project} | engineering-api |
| Name | Human-readable identifier | {service}-{env}-{function} | web-prod-api-01 |

### Production-Specific Tags

| Tag | Purpose | Format | Example |
|---|---|---|---|
| Backup | Backup frequency | daily, hourly, weekly | daily |
| Compliance | Compliance frameworks | SOC2, HIPAA, PCI | SOC2,HIPAA |
| DataClassification | Data sensitivity level | public, internal, confidential | confidential |

## Security Group Best Practices

### Ingress Rules

- **SSH access (port 22):** Restrict to VPN CIDR blocks only (e.g., 10.0.0.0/8)
- **Database ports (3306, 5432, 1433):** Restrict to application security group IDs only
- **HTTP/HTTPS (80, 443):** Can be open to 0.0.0.0/0 for public-facing services
- **Never use 0.0.0.0/0 for management ports** (SSH, RDP, database ports)

### Egress Rules

- **Production resources:** Restrict egress to HTTP/HTTPS only unless explicitly required
- **Database instances:** Deny all egress except to CloudWatch logs endpoint
- **Log all egress traffic:** Use VPC Flow Logs for audit trail

## State File Management

### Local State Files

- Store `.tfstate` files in version-controlled repository (Git)
- Use `.gitignore` to exclude sensitive state files from public repositories
- Encrypt state files at rest using git-crypt or similar tool

### Remote State (Recommended)

- Use Terraform Cloud or S3 backend with encryption
- Enable versioning on S3 backend
- Restrict access using IAM policies

## Drift Prevention Strategies

1. **Lock down production IAM permissions:** Use SCPs to prevent manual changes to Terraform-managed resources
2. **CloudTrail monitoring:** Alert on manual resource modifications
3. **Terraform Cloud Sentinel:** Enforce policies at plan time
4. **Regular drift scans:** Run `terraform plan` daily in CI/CD pipeline
5. **Change request process:** Require approval for production changes

## Resource Lifecycle

### Creation

1. Define resource in Terraform code
2. Add required tags (Environment, Owner, CostCenter)
3. Run `terraform plan` to preview changes
4. Get approval from team lead (for production)
5. Run `terraform apply`

### Updates

1. Modify Terraform code
2. Run `terraform plan` to see impact
3. Document reason for change in commit message
4. Apply changes during maintenance window (production)

### Deletion

1. Verify resource is no longer needed (check dependencies)
2. Take backup if resource contains data
3. Remove resource from Terraform code
4. Run `terraform plan` to confirm only intended resources will be destroyed
5. Run `terraform destroy -target=<resource>`

## Cost Optimization

- **Right-size instances:** Use t3 instances for variable workloads
- **Use Auto Scaling:** Scale down non-production resources outside business hours
- **Tag resources for cost allocation:** Enables cost tracking by team/project
- **Delete unused resources:** Run weekly scan for orphaned resources
