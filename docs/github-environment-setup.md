# GitHub Environment Setup Guide

This guide walks through setting up GitHub Environments and protection rules for the CI/CD pipeline.

## Prerequisites

- Repository admin access
- CODEOWNERS file committed to the repository
- CI/CD workflows deployed

---

## Step 1: Enable GitHub Actions Permissions

1. Navigate to **Settings** → **Actions** → **General**

2. Under **"Workflow permissions"**, select:
   - ✅ **Read and write permissions**
   
3. Under **"Workflow permissions"**, also enable:
   - ✅ **Allow GitHub Actions to create and approve pull requests**

4. Click **Save**

**Why this matters**: These permissions allow workflows to:
- Create issue comments
- Assign issues
- Add labels
- Create pull requests
- Post deployment notifications

---

## Step 2: Create Staging Environment

1. Navigate to **Settings** → **Environments**

2. Click **New environment**

3. Enter environment name: `staging`

4. Click **Configure environment**

5. **Protection rules** (for staging):
   - ⬜ Leave "Required reviewers" **unchecked** (auto-deploy)
   - ⬜ Leave "Wait timer" **unchecked**

6. **Deployment branches** (optional but recommended):
   - Select **Selected branches**
   - Add branch: `dev`
   - This restricts staging deployments to the `dev` branch only

7. **Environment secrets** (if needed):
   - Add any staging-specific secrets
   - Example: `DEPLOY_HOST_STAGING`, `DATABASE_URL_STAGING`

8. Click **Save protection rules**

---

## Step 3: Create Production Environment

1. Still in **Settings** → **Environments**, click **New environment**

2. Enter environment name: `production`

3. Click **Configure environment**

4. **Protection rules** (for production):
   
   a. **Required reviewers**:
   - ✅ **Check** "Required reviewers"
   - Click **Add reviewers**
   - Add CODEOWNERS (e.g., `@vibhatsrivastava`)
   - You can add multiple reviewers or teams (e.g., `@org/release-team`)
   - Set required number of approvals (default: 1)
   
   b. **Wait timer** (optional):
   - ⬜ Leave **unchecked** for immediate approval prompt
   - OR set a wait time (e.g., 5 minutes) for a mandatory delay
   
   c. **Prevent self-review** (recommended):
   - ✅ **Check** "Prevent self-review" if available
   - This prevents the person who triggered deployment from approving it

5. **Deployment branches**:
   - Select **Selected branches**
   - Add branch: `main`
   - This restricts production deployments to the `main` branch only

6. **Environment secrets** (production-specific):
   - Add production secrets here
   - Example: `DEPLOY_HOST_PRODUCTION`, `DATABASE_URL_PRODUCTION`, `API_KEY_PRODUCTION`
   - These secrets override repository secrets when deploying to production

7. Click **Save protection rules**

---

## Step 4: Set Up Branch Protection Rules

### Protect the `main` Branch

1. Navigate to **Settings** → **Branches**

2. Click **Add branch protection rule**

3. **Branch name pattern**: `main`

4. Configure protections:

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: `1` (or more)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require review from Code Owners
   - ⬜ Require approval of the most recent reviewable push (optional, stricter)
   
   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - Add required status checks:
     - `test` (from test.yml workflow)
     - `lint` (from test.yml workflow)
     - `build` (from deploy.yml workflow)
   
   ✅ **Require conversation resolution before merging**
   
   ✅ **Require signed commits** (optional, for higher security)
   
   ⬜ **Require linear history** (optional, prevents merge commits)
   
   ✅ **Do not allow bypassing the above settings**
   - Uncheck "Allow force pushes"
   - Uncheck "Allow deletions"
   
   **Note**: You may want to allow administrators to bypass these settings during emergencies

5. Click **Create** or **Save changes**

### Protect the `dev` Branch (Optional but Recommended)

1. Click **Add branch protection rule** again

2. **Branch name pattern**: `dev`

3. Configure protections (lighter than main):

   ✅ **Require status checks to pass before merging**
   - Add required status checks:
     - `test` (from test.yml workflow)
   
   ⬜ **Require a pull request before merging** (optional)
   - If checked, requires PRs even for CODEOWNERS
   - If unchecked, allows CODEOWNERS to push directly
   
   ⬜ **Do not allow bypassing the above settings**
   - Consider allowing administrators to bypass

4. Click **Create**

---

## Step 5: Configure Repository Secrets

1. Navigate to **Settings** → **Secrets and variables** → **Actions**

2. Click **New repository secret**

3. Add the following secrets (as needed):

   | Secret Name | Description | Example |
   |-------------|-------------|---------|
   | `OLLAMA_BASE_URL` | Ollama server URL (if using remote) | `https://ollama.example.com` |
   | `OLLAMA_API_KEY` | Ollama API key (if using remote) | `your_bearer_token` |
   | `DEPLOY_SSH_KEY` | SSH key for deployment | `-----BEGIN PRIVATE KEY-----...` |
   | `DEPLOY_HOST` | Deployment server hostname | `production.example.com` |

4. Click **Add secret** for each

**Note**: Environment-specific secrets should be added to **Environments** (see Steps 2 and 3) rather than repository secrets.

---

## Step 6: Verify CODEOWNERS Placement

The `CODEOWNERS` file must be in one of these locations:
- ✅ `/CODEOWNERS` (root, recommended)
- ⚠️ `/.github/CODEOWNERS` (alternative)
- ⚠️ `/docs/CODEOWNERS` (alternative)

