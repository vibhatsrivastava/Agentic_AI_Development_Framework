# Test Infrastructure for Drift Detection

> **Purpose:** Provision a test EC2 instance with tags to manually simulate drift for testing the Terraform Drift Detector agent.

This directory contains self-contained Terraform configuration for creating an AWS EC2 instance. You'll create the instance, manually remove a tag in the AWS Console to simulate drift, then run the drift detector agent to validate it detects the change.

---

## Prerequisites

Before running this test infrastructure, ensure you have:

1. **Terraform installed** (version >= 1.0)
   ```powershell
   # Verify installation
   terraform version
   ```

2. **AWS CLI configured** with valid credentials
   ```powershell
   # Verify AWS CLI is configured
   aws sts get-caller-identity
   ```
   
   If not configured, run:
   ```powershell
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region
   ```

3. **AWS IAM permissions** for EC2 operations:
   - `ec2:RunInstances`
   - `ec2:DescribeInstances`
   - `ec2:CreateTags`
   - `ec2:DeleteTags`
   - `ec2:TerminateInstances`
   - `ssm:GetParameter` (for fetching Amazon Linux 2023 AMI)

---

## Cost Information

**This configuration uses AWS Free Tier eligible resources:**

- **EC2 Instance:** t2.micro (750 hours/month free for first 12 months)
- **EBS Volume:** 8 GB gp3 (30 GB free per month)
- **Data Transfer:** Minimal (first 1 GB/month free)

**Estimated cost if outside Free Tier:** ~$0.01/hour ($7-8/month if left running)

**⚠️ IMPORTANT:** Always run `terraform destroy` after testing to avoid charges!

---

## Configuration

1. **Copy the example variables file:**
   ```powershell
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars`** (optional — defaults work for most users):
   ```hcl
   aws_region    = "us-east-1"
   instance_type = "t2.micro"
   instance_name = "drift-detector-test-instance"
   environment   = "production"
   owner         = "test-user"
   ```

---

## Testing Workflow

### Step 1: Provision the EC2 Instance

```powershell
# Initialize Terraform (downloads AWS provider)
terraform init

# Preview changes
terraform plan

# Create the EC2 instance
terraform apply
# Type 'yes' when prompted
```

**Expected output:**
```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "i-0123456789abcdef0"
instance_public_ip = "54.123.45.67"
instance_private_ip = "172.31.10.20"
ami_id = "ami-0abcdef1234567890"
state_file_path = "C:/Users/vsrivastava/.../test_infrastructure/terraform.tfstate"
tags = tomap({
  "Environment" = "production"
  "ManagedBy" = "terraform"
  "Name" = "drift-detector-test-instance"
  "Owner" = "test-user"
  "Project" = "drift-detector-demo"
})
```

**Save the `instance_id` — you'll need it for the next step!**

---

### Step 2: Verify Instance in AWS Console

