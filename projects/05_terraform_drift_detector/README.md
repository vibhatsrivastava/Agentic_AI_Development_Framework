# 05 — Terraform Drift Detector & Explainer

> **Difficulty:** Intermediate-Advanced  
> **Pattern:** ReAct Agent with RAG (Retrieval Augmented Generation)  
> **LangChain Components:** `ChatOllama`, `@tool`, `create_react_agent`, `Chroma`, `OllamaEmbeddings`, `boto3`

An intelligent drift detection agent that identifies discrepancies between Terraform state files and live AWS cloud resources, then explains **why they matter** by analyzing organizational policies using RAG.

---

## Overview

### What Problem Does This Solve?

Manual changes to cloud infrastructure (emergency hotfixes, accidental modifications, testing) create **drift** between Terraform's desired state and reality. This causes:

- **Security risks:** Missing tags → instances lose backup policies, violate compliance
- **Cost overruns:** Instance types manually changed → unexpected AWS bills
- **Audit failures:** Security groups modified → compliance violations (SOC2, HIPAA, PCI)
- **Team confusion:** State file doesn't match reality → deployments fail

### How Does It Work?

1. **Parse Terraform state** (`.tfstate` files) to extract desired resource configurations
2. **Fetch live AWS resources** via boto3 API (EC2, RDS, S3, Security Groups)
3. **Compare state vs. cloud** using deepdiff to identify drift
4. **Analyze with RAG:** Query vector store of organizational policies (YAML files) to explain security/compliance impact
5. **Generate reports:** Structured markdown output with severity classification, policy violations, and remediation commands

**Key Innovation:** RAG ensures all policy violations cite **actual organizational policies** stored in `policies/*.yaml` files, eliminating LLM hallucination.

---

## Setup

### 1. Environment Variables

This project requires AWS credentials. Copy `.env.example` to `.env` and configure:

```powershell
cp .env.example .env
notepad .env  # Add your AWS credentials
```

**Required variables (add to project `.env`):**
```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Chroma Vector Store
CHROMA_COLLECTION_NAME=terraform_policies
CHROMA_PERSIST_DIR=./vector_store
```

**Root `.env` variables (inherited automatically):**
- `OLLAMA_BASE_URL` — Ollama server URL
- `OLLAMA_MODEL` — Default LLM model (e.g., `gpt-oss:20b`)
- `OLLAMA_EMBEDDING_MODEL` — Embedding model (e.g., `nomic-embed-text`)

### 2. AWS IAM Permissions

The agent requires read-only AWS permissions. Attach this IAM policy to your user/role:

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
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Install Dependencies

```powershell
# Activate project virtual environment
.venv\Scripts\Activate.ps1

# Dependencies are already installed during scaffold
# To reinstall:
uv pip install -r requirements.txt
```

### 4. Initialize RAG Vector Store

On first run, the agent automatically indexes policy files from `policies/` directory into the Chroma vector store:

```powershell
# Run with --rebuild-vector-store to force reindex
python src/main.py --check --workspace dev --rebuild-vector-store
```

**Policy files included:**
- `policies/tags.yaml` — Tag requirements per environment (prod, staging, dev)
- `policies/compliance.yaml` — Compliance framework mappings (SOC2, HIPAA, PCI)
- `policies/security_groups.yaml` — Ingress/egress rule policies
- `docs/terraform_best_practices.md` — Naming conventions, tagging strategy

**Customizing policies:** Edit YAML files in `policies/` directory and rebuild the vector store to update policy enforcement.

---

## Usage

### Check Mode — Full Workspace Drift Scan

Scans all resources in Terraform state file and generates drift report:

```powershell
python src/main.py --check --workspace prod --state-file terraform.tfstate
```

**Sample output:**
```markdown
================================================================================
## Drift Analysis Report — Production Workspace (prod)
**Scan completed:** 2026-05-23 14:32:15 UTC
**State file:** terraform.tfstate
**Total resources scanned:** 12  |  **Drifted:** 3  |  **Compliant:** 9

### Critical Severity (2 resources)

┌────────────────────────────────────────────────────────────────────────────┐
│  Resource: aws_instance.web-prod-01 (i-0123456789abcdef0)                 │
├────────────────────────────────────────────────────────────────────────────┤
│  Drift Type: Tags Modified                                                 │
│  ├─ Removed tags: ["Environment"]                                          │
│                                                                             │
│  ⚠️ Policy Violation: policies/tags.yaml → production.required_tags[0]    │
│  ├─ Severity: CRITICAL                                                     │
│  ├─ Impact: "Instance not enrolled in automated backup schedule"          │
│  ├─ Compliance Frameworks: SOC2 Section 4.2.1 - Data Retention           │
│                                                                             │
│  🔧 Remediation:                                                           │
│     terraform apply -target=aws_instance.web-prod-01                       │
└────────────────────────────────────────────────────────────────────────────┘

================================================================================
## Remediation Summary

Run the following commands to restore compliance:

```bash
terraform apply -target=aws_instance.web-prod-01
terraform apply -target=aws_security_group.web-sg
```
================================================================================
```

