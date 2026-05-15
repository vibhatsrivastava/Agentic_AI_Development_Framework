# CI/CD Pipeline Quick Reference

Quick reference guide for using the CI/CD pipeline in the Agentic AI Development Framework.

---

## 🚀 Quick Commands

### Trigger Implementation
```bash
# Basic (uses defaults: branch=copilot/issue-N, model=gpt-oss:20b)
/implement-plan

# Custom branch
/implement-plan branch=feature/my-feature

# Custom model
/implement-plan model=llama3.1:8b

# Both parameters
/approved branch=feature/auth-fix model=gpt-oss:20b
```

### Deploy to Production
```bash
# 1. Merge to main (requires CODEOWNER approval)
# 2. Go to Actions → Deploy workflow
# 3. Click "Review deployments"
# 4. Approve production deployment
```

---

## 📋 Workflows

| Workflow | Trigger | Purpose | Auto/Manual |
|----------|---------|---------|-------------|
| **Test** | Push, PR | Lint, test, coverage | ✅ Auto |
| **Copilot Implement** | Issue comment `/implement-plan` or `/approved` | Trigger implementation | ✅ Auto (CODEOWNERS only) |
| **Teams Notifications** | PR opened, closed | Send Teams notifications with adaptive cards | ✅ Auto |
| **Deploy** (Staging) | Push to `dev` | Deploy to staging | ✅ Auto |
| **Deploy** (Production) | Push to `main` | Deploy to production | 🔐 Manual approval required |

---

## 🔐 CODEOWNERS

### Who Can Approve?

Only users listed in `/CODEOWNERS` can:
- Trigger `/implement-plan` or `/approved`
- Approve production deployments
- Merge PRs to protected branches

### Check Current CODEOWNERS

View the file: [`/CODEOWNERS`](../CODEOWNERS)

### Add New CODEOWNER

Edit `/CODEOWNERS`:
```bash
# Add user to all files
* @vibhatsrivastava @newowner

# Add user to specific path
/projects/my_project/ @newowner
```

---

## 🔄 Workflow: Issue to Implementation

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Issue Created                                             │
│    Developer or bot creates issue with problem/feature      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Analysis & Discussion                                     │
│    Team discusses, bot provides recommendations              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. CODEOWNER Approval                                        │
│    CODEOWNER comments: /implement-plan branch=X model=Y      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Validation                                                │
│    ✅ Check if commenter is CODEOWNER                        │
│    ✅ Parse branch and model parameters                      │
│    ✅ Collect all issue comments                             │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. Implementation Trigger                                    │
│    🤖 Issue assigned to copilot                              │
│    📋 Implementation context posted                          │
│    🏷️  Labels added: copilot-implementing, approved          │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. Implementation                                            │
│    GitHub Copilot or developer implements on branch          │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. Pull Request                                              │
│    PR created, CODEOWNERS requested for review               │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. Review & Merge                                            │
│    CODEOWNERS review and approve, merge to dev               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Flow

### Staging (Automatic)

```
dev branch → Push → Tests → ✅ Auto-deploy to Staging
```

**Timeline**: ~5 minutes from push to deployment

### Production (Manual Approval)

```
main branch → Push → Tests → ⏸️ Wait for Approval → ✅ Deploy to Production
```

**Timeline**: Tests ~5 minutes, then waits indefinitely for CODEOWNER approval

**Approval Process**:
1. GitHub notification sent to CODEOWNERS
2. Navigate to **Actions** tab
3. Find running "Deploy" workflow
4. Click yellow "Review deployments" button
5. Review details and approve
6. Deployment executes

---

## ⚙️ Configuration

### Default Parameters

```yaml
# Copilot Implementation
Default Branch: copilot/issue-{number}
Default Model:  gpt-oss:20b

# Deployment
Staging:    Auto-deploy from 'dev'
Production: Manual approval from 'main'
```

### Override Parameters

```bash
# In issue comment
/implement-plan branch=feature/custom-name model=llama3.1:8b

# Manual deployment (workflow_dispatch)
Actions → Deploy → Run workflow
  Environment: [staging/production]
  Ref: [branch/tag/SHA]
```

---

## 🛡️ Security & Permissions

### Required Permissions

**CODEOWNERS can:**
- ✅ Trigger implementations
- ✅ Approve production deployments
- ✅ Merge to protected branches

**Non-CODEOWNERS can:**
- ✅ Create issues
- ✅ Comment on issues
- ✅ Create PRs
- ❌ Trigger implementations
- ❌ Approve production deployments
- ❌ Merge to main

### Branch Protection

**main branch**:
- 🔒 Require PR reviews from CODEOWNERS
- 🔒 Require status checks to pass
- 🔒 No direct pushes

**dev branch**:
- ✅ Require status checks to pass
- ✅ Allow direct pushes from CODEOWNERS

---

## 🐛 Troubleshooting

### Command Not Working

**Problem**: `/implement-plan` doesn't trigger workflow

**Solutions**:
1. ✅ Are you a CODEOWNER? Check `/CODEOWNERS`
2. ✅ Is command at start of line? Must start with `/`
3. ✅ Check Actions tab for workflow run
4. ✅ Check workflow logs for errors

### Production Deployment Not Asking for Approval

**Problem**: Production deploys without approval

**Solutions**:
1. ✅ Check **Settings** → **Environments** → **production**
2. ✅ Enable "Required reviewers"
3. ✅ Add CODEOWNERS as reviewers
4. ✅ Set deployment branches to "main" only

### Tests Failing in CI

**Problem**: Tests pass locally, fail in CI

**Solutions**:
1. ✅ Check Python version (CI uses 3.13, 3.14)
2. ✅ Verify dependencies in `requirements-base.txt`
3. ✅ Integration tests marked with `@pytest.mark.integration`
4. ✅ Don't use `.env` values in tests

### Permission Errors

**Problem**: Workflow fails with "Resource not accessible"

**Solutions**:
1. Go to **Settings** → **Actions** → **General**
2. Set "Workflow permissions" to "Read and write"
3. Enable "Allow GitHub Actions to create PRs"

---

## 📚 Full Documentation

See [`docs/ci-cd.md`](ci-cd.md) for complete documentation including:
- Detailed workflow descriptions
- Environment setup
- Security best practices
- Advanced configuration
- Complete troubleshooting guide

### Microsoft Teams Notifications

See [`docs/teams-notifications.md`](teams-notifications.md) for Teams integration:
- Quick setup guide (5 minutes)
- Webhook configuration
- Adaptive card customization
- Troubleshooting common issues

Quick reference: [`docs/teams-notifications-quickref.md`](teams-notifications-quickref.md)

---

## 💡 Tips

1. **Use defaults**: For most cases, `/implement-plan` with defaults is sufficient
2. **Custom branches**: Use descriptive branch names: `feature/`, `bugfix/`, `hotfix/`
3. **Deploy timing**: Deploy to production during business hours when team is available
4. **Review before approve**: Always check what code is being deployed to production
5. **Communication**: Announce major deployments in team chat before triggering

---

## 📞 Support

**Need help?**
1. 📖 Read this quick reference
2. 📚 Check full docs: [`docs/ci-cd.md`](ci-cd.md)
3. 🔍 Review workflow logs in Actions tab
4. 💬 Create issue and tag @vibhatsrivastava

---

*Quick Reference v1.0 | Last updated: 2026-05-15*
