# Continue Agent Rules

## General Principles

* Always understand the existing codebase before proposing modifications.
* Read relevant files before making changes.
* Prefer extending existing patterns over introducing new frameworks.
* Keep implementations simple and maintainable.
* Avoid unnecessary abstractions.
* Avoid over-engineering.

---

# Operating System Rules

## Environment

This project is developed and executed on:

* Windows 10
* PowerShell 5.1 or later
* VS Code
* Continue Extension
* Python
* Terraform

The agent must assume Windows as the primary operating system.

---

## File Modification Rules

Before creating a new file:

1. Search for an existing implementation.
2. Reuse existing files whenever possible.
3. Do not create duplicate files.
4. Do not create files with suffixes such as:
   - _new
   - _v2
   - _updated
   - _fixed
   - _copy

Modify the existing file unless explicitly instructed otherwise.

Always explain why a new file is required.

---

## Command Execution Rules

### Always Use PowerShell Commands

Use PowerShell syntax for all terminal commands.

Examples:

```powershell
Get-ChildItem
Get-Content
Set-Location
Copy-Item
Move-Item
Remove-Item
New-Item
Add-Content
```

Preferred file search:

```powershell
Get-ChildItem -Recurse
```

Preferred file content search:

```powershell
Select-String
```

Preferred environment variable access:

```powershell
$env:GITHUB_TOKEN
```

---

## Forbidden Commands

Do not use Linux or macOS shell commands.

Avoid:

```bash
ls
cat
grep
find
pwd
mv
cp
rm
touch
chmod
chown
sudo
apt
apt-get
yum
dnf
brew
bash
sh
zsh
```

Always provide PowerShell equivalents.

---

## Path Rules

Use Windows paths.

Examples:

```text
C:\Projects\TerraformDriftAnalyzer
```

Use escaped backslashes where required.

Do not assume:

```text
/home/user/project
~/project
```

---

# Development Workflow

## Planning First

Before implementation:

1. Understand requirements.
2. Review architecture.
3. Identify impacted components.
4. Produce a plan.
5. Then implement.

Never immediately generate code without understanding context.

---

## Architecture Compliance

All changes must align with architecture.md.

If implementation conflicts with architecture.md:

* Explain the conflict.
* Propose alternatives.
* Request clarification.

Do not silently deviate from architecture decisions.

---

# Coding Standards

## Python

Target Python version:

```text
Python 3.11+
```

Use:

* Type hints
* Dataclasses where appropriate
* Structured logging
* Clear function names

Avoid:

* Global mutable state
* Hardcoded secrets
* Magic values

---

## Error Handling

Always:

* Catch expected exceptions.
* Log meaningful messages.
* Return actionable error information.

Avoid:

```python
except Exception:
    pass
```

---

## Logging

Use Python logging.

Required log levels:

* INFO
* WARNING
* ERROR

Log:

* Drift detection events
* GitHub issue creation
* Webhook processing
* Dashboard refresh events
* Remediation actions

Never log secrets.

---

# Project-Specific Rules

## Terraform Drift Analyzer

The project is an Agentic AI Terraform Drift Analyzer.

Current capabilities:

* Detect Terraform drift
* Create GitHub issues
* Send Teams notifications

Planned capabilities:

* Streamlit dashboard
* GitHub webhook integration
* Real-time status updates
* Future HITL approval workflow

---

## Dashboard Rules

Technology:

* Streamlit

Do not introduce:

* React
* Angular
* Vue
* Next.js

unless explicitly requested.

---

## Data Storage Rules

Current source of truth:

GitHub Issues

Do not introduce:

* PostgreSQL
* MySQL
* SQL Server
* MongoDB
* Redis

unless explicitly requested.

The dashboard should obtain drift status directly from GitHub.

---

## Event Processing Rules

Use GitHub Webhooks for real-time updates.

Avoid introducing:

* Kafka
* RabbitMQ
* ActiveMQ
* Azure Service Bus

unless explicitly requested.

Keep architecture simple.

---

## Deployment Rules

Current deployment target:

Single Windows VM

Agent and Streamlit dashboard run on the same machine.

Do not introduce:

* Kubernetes
* Docker Swarm
* Service Mesh

unless explicitly requested.

---

# GitHub Integration Rules

GitHub is the source of truth for drift status.

Issue lifecycle:

```text
DETECTED
    ↓
ISSUE_CREATED
    ↓
NOTIFIED
    ↓
REMEDIATION_RUNNING
    ↓
VALIDATION_RUNNING
    ↓
RESOLVED
```

When GitHub issue status changes:

* Dashboard must reflect changes.
* Webhook processing must be event-driven.

---

# Security Rules

Never hardcode:

* Tokens
* Secrets
* Passwords
* Webhook secrets

Use:

```powershell
$env:VARIABLE_NAME
```

or

```text
.env
```

with secure loading mechanisms.

---

# Testing Rules

Generate tests for:

* Drift parsing
* GitHub integration
* Webhook processing
* Dashboard services
* Status transitions

Prefer:

```text
pytest
```

All new features should include tests.

---

# Documentation Rules

Whenever implementing a new feature:

Update:

* architecture.md
* tasks.md
* README.md

when applicable.

Document:

* Assumptions
* Dependencies
* Configuration requirements

---

# Agent Behavior

Before coding:

1. Read requirements.md.
2. Read architecture.md.
3. Read tasks.md.
4. Review impacted files.
5. Explain implementation plan.
6. Then implement.

Never make large architectural changes without justification.

Prefer incremental, reviewable changes.