### Remediation Mode — Single Resource Fix Plan

Generates detailed remediation plan for a specific drifted resource:

```powershell
python src/main.py --fix --workspace prod --resource i-0123456789abcdef0
```

**Sample output:**
```markdown
================================================================================
## Remediation Plan — Resource: i-0123456789abcdef0
**Workspace:** prod

### Drift Details
**What Changed:** Environment tag removed

**Policy Violation:** policies/tags.yaml → production.required_tags[0]
**Impact:** Instance not enrolled in automated backup schedule

**Compliance Frameworks Affected:**
- SOC2 Section 4.2.1 - Data Retention
- HIPAA §164.308(a)(7)(ii)(A)

### Remediation Steps
1. Apply Terraform: `terraform apply -target=aws_instance.web-prod-01`
2. Verify tags: `aws ec2 describe-instances --instance-ids i-abc123`
3. Confirm backup enrollment in AWS Backup console
================================================================================
```

### CLI Options

```powershell
# Check mode options
python src/main.py --check \
  --workspace <workspace_name> \
  --state-file <path_to_tfstate> \
  [--rebuild-vector-store] \
  [--vector-store-dir <path>]

# Fix mode options
python src/main.py --fix \
  --workspace <workspace_name> \
  --resource <aws_resource_id> \
  --state-file <path_to_tfstate>
```

| Option | Description | Required |
|---|---|---|
| `--check` | Check mode: full workspace scan | Yes (mutually exclusive with `--fix`) |
| `--fix` | Fix mode: single resource remediation | Yes (mutually exclusive with `--check`) |
| `--workspace` | Terraform workspace name (alphanumeric + `_-`) | Yes |
| `--state-file` | Path to `.tfstate` file (default: `terraform.tfstate`) | No |
| `--resource` | AWS resource ID for fix mode (e.g., `i-abc123`) | Required for `--fix` |
| `--rebuild-vector-store` | Force rebuild of RAG vector store from policies | No |
| `--vector-store-dir` | Vector store directory (default: `./vector_store`) | No |

---

## Project Structure

```
05_terraform_drift_detector/
├── src/
│   ├── main.py                    # CLI entry point + agent builder
│   ├── rag/
│   │   ├── __init__.py
│   │   └── vector_store.py        # RAG initialization (Chroma + embeddings)
│   └── tools/
│       ├── __init__.py
│       ├── terraform_tools.py     # parse_terraform_state tool
│       ├── aws_tools.py           # fetch_cloud_resources tool (boto3)
│       ├── diff_tools.py          # compare_resources tool (deepdiff)
│       └── policy_tools.py        # analyze_drift_with_policies tool (RAG + LLM)
├── policies/
│   ├── tags.yaml                  # Tag requirements per environment
│   ├── compliance.yaml            # SOC2/HIPAA/PCI framework mappings
│   └── security_groups.yaml       # Ingress/egress rule policies
├── docs/
│   └── terraform_best_practices.md # Best practices documentation
├── vector_store/                  # Chroma vector store (auto-generated)
├── tests/
│   ├── conftest.py                # pytest fixtures (mock boto3, LLM, vector store)
│   ├── test_terraform_tools.py    # Tests for state parsing + redaction
│   ├── test_aws_tools.py          # Tests for AWS API calls (mocked with moto)
│   ├── test_diff_tools.py         # Tests for drift comparison
│   ├── test_policy_tools.py       # Tests for RAG policy analysis
│   ├── test_vector_store.py       # Tests for Chroma initialization
│   └── test_main.py               # Integration tests for agent + CLI
├── requirements.txt               # boto3, pyyaml, deepdiff, langchain-chroma
├── .env.example                   # AWS credentials template
└── README.md                      # This file
```

---

## Testing

All code maintains >= 75% test coverage (enforced via `pytest.ini`).

### Run Tests

```powershell
# Run all tests with coverage report
pytest --cov --cov-report=term-missing

# Run specific test module
pytest tests/test_terraform_tools.py -v

# Verify >= 75% coverage threshold
pytest --cov --cov-fail-under=75
```

### Test Strategy

- **Unit tests:** All tools tested in isolation with mocked dependencies
- **Mocking strategy:** 
  - boto3 calls mocked with `unittest.mock.MagicMock`
  - LLM calls mocked via `conftest.py` fixtures
  - Vector store mocked to return predefined policy documents
