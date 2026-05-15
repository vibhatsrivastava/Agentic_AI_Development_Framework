# Microsoft Teams Notifications Setup Guide

This guide explains how to configure Microsoft Teams notifications for GitHub pull requests in the Agentic AI Development Framework repository.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Configuration](#step-by-step-configuration)
4. [Notification Details](#notification-details)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

---

## Overview

The CI/CD pipeline automatically sends rich adaptive card notifications to a Microsoft Teams channel when:
- A pull request is **opened**
- A pull request is **closed** (including merged)

These notifications provide:
- PR title, description, and status
- Author information with avatar
- Repository and branch details
- Commit count and change statistics
- Direct links to view the PR and repository

**Workflow File:** `.github/workflows/teams-notification.yml`

---

## Prerequisites

Before configuring Teams notifications, ensure you have:

1. **Administrator access** to a Microsoft Teams team/channel
2. **Repository admin access** to configure GitHub secrets
3. **Microsoft Teams** desktop or web app

---

## Step-by-Step Configuration

### Step 1: Create an Incoming Webhook in Microsoft Teams

1. **Open Microsoft Teams** and navigate to the channel where you want to receive notifications

2. **Click on the three dots (•••)** next to the channel name

3. **Select "Connectors"** (or "Workflows" in newer Teams versions)
   - If using classic Teams: Select **"Connectors"**
   - If using new Teams: Select **"Workflows"** → **"Post to a channel when a webhook request is received"**

4. **Configure the Incoming Webhook:**
   - **Name:** `GitHub PR Notifications` (or any descriptive name)
   - **Description:** `Notifications for pull requests from GitHub Actions`
   - **Icon:** Upload a GitHub icon (optional)

5. **Click "Create"** and copy the generated webhook URL
   - The URL will look like: `https://your-tenant.webhook.office.com/webhookb2/...`
   - ⚠️ **Keep this URL secure** — anyone with this URL can post to your channel

6. **Click "Done"** to save the webhook

---

### Step 2: Add the Webhook URL to GitHub Secrets

1. **Navigate to your GitHub repository** settings:
   ```
   https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Add the secret:**
   - **Name:** `MS_TEAMS_WEBHOOK_URL` (must be exactly this name)
   - **Value:** Paste the webhook URL from Step 1
   
4. **Click "Add secret"** to save

---

### Step 3: Enable the Workflow (Already Done)

The workflow is already configured in `.github/workflows/teams-notification.yml` and will automatically trigger on PR events. No additional action needed.

---

### Step 4: Test the Integration

To test if the integration is working:

1. **Create a test branch:**
   ```bash
   git checkout -b test/teams-notification
   ```

2. **Make a small change** (e.g., update README.md)

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "test: Teams notification integration"
   git push origin test/teams-notification
   ```

4. **Create a pull request** on GitHub

5. **Check your Teams channel** — you should see a notification within a few seconds

6. **Close or merge the PR** — you should see another notification

---

## Notification Details

### What's Included in Notifications

Each notification displays:

| Field | Description |
|-------|-------------|
| **Status** | PR Opened, Closed, or Merged |
| **Title** | Pull request title |
| **Description** | First 500 characters of PR body |
| **Author** | GitHub username with avatar |
| **Repository** | Full repository name |
| **Branch** | Source branch → Target branch |
| **Changes** | Commit count, files changed, lines added/removed |
| **Actions** | Quick links to view PR and repository |

### Adaptive Card Color Coding

- **🔔 Opened** — Blue/Accent color
- **✅ Merged** — Green/Good color  
- **❌ Closed (not merged)** — Orange/Attention color

---

## Troubleshooting

### Notification Not Received

**Check 1: Verify the secret is configured**
```bash
# Go to: Settings → Secrets and variables → Actions
# Confirm MS_TEAMS_WEBHOOK_URL exists
```

**Check 2: Check workflow logs**
```bash
# Go to: Actions → Teams Notifications → View latest run
# Look for errors in the "Send Teams notification" step
```

**Check 3: Verify webhook URL is valid**
- The webhook URL should start with `https://`
- It should contain `webhook.office.com` or `outlook.office.com`
- Test the webhook manually:
  ```bash
  curl -X POST "YOUR_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"text": "Test message from GitHub Actions"}'
  ```

**Check 4: Verify workflow triggers**
```yaml
# In .github/workflows/teams-notification.yml
on:
  pull_request:
    types: [opened, closed]  # Must include both
```

---

### HTTP 400 Error (Bad Request)

**Cause:** Invalid adaptive card JSON format

**Solution:**
- Check that PR title/body doesn't contain unescaped quotes or special characters
- The workflow automatically escapes JSON — no manual changes needed
- If issue persists, check workflow logs for the exact payload sent

---

### HTTP 401 Error (Unauthorized)

**Cause:** Invalid or expired webhook URL

**Solution:**
1. Delete the old webhook in Teams
2. Create a new incoming webhook (Step 1)
3. Update `MS_TEAMS_WEBHOOK_URL` secret in GitHub (Step 2)

---

### HTTP 404 Error (Not Found)

**Cause:** Webhook URL is incorrect or webhook was deleted

**Solution:**
1. Verify the webhook still exists in Teams channel connectors
2. If deleted, create a new webhook and update the secret

---

### Workflow Doesn't Trigger

**Check 1: PR events**
```yaml
# Workflow only triggers on PR opened/closed
# Does NOT trigger on:
# - Commits pushed to existing PR
# - PR comments
# - PR reviews
```

**Check 2: Branch protection**
```bash
# Ensure workflow has permissions:
permissions:
  pull-requests: read
  contents: read
```

---

## Advanced Configuration

### Customize Notification Triggers

To receive notifications on additional PR events, edit `.github/workflows/teams-notification.yml`:

```yaml
on:
  pull_request:
    types: 
      - opened
      - closed
      - reopened        # Add: PR reopened
      - synchronize     # Add: New commits pushed to PR
      - ready_for_review # Add: PR marked ready for review
```

### Filter Notifications by Branch

To only send notifications for specific branches:

```yaml
on:
  pull_request:
    types: [opened, closed]
    branches:
      - main
      - dev
```

### Customize Adaptive Card

The adaptive card template is in the workflow file at the "Send Teams notification" step. Modify the JSON structure to:
- Add more fields
- Change colors
- Add additional action buttons
- Include custom facts

**Example: Add PR labels**

Add this to the `facts` array:
```json
{
  "title": "Labels:",
  "value": "${{ join(github.event.pull_request.labels.*.name, ', ') }}"
}
```

### Send to Multiple Channels

To send notifications to multiple Teams channels:

1. **Add additional secrets:**
   - `MS_TEAMS_WEBHOOK_URL_DEV`
   - `MS_TEAMS_WEBHOOK_URL_PROD`

2. **Duplicate the "Send Teams notification" step** with different webhook URLs

3. **Use conditionals** to control which channels receive notifications:
   ```yaml
   - name: Send to Dev channel
     if: github.event.pull_request.base.ref == 'dev'
     env:
       TEAMS_WEBHOOK_URL: ${{ secrets.MS_TEAMS_WEBHOOK_URL_DEV }}
     run: |
       # Send notification logic...
   ```

---

## Security Best Practices

1. **Never commit webhook URLs** to the repository
2. **Use GitHub Secrets** for all sensitive values
3. **Rotate webhook URLs** periodically (e.g., every 90 days)
4. **Limit webhook scope** to a single channel (not team-wide)
5. **Monitor webhook usage** in Teams connector settings
6. **Disable unused webhooks** immediately

---

## Adaptive Card Schema Reference

The notifications use [Microsoft Adaptive Cards v1.4](https://adaptivecards.io/explorer/) with the following elements:

- **Container**: Groups content with color-coded styling
- **ColumnSet**: Displays avatar and header side-by-side
- **TextBlock**: Displays text with markdown support
- **FactSet**: Shows key-value pairs (repository, branch, changes)
- **Action.OpenUrl**: Creates clickable buttons

**Preview your own cards:**  
🔗 [Adaptive Cards Designer](https://adaptivecards.io/designer/)

---

## FAQ

**Q: Can I send notifications to multiple Teams workspaces?**  
A: Yes, create separate webhooks for each workspace and add them as separate secrets.

**Q: How do I disable notifications temporarily?**  
A: Disable the workflow in `.github/workflows/teams-notification.yml` by adding:
```yaml
on:
  workflow_dispatch:  # Manual trigger only
```

**Q: Can I customize the notification message?**  
A: Yes, edit the adaptive card JSON in the workflow file. See [Advanced Configuration](#advanced-configuration).

**Q: Do notifications work with forks?**  
A: No, secrets are not available to fork PRs for security reasons. Only PRs from repository branches will trigger notifications.

**Q: Can I add @mentions in notifications?**  
A: Adaptive cards don't support @mentions directly. Use `<at>username</at>` tags in text blocks, but this requires additional configuration.

---

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Microsoft Adaptive Cards](https://adaptivecards.io/)
- [Teams Incoming Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
- [CI/CD Pipeline Overview](./ci-cd-quickref.md)

---

## Support

If you encounter issues not covered in this guide:

1. Check [workflow logs](https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework/actions/workflows/teams-notification.yml)
2. Review [GitHub Actions documentation](https://docs.github.com/en/actions)
3. Open an issue in the repository with:
   - Error message from workflow logs
   - Screenshot of Teams connector settings
   - Steps to reproduce the issue

---

*Last updated: 2026-05-15*
