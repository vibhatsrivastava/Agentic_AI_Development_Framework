# Microsoft Teams Issue Notification Preview

This document shows what the AI Issue Reporter Teams notification will look like in Microsoft Teams.

## Notification Appearance

When the GitHub Issue Reporter Agent completes analysis and posts a recommendation, it sends an adaptive card notification to Teams with the following structure:

---

### Card Header (Green/Success Style)
```
🤖  ✅ AI Analysis Complete
    GitHub Issue Reporter Agent
```

---

### Card Body
```
[Issue #123](https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework/issues/123): Add Microsoft Teams notification feature

The AI agent has analyzed this issue and posted recommendations to GitHub.
```

---

### Details Section
```
Repository:      vibhatsrivastava/Agentic_AI_Development_Framework
Issue Number:    #123
Status:          Analysis Posted
```

---

### Action Buttons
```
[ View Issue on GitHub ]  [ View AI Recommendation ]
```

---

## Full Card Preview (Text Representation)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  🤖  ✅ AI Analysis Complete                                    │
│      GitHub Issue Reporter Agent                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Issue #123]: Add Microsoft Teams notification feature        │
│                                                                 │
│  The AI agent has analyzed this issue and posted               │
│  recommendations to GitHub.                                     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Repository:     vibhatsrivastava/Agentic_AI_Development...    │
│  Issue Number:   #123                                           │
│  Status:         Analysis Posted                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [ View Issue on GitHub ]    [ View AI Recommendation ]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Color Scheme

- **Card Style:** Green/Good (indicates successful completion)
- **Header:** Large, bold text with robot emoji
- **Links:** Blue, clickable
- **Facts:** Gray labels with bold values
- **Buttons:** Blue action buttons

## Adaptive Card Features

- **Markdown Support:** Issue title and description support markdown formatting
- **Clickable Links:** Issue number links directly to GitHub
- **Action Buttons:** Two buttons for quick navigation
  - **View Issue on GitHub** → Opens the GitHub issue page
  - **View AI Recommendation** → Opens the specific comment with AI analysis
- **Responsive Layout:** Adapts to Teams desktop and mobile clients

## When Notifications Are Sent

Notifications are sent in these scenarios:

1. **Single Issue Mode** (`--issue N`):
   - After successfully posting AI recommendation to GitHub
   - Only if `MS_TEAMS_WEBHOOK_URL` is configured

2. **Auto-Analyze Mode** (`--auto-analyze`):
   - After successfully posting AI recommendation for each issue
   - Only if `MS_TEAMS_WEBHOOK_URL` is configured
   - Skipped for issues that already have bot recommendations

## Configuration Required

To enable Teams notifications:

1. Configure incoming webhook in Teams channel
2. Add `MS_TEAMS_WEBHOOK_URL` to project `.env` file
3. Run the agent normally — notifications are automatic

**Note:** If webhook URL is not configured, the agent works normally without sending notifications (optional feature).

## Sample JSON Payload

See `teams-notification-sample.json` for the full adaptive card payload structure.

## Testing the Notification

To test your webhook configuration:

```powershell
# Set environment variables
$env:MS_TEAMS_WEBHOOK_URL="https://your-org.webhook.office.com/..."
$env:GITHUB_TOKEN="ghp_your_token"
$env:GITHUB_REPO_OWNER="your_username"
$env:GITHUB_REPO_NAME="your_repo"

# Run agent on a test issue
python src/main.py --issue 123

# Check your Teams channel for the notification
```

---

*For more information about adaptive cards, visit: https://adaptivecards.io/*
