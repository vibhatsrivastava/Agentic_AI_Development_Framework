# CI/CD Pipeline Documentation

This document describes the CI/CD pipeline implementation for the Agentic AI Development Framework.

## Table of Contents

1. [Overview](#overview)
2. [Workflows](#workflows)
3. [CODEOWNERS Setup](#codeowners-setup)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Manual Approvals](#manual-approvals)
7. [Security](#security)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The CI/CD pipeline consists of three main workflows:

1. **Test Workflow** (`test.yml`) - Automated testing on all pushes and PRs
2. **Copilot Implementation** (`copilot-implement.yml`) - Automated implementation triggered by CODEOWNERS
3. **Deployment** (`deploy.yml`) - Controlled deployment with manual approval for production

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Test Workflow │      │ Copilot Implement │      │ Deploy Workflow │
│   (test.yml)   │      │ (copilot-impl.yml)│      │   (deploy.yml)  │
└───────────────┘      └──────────────────┘      └─────────────────┘
        │                         │                         │
        ├─ Lint                   ├─ Validate CODEOWNER     ├─ Build & Test
        ├─ Test                   ├─ Parse Parameters       ├─ Deploy Staging
        └─ Coverage               ├─ Collect Context        └─ Deploy Prod
                                  └─ Trigger Copilot               (Manual)
```

---

## Workflows

### 1. Test Workflow (`test.yml`)

**Triggers:**
- Push to `main` or `dev` branches
- Pull requests targeting `main` or `dev`

**Jobs:**
- **test**: Runs on Python 3.13 and 3.14 matrix
  - Linting with `ruff`
  - Unit tests (excluding integration tests)
  - Coverage reporting (75% minimum)
  - Codecov upload
- **lint**: Code style checks

**Features:**
- Matrix testing across Python versions
- Coverage comments on PRs
- Automatic artifact upload

### 2. Copilot Implementation Workflow (`copilot-implement.yml`)

**Triggers:**
- Issue comments containing `/implement-plan` or `/approved`

**Jobs:**
- **validate-and-trigger**: Main orchestration job
  - Validates commenter is CODEOWNER
  - Parses optional parameters (branch, model)
  - Collects all issue context and comments
  - Assigns issue to copilot
  - Posts implementation context
  - Triggers GitHub Copilot (manual or automated)

**Command Format:**
```bash
# Basic usage (uses defaults)
/implement-plan

# With custom branch
/implement-plan branch=feature/my-feature

# With custom model
/implement-plan model=llama3.1:8b

# With both parameters
/implement-plan branch=feature/my-feature model=gpt-oss:20b

# Alternative command
/approved branch=hotfix/security-patch
```

**Default Values:**
- **Branch**: `copilot/issue-{issue_number}`
- **Model**: `gpt-oss:20b`

### 3. Deployment Workflow (`deploy.yml`)

**Triggers:**
- Push to `dev` → Auto-deploy to staging
- Push to `main` → Deploy to production (manual approval required)
- Manual trigger via `workflow_dispatch`

**Jobs:**
- **build**: Build and test before deployment
- **deploy-staging**: Automatic deployment to staging (dev branch only)
- **deploy-production**: Manual approval deployment to production (main branch only)
- **manual-deploy**: On-demand deployment via workflow dispatch

**Environments:**
- **staging**: Auto-deployed from `dev` branch
- **production**: Requires manual approval, deployed from `main` branch

---

## CODEOWNERS Setup

### File Location

```
/CODEOWNERS
```

### Format

```
# Default owner for all files
* @vibhatsrivastava

# Specific paths
/common/ @vibhatsrivastava
/.github/workflows/ @vibhatsrivastava @security-team
/projects/04_github_issue_reporter/ @vibhatsrivastava @api-team
```

### Configuring Code Owners

1. Edit the `CODEOWNERS` file in the repository root
2. Use GitHub usernames with `@` prefix
3. Use team names with `@org/team-name` format
4. More specific paths override general patterns

**Example:**
```
# Everyone needs approval from core team
* @vibhatsrivastava @core-team

# Security-sensitive paths require security team
/.github/ @security-team
/common/vault.py @security-team

# Project-specific owners
/projects/01_hello_langchain/ @langchain-experts
/projects/04_github_issue_reporter/ @github-integration-team
```

### Required Repository Settings

To enforce CODEOWNERS:

1. Go to repository **Settings** → **Branches**
2. Add branch protection rule for `main`:
   - ✅ Require pull request reviews before merging
   - ✅ Require review from Code Owners
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
   - ✅ Require conversation resolution before merging

---

## Usage

### Triggering Copilot Implementation

1. **CODEOWNER reviews the issue** and any recommendations from the agentic bot
2. **CODEOWNER adds comments** with additional requirements or changes
3. **CODEOWNER posts approval** using one of these commands:

```bash
# Basic approval with defaults
/implement-plan

# Custom branch name
/implement-plan branch=feature/issue-123-fix

# Custom LLM model
/implement-plan model=llama3.1:8b

# Both parameters
/approved branch=feature/new-auth model=gpt-oss:20b
```

4. **System validates** the commenter is a CODEOWNER
5. **System collects context:**
   - Issue title and description
   - All comments (including proposed changes)
   - Labels and metadata
6. **System prepares implementation:**
   - Assigns issue to copilot
   - Adds labels: `copilot-implementing`, `approved`
   - Posts confirmation with configuration
   - Creates implementation context comment
7. **Implementation happens:**
   - GitHub Copilot (or manual developer) implements on specified branch
   - Creates pull request
   - CODEOWNERS are requested for review

### Deployment Process

#### Automatic Staging Deployment

```
dev branch → Push → Build & Test → Auto-deploy to Staging
```

**Steps:**
1. Merge PR to `dev` branch
2. Test workflow runs automatically
3. If tests pass, staging deployment starts
4. Staging environment is updated
5. Notification posted to related PR

#### Manual Production Deployment

```
main branch → Push → Build & Test → Manual Approval → Deploy to Production
```

**Steps:**
1. Merge PR to `main` branch (requires CODEOWNER approval)
2. Test workflow runs automatically
3. Deployment workflow starts and waits
4. **CODEOWNER must approve** in GitHub Actions UI:
   - Navigate to **Actions** → **Deploy** workflow run
   - Click **Review deployments**
   - Select **production** environment
   - Click **Approve and deploy**
5. Production deployment executes
6. Deployment tag created
7. Notification posted

#### Manual Deployment (Any Branch)

For testing or emergency deployments:

1. Go to **Actions** → **Deploy** workflow
2. Click **Run workflow**
3. Select environment: `staging` or `production`
4. Enter branch/tag/commit SHA (optional)
5. Click **Run workflow**
6. For production, approve in UI when prompted

---

## Configuration

### Environment Variables

No environment variables are required for the CI/CD workflows themselves. However, deployment scripts may need:

```yaml
# Add to repository secrets (Settings → Secrets and variables → Actions)
OLLAMA_BASE_URL: https://your-ollama-server.com
OLLAMA_API_KEY: your_api_key
DEPLOY_SSH_KEY: your_deployment_ssh_key
DEPLOY_HOST: your-production-server.com
```

### GitHub Actions Secrets

Configure in **Settings** → **Secrets and variables** → **Actions**:

- `GITHUB_TOKEN`: Automatically provided by GitHub
- Add any deployment-specific secrets as needed

### Environment Protection Rules

Configure in **Settings** → **Environments**:

#### Staging Environment

- **Protection rules**: None (auto-deploy)
- **Deployment branches**: `dev` only

#### Production Environment

- **Protection rules**:
  - ✅ Required reviewers: Add CODEOWNERS
  - ✅ Wait timer: 0 minutes (immediate approval prompt)
- **Deployment branches**: `main` only
- **Secrets**: Add production-specific secrets here

---

## Manual Approvals

### Setting Up Environment Protection

1. Go to **Settings** → **Environments**
2. Click **New environment** or edit **production**
3. Configure protection rules:

```
Environment name: production

Protection rules:
☑ Required reviewers
  Add reviewers: @vibhatsrivastava, @team-leads
  
☑ Deployment branches
  Selected branches: main

Wait timer: 0 minutes (manual approval required immediately)
```

4. Save protection rules

### Approving Deployments

When a deployment to production is triggered:

1. **Notification**: You'll receive a GitHub notification
2. **Navigate**: Go to **Actions** → Find the running workflow
3. **Review**: Click the yellow "Review pending deployments" button
4. **Approve**: 
   - Review deployment details
   - Check commit SHA, branch, triggering user
   - Add optional comment
   - Click **Approve and deploy**
5. **Monitor**: Watch deployment logs in real-time

### Approval Best Practices

- ✅ **Verify commit**: Check what code is being deployed
- ✅ **Review changes**: Look at the PR that triggered deployment
- ✅ **Check tests**: Ensure all tests passed
- ✅ **Timing**: Deploy during business hours when team is available
- ✅ **Communication**: Notify team before approving large deployments
- ❌ **Never** approve blindly without reviewing changes

---

## Security

### Access Control

1. **CODEOWNERS Validation**:
   - Only users listed in `CODEOWNERS` can trigger implementations
   - Validation happens in workflow before any action
   - Unauthorized users receive error message

2. **Branch Protection**:
   - `main` branch requires PR reviews from CODEOWNERS
   - Status checks must pass before merging
   - Direct pushes to `main` are blocked

3. **Environment Protection**:
   - Production deployments require manual approval
   - Only CODEOWNERS can approve production deployments
   - All deployments are logged and auditable

### Secrets Management

- Never commit secrets to code
- Use GitHub Actions secrets for sensitive data
- Use environment-specific secrets when possible
- Rotate secrets regularly

### Audit Trail

All CI/CD actions are logged:
- Workflow runs in Actions tab
- Deployment history in Environments tab
- Issue comments show who triggered what
- Git tags mark production deployments

---

## Troubleshooting

### Issue: CODEOWNER command not working

**Symptoms**: Command `/implement-plan` doesn't trigger workflow

**Solutions**:
1. Check if user is in `CODEOWNERS` file
2. Verify command format is correct (starts with `/`)
3. Check workflow logs in Actions tab
4. Ensure workflow file has correct permissions

### Issue: Workflow fails with permission error

**Symptoms**: Workflow fails with "Resource not accessible by integration"

**Solutions**:
1. Check workflow permissions in YAML file
2. Verify repository settings allow Actions to create PRs
3. Go to **Settings** → **Actions** → **General**:
   - Set "Workflow permissions" to "Read and write permissions"
   - Enable "Allow GitHub Actions to create and approve pull requests"

### Issue: Production deployment not requiring approval

**Symptoms**: Production deployment starts without manual approval

**Solutions**:
1. Check environment protection rules:
   - **Settings** → **Environments** → **production**
   - Ensure "Required reviewers" is enabled
   - Add CODEOWNERS as required reviewers
2. Verify workflow uses `environment: production` in job definition

### Issue: Copilot not implementing after approval

**Symptoms**: Approval comment posted but no implementation happens

**Solutions**:
1. This is expected - automatic Copilot triggering requires Copilot for Business
2. Manual implementation:
   - Use GitHub Copilot Workspace on the issue
   - Or manually create branch and implement
   - Reference the implementation context comment
3. For automatic implementation, integrate with Copilot API (requires enterprise plan)

### Issue: Tests failing in CI but passing locally

**Symptoms**: Local tests pass, CI tests fail

**Solutions**:
1. Check Python version match (CI uses 3.13 and 3.14)
2. Verify all dependencies in `requirements-base.txt`
3. Check for environment-specific issues
4. Review integration tests (should be marked with `@pytest.mark.integration`)
5. Ensure `.env` variables not being used in tests

### Issue: Cannot push to repository

**Symptoms**: Workflow fails with "refusing to allow a GitHub App to create or update workflow"

**Solutions**:
1. Check workflow file location (must be in `.github/workflows/`)
2. Verify workflow syntax is correct
3. Ensure branch is not protected against workflow changes
4. Review repository settings for GitHub Actions permissions

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [About CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Copilot Workspace](https://github.com/features/copilot)

---

## Support

For issues or questions:
1. Check this documentation
2. Review workflow logs in Actions tab
3. Create an issue in the repository
4. Tag @vibhatsrivastava or relevant CODEOWNERS

---

*Last updated: 2026-05-15*