- **Integration tests:** End-to-end tests in `test_main.py` mock agent invocation but test CLI argument parsing and validation

**No real AWS API calls in tests** — all boto3 clients are mocked.

---

## Manual Integration Testing

To test the agent end-to-end with real AWS resources, use the provided test infrastructure:

### Quick Start

```powershell
# 1. Provision test EC2 instance with tags
cd test_infrastructure
terraform init
terraform apply

# 2. Manually remove a tag in AWS Console to simulate drift

# 3. Run the agent to detect drift
cd ..
python src/main.py --state-file test_infrastructure/terraform.tfstate

# 4. Clean up resources
cd test_infrastructure
terraform destroy
```

### Detailed Testing Guide

See [test_infrastructure/README.md](test_infrastructure/README.md) for:
- **Prerequisites:** AWS CLI setup, Terraform installation, IAM permissions
- **Cost information:** Free Tier eligibility, estimated costs
- **Step-by-step workflow:** EC2 provisioning → manual drift simulation → agent execution → cleanup
- **Expected results:** Sample agent output with drift detection and policy violations
- **Troubleshooting:** Common issues and solutions

**Why use test infrastructure?**
- ✅ **Isolated testing:** Self-contained AWS resources that won't affect production
- ✅ **Reproducible drift:** Controlled environment to simulate specific drift scenarios
- ✅ **Cost-effective:** Uses Free Tier eligible resources (t2.micro EC2 instance)
- ✅ **Independent:** Can be deleted after testing without breaking the agent

---

## Security Considerations

1. **Terraform state secrets:** Sensitive attributes (passwords, API keys) are redacted before passing to LLM. State files marked with `"sensitive": true"` have values replaced with `[REDACTED]`.

2. **AWS credentials:** Never logged or printed. Read exclusively via `require_env()` from `common/utils.py`.

3. **Prompt injection:** Resource names/tags from user-controlled sources are wrapped in XML delimiters (`<drift_details>...</drift_details>`) to prevent LLM instruction injection.

4. **Policy file integrity:** Policy files must be version-controlled (Git) and read-only to the agent.

5. **Rate limiting:** AWS API calls throttled to 2 req/sec using `common/rate_limiter.py` to stay under AWS limits.

---

## Advanced Usage

### Custom Policy Files

Add new policy files to `policies/` directory and rebuild vector store:

```powershell
# Create custom policy
notepad policies/cost_optimization.yaml

# Rebuild vector store to index new policy
python src/main.py --check --workspace dev --rebuild-vector-store
```

**Policy file format (YAML):**
```yaml
environments:
  production:
    required_tags:
      - name: CostCenter
        value: "^dept-.*"
        violations:
          missing: "Cannot allocate costs to department budget"
        compliance_frameworks:
          - framework: Internal
            section: "Cost Allocation Policy 2.3"
```

### Extending to Other Cloud Providers

To add Azure/GCP support:

1. Create new tool files: `src/tools/azure_tools.py`, `src/tools/gcp_tools.py`
2. Implement resource fetchers using azure-mgmt-resource SDK or google-cloud-resource-manager
3. Update `src/tools/__init__.py` to export new tools
4. Add provider-specific policies to `policies/` directory

---

## Troubleshooting

### Vector Store Initialization Fails

**Error:** `FileNotFoundError: Policies directory not found`

**Solution:** Ensure `policies/` directory exists and contains at least one `.yaml` file.

### AWS API Throttling

**Error:** `AWS API rate limit exceeded`

**Solution:** Reduce number of resources in state file or increase rate limit in `src/tools/aws_tools.py` (line 11: `TokenBucketRateLimiter(tokens_per_second=2)`).

### LLM Hallucinating Policy Violations

**Issue:** Agent reports policy violations not present in `policies/` files.

**Solution:** 
1. Verify vector store contains correct policies: `python src/main.py --check --workspace dev --rebuild-vector-store`
2. Check `SYSTEM_PROMPT` in `src/main.py` includes grounding instructions
3. Reduce RAG retrieval `k` parameter in `src/main.py` (line 88: `get_retriever(vector_store, k=5)`)

---

## Future Enhancements

- [ ] Support for Terraform Cloud API (remote state)
- [ ] Azure and GCP resource drift detection
- [ ] Automated remediation mode (apply Terraform fixes automatically)
- [ ] Web UI for drift visualization (Streamlit)
- [ ] CI/CD integration (GitHub Actions workflow)
- [ ] Slack/Teams notifications for critical drift
- [ ] Historical drift trend analysis

---

## License

This project is part of the Agentic AI Development Framework. See repository root LICENSE file.

## Resources

- [Repository Docs](../../docs/getting_started.md)
- [LangChain Documentation](https://docs.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.com/)

---

## License

See repository LICENSE file.
