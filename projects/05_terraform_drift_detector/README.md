# 05 — Terraform Drift Detector & Explainer

> **Difficulty:** Intermediate-Advanced  
> **Pattern:** ReAct Agent with RAG (Retrieval Augmented Generation)  
> **LangChain Components:** `ChatOllama`, `@tool`, `create_react_agent`, `Chroma`, `OllamaEmbeddings`, `boto3`

An intelligent drift detection agent that identifies discrepancies between Terraform state files and live AWS cloud resources, then explains **why they matter** by analyzing organizational policies using RAG.

---

## Table of Contents

1. [Objectives](#objectives)
2. [Approach & Architecture](#approach--architecture)
3. [Quick Start](#quick-start)
4. [Setup & Configuration](#setup--configuration)
5. [Usage Guide](#usage-guide)
6. [CLI Reference](#cli-reference)
7. [Integration Features](#integration-features)
8. [Policy Management](#policy-management)
9. [Testing & Validation](#testing--validation)
10. [Troubleshooting](#troubleshooting)
11. [Future Phases](#future-phases)
12. [Project Structure](#project-structure)

---

## Objectives

This project addresses **infrastructure governance** challenges by automating drift detection with intelligent policy enforcement.

### Business Objectives

- ✅ **Prevent security incidents** — Detect missing compliance tags and policy violations before they cause breaches
- ✅ **Control costs** — Identify untracked infrastructure changes that may increase cloud spend
- ✅ **Enable compliance audits** — Maintain audit trails linking drift to specific policy violations and frameworks (SOC2, HIPAA, PCI-DSS)
- ✅ **Accelerate incident response** — Automatically create GitHub issues and Teams notifications when drift is detected
- ✅ **Empower non-developers** — Allow security/compliance teams to define policies in YAML without touching code

### Technical Objectives

- ✅ Build a **ReAct agent** with LangGraph that orchestrates drift detection tools and RAG-based policy analysis
- ✅ Implement **RAG** (Retrieval Augmented Generation) to ground policy violations in actual organizational policies
- ✅ Support **multi-cloud potential** with extensible tool architecture (AWS now, designed for Azure/GCP)
- ✅ Provide **intelligent severity classification** using LLM analysis of drift impact
- ✅ Enable **automated remediation** with GitHub issue creation and Teams notifications
- ✅ Optimize **performance** with aggressive caching and Langfuse observability

---

## Approach & Architecture

### Why ReAct + RAG?

The project requires **two distinct layers of intelligence**:

1. **Drift Detection (Deterministic Logic)**
   - Parse Terraform state → extract desired resources
   - Query AWS API → fetch current state
   - Compute diffs → identify changes
   - Implemented as `@tool` functions (deterministic, reproducible)

2. **Policy Analysis (Semantic Reasoning)**
   - Retrieve relevant policies from vector store
   - LLM interprets policy + drift context → explains impact
   - LLM generates remediation recommendations
   - Requires RAG + reasoning (context-aware)

**ReAct agent** orchestrates both layers: decides when to call drift tools vs. RAG retriever, synthesizes results into structured reports.

### Why RAG is Essential

- **Policy Grounding:** Without RAG, LLM would hallucinate policy violations. RAG ensures all citations reference *actual policies* in `policies/*.yaml`
- **Maintainability:** Non-developers update policies in YAML. Agent automatically learns new policies—no code changes needed
- **Explainability:** Every violation cites specific file and section (e.g., `policies/tags.yaml → production.required_tags[0]`)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                TERRAFORM DRIFT DETECTOR AGENT                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌──────────────────┐              ┌──────────────────┐        │
│ │  Drift Detection │              │ Policy Analysis  │        │
│ │     (Tools)      │              │  (RAG + LLM)     │        │
│ └────────┬─────────┘              └────────┬─────────┘        │
│          │                                 │                  │
│ ┌────────▼──────────────┐     ┌───────────▼──────────┐       │
│ │ 1. Parse State        │     │ 4. Query RAG Vector  │       │
│ │ 2. Fetch AWS Resources│     │ 5. Retrieve Policies │       │
│ │ 3. Compute Diff       │     │ 6. LLM Analysis      │       │
│ └────────┬──────────────┘     └───────────┬──────────┘       │
│          │                              │                    │
│          └──────────────┬───────────────┘                    │
│                         │                                    │
│                    ┌────▼─────────┐                         │
│                    │ 7. Format    │                         │
│                    │ Markdown,    │                         │
│                    │ GitHub, Teams│                         │
│                    └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Prerequisites

```powershell
# Verify Ollama is running
ollama list

# Verify AWS credentials are configured
$env:AWS_ACCESS_KEY_ID
```

### 2. Install Dependencies

```powershell
cd projects/05_terraform_drift_detector
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
cp .env.example .env
notepad .env  # Add AWS credentials
```

### 4. Run Drift Check

```powershell
python src/main.py --check --workspace prod

# Output: Markdown report with detected drift + policy violations
```

---

## Setup & Configuration

### Step 1: Environment Variables

**Project `.env` (integration-specific):**

```env
# AWS Credentials (REQUIRED)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# Vector Store
CHROMA_COLLECTION_NAME=terraform_policies
CHROMA_PERSIST_DIR=./vector_store

# GitHub Integration (OPTIONAL)
GITHUB_TOKEN=ghp_your_token
GITHUB_OWNER=your_org_name
GITHUB_REPO=infrastructure_repo
GITHUB_ISSUE_STRATEGY=per-resource  # Options: per-resource, per-severity, summary
GITHUB_ISSUE_ENABLED=false
GITHUB_ISSUE_ASSIGNEE=@infrastructure-team

# Microsoft Teams (OPTIONAL)
TEAMS_WEBHOOK_URL=https://your-tenant.webhook.office.com/webhookb2/...
TEAMS_NOTIFICATION_ENABLED=false
```

**Root `.env` (inherited automatically):**

These come from repo root and are inherited by all projects:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
LOG_LEVEL=INFO
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://10.0.0.15:3000
```

### Step 2: AWS IAM Permissions

Required IAM policy (read-only):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeTags",
        "rds:DescribeDBInstances",
        "rds:ListTagsForResource",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Verify Setup

```powershell
# Test AWS credentials
aws s3 ls

# Test Ollama connection
curl http://localhost:11434/api/tags

# Initialize vector store
python src/main.py --check --workspace dev --rebuild-vector-store
```

---

## Usage Guide

### Mode 1: Check — Full Workspace Drift Scan

Scans all Terraform resources and generates comprehensive drift report.

```powershell
python src/main.py --check --workspace prod --state-file terraform.tfstate
```

**Output includes:**
- Total resources scanned, drifted, compliant counts
- Severity breakdown (Critical/High/Medium/Low)
- Per-resource details: ID, type, drift type, changes, policy violations
- Remediation commands

**Sample output:**
```
================================================================================
## Drift Analysis Report — Production Workspace (prod)
Scan completed: 2026-06-07 14:32:15 UTC
Total resources: 12 | Drifted: 3 | Compliant: 9

### Severity Summary
- CRITICAL: 1
- HIGH: 1
- MEDIUM: 1

### Critical Severity

Resource: aws_instance.web-prod-01 (i-0123456789abcdef0)
Drift Type: Tags Modified
├─ Removed tags: ["Environment"]

Policy Violation: policies/tags.yaml → production.required_tags[0]
├─ Severity: CRITICAL
├─ Impact: Instance not enrolled in automated backup schedule
├─ Compliance: SOC2 Section 4.2.1 - Data Retention

Remediation:
  terraform apply -target=aws_instance.web-prod-01

================================================================================
```

### Mode 2: Fix — Single Resource Remediation

Generates detailed remediation plan for a specific resource.

```powershell
python src/main.py --fix --workspace prod --resource i-0123456789abcdef0
```

### Real-World Example: GitHub Issue Output

When GitHub integration is enabled, the agent creates detailed GitHub issues. Here's an actual example from issue #81:

```markdown
## Drift Detection Alert
                
**Workspace:** `default`  
**Resource ID:** `i-07f8e56537fcd8ce7`  
**Resource Type:** `aws_instance`  
**Resource Name:** `drift_test`  
**Severity:** `CRITICAL`  

### Drift Details
**Type:** tag_mismatch

**Changes:**
- missing_tags_in_state: `['Environment', 'ManagedBy']`
- present_in_cloud_only: `[]`
- difference_summary: `State tags missing Environment and ManagedBy keys present in cloud.`

### ⚠️ Policy Violations

**Violation 1:**
- **Policy Violation:** policies/tags.yaml → environments.production.required_tags
- **Severity:** CRITICAL
- **Impact:** The Terraform state for the EC2 instance does not include the mandatory **Environment** tag (and consequently the **ManagedBy** tag is also absent). Production resources are governed by a strict enforcement policy that requires these tags to enforce environment segregation, cost allocation, and automated backup schedules. Without them, the instance cannot be reliably identified as production, making it impossible to apply backup policies or track ownership, thereby exposing the organization to data loss, audit failures, and regulatory non‑compliance.
- **Compliance Frameworks:** SOC2, HIPAA

**Violation 2:**
- **Policy Violation:** policies/compliance.yaml → frameworks.SOC2.sections[0].validation
- **Severity:** CRITICAL
- **Impact:** SOC2 Section 4.2.1 mandates that all production data stores—including EC2 instances—must carry the **Environment** and **Backup** tags to prove automated backup schedules and retention periods. The missing Environment tag in the Terraform state violates this requirement, meaning the instance cannot be audited for proper backup frequency or retention compliance. This jeopardizes audit readiness, increases risk of data loss, and could lead to regulatory penalties.
- **Compliance Frameworks:** SOC2

### Remediation
```bash
aws ec2 create-tags --resources i-07f8e56537fcd8ce7 \
  --tags Key=Environment,Value=production Key=ManagedBy,Value=terraform
```

---
*Generated by Terraform Drift Detector*
```

**What this example demonstrates:**

✅ **Intelligent drift detection** — Identifies missing tags and explains exactly which ones  
✅ **Policy-driven analysis** — References actual policy files (`policies/tags.yaml`, `policies/compliance.yaml`)  
✅ **Compliance mapping** — Links violations to frameworks (SOC2, HIPAA)  
✅ **Business impact** — Explains why drift matters (data loss, audit failures, regulatory penalties)  
✅ **Actionable remediation** — Provides exact AWS CLI commands to fix the drift  
✅ **Severity classification** — Clear CRITICAL label for urgent issues  

This is what makes the agent powerful: it doesn't just say "tag missing" — it explains why that matters to your organization and how to fix it.

---

## CLI Reference

```powershell
# Check mode
python src/main.py --check \
  --workspace <name> \
  [--state-file <path>] \
  [--rebuild-vector-store]

# Fix mode
python src/main.py --fix \
  --workspace <name> \
  --resource <aws_id> \
  [--state-file <path>]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--check` | ✅ | Full workspace scan |
| `--fix` | ✅ | Single resource remediation |
| `--workspace` | ✅ | Terraform workspace name |
| `--state-file` | ❌ | Path to `.tfstate` (default: `terraform.tfstate`) |
| `--resource` | ✅ for `--fix` | AWS resource ID (e.g., `i-abc123`) |
| `--rebuild-vector-store` | ❌ | Force rebuild RAG vector store |
| `--vector-store-dir` | ❌ | Vector store directory |

**Examples:**

```powershell
python src/main.py --check --workspace prod
python src/main.py --check --workspace staging --state-file terraform-staging.tfstate
python src/main.py --fix --workspace prod --resource i-0abc123def456
python src/main.py --check --workspace test --rebuild-vector-store
```

---

## Integration Features

### GitHub Integration

Automatically create GitHub issues for detected drift.

**Setup:**

1. Generate token: GitHub Settings → Developer Settings → Personal Access Tokens → `repo` scope
2. Configure `.env`:
   ```env
   GITHUB_TOKEN=ghp_your_token
   GITHUB_OWNER=your_org
   GITHUB_REPO=infrastructure_repo
   GITHUB_ISSUE_ENABLED=true
   ```

**Issue Strategies:**

| Strategy | Behavior |
|----------|----------|
| `per-resource` | One issue per drifted resource (default) |
| `per-severity` | One issue per severity level |
| `summary` | Single issue with all drift |

**Deduplication:** Searches for existing issues by workspace, resource ID, and type to prevent duplicates.

**Resource Ownership:** Edit `policies/teams.yaml` to assign issues to teams based on resource patterns:

```yaml
resource_ownership:
  ec2:
    default_owner: "@infrastructure-team"
    patterns:
      - pattern: "web-.*"
        owner: "@web-team"
      - pattern: "api-.*"
        owner: "@backend-team"
```

### Microsoft Teams Integration

Send formatted notifications to Teams channels.

**Setup:**

1. Teams Channel → More options (···) → Connectors → Incoming Webhook
2. Configure `.env`:
   ```env
   TEAMS_WEBHOOK_URL=https://your-tenant.webhook.office.com/webhookb2/...
   TEAMS_NOTIFICATION_ENABLED=true
   ```

**Notification includes:**
- Workspace name and timestamp
- Summary: total, drifted, compliant resources
- Severity breakdown
- Top 3 most severe resources
- Action buttons: View Details, GitHub Issues

---

## Policy Management

### Understanding Policies

Policies are YAML files in `policies/` that define compliance requirements.

**Policy files:**

| File | Purpose |
|------|---------|
| `policies/tags.yaml` | Required tags per environment |
| `policies/compliance.yaml` | SOC2, HIPAA, PCI framework mappings |
| `policies/security_groups.yaml` | Ingress/egress rule policies |
| `policies/teams.yaml` | Team ownership patterns |

### Customizing Policies

**Example: Add new required tag**

Edit `policies/tags.yaml`:
```yaml
production:
  required_tags:
    - Name
    - Environment
    - CostCenter
    - DataClassification  # NEW
    - BackupPolicy         # NEW
```

**Example: Add compliance framework**

Edit `policies/compliance.yaml`:
```yaml
GDPR:
  applies_to:
    - EU data processing
  requirements:
    - data_residency: "EU-only"
    - encryption: "mandatory"
```

**Rebuild vector store after changes:**

```powershell
python src/main.py --check --workspace test --rebuild-vector-store
```

### Policy Best Practices

- ✅ Keep policies **specific and testable**
- ✅ Include **compliance framework references** (SOC2, HIPAA, etc.)
- ✅ Document **business rationale** (why this policy exists)
- ✅ Review policies **quarterly** with security/compliance teams
- ✅ Test on **dev/staging** before production
- ✅ **Version control** policies in Git

---

## Testing & Validation

### Run Tests

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest --cov --cov-report=term-missing

# Run specific test file
pytest tests/test_main.py -v

# Verify coverage threshold
pytest --cov --cov-fail-under=75
```

**Test Coverage:**
- `tools/` — 85% ✅
- `main.py` — 80% ✅
- `integrations/` — 78% ✅
- `rag/` — 82% ✅

### Manual Testing

Test with real AWS resources:

```powershell
# 1. Provision test infrastructure
cd test_infrastructure
terraform init && terraform apply

# 2. Manually remove a tag in AWS Console to simulate drift

# 3. Run agent to detect drift
cd ..
python src/main.py --check --workspace test --state-file test_infrastructure/terraform.tfstate

# 4. Cleanup
cd test_infrastructure && terraform destroy
```

### Langfuse Tracing

View detailed traces in Langfuse dashboard:

```powershell
# Ensure LANGFUSE_ENABLED=true in root .env
# Run drift check
python src/main.py --check --workspace prod

# Open dashboard: http://10.0.0.15:3000
# Sessions tab → Filter by workspace name
# Review LLM calls, cache hit rates, latency breakdown
```

---

## Troubleshooting

### AWS Credential Errors

**Error:** `InvalidSignatureException` or `UnauthorizedOperation`

**Solution:**
1. Verify credentials in `.env`
2. Test: `aws s3 ls`
3. Check IAM policy has `Describe*` permissions
4. Verify credentials haven't expired

### Ollama Connection Errors

**Error:** `ConnectionError: Failed to connect to Ollama server`

**Solution:**
1. Verify Ollama is running: `ollama serve` in another terminal
2. Verify `OLLAMA_BASE_URL=http://localhost:11434` in root `.env`
3. Test: `curl http://localhost:11434/api/tags`
4. Check firewall isn't blocking port 11434

### Vector Store Issues

**Error:** `Vector store not found` or `Failed to load Chroma collection`

**Solution:**
1. Rebuild: `python src/main.py --check --workspace test --rebuild-vector-store`
2. Verify `CHROMA_PERSIST_DIR` directory exists and is writable
3. Check `policies/` directory contains `.yaml` files
4. Validate YAML: Use online YAML linter

### Drift False Positives

**Symptom:** Agent reports drift that doesn't actually exist

**Solution:**
1. Verify correct state file: `--state-file terraform.tfstate`
2. Verify AWS credentials have access to all resource types
3. Filter timestamp-based attributes that always differ
4. Check state file integrity: `terraform validate`

### GitHub Integration Issues

**Error:** `GitHub API rate limit exceeded`

**Solution:**
1. Verify token is valid and hasn't expired
2. Wait for rate limit reset (1 hour)
3. Consider GitHub App instead of PAT for higher limits

**Error:** `Failed to create issue: Repository not found`

**Solution:**
1. Verify `GITHUB_OWNER` and `GITHUB_REPO` in `.env`
2. Verify token has `repo` permission
3. Verify token can access the repository

### Teams Integration Issues

**Error:** `Teams notification failed: Invalid webhook URL`

**Solution:**
1. Verify `TEAMS_WEBHOOK_URL` is correct
2. Test webhook: 
   ```powershell
   $body = @{"text"="Test"} | ConvertTo-Json
   Invoke-WebRequest -Uri $TEAMS_WEBHOOK_URL -Method Post -Body $body
   ```
3. Webhook URL should start with `https://your-tenant.webhook.office.com/`

### Performance Issues

**Symptom:** Drift scan takes > 5 minutes

**Solution:**
1. Check cache hit rates in logs: `RAG cache: X.XX% hit rate`
2. Rebuild vector store if low hit rates
3. Check Ollama response time: `time curl http://localhost:11434/api/tags`
4. Check AWS API: `time aws ec2 describe-instances`
5. View Langfuse traces: http://10.0.0.15:3000

---

## Future Phases

### 🚧 Phase 3: Automated Remediation (Planned)

- GitHub slash command: `/fix-terraform-drift`
- Auto-execute `terraform apply` via AWX
- Validate remediation
- Auto-close issue on success

### 🚧 Phase 4: Analytics (Planned)

- Dashboard: drift trends over time
- Most common drift types
- Policy violation heatmaps
- Cost impact analysis
- Team-wise compliance scores

---

## Project Structure

```
05_terraform_drift_detector/
├── src/
│   ├── main.py                    # CLI + agent + GitHub/Teams orchestration
│   ├── llm_policy_analyzer.py     # LLM-based policy analysis
│   ├── impact_assessment_formatter.py # Violation formatting
│   ├── rag/
│   │   ├── __init__.py
│   │   └── vector_store.py        # Chroma + embeddings initialization
│   ├── tools/
│   │   ├── terraform_tools.py     # Terraform state parsing
│   │   ├── aws_tools.py           # AWS API (boto3)
│   │   ├── diff_tools.py          # Drift comparison (deepdiff)
│   │   ├── policy_tools.py        # RAG policy retrieval
│   │   └── github_tools.py        # GitHub API integration
│   ├── utils/
│   │   └── teams_parser.py        # teams.yaml parser
│   └── integrations/
│       └── teams_notifications.py # Teams adaptive cards
├── policies/
│   ├── tags.yaml                  # Tag requirements
│   ├── compliance.yaml            # Framework mappings
│   ├── security_groups.yaml       # Ingress/egress rules
│   └── teams.yaml                 # Resource ownership
├── docs/
│   └── terraform_best_practices.md
├── test_infrastructure/
│   ├── main.tf, outputs.tf, etc.  # Test resources
│   └── README.md                  # Testing guide
├── tests/
│   ├── conftest.py                # Fixtures
│   ├── test_terraform_tools.py
│   ├── test_aws_tools.py
│   ├── test_diff_tools.py
│   ├── test_policy_tools.py
│   ├── test_github_tools.py
│   ├── test_teams_notifications.py
│   ├── test_teams_parser.py
│   ├── test_vector_store.py
│   └── test_main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Additional Resources

- **Planner:** [planner/03_Terraform_Drift_Detector.md](../../planner/03_Terraform_Drift_Detector.md) — Use case, approach, design
- **LLM Integration:** [LLM_POLICY_ANALYZER_INTEGRATION.md](LLM_POLICY_ANALYZER_INTEGRATION.md) — Policy analysis details
- **Performance:** [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) — Caching, Langfuse, optimization
- **Testing:** [TESTING_GUIDE.md](TESTING_GUIDE.md) — Test validation procedures
- **Best Practices:** [docs/terraform_best_practices.md](docs/terraform_best_practices.md) — Infrastructure conventions
- **Repo Docs:** [../../docs/](../../docs/) — Common setup, LLM factory, Langfuse, vault

---

## Support

- **Questions?** Check [Troubleshooting](#troubleshooting) above
- **Found a bug?** Open GitHub issue with:
  - Error message and logs
  - Command and arguments
  - Terraform state file size (resource count)
  - AWS resources being checked
- **Contributing?** See [../../docs/contributing.md](../../docs/contributing.md)

---

## License

See repository root [LICENSE](../../LICENSE) file.
