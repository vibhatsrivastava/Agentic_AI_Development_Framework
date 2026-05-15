# Teams Notifications Quick Reference

**Quick setup guide for Microsoft Teams PR notifications**

---

## 🚀 Quick Setup (5 Minutes)

### 1. Create Teams Webhook

1. Open Teams → Channel → `•••` → **Connectors** (or **Workflows**)
2. Add **"Incoming Webhook"**
3. Name: `GitHub PR Notifications`
4. Copy the webhook URL

### 2. Add GitHub Secret

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `MS_TEAMS_WEBHOOK_URL`
4. Value: Paste webhook URL
5. Click **"Add secret"**

### 3. Test

1. Create a pull request
2. Check Teams channel for notification
3. ✅ Done!

---

## 📋 Configuration Checklist

- [ ] Incoming webhook created in Teams
- [ ] Webhook URL copied
- [ ] `MS_TEAMS_WEBHOOK_URL` secret added to GitHub
- [ ] Workflow file exists: `.github/workflows/teams-notification.yml`
- [ ] Test PR created and notification received

---

## 🎯 What Gets Notified

| Event | Notification Sent |
|-------|-------------------|
| PR Opened | ✅ Yes |
| PR Closed (not merged) | ✅ Yes |
| PR Merged | ✅ Yes |
| New commit to PR | ❌ No |
| PR comment | ❌ No |
| PR review | ❌ No |

---

## 🔍 Troubleshooting

### Not receiving notifications?

```bash
# 1. Check secret exists
GitHub → Settings → Secrets → MS_TEAMS_WEBHOOK_URL ✓

# 2. Check workflow logs
GitHub → Actions → Teams Notifications → View logs

# 3. Test webhook manually
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from terminal"}'

# 4. Verify workflow triggers
# File: .github/workflows/teams-notification.yml
# Line 4: types: [opened, closed]
```

### Common HTTP Errors

| Code | Cause | Fix |
|------|-------|-----|
| 400 | Invalid JSON format | Check workflow logs for payload errors |
| 401 | Invalid webhook URL | Re-create webhook and update secret |
| 404 | Webhook deleted | Create new webhook in Teams |

---

## 🎨 Notification Preview

**Opened PR:**
```
🔔 Pull Request Opened
By @username

PR #123: Add Microsoft Teams notifications
Implement Teams notifications for PR events using adaptive cards...

Repository: vibhatsrivastava/Agentic_AI_Development_Framework
Branch: feature/teams-notification → dev
Status: Opened
Changes: 2 commits, 3 files (+150/-0)

[View Pull Request] [View Repository]
```

**Merged PR:**
```
✅ Pull Request Merged
By @username

PR #123: Add Microsoft Teams notifications
...

Status: Merged
[View Pull Request] [View Repository]
```

---

## 🛠️ Quick Customization

### Add more PR events:

```yaml
# .github/workflows/teams-notification.yml
on:
  pull_request:
    types: [opened, closed, reopened, synchronize]
```

### Filter by branch:

```yaml
on:
  pull_request:
    types: [opened, closed]
    branches: [main, dev]
```

### Disable temporarily:

```yaml
on:
  workflow_dispatch:  # Manual only
```

---

## 📚 Full Documentation

For detailed setup, advanced configuration, and troubleshooting:  
→ [docs/teams-notifications.md](./teams-notifications.md)

---

## 🔐 Security Reminder

- ⚠️ Never commit webhook URLs
- ✅ Always use GitHub Secrets
- 🔄 Rotate webhook URLs periodically
- 🗑️ Disable unused webhooks

---

*Part of the Agentic AI Development Framework CI/CD Pipeline*
