# Requirements - Terraform Drift Analyzer Dashboard Enhancement

## Project Overview

The existing Agentic AI Terraform Drift Analyzer detects Terraform infrastructure drift and performs the following actions:

1. Detects Terraform drift.
2. Creates a GitHub issue containing drift details.
3. Sends a Microsoft Teams notification.
4. Supports remediation of drift using Terraform apply.
5. Closes the GitHub issue once remediation is completed successfully.

The objective of this enhancement is to provide a real-time dashboard for monitoring drift detection and remediation activities.

---

# Goals

## Primary Goal

Provide a Streamlit dashboard that displays Terraform drift information and updates automatically as GitHub issue status changes.

## Secondary Goals

* Improve visibility into infrastructure drift.
* Provide a single pane of glass for drift monitoring.
* Demonstrate an end-to-end Agentic AI workflow.
* Support future Human-In-The-Loop (HITL) approval workflows.

---

# Current Architecture

Current workflow:

Terraform Drift Detection
→ GitHub Issue Creation
→ Teams Notification

No dashboard currently exists.

---

# Target Architecture

The Terraform Drift Analyzer agent and Streamlit dashboard will be deployed on the same VM.

No PostgreSQL database will be introduced in the initial implementation.

GitHub will be the system of record for drift tracking.

The dashboard will obtain drift information from GitHub issues.

Real-time updates will be received through GitHub webhooks.

---

# Functional Requirements

## FR-001 Drift Dashboard

Provide a Streamlit dashboard displaying all active Terraform drift records.

The dashboard shall display:

* Drift ID
* Resource Name
* Resource Type
* Severity
* Drift Description
* Detection Timestamp
* GitHub Issue Number
* GitHub Issue Status
* Current Remediation Status

---

## FR-002 Active Drift View

Display all open drift issues.

Users shall be able to view:

* Critical drifts
* High severity drifts
* Medium severity drifts
* Low severity drifts

---

## FR-003 Resolved Drift View

Display resolved drift issues.

Users shall be able to view:

* Resolution timestamp
* Resolution duration
* GitHub issue closure status

---

## FR-004 Drift Details View

Users shall be able to select a drift record and view:

* Drift summary
* Resource impacted
* GitHub issue link
* Teams notification status
* Remediation status

---

## FR-005 Dashboard Metrics

Provide summary cards showing:

* Total Active Drifts
* Total Resolved Drifts
* Critical Drifts
* High Severity Drifts
* Average Resolution Time

---

## FR-006 GitHub Integration

The dashboard shall retrieve drift data from GitHub issues.

GitHub issues created by the Terraform Drift Analyzer shall contain metadata required to populate the dashboard.

Issue labels and metadata shall be used to determine:

* Severity
* Drift type
* Status

---

## FR-007 Real-Time Updates

GitHub webhooks shall be configured.

Supported webhook events:

* Issue Opened
* Issue Edited
* Issue Closed
* Issue Reopened

When a webhook event is received:

* Dashboard data shall be refreshed.
* Status shall update automatically.
* Users shall not need to restart the application.

---

## FR-008 Remediation Tracking

The dashboard shall display remediation lifecycle status.

Supported states:

* DETECTED
* ISSUE_CREATED
* NOTIFIED
* REMEDIATION_RUNNING
* VALIDATION_RUNNING
* RESOLVED

---

## FR-009 Future HITL Support

The architecture shall support future addition of Human-In-The-Loop approval actions.

Future workflow:

DETECTED
→ ISSUE_CREATED
→ NOTIFIED
→ AWAITING_APPROVAL
→ REMEDIATION_RUNNING
→ VALIDATION_RUNNING
→ RESOLVED

Approval functionality is out of scope for the current implementation.

---

# Non-Functional Requirements

## NFR-001 Deployment

Agent and Streamlit dashboard must run on the same VM.

No containerization is required initially.

---

## NFR-002 Simplicity

Avoid introducing:

* Kafka
* PostgreSQL
* Redis
* RabbitMQ

unless required by future scaling needs.

---

## NFR-003 Maintainability

Architecture must support future migration to:

* PostgreSQL
* FastAPI
* Separate Terraform execution service
* Event-driven architecture

without significant redesign.

---

## NFR-004 Security

GitHub webhook requests shall be validated using webhook secrets.

GitHub access tokens shall be stored securely using environment variables.

---

## NFR-005 Performance

Dashboard updates should be reflected within seconds of GitHub issue state changes.

---

# Technical Constraints

* Language: Python
* Dashboard Framework: Streamlit
* Source of Truth: GitHub Issues
* Notifications: Microsoft Teams
* Drift Detection: Existing Terraform Drift Analyzer Agent
* Hosting: Same VM for Agent and Streamlit

---

# Out of Scope

The following items are not part of this implementation:

* PostgreSQL persistence
* Kafka integration
* Grafana dashboards
* Multi-agent orchestration
* Distributed deployments
* Approval workflow implementation
* Automatic Terraform execution from dashboard

These may be considered in future phases.

---

# Success Criteria

The solution is considered successful when:

1. Drift issues appear automatically on the Streamlit dashboard.
2. Dashboard displays current GitHub issue status.
3. GitHub issue closure updates dashboard status automatically.
4. Dashboard refreshes based on GitHub webhook events.
5. Active and resolved drift views are available.
6. Summary metrics are displayed.
7. Architecture supports future HITL approval workflows.