1. Open [AWS EC2 Console](https://console.aws.amazon.com/ec2/v2/home)
2. Navigate to **Instances** → Select your instance (`drift-detector-test-instance`)
3. Click the **Tags** tab
4. Verify all 5 tags are present:
   - `Name`: drift-detector-test-instance
   - `Environment`: production ✅ ← **This is the tag we'll remove**
   - `Owner`: test-user
   - `Project`: drift-detector-demo
   - `ManagedBy`: terraform

---

### Step 3: Manually Simulate Drift (Remove a Tag)

**In AWS Console:**
1. Select your instance → Click **Tags** tab
2. Click **Manage tags**
3. **Remove the `Environment` tag** (click the X button next to it)
4. Click **Save**

**Or via AWS CLI:**
```powershell
# Replace with your actual instance ID
aws ec2 delete-tags --resources i-0123456789abcdef0 --tags Key=Environment
```

---

### Step 4: Run the Drift Detector Agent

```powershell
# Navigate to project root
cd ..

# Activate project virtual environment
.venv\Scripts\Activate.ps1

# Run the agent with the test infrastructure state file
python src/main.py --state-file test_infrastructure/terraform.tfstate
```

**Expected agent behavior:**
- ✅ Parses `terraform.tfstate` and extracts the EC2 instance with all 5 tags
- ✅ Fetches live AWS EC2 instance data
- ✅ Compares state vs. cloud and detects missing `Environment` tag
- ✅ Queries RAG vector store for policy violations
- ✅ Reports drift with severity: **HIGH** (missing required tag per `policies/tags.yaml`)
- ✅ Cites specific policy: `policies/tags.yaml → production.required_tags[0]`
- ✅ Provides remediation command: `terraform apply` or manual tag addition

**Sample agent output:**
```markdown
## Drift Analysis Report

### Summary
- **Total Resources Scanned:** 1
- **Resources with Drift:** 1
- **Critical Severity:** 0
- **High Severity:** 1 (missing required tag)
- **Medium Severity:** 0
- **Low Severity:** 0

### Drift Details

#### Resource: aws_instance.drift_test (i-0123456789abcdef0)

**Drift Type:** Missing Tag  
**Severity:** HIGH  
**Policy Violation:** Required tag "Environment" is missing

**Policy Citation:**
- File: `policies/tags.yaml`
- Section: `production.required_tags[0]`
- Rule: All production EC2 instances must have Environment tag

**Compliance Impact:**
- SOC2: Fails asset tagging requirement
- Cost Allocation: Instance excluded from production cost reports
- Backup Policy: Instance may not be included in automated backups

**Remediation:**
```bash
# Option 1: Restore tag manually
aws ec2 create-tags --resources i-0123456789abcdef0 --tags Key=Environment,Value=production

# Option 2: Re-apply Terraform
terraform apply
```
```

---

### Step 5: Verify Drift Detection

**Expected results:**
- ✅ Agent correctly identifies the missing `Environment` tag
- ✅ Agent classifies drift as **HIGH severity** (matches `policies/tags.yaml`)
- ✅ Agent provides specific policy citation with file path
- ✅ Agent suggests remediation commands

**Troubleshooting:**

| Issue | Solution |
|---|---|
| Agent doesn't detect drift | Verify tag was actually removed in AWS Console; check instance ID matches state file |
| AWS API errors | Verify AWS CLI credentials: `aws sts get-caller-identity` |
| State file not found | Use absolute path: `python src/main.py --state-file C:/Users/.../test_infrastructure/terraform.tfstate` |
| RAG vector store empty | Run `python src/main.py` once to initialize vector store from `policies/*.yaml` files |

---

### Step 6: Restore Tag (Optional)

To test that the agent reports **no drift** when tags match:

```powershell
# Restore the Environment tag
terraform apply
# Type 'yes' when prompted
```

Then re-run the agent:
```powershell
python src/main.py --state-file test_infrastructure/terraform.tfstate
```

**Expected output:** "No drift detected" (or minimal differences like timestamps)

---

### Step 7: Clean Up Resources

**⚠️ CRITICAL: Always destroy resources after testing to avoid AWS charges!**

```powershell
# Destroy the EC2 instance
terraform destroy
# Type 'yes' when prompted
```

**Verify destruction:**
```powershell
# Check no resources remain
terraform show
# Should output: "No state."
```

---

## Architecture

### Resources Created

| Resource | Type | Cost | Purpose |
|---|---|---|---|
| EC2 Instance | `t2.micro` | Free Tier | Test subject for drift detection |
| EBS Volume | 8 GB gp3 | Free Tier | Root volume for EC2 instance |
| Default VPC | Existing | Free | Network for EC2 instance |

### AMI Selection

The configuration uses a **Terraform data source** to fetch the latest Amazon Linux 2023 AMI:

```hcl
data "aws_ssm_parameter" "amazon_linux_2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
```

**Benefits:**
- ✅ **Region-agnostic:** Works in any AWS region without modification
- ✅ **Always latest:** Automatically uses newest Amazon Linux 2023 AMI
- ✅ **Free:** Amazon Linux 2023 has no license cost
- ✅ **Secure:** AWS-maintained with regular security updates

---

## Project Independence

**This directory is completely standalone:**
- ✅ Has its own Terraform state file (`terraform.tfstate`)
- ✅ Uses separate AWS provider configuration
- ✅ No imports/exports to parent project
- ✅ Can be deleted without breaking the drift detector agent

**After testing, you can safely delete this directory:**
```powershell
# Ensure resources are destroyed first
terraform destroy

# Then delete the directory
cd ..
rm -r test_infrastructure
```

The drift detector agent (`src/main.py`) will continue to work with any other `.tfstate` file.

---

## Next Steps

1. **Test other drift scenarios:**
   - Change instance type: `aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type t2.small`
   - Modify security groups: Add/remove security group rules in AWS Console
   - Change tags: Modify existing tag values

2. **Test with multiple resources:**
   - Add an S3 bucket to `main.tf`
   - Add an RDS instance to `main.tf`
   - Create drift on multiple resources simultaneously

3. **Test custom policies:**
   - Add new policy rules to `policies/*.yaml` files
   - Re-run agent to verify RAG retrieves custom policies

4. **Production usage:**
   - Point the agent at real production Terraform state files
   - Schedule automated drift detection with cron/Task Scheduler
   - Integrate with CI/CD pipeline for pre-deployment drift checks

---

## Troubleshooting

### Common Issues

**1. `terraform init` fails with provider download error**
- Check internet connectivity
- Verify Terraform version >= 1.0: `terraform version`
- Clear Terraform cache: `rm -r .terraform/` then re-run `terraform init`

**2. `terraform apply` fails with authentication error**
```
Error: error configuring Terraform AWS Provider: no valid credential sources for Terraform AWS Provider found.
```
- Run `aws configure` to set up AWS CLI credentials
- Verify credentials work: `aws sts get-caller-identity`
- Check AWS environment variables are not set incorrectly

**3. EC2 instance creation fails with VPC error**
- Verify your AWS account has a default VPC in the selected region
- If no default VPC, create one in AWS Console → VPC → Your VPCs → Actions → Create default VPC

**4. Agent doesn't detect drift after tag removal**
- Verify tag removal in AWS Console (refresh page to confirm)
- Check instance ID in state file matches AWS Console
- Ensure AWS CLI credentials are configured (agent uses boto3)

**5. Cost concerns**
- Instance should cost ~$0.01/hour outside Free Tier
- Always run `terraform destroy` after testing
- Set up AWS billing alerts in AWS Console → Billing Dashboard

---

## Additional Resources

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [Amazon Linux 2023 AMI Docs](https://docs.aws.amazon.com/linux/al2023/)
- [Project README](../README.md) — Main drift detector documentation
