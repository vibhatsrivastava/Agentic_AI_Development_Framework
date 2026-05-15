# Teams Notifications - Configuration Checklist

This document provides step-by-step actions to configure Microsoft Teams notifications for GitHub pull requests.

---

## ✅ Step-by-Step Configuration

Follow these steps in order to enable Teams notifications:

### Step 1: Create Incoming Webhook in Microsoft Teams (5 minutes)

**Prerequisites:**
- Microsoft Teams installed (desktop or web)
- Admin or owner permissions on the Teams channel

**Actions:**
1. Open **Microsoft Teams**
2. Navigate to the channel where you want notifications (e.g., `#github-notifications`)
3. Click the **three dots (•••)** next to the channel name
4. Select **"Connectors"** (classic Teams) or **"Workflows"** (new Teams)
5. Search for **"Incoming Webhook"**
6. Click **"Configure"** or **"Add"**
7. Provide a name: `GitHub PR Notifications`
8. Optionally upload an icon (e.g., GitHub logo)
9. Click **"Create"**
10. **Copy the webhook URL** — it looks like:
    ```
    https://your-tenant.webhook.office.com/webhookb2/...@.../IncomingWebhook/.../...
    ```
11. Click **"Done"**

**✅ Success Criteria:** You have the webhook URL copied to your clipboard

---

### Step 2: Add Webhook URL to GitHub Secrets (2 minutes)

**Prerequisites:**
- Repository admin access
- Webhook URL from Step 1

**Actions:**
1. Navigate to your GitHub repository
2. Go to **Settings** tab
3. In the left sidebar, expand **Secrets and variables** → **Actions**
4. Click **"New repository secret"** button
5. In the **Name** field, enter exactly: `MS_TEAMS_WEBHOOK_URL`
6. In the **Secret** field, paste the webhook URL from Step 1
7. Click **"Add secret"**

**✅ Success Criteria:** Secret `MS_TEAMS_WEBHOOK_URL` appears in the list

---

### Step 3: Verify Workflow File Exists (30 seconds)

**Actions:**
1. In your repository, navigate to `.github/workflows/teams-notification.yml`
2. Verify the file exists and contains:
   ```yaml
   on:
     pull_request:
       types: [opened, closed]
   ```

**✅ Success Criteria:** Workflow file exists with correct trigger configuration

---

### Step 4: Test the Integration (5 minutes)

**Actions:**
1. Create a test branch:
   ```bash
   git checkout -b test/teams-notification-test
   ```

2. Make a small change (e.g., add a comment to README.md)

3. Commit and push:
   ```bash
   git add .
   git commit -m "test: Verify Teams notification integration"
   git push origin test/teams-notification-test
   ```

4. Create a pull request in GitHub

5. Check your Teams channel — you should see a notification within 10-30 seconds

6. Close or merge the PR — you should see another notification

**✅ Success Criteria:**
- Notification appears in Teams when PR is opened
- Notification appears in Teams when PR is closed/merged
- Notification includes PR details, author, and action buttons

---

## 🎉 Configuration Complete

If you received notifications in both tests, your setup is complete!

---

## 🔍 Troubleshooting

### No notification received?

**Check 1: Verify secret exists**
```bash
GitHub → Settings → Secrets and variables → Actions
Confirm: MS_TEAMS_WEBHOOK_URL is present
```

**Check 2: Check workflow run**
```bash
GitHub → Actions tab → "Microsoft Teams Notifications"
View the latest run for any errors
```

**Check 3: Test webhook manually**
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from command line"}'
```
Expected: Message appears in Teams channel

**Check 4: Verify workflow triggered**
```bash
GitHub → Actions → Look for "Microsoft Teams Notifications" workflow run
Check: Run should have been triggered by the PR event
```

### Notification format looks wrong?

Check the workflow logs for JSON formatting errors. The workflow automatically escapes special characters in PR titles and descriptions.

### Multiple notifications per PR?

This is expected:
- One notification when PR is **opened**
- One notification when PR is **closed** (or merged)

---

## 🔐 Security Notes

- **Never commit the webhook URL** to the repository
- **Use GitHub Secrets** for all sensitive values
- **Rotate webhook URLs** periodically (e.g., every 90 days)
- **Disable unused webhooks** in Teams immediately
- **Limit permissions** to the specific channel (not team-wide)

---

## 📋 Maintenance Checklist

Run these checks periodically:

- [ ] Webhook still exists in Teams connectors
- [ ] `MS_TEAMS_WEBHOOK_URL` secret is current
- [ ] Workflow is enabled in `.github/workflows/teams-notification.yml`
- [ ] Notifications are being received for recent PRs
- [ ] No errors in workflow logs

**Recommended frequency:** Monthly or after any Teams/GitHub configuration changes

---

## 📚 Additional Resources

- **Full Documentation:** [docs/teams-notifications.md](./teams-notifications.md)
- **Quick Reference:** [docs/teams-notifications-quickref.md](./teams-notifications-quickref.md)
- **Sample Adaptive Card:** [docs/teams-notification-sample.json](./teams-notification-sample.json)
- **Adaptive Cards Designer:** https://adaptivecards.io/designer/
- **Teams Webhook Docs:** https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook

---

## ✅ Configuration Summary

Once configured, this feature:
- ✅ Automatically sends Teams notifications for PR opened events
- ✅ Automatically sends Teams notifications for PR closed/merged events
- ✅ Displays rich adaptive cards with PR details
- ✅ Includes direct links to view PR and repository
- ✅ Color-codes notifications (blue=opened, green=merged, orange=closed)
- ✅ Shows author avatar, commit count, and change statistics
- ✅ Requires zero maintenance after initial setup

---

**Estimated Total Setup Time:** 15-20 minutes  
**Technical Difficulty:** Easy (no coding required)  
**Prerequisites:** Teams admin, GitHub admin, webhook URL

---

*Configuration guide v1.0 | Last updated: 2026-05-15*