**Current placement**: `/CODEOWNERS` ✅

**Test CODEOWNERS**:
1. Create a test PR
2. Verify that the users/teams in CODEOWNERS are automatically requested for review
3. If not working, check:
   - File is in correct location
   - Branch protection rule has "Require review from Code Owners" enabled
   - Usernames in CODEOWNERS match GitHub usernames exactly

---

## Step 7: Test the CI/CD Pipeline

### Test 1: Automated Tests

1. Create a branch: `test/ci-pipeline`
2. Make a small change (e.g., update a comment in `README.md`)
3. Push to GitHub
4. Verify in **Actions** tab:
   - ✅ Test workflow runs
   - ✅ Lint workflow runs
   - ✅ Both pass

### Test 2: CODEOWNER Implementation Trigger

1. Create a test issue in the repository
2. Add some description and comments
3. As a CODEOWNER, comment: `/implement-plan`
4. Verify in **Actions** tab:
   - ✅ "Copilot Auto-Implementation" workflow runs
   - ✅ Validation passes
   - ✅ Implementation context is posted
5. Check the issue:
   - ✅ Labels added: `copilot-implementing`, `approved`
   - ✅ Confirmation comment posted
   - ✅ Implementation context comment created

### Test 3: Unauthorized User (Negative Test)

1. Create or use a test issue
2. Comment as a **non-CODEOWNER** user: `/implement-plan`
3. Verify:
   - ✅ Workflow runs but validation fails
   - ✅ Error comment posted explaining authorization failure
   - ✅ No labels added
   - ✅ Issue not assigned

### Test 4: Staging Deployment

1. Merge a PR to the `dev` branch
2. Verify in **Actions** tab:
   - ✅ Test workflow runs and passes
   - ✅ Deploy workflow starts
   - ✅ "Deploy to Staging" job runs automatically
   - ✅ Deployment completes
3. Check for deployment notification in the PR

### Test 5: Production Deployment (Manual Approval)

1. Merge a PR to the `main` branch (requires CODEOWNER approval)
2. Verify in **Actions** tab:
   - ✅ Test workflow runs and passes
   - ✅ Deploy workflow starts
   - ✅ "Deploy to Production" job waits for approval
3. You should see a yellow banner: **"Review pending deployments"**
4. Click **Review pending deployments**
5. Select **production** environment
6. Add an optional comment
7. Click **Approve and deploy**
8. Verify:
   - ✅ Production deployment executes
   - ✅ Deployment tag created
   - ✅ Notification posted to PR

---

## Troubleshooting

### Issue: Workflows not running

**Symptoms**: Workflows don't trigger when expected

**Solutions**:
1. Check **Settings** → **Actions** → **General**: Ensure Actions are enabled
2. Verify workflow files are in `.github/workflows/` directory
3. Check workflow syntax: Use [GitHub Actions validator](https://rhysd.github.io/actionlint/)
4. Review **Actions** tab for error messages

### Issue: Permission denied errors

**Symptoms**: Workflow fails with "Resource not accessible by integration"

**Solutions**:
1. **Settings** → **Actions** → **General**
2. Set "Workflow permissions" to "Read and write"
3. Enable "Allow GitHub Actions to create and approve pull requests"

### Issue: CODEOWNERS not working

**Symptoms**: Reviews not requested automatically on PRs

**Solutions**:
1. Verify file location: `/CODEOWNERS` (root directory)
2. Check branch protection: Enable "Require review from Code Owners"
3. Verify usernames match exactly (case-sensitive)
4. Check for syntax errors in CODEOWNERS file

### Issue: Environment not requiring approval

**Symptoms**: Production deploys without approval

**Solutions**:
1. **Settings** → **Environments** → **production**
2. Verify "Required reviewers" is enabled
3. Ensure reviewers are added
4. Check workflow file has `environment: production` in job definition

### Issue: Status checks not required

**Symptoms**: Can merge PRs without passing tests

**Solutions**:
1. **Settings** → **Branches** → **main** protection rule
2. Enable "Require status checks to pass before merging"
3. Add required checks: `test`, `lint`, `build`
4. Save changes

---

## Security Best Practices

1. **Limit CODEOWNERS**: Only add trusted users who should approve implementations and deployments
2. **Rotate secrets regularly**: Update API keys and tokens periodically
3. **Use environment secrets**: Store production secrets in environment, not repository secrets
4. **Enable signed commits**: Require GPG signatures for commits (optional but recommended)
5. **Review workflow logs**: Regularly audit Actions logs for unusual activity
6. **Restrict environment access**: Use teams for required reviewers when possible
7. **Use branch protection**: Always protect `main` and `dev` branches
8. **Audit trail**: Keep deployment approvals logged (automatic in GitHub)

---

## Maintenance

### Weekly Tasks
- Review pending deployments
- Check for failed workflow runs
- Verify test coverage remains above threshold

### Monthly Tasks
- Review CODEOWNERS list (add/remove as team changes)
- Audit secrets (rotate if needed)
- Review and update branch protection rules
- Check for workflow updates from GitHub Actions marketplace

### Quarterly Tasks
- Review entire CI/CD pipeline for optimization
- Update dependencies in workflows (actions versions)
- Review deployment frequency and patterns
- Gather feedback from team on workflow improvements

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

*Last updated: 2026-05-15*
