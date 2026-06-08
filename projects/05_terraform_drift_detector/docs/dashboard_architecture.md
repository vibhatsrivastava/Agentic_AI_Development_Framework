# Dashboard Architecture - Terraform Drift Analyzer

## Overview

This document outlines the architecture for the Streamlit dashboard that will monitor Terraform drift detection and remediation activities. The dashboard will provide real-time visibility into infrastructure drift status using GitHub issues as the system of record.

## System Components

### 1. Streamlit Dashboard Application
- Built using Python and Streamlit framework
- Displays active and resolved drift records
- Provides real-time updates through GitHub webhooks
- Supports multiple views: active drifts, resolved drifts, and detailed views
- Single pane of glass for drift monitoring

### 2. GitHub Integration Layer
- Retrieves drift data from GitHub issues
- Parses issue labels and metadata to determine:
  * Severity levels (Critical, High, Medium, Low)
  * Drift types
  * Current status
- Validates webhook requests using webhook secrets
- Uses GitHub access tokens stored in environment variables

### 3. Data Flow Architecture
```
Terraform Drift Detection → GitHub Issue Creation → Teams Notification
                                      ↓
                         Streamlit Dashboard (Reads from GitHub)
```

### 4. Webhook Integration
- Listens for GitHub webhook events:
  * Issue Opened
  * Issue Edited
  * Issue Closed
  * Issue Reopened
- Automatically refreshes dashboard data upon event receipt
- No manual refresh required by users

## Data Model

### Drift Record Structure
Each drift record will contain the following fields:

- **Drift ID**: Unique identifier for the drift instance
- **Resource Name**: Name of the affected resource
- **Resource Type**: Type of the affected resource (e.g., aws_instance, aws_s3_bucket)
- **Severity**: Critical, High, Medium, or Low
- **Drift Description**: Detailed description of the drift
- **Detection Timestamp**: When drift was detected
- **GitHub Issue Number**: Reference to the GitHub issue
- **GitHub Issue Status**: Current status (open/closed)
- **Current Remediation Status**: Lifecycle status (DETECTED, ISSUE_CREATED, NOTIFIED, REMEDIATION_RUNNING, VALIDATION_RUNNING, RESOLVED)

### Dashboard Views

#### Active Drift View
Displays all open drift issues with filtering capabilities:
- Critical drifts
- High severity drifts
- Medium severity drifts
- Low severity drifts

#### Resolved Drift View
Displays resolved drift issues with:
- Resolution timestamp
- Resolution duration
- GitHub issue closure status

#### Drift Details View
Provides detailed information for selected drift records:
- Drift summary
- Resource impacted
- GitHub issue link
- Teams notification status
- Remediation status

## Dashboard Metrics

Summary cards showing:
- Total Active Drifts
- Total Resolved Drifts
- Critical Drifts
- High Severity Drifts
- Average Resolution Time

## Security Considerations

### Authentication & Authorization
- GitHub webhook requests validated using webhook secrets
- GitHub access tokens stored securely in environment variables
- No direct database access required (uses GitHub as system of record)

### Data Protection
- All sensitive information handled through secure environment variables
- No data stored locally on the dashboard VM
- All communications use HTTPS

## Deployment Architecture

### Hosting Environment
- Both Terraform Drift Analyzer agent and Streamlit dashboard deployed on same Windows VM
- No containerization required initially
- Single pane of glass approach for monitoring

### Performance Requirements
- Dashboard updates reflected within seconds of GitHub issue state changes
- Responsive UI with real-time data refresh capabilities

## Future Extensibility

### HITL (Human-In-The-Loop) Support
The architecture supports future addition of Human-In-The-Loop approval actions:

```
DETECTED → ISSUE_CREATED → NOTIFIED → AWAITING_APPROVAL → REMEDIATION_RUNNING → VALIDATION_RUNNING → RESOLVED
```

### Migration Path
Architecture designed to support future migration to:
- PostgreSQL database for enhanced performance
- FastAPI backend for improved scalability
- Separate Terraform execution service
- More sophisticated event-driven architecture

## Technical Constraints

### Development Language
- Python 3.11+ (consistent with existing codebase)

### Frameworks & Libraries
- Streamlit for dashboard UI
- GitHub REST API for data retrieval
- Webhook handling for real-time updates

### Infrastructure
- Same VM hosting both agent and dashboard
- No external databases or message queues
- No containerization initially

## Integration Points

### With Existing Terraform Drift Analyzer
- Leverages existing GitHub issue creation workflow
- Uses same issue metadata structure
- Integrates with existing Teams notification system

### With GitHub Webhooks
- Real-time event-driven updates
- Automatic dashboard refresh on state changes
- Secure webhook validation

## Monitoring & Maintenance

### Dashboard Health
- Automatic refresh on GitHub events
- Error handling for API failures
- Logging of dashboard interactions

### Performance Monitoring
- Response time monitoring
- Data refresh frequency tracking
- User interaction analytics (future enhancement)

## Assumptions

1. Existing Terraform Drift Analyzer agent continues to create GitHub issues with proper metadata
2. Webhook endpoint is configured and accessible
3. GitHub access tokens are properly configured in environment variables
4. Network connectivity exists between dashboard VM and GitHub API
5. Standard Python 3.11+ environment is available

## Limitations

1. No local data persistence (relies entirely on GitHub)
2. No automatic Terraform execution from dashboard (by design)
3. No approval workflow implementation in current scope
4. Single VM deployment constraint
5. No containerization or orchestration support initially

## Future Enhancements

1. Integration with PostgreSQL for enhanced performance
2. Addition of approval workflow functionality
3. Grafana dashboard integration
4. Multi-agent orchestration capabilities
5. Distributed deployment support
6. Enhanced notification systems
7. Automated Terraform execution from dashboard (future phase)
8. Advanced analytics and reporting features