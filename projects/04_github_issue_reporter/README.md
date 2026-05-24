# 04 — GitHub Issue Reporter & Solution Recommender Agent

> **Architecture:** LangGraph ReAct Agent  
> **Difficulty:** Intermediate  
> **LangChain Components:** `ChatOllama`, `create_react_agent`, `@tool`, GitHub REST API  
> **Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Benefits & Use Cases](#benefits--use-cases)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)
13. [Performance & Limitations](#performance--limitations)
14. [Contributing](#contributing)

---

## Overview

The **GitHub Issue Reporter & Solution Recommender Agent** is an AI-powered tool that helps development teams manage GitHub repository issues more efficiently. It operates in three modes:

1. **Report Mode** (`--report`): Generates a comprehensive markdown report of all open issues in a repository, including metadata like age, assignees, labels, and last update time. Uses direct Python formatting for fast execution without LLM overhead.

2. **Recommendation Mode** (`--issue N`): Analyzes a specific issue and provides AI-generated recommendations for resolution, including root cause analysis (for bugs) or implementation approaches (for features). Posts the recommendation directly to GitHub as a collapsible comment.

3. **Auto-Analyze Mode** (`--auto-analyze`): Automatically discovers all issues opened in the last 24 hours, analyzes each one (skipping issues that already have bot recommendations), and posts AI-generated recommendations directly to GitHub. Supports `--dry-run` for preview without posting.

This agent uses LangGraph's ReAct (Reasoning + Acting) pattern to orchestrate multiple GitHub API tools and an LLM to provide intelligent insights.

---

## Features

### Core Capabilities

✅ **Automated Issue Reporting**
- Fetches all open issues from a GitHub repository
- Displays issue metadata in a structured markdown table
- Calculates issue age and staleness metrics
- Handles pagination automatically (up to 200 issues)
- Excludes pull requests from the issue list
- **NEW:** Direct Python formatting (no LLM) for faster execution
- **NEW:** Microsoft Teams integration via adaptive cards

✅ **Microsoft Teams Integration** (NEW)
- Send issue reports to Teams channels using adaptive cards
- Color-coded status badges based on issue count (Green/Yellow/Red)
- Visual dashboard with summary statistics (total, bugs, enhancements, oldest issue)
- Top 5 recent issues with click-through links to GitHub
- Optional notification via `--send-teams` flag
- Supports AWX automation with `SEND_TEAMS` environment variable

✅ **AI-Powered Recommendations**
- Analyzes issue content including title, body, labels, and comments
- Provides structured recommendations based on issue type:
  - **Bugs:** Root cause hypothesis, affected area, suggested fix, test cases
  - **Features:** Implementation approach, design notes, acceptance criteria
- Grounds recommendations in actual issue data (no hallucination)
- Handles prompt injection attacks with safe content processing
- **NEW:** Posts recommendations directly to GitHub as collapsible comments
- **NEW:** Duplicate detection prevents redundant bot comments

✅ **Microsoft Teams Notifications** (NEW)
- Sends rich adaptive card notifications to Teams when analysis completes
- Includes issue title, number, repository, and analysis status
- Provides direct links to GitHub issue and AI recommendation
- Optional feature (only enabled when webhook URL is configured)
- Non-critical failure handling (notification errors don't break agent)
- Beautiful card UI with emojis and color-coded status

✅ **Automated Batch Processing**
- **NEW:** Auto-analyze mode discovers and processes new issues automatically
- Filters issues by creation time (last 24 hours)
- Skips issues that already have bot recommendations
- Supports dry-run mode for safe preview
- Configurable issue limit prevents rate limiting
- Comprehensive summary report after batch processing

✅ **Multi-Repository Support** (NEW)
- Process multiple repositories in a single run
- Flexible token management:
  - Shared token for all repositories
  - Per-repository token overrides
  - Mixed mode (some shared, some per-repo)
- Configuration via JSON file (`repos.json`)
- Sequential processing with clear per-repo output
- Backward compatible with single-repo environment variables

✅ **Robust Error Handling**
- Graceful handling of HTTP errors (404, 403, 429)
- Clear error messages for configuration issues
- Input validation for issue numbers
- Automatic retry and rate limiting support
- Detects insufficient token permissions and provides guidance

✅ **Security Hardened**
- Secure token management via environment variables or config file
- Content truncation to prevent context overflow
- Prompt injection mitigation with XML delimiters
- No sensitive data logging
- Bot marker prevents comment tampering

---

## Benefits & Use Cases

### For Development Teams

1. **Faster Issue Triage**
   - Quickly audit the entire issue backlog without clicking through GitHub UI
   - Identify stale issues that need attention
   - See priority distribution at a glance

2. **Accelerated Onboarding**
   - New team members can get AI-generated context for unfamiliar issues
   - Reduces time spent reading through long issue threads
   - Provides starting points for implementation

3. **Enhanced Code Quality**
   - AI-generated test case suggestions for bugs
   - Acceptance criteria recommendations for features
   - Root cause analysis helps prevent recurring issues
   - **NEW:** Proactive recommendations on new issues prevent stale backlogs

4. **Better Project Management**
   - Age and staleness metrics help prioritize work
   - Unassigned issues are highlighted
   - Label distribution shows work categories
   - **NEW:** Automated analysis reduces manual triage time
   - **NEW:** Batch processing keeps pace with active repositories

### For Individual Developers

1. **Quick Issue Understanding**
   - Get a summary and action plan for complex issues
   - Identify affected code areas before diving in
   - Leverage LLM reasoning on multi-comment threads

2. **Implementation Guidance**
   - Suggested approaches for feature requests
   - Design considerations for complex changes
   - Test coverage recommendations

---

## Architecture

### High-Level Design

```
User CLI
  ↓
Argument Parser (--report | --issue N | --auto-analyze)
  ↓
┌─────────────────────────────────────────────┐
│  Report Mode (Direct Python)                │
│  • list_open_issues() → format_report()     │
│  • No LLM required                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Issue / Auto-Analyze Mode (LangGraph)      │
│  ↓                                          │
│  Agent Orchestrator (LangGraph ReAct)       │
│  ↓                                          │
│  GitHub API Tools (6 tools)                 │
│  • list_open_issues                         │
│  • get_issue_details                        │
│  • get_issue_comments                       │
│  • check_existing_bot_comments (NEW)        │
│  • post_issue_comment (NEW)                 │
│  • list_recent_issues (NEW)                 │
│  ↓                                          │
│  LLM Reasoning (ChatOllama)                 │
│  ↓                                          │
│  Structured Output + GitHub Write           │
└─────────────────────────────────────────────┘
```

### End-to-End Solution Workflow

The following diagram illustrates the complete workflow for all three execution modes (Report, Issue Analysis, and Auto-Analyze):

```mermaid
flowchart TD
    Start([User Executes CLI]) --> ParseArgs{Parse Arguments}
    
    ParseArgs -->|--report| ReportMode[Report Mode]
    ParseArgs -->|--issue N| IssueMode[Issue Analysis Mode]
    ParseArgs -->|--auto-analyze| AutoMode[Auto-Analyze Mode]
    
    %% Report Mode Flow
    ReportMode --> CheckMultiRepo1{Multi-Repo<br/>Config?}
    CheckMultiRepo1 -->|Yes| LoadRepos1[Load repos.json]
    CheckMultiRepo1 -->|No| SingleRepo1[Use ENV vars]
    LoadRepos1 --> LoopRepos1[For Each Repository]
    SingleRepo1 --> FetchIssues[Fetch Open Issues<br/>GitHub API]
    LoopRepos1 --> FetchIssues
    
    FetchIssues --> FormatReport[Format Report<br/>Direct Python]
    FormatReport --> CheckTeams{--send-teams<br/>flag?}
    CheckTeams -->|Yes| SendTeams[Send to MS Teams<br/>Adaptive Card]
    CheckTeams -->|No| DisplayReport[Display in Console]
    SendTeams --> DisplayReport
    DisplayReport --> End1([End])
    
    %% Issue Analysis Mode Flow
    IssueMode --> CheckMultiRepo2{Multi-Repo<br/>Config?}
    CheckMultiRepo2 -->|Yes| LoadRepos2[Load repos.json]
    CheckMultiRepo2 -->|No| SingleRepo2[Use ENV vars]
    LoadRepos2 --> LoopRepos2[For Each Repository]
    SingleRepo2 --> FetchDetails[Fetch Issue Details<br/>GitHub API]
    LoopRepos2 --> FetchDetails
    
    FetchDetails --> CheckExisting{Bot Comment<br/>Exists?}
    CheckExisting -->|Yes| SkipIssue[Skip - Already Analyzed]
    CheckExisting -->|No| FetchComments[Fetch Issue Comments<br/>GitHub API]
    
    FetchComments --> InitAgent[Initialize LangGraph<br/>ReAct Agent]
    InitAgent --> LLMAnalysis[LLM Analysis<br/>via Ollama]
    LLMAnalysis --> GenerateRec[Generate Structured<br/>Recommendation]
    GenerateRec --> PostComment[Post Comment to GitHub<br/>with Bot Marker]
    PostComment --> CheckTeamsWebhook1{Teams Webhook<br/>Configured?}
    CheckTeamsWebhook1 -->|Yes| SendTeamsNotif1[Send Teams Notification]
    CheckTeamsWebhook1 -->|No| ShowURL1[Display Comment URL]
    SendTeamsNotif1 --> ShowURL1
    ShowURL1 --> End2([End])
    SkipIssue --> End2
    
    %% Auto-Analyze Mode Flow
    AutoMode --> CheckMultiRepo3{Multi-Repo<br/>Config?}
    CheckMultiRepo3 -->|Yes| LoadRepos3[Load repos.json]
    CheckMultiRepo3 -->|No| SingleRepo3[Use ENV vars]
    LoadRepos3 --> LoopRepos3[For Each Repository]
    SingleRepo3 --> FetchRecent[Fetch Recent Issues<br/>Last 24h - GitHub API]
    LoopRepos3 --> FetchRecent
    
    FetchRecent --> CheckDryRun{--dry-run<br/>flag?}
    CheckDryRun -->|Yes| DryRunLoop[Preview Mode Loop]
    CheckDryRun -->|No| ProcessLoop[Process Each Issue]
    
    DryRunLoop --> CheckExisting2{Bot Comment<br/>Exists?}
    CheckExisting2 -->|Yes| SkipDry[Preview: Would Skip]
    CheckExisting2 -->|No| PreviewAnalyze[Preview: Would Analyze]
    SkipDry --> NextIssue1{More<br/>Issues?}
    PreviewAnalyze --> NextIssue1
    NextIssue1 -->|Yes| DryRunLoop
    NextIssue1 -->|No| ShowSummary1[Display Summary Report]
    ShowSummary1 --> End3([End])
    
    ProcessLoop --> CheckExisting3{Bot Comment<br/>Exists?}
    CheckExisting3 -->|Yes| SkipProcessed[Skip - Already Analyzed]
    CheckExisting3 -->|No| FetchDetails2[Fetch Issue Details & Comments]
    
    FetchDetails2 --> InitAgent2[Initialize LangGraph<br/>ReAct Agent]
    InitAgent2 --> LLMAnalysis2[LLM Analysis<br/>via Ollama]
    LLMAnalysis2 --> GenerateRec2[Generate Structured<br/>Recommendation]
    GenerateRec2 --> PostComment2[Post Comment to GitHub]
    PostComment2 --> CheckTeamsWebhook2{Teams Webhook<br/>Configured?}
    CheckTeamsWebhook2 -->|Yes| SendTeamsNotif2[Send Teams Notification]
    CheckTeamsWebhook2 -->|No| LogSuccess[Log Success]
    SendTeamsNotif2 --> LogSuccess
    LogSuccess --> NextIssue2{More<br/>Issues?}
    SkipProcessed --> NextIssue2
    NextIssue2 -->|Yes| ProcessLoop
    NextIssue2 -->|No| ShowSummary2[Display Summary Report]
    ShowSummary2 --> End3
    
    %% Styling
    classDef modeClass fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef apiClass fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef llmClass fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef decisionClass fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    classDef outputClass fill:#00BCD4,stroke:#006064,stroke-width:2px,color:#fff
    
    class ReportMode,IssueMode,AutoMode modeClass
    class FetchIssues,FetchDetails,FetchComments,FetchRecent,FetchDetails2,PostComment,PostComment2 apiClass
    class InitAgent,LLMAnalysis,GenerateRec,InitAgent2,LLMAnalysis2,GenerateRec2 llmClass
    class ParseArgs,CheckMultiRepo1,CheckMultiRepo2,CheckMultiRepo3,CheckTeams,CheckExisting,CheckExisting2,CheckExisting3,CheckDryRun,NextIssue1,NextIssue2,CheckTeamsWebhook1,CheckTeamsWebhook2 decisionClass
    class DisplayReport,ShowURL1,ShowSummary1,ShowSummary2,SendTeams,SendTeamsNotif1,SendTeamsNotif2 outputClass
```

**Workflow Legend:**
- 🟢 **Green Nodes**: Execution modes (Report/Issue/Auto-Analyze)
- 🔵 **Blue Nodes**: GitHub API operations (fetch, post)
- 🟠 **Orange Nodes**: LLM/AI processing (analysis, recommendation generation)
- 🟣 **Purple Nodes**: Decision points (conditionals, loops)
- 🔷 **Cyan Nodes**: Output operations (display, Teams notifications)

**Key Decision Points:**
1. **Multi-Repo Config**: Determines single vs. multi-repository execution
2. **Bot Comment Exists**: Prevents duplicate analysis via marker detection
3. **--send-teams Flag**: Controls Microsoft Teams notification delivery
4. **--dry-run Flag**: Enables preview mode without posting to GitHub
5. **Teams Webhook Configured**: Optional notification on analysis completion

### Components

| Component | Technology | Purpose |
|---|---|---|
| **CLI** | Python `argparse` | User interface and argument validation |
| **Agent Core** | LangGraph `create_react_agent` | Orchestrates tool calls and LLM reasoning |
| **LLM** | Ollama (ChatOllama) | Reasoning, analysis, and output formatting |
| **Tools** | `@tool` decorators | GitHub REST API integration |
| **HTTP Client** | `requests` | External API communication |
| **Logging** | `common.utils.get_logger` | Structured logging and debugging |

### Tool Descriptions

1. **`list_open_issues(owner, repo, token=None)`**
   - Fetches all open issues (paginated, max 2 pages)
   - Computes age and staleness metrics
   - Excludes pull requests
   - Returns JSON with issue metadata
   - **NEW:** Optional token parameter for multi-repo support

2. **`get_issue_details(owner, repo, issue_number, token=None)`**
   - Fetches single issue details
   - Truncates body to 4000 chars (context window protection)
   - Returns JSON with full issue data
   - **NEW:** Optional token parameter for multi-repo support

3. **`get_issue_comments(owner, repo, issue_number, token=None)`**
   - Fetches top 10 comments for an issue
   - Truncates each comment to 1000 chars
   - Returns JSON with comment metadata
   - **NEW:** Optional token parameter for multi-repo support

4. **`check_existing_bot_comments(owner, repo, issue_number, token=None)` (NEW)**
   - Searches issue comments for bot marker (`<!-- AI-ANALYSIS-BOT -->`)
   - Prevents duplicate recommendations
   - Returns boolean flag and comment ID if found
   - **NEW:** Optional token parameter for multi-repo support

5. **`post_issue_comment(owner, repo, issue_number, comment_body, token=None)` (NEW)**
   - Posts AI recommendation as a GitHub comment
   - Formats comment with collapsible details block
   - Includes hidden bot marker for duplicate detection
   - Returns comment URL and timestamp
   - **NEW:** Optional token parameter for multi-repo support

6. **`list_recent_issues(owner, repo, hours=24, token=None)` (NEW)**
   - Fetches issues created within last N hours (default 24)
   - Filters by creation timestamp
   - Excludes pull requests
   - Returns JSON with recent issues metadata
   - **NEW:** Optional token parameter for multi-repo support

---

## Prerequisites

### System Requirements

- **Python:** 3.11 or higher
- **Ollama:** Installed and running (local or remote)
- **Operating System:** Windows, macOS, or Linux
- **Network:** Internet access for GitHub API calls

### Required Tools

```powershell
# Check Python version
python --version  # Should be 3.11+

# Check Ollama installation
ollama --version

# Verify Ollama is running
ollama list
```

### GitHub Personal Access Token

You need a GitHub Personal Access Token (PAT) with **write permissions** for posting comments:

1. Navigate to [GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Configure token:
   - **Name:** `Agentic AI Issue Reporter`
   - **Expiration:** Choose appropriate duration
   - **Scopes:**
     - For **public repositories:** Select `public_repo` (includes read AND write)
     - For **private repositories:** Select `repo` (full repository access)
4. Click **Generate token**
5. **IMPORTANT:** Copy the token immediately (you won't see it again)

⚠️ **Token Scope Requirements:**
- **Read-only access is NOT sufficient** — the agent posts comments to GitHub
- `public_repo` scope grants full read/write access to public repositories
- `repo` scope grants full read/write access to all repositories (public and private)
- If you see "403 Forbidden" errors, regenerate your token with correct scopes

---

## Installation & Setup

### Step 1: Clone Repository (if not already done)

```powershell
git clone https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework.git
cd Agentic_AI_Development_Framework
```

### Step 2: Verify Root Environment Configuration

Ensure the root `.env` file exists and has required base variables:

```powershell
# Check root .env exists
Get-Content .env
```

If it doesn't exist, copy from example:

```powershell
Copy-Item .env.example .env
```

### Step 3: Activate Project Virtual Environment

The project's virtual environment was created during scaffolding:

```powershell
cd projects\04_github_issue_reporter
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
cd projects/04_github_issue_reporter
source .venv/bin/activate
```

### Step 4: Install Dependencies

Dependencies should already be installed during scaffolding. To reinstall or update:

```powershell
# Ensure you're in the project directory with venv activated
uv pip install -r requirements.txt
uv pip install -e ../../common
```

### Step 5: Verify Installation

```powershell
# Check installed packages
uv pip list | Select-String -Pattern "langchain|requests|ollama"

# Verify common package is accessible
python -c "from common.llm_factory import get_chat_llm; print('✅ Common package imported successfully')"
```

---

## Configuration

### Environment Variables

All configuration is managed via environment variables. This project uses **hierarchical environment loading**: root `.env` for common variables (OLLAMA_*) and project `.env` for GitHub-specific variables.

**Root `.env` (already configured):**
```env
# === Ollama Configuration ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=  # Leave blank for local; set Bearer token for remote
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# === Logging ===
LOG_LEVEL=INFO
```

**Project `.env` (this directory):**
```env
# === GitHub Configuration ===
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO_OWNER=your_github_username_or_org
GITHUB_REPO_NAME=your_repository_name

# === Microsoft Teams Integration (Optional) ===
MS_TEAMS_WEBHOOK_URL=https://your-org.webhook.office.com/webhookb2/your-webhook-url
```

Create the project `.env` file from the example:

```powershell
# From project directory (04_github_issue_reporter/)
Copy-Item .env.example .env

# Edit .env with your values
notepad .env
```

### Configuration Details

| Variable | Required | Description | Example |
|---|---|---|---|
| `GITHUB_TOKEN` | ✅ Yes | GitHub Personal Access Token | `ghp_abc123...` |
| `GITHUB_REPO_OWNER` | ✅ Yes | Repository owner (user or org) | `your_github_username` |
| `GITHUB_REPO_NAME` | ✅ Yes | Repository name | `your_repository_name` |
| `MS_TEAMS_WEBHOOK_URL` | ❌ Optional | Teams incoming webhook URL | `https://your-org.webhook...` |
| `OLLAMA_BASE_URL` | ✅ Yes | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_API_KEY` | ⚠️ Conditional | Required for remote Ollama | `Bearer token` |
| `OLLAMA_MODEL` | ✅ Yes | LLM model name | `llama3.2:3b` |
| `LOG_LEVEL` | ❌ Optional | Logging verbosity | `INFO`, `DEBUG` |

### Microsoft Teams Webhook Setup

To enable Teams notifications (optional):

1. **Open Microsoft Teams** and navigate to the channel where you want notifications
2. **Click the "..." (More options)** next to the channel name
3. **Select "Connectors"**
4. **Search for "Incoming Webhook"** and click "Configure"
5. **Provide a name** (e.g., "GitHub Issue Reporter") and optionally upload an icon
6. **Click "Create"** — Teams will generate a webhook URL
7. **Copy the webhook URL** and add it to your project `.env` file as `MS_TEAMS_WEBHOOK_URL`

**Note:** The webhook URL is sensitive — treat it like a password. Do not commit it to version control.

### Security Best Practices

⚠️ **NEVER commit `.env` files to version control!**

```powershell
# Verify .env is gitignored
git check-ignore .env
# Should output: .env
```

🔒 **Token Permissions:** Use the principle of least privilege. Grant only necessary scopes.

🔐 **Token Storage:** For teams, consider using HashiCorp Vault (see [docs/vault.md](../../docs/vault.md)).

---

## Usage

### Basic Commands

#### Report Mode: List All Open Issues

```powershell
# Activate venv (if not already active)
.venv\Scripts\Activate.ps1

# Generate issue report
python src\main.py --report
```

**Example Output:**

```markdown
================================================================================
## Open Issues Report — your_org/your_repository
**Total open issues: 4** | Generated: 2026-05-06

| # | Title | Author | Assignee | Labels | Opened | Age (days) | Last Updated | URL |
|---|---|---|---|---|---|---|---|---|
| 42 | Fix token counter edge case | alice | bob | bug, priority:high | 2026-04-01 | 35 | 2 days ago | [#42](https://github.com/...) |
| 38 | Add Redis caching integration | carol | Unassigned | enhancement | 2026-03-15 | 52 | 10 days ago | [#38](https://github.com/...) |
| 31 | LLM factory streaming support | alice | alice | feature | 2026-02-20 | 75 | 25 days ago | [#31](https://github.com/...) |
| 12 | Update vault documentation | dave | Unassigned | docs | 2025-12-01 | 156 | 60 days ago | [#12](https://github.com/...) |
================================================================================
```

#### Report Mode with Microsoft Teams Notifications

```powershell
# Generate issue report and send to Microsoft Teams
python src\main.py --report --send-teams
```

**Prerequisites:**
1. Configure `MS_TEAMS_WEBHOOK_URL` in your project `.env` file (see Configuration section)
2. Create an Incoming Webhook in your Microsoft Teams channel

**What it does:**
1. Generates the standard issue report (displayed in console)
2. Formats the report as a Microsoft Teams adaptive card
3. Sends the card to the configured Teams channel
4. Shows confirmation message

**Example Output:**

```markdown
================================================================================
**Open Issues Report**

| # | Title | Author | Assignee | Labels | Opened | Age (days) | Last Updated | URL |
|---|-------|--------|----------|--------|--------|------------|--------------|-----|
| 42 | Fix token counter edge case | alice | bob | bug, priority:high | 2026-04-01 | 35 | 2 days ago | [#42](https://github.com/...) |

**Summary:** 4 open issues. Oldest: 156 days.
================================================================================

✅ Report sent to Microsoft Teams
```

**Microsoft Teams Card Format:**

The adaptive card includes:
- **Status Badge:** Color-coded based on issue count (Green: ≤5, Yellow: 6-20, Red: >20)
- **Repository Info:** Owner/repo name
- **Summary Statistics:** Total issues, bug count, enhancement count, oldest issue age
- **Recent Issues:** Top 5 issues with title, author, labels, and age
- **Action Buttons:** Links to view all issues and repository

![Teams Notification Example](screenshots/teams-notification.png)

**Benefits:**
- ✅ Share issue reports with non-technical stakeholders in Teams
- ✅ Automated notifications for scheduled reports (via AWX/cron)
- ✅ Visual dashboard for issue health in team channels
- ✅ Click-through links directly to GitHub issues

#### Recommendation Mode: Analyze Specific Issue and Post to GitHub

```powershell
# Analyze issue #42 and post recommendation as a comment
python src\main.py --issue 42
```

**What it does:**
1. Checks if issue #42 already has a bot recommendation (duplicate detection)
2. If not, fetches issue details and comments
3. Generates AI-powered recommendation with structured analysis
4. Posts recommendation to GitHub as a collapsible comment
5. Prints confirmation with comment URL

**Example Output:**

```markdown
================================================================================
✅ Posted recommendation to issue #42
Comment URL: https://github.com/owner/repo/issues/42#issuecomment-123456789

The recommendation has been added as a collapsible comment on GitHub.
================================================================================
```

**If issue already has bot recommendation:**

```markdown
================================================================================
ℹ️  Skipping: Issue #42 already has a bot recommendation
================================================================================
```

**GitHub Comment Format:**

The recommendation appears as a collapsible comment:

```markdown
<!-- AI-ANALYSIS-BOT -->
## 🤖 AI Analysis

<details>
<summary>View Recommendation</summary>

**Issue Type:** Bug

**Root Cause Hypothesis:**
The `token_counter.py` module calls `split()` on the input string...

**Affected Area:**
`common/token_counter.py` — `count_tokens()` function

**Suggested Fix:**
Add input guard...

**Test Cases to Add:**
1. `test_count_tokens_empty_string`

</details>

---
*Generated by GitHub Issue Reporter Agent*
```

#### Auto-Analyze Mode: Batch Process Recent Issues

```powershell
# Analyze all issues opened in the last 24 hours
python src\main.py --auto-analyze
```

**What it does:**
1. Fetches all issues opened in the last 24 hours
2. For each issue:
   - Checks if it already has a bot recommendation (skips if yes)
   - Analyzes the issue with AI
   - Posts recommendation as a GitHub comment
3. Prints summary report

**Example Output:**

```markdown
📊 Found 3 issues opened in the last 24 hours

--- Issue #100: Add streaming support ---
✅ Posted recommendation for issue #100

--- Issue #99: Fix memory leak ---
✅ Posted recommendation for issue #99

--- Issue #98: Update docs ---
ℹ️  Skipping: Issue #98 already has a bot recommendation

================================================================================
**Auto-Analysis Summary**

Total issues found (last 24h): 3
Issues processed: 3
Recommendations posted: 2
Skipped (already analyzed): 1
================================================================================
```

#### Auto-Analyze with Dry Run (Preview Mode)

```powershell
# Preview what would be analyzed without posting
python src\main.py --auto-analyze --dry-run
```

**Example Output:**

```markdown
🔍 DRY RUN MODE: No comments will be posted to GitHub

📊 Found 3 issues opened in the last 24 hours

--- Issue #100: Add streaming support ---
🔍 DRY RUN: Would analyze and post recommendation for issue #100

--- Issue #99: Fix memory leak ---
🔍 DRY RUN: Would analyze and post recommendation for issue #99

================================================================================
**Auto-Analysis Summary**

Total issues found (last 24h): 3
Issues processed: 3
Would analyze: 2
Skipped (already analyzed): 1
================================================================================
```

#### Limit Number of Issues Processed

```powershell
# Process maximum of 10 issues (default is 100)
python src\main.py --auto-analyze --max-issues 10
```

---

### Multi-Repository Mode

**NEW:** Process multiple repositories in a single run using a configuration file.

#### Configuration File Setup

Create a `repos.json` file from the example template:

```powershell
# From project directory (04_github_issue_reporter/)
Copy-Item repos.json.example repos.json

# Edit with your repository configuration
notepad repos.json
```

**Configuration Format:**

```json
{
  "default_token": "ghp_your_shared_github_token_here",
  "repositories": [
    {
      "owner": "myorg",
      "name": "repo1"
    },
    {
      "owner": "myorg",
      "name": "repo2"
    },
    {
      "owner": "othercorp",
      "name": "private-repo",
      "token": "ghp_specific_token_for_this_repo"
    }
  ]
}
```

**Configuration Options:**

1. **Shared Token Mode**: All repositories use the same token
   - Set `default_token` at the top level
   - Repositories without `token` field use the `default_token`

2. **Per-Repository Token Mode**: Each repository has its own token
   - Set `token` field in each repository object
   - Overrides `default_token` when specified

3. **Mixed Mode**: Combination of shared and per-repo tokens
   - Some repositories use `default_token`
   - Others override with their own `token` field

#### Multi-Repository Commands

All modes support the `--repos-config` flag:

```powershell
# Report mode: Generate reports for all repositories
python src\main.py --report --repos-config repos.json

# Issue mode: Analyze issue #42 in all repositories
python src\main.py --issue 42 --repos-config repos.json

# Auto-analyze mode: Process recent issues in all repositories
python src\main.py --auto-analyze --repos-config repos.json

# With dry-run preview
python src\main.py --auto-analyze --dry-run --repos-config repos.json
```

**Example Output (Multi-Repo Report):**

```markdown
================================================================================
Repository 1/3: myorg/repo1
================================================================================

**Open Issues Report**
...

================================================================================
Repository 2/3: myorg/repo2
================================================================================

**Open Issues Report**
...

================================================================================
Repository 3/3: othercorp/private-repo
================================================================================

**Open Issues Report**
...
```

#### Multi-Repository Use Cases

**Scenario 1: Multiple Repositories, Same Organization**
```json
{
  "default_token": "ghp_shared_org_token",
  "repositories": [
    {"owner": "myorg", "name": "frontend"},
    {"owner": "myorg", "name": "backend"},
    {"owner": "myorg", "name": "mobile-app"}
  ]
}
```

**Scenario 2: Multiple Organizations, Different Tokens**
```json
{
  "repositories": [
    {"owner": "company-a", "name": "repo1", "token": "ghp_company_a_token"},
    {"owner": "company-b", "name": "repo2", "token": "ghp_company_b_token"}
  ]
}
```

**Scenario 3: Personal and Work Repositories**
```json
{
  "default_token": "ghp_personal_token",
  "repositories": [
    {"owner": "myusername", "name": "personal-project1"},
    {"owner": "myusername", "name": "personal-project2"},
    {"owner": "work-org", "name": "work-project", "token": "ghp_work_token"}
  ]
}
```

---

### Legacy Single-Repository Mode

The original environment variable approach still works for single repositories:
```

**Use case:** Prevent rate limiting or excessive LLM costs in very active repositories.

### Advanced Usage

#### Different Repository

To analyze a different repository, update `.env`:

```env
GITHUB_REPO_OWNER=facebook
GITHUB_REPO_NAME=react
```

Then run commands as usual.

#### Debug Mode

For troubleshooting, enable debug logging:

```env
LOG_LEVEL=DEBUG
```

This will show:
- Tool invocations with parameters
- API request URLs (tokens are masked)
- Agent reasoning steps
- HTTP response codes

#### Output Redirection

Save report to a file (report mode only):

```powershell
python src\main.py --report > issue_report_$(Get-Date -Format 'yyyy-MM-dd').md
```

**Note:** `--issue` and `--auto-analyze` modes post to GitHub, not stdout.

### Scheduled Automation

#### Windows Task Scheduler

Run auto-analyze daily at 9 AM:

1. Open Task Scheduler: `taskschd.msc`
2. Create Task:
   - **Name:** GitHub Issue Auto-Analyzer
   - **Trigger:** Daily at 9:00 AM
   - **Action:** Start a program
     - **Program:** `path\to\.venv\Scripts\python.exe`
     - **Arguments:** `src\main.py --auto-analyze`
     - **Start in:** `path\to\04_github_issue_reporter`

#### Linux/Mac Cron

Edit crontab:

```bash
crontab -e
```

Add line (runs daily at 9 AM):

```
0 9 * * * cd /path/to/04_github_issue_reporter && .venv/bin/python src/main.py --auto-analyze
```

#### GitHub Actions Workflow

Create `.github/workflows/auto-analyze-issues.yml` in your repository:

```yaml
name: Auto-Analyze New Issues

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: vibhatsrivastava/Agentic_AI_Development_Framework
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install uv
          cd projects/04_github_issue_reporter
          uv venv .venv
          source .venv/bin/activate
          uv pip install -r requirements.txt
          uv pip install -e ../../common
      
      - name: Run auto-analyze
        env:
          GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
          GITHUB_REPO_OWNER: ${{ github.repository_owner }}
          GITHUB_REPO_NAME: ${{ github.event.repository.name }}
          OLLAMA_BASE_URL: ${{ secrets.OLLAMA_BASE_URL }}
          OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
          OLLAMA_MODEL: llama3.2:3b
        run: |
          cd projects/04_github_issue_reporter
          source .venv/bin/activate
          python src/main.py --auto-analyze
```

**Required Secrets:**
- `GH_TOKEN` — GitHub PAT with `repo` scope
- `OLLAMA_BASE_URL` — Remote Ollama server URL
- `OLLAMA_API_KEY` — Ollama Bearer token (if required)

---

## Deployment

### Local Development

Already configured by default. Just ensure:
1. Ollama is running: `ollama serve`
2. Model is downloaded: `ollama pull llama3.2:3b`
3. Environment variables are set in root `.env`

### CI/CD Integration (GitHub Actions)

Create `.github/workflows/issue-audit.yml`:

```yaml
name: Weekly Issue Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  audit-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: |
          cd projects/04_github_issue_reporter
          uv venv .venv
          source .venv/bin/activate
          uv pip install -r requirements.txt
          uv pip install -e ../../common
      
      - name: Run issue report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO_OWNER: ${{ github.repository_owner }}
          GITHUB_REPO_NAME: ${{ github.event.repository.name }}
          OLLAMA_BASE_URL: ${{ secrets.OLLAMA_BASE_URL }}
          OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
          OLLAMA_MODEL: llama3.2:3b
        run: |
          cd projects/04_github_issue_reporter
          source .venv/bin/activate
          python src/main.py --report > weekly_report.md
      
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: issue-report
          path: projects/04_github_issue_reporter/weekly_report.md
```

**Required Secrets:**
- `OLLAMA_BASE_URL`: Remote Ollama server URL
- `OLLAMA_API_KEY`: Remote Ollama Bearer token

### Docker Deployment

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY projects/04_github_issue_reporter/ /app/
COPY common/ /app/common/
COPY requirements-base.txt /app/

# Install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt && \
    uv pip install -e ./common

ENTRYPOINT [".venv/bin/python", "src/main.py"]
```

Build and run:

```bash
docker build -t github-issue-reporter .

docker run --rm \
  -e GITHUB_TOKEN=ghp_xxx \
  -e GITHUB_REPO_OWNER=youruser \
  -e GITHUB_REPO_NAME=yourrepo \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.2:3b \
  github-issue-reporter --report
```

### Ansible AWX Deployment (Recommended for Production)

**AWX Integration** enables scheduled execution, on-demand triggering, and centralized credential management for the GitHub Issue Reporter agent.

**Features:**
- 🕐 **Scheduled Execution**: Automate issue analysis on a cron schedule (daily, hourly, weekly)
- 🚀 **On-Demand Triggering**: Launch jobs manually via AWX UI or API
- 🔐 **Secure Credential Management**: Store GitHub tokens and Ollama API keys in AWX credentials
- 📊 **Survey Forms**: Collect execution parameters (mode, issue number, dry run) via UI
- 📈 **Job History & Logs**: Track execution history, view logs, and monitor success rates
- 🔗 **Webhook Integration**: Trigger analysis automatically when new issues are opened on GitHub

**Quick Start:**

1. **AWX Setup Files**: All required files are in the `awx/` directory:
   - `playbook.yml` — Ansible playbook for agent execution
   - `survey.json` — AWX survey specification for UI parameters
   - `credentials.yml` — Custom credential type definitions
   - `README.md` — Complete setup guide (7 sections, 300+ lines)

2. **Setup Steps** (see `awx/README.md` for details):
   - Import credential types (Ollama, GitHub, Langfuse)
   - Create credentials with GitHub token and repository config
   - Create AWX project pointing to this repository
   - Create job template with playbook and survey
   - Test execution manually
   - Configure schedule for automated runs

3. **Usage Patterns**:
   - **Daily Auto-Analysis**: Automatically analyze new issues every morning
   - **Manual Issue Analysis**: Analyze specific issues on demand via AWX UI
   - **Webhook-Triggered**: Auto-analyze new issues immediately when opened
   - **Scheduled Reports**: Generate weekly issue reports for stakeholder review

**Example AWX Job Template**:
- **Name**: `GitHub Issue Reporter - Run Agent`
- **Playbook**: `projects/04_github_issue_reporter/awx/playbook.yml`
- **Survey**: Execution Mode (report/issue/auto-analyze), Issue Number, Dry Run, Max Issues, Log Level
- **Credentials**: Ollama API, GitHub API, Langfuse (optional)
- **Schedule**: Daily at 9:00 AM UTC (for auto-analyze mode)

**Expected Output** (JSON format for Ansible parsing):
```json
{
  "status": "success",
  "result": "**Open Issues Report**\n\n| # | Title | ...",
  "metadata": {
    "agent": "04_github_issue_reporter",
    "execution_time": 12.34,
    "awx_job_id": "12345"
  }
}
```

**For detailed setup instructions**, see [`awx/README.md`](awx/README.md).

---

## Testing

### Run Test Suite

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90 -v
```

### Test Coverage Report

```
---------- coverage: platform win32, python 3.11.x -----------
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
src/__init__.py           0      0   100%
src/main.py             185      8    96%   42-45, 89
---------------------------------------------------
TOTAL                   185      8    96%
```

### Run Specific Test Classes

```powershell
# Test only tool functions
pytest tests/test_main.py::TestListOpenIssuesTool -v

# Test CLI argument parsing
pytest tests/test_main.py::TestCLIArgumentParsing -v

# Test error handling
pytest tests/test_main.py::TestErrorHandling -v
```

### Test Strategy

- **Unit tests:** Individual tool functions with mocked HTTP calls
- **Integration tests:** Agent invocation with mocked LLM and GitHub API
- **CLI tests:** Argument parsing and validation
- **Error handling tests:** Network errors, invalid inputs, missing config

**Key principle:** No real API calls in tests. All LLM and HTTP interactions are mocked.

---

## Troubleshooting

### Common Issues

#### Issue: `EnvironmentError: GITHUB_TOKEN not found`

**Cause:** Missing GitHub token in `.env` file.

**Solution:**
1. Create token at https://github.com/settings/tokens
2. Add to root `.env`: `GITHUB_TOKEN=ghp_your_token`
3. Verify: `python -c "from common.utils import require_env; require_env('GITHUB_TOKEN')"`

---

#### Issue: `GitHub API error: 404 - Not Found`

**Cause:** Repository doesn't exist or token lacks access.

**Solution:**
1. Verify repository exists: `https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}`
2. Check token scopes (needs `repo` or `public_repo`)
3. For private repos, ensure token has `repo` scope

---

#### Issue: `GitHub API error: 403 - Forbidden` or `429 - Too Many Requests`

**Cause:** Rate limit exceeded or insufficient permissions.

**Solution:**
1. **Rate limiting:** Wait 1 hour or use authenticated token (5000 req/hr vs 60 req/hr)
2. **Permissions:** Regenerate token with correct scopes
3. Check rate limit status:
   ```powershell
   curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

---

#### Issue: `ModuleNotFoundError: No module named 'common'`

**Cause:** `ai-agent-common` package not installed in project venv.

**Solution:**
```powershell
cd projects\04_github_issue_reporter
.venv\Scripts\Activate.ps1
uv pip install -e ..\..\common
```

---

#### Issue: Agent produces generic/hallucinated recommendations

**Cause:** LLM not grounding responses in tool data.

**Solution:**
1. Verify tools are returning data (check logs with `LOG_LEVEL=DEBUG`)
2. Ensure issue has sufficient context (body + comments)
3. Try a larger/more capable model: `OLLAMA_MODEL=llama3.1:8b`

---

#### Issue: `Connection refused` to Ollama

**Cause:** Ollama server not running.

**Solution:**
```powershell
# Start Ollama
ollama serve

# Verify it's running
ollama list
```

---

### Debug Mode

Enable verbose logging for troubleshooting:

```env
LOG_LEVEL=DEBUG
```

This shows:
- Tool invocation parameters
- API request URLs (tokens masked)
- HTTP response status codes
- Agent reasoning steps
- Error stack traces

---

## Security Considerations

### Threat Model

| Threat | Mitigation |
|---|---|
| **Prompt Injection** | Content wrapped in XML delimiters; truncation; strict system prompt |
| **Token Leakage** | Tokens never logged; read via `require_env()`; gitignored `.env` |
| **Sensitive Data in Issues** | Bodies/comments not persisted; only passed to LLM |
| **Unbounded API Calls** | Pagination capped at 2 pages (200 issues); recursion limit set |
| **Rate Limiting** | Authenticated calls (5000 req/hr); handles 429 gracefully |

### Best Practices

✅ **DO:**
- Use tokens with minimum required scopes
- Rotate tokens regularly (90-day expiration recommended)
- Enable debug logging only when troubleshooting
- Review issue content before sharing LLM output externally

❌ **DON'T:**
- Commit `.env` files to version control
- Share tokens in chat/email
- Use `repo` scope for public-only access (use `public_repo`)
- Log full issue bodies or comments

---

## Performance & Limitations

### Performance Characteristics

| Metric | Value |
|---|---|
| **Report Mode (100 issues)** | ~5-10 seconds (2 API calls + LLM formatting) |
| **Recommendation Mode** | ~8-15 seconds (2-3 API calls + LLM reasoning) |
| **Max Issues Fetched** | 200 (2 pages × 100 per page) |
| **Issue Body Truncation** | 4000 characters |
| **Comment Truncation** | 1000 characters each, max 10 comments |
| **Agent Recursion Limit** | 10 iterations |

### Known Limitations

1. **Large Repositories:**
   - Only fetches first 200 open issues
   - For repos with > 200 issues, oldest issues may be missed
   - **Workaround:** Use GitHub filters before running (e.g., filter by label)

2. **Long Issue Threads:**
   - Only top 10 comments fetched
   - Each comment truncated to 1000 chars
   - **Workaround:** For critical issues, review full thread on GitHub

3. **LLM Context Window:**
   - Issue bodies truncated to 4000 chars
   - Very long issues lose tail content
   - **Workaround:** Use larger context models (e.g., `codellama:70b`)

4. **Language Support:**
   - LLM responses in English by default
   - Issue content in any language supported
   - **Workaround:** Modify system prompt for multilingual output

5. **No Write Operations:**
   - Agent is read-only (no issue creation, labeling, or commenting)
   - Intentional security constraint
   - **Workaround:** Manually apply recommendations

---

## Contributing

### Adding New Features

1. **New Tool:** Add `@tool` function in `src/main.py`
2. **Register Tool:** Add to `tools` list in `build_agent()`
3. **Test Tool:** Add test class in `tests/test_main.py`
4. **Update Docs:** Document in this README

### Reporting Issues

Use the GitHub issue tracker:
- **Bugs:** Use `bug` label, include error logs
- **Features:** Use `enhancement` label, describe use case
- **Questions:** Use `question` label

### Pull Request Guidelines

1. All changes must maintain >= 90% test coverage
2. Run tests before submitting: `pytest --cov --cov-fail-under=90`
3. Follow repository coding conventions (see [docs/contributing.md](../../docs/contributing.md))
4. Update README if behavior changes

---

## License

This project is part of the Agentic AI Development Framework.  
See root [LICENSE](../../LICENSE) file for details.

---

## Support & Resources

- **Documentation:** [docs/getting_started.md](../../docs/getting_started.md)
- **GitHub API Reference:** https://docs.github.com/en/rest
- **LangGraph Guide:** https://langchain-ai.github.io/langgraph/
- **Ollama Models:** https://ollama.com/library

---

**Built with ❤️ using LangChain, LangGraph, and Ollama**
