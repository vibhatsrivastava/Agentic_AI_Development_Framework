# Tasks - Terraform Drift Analyzer Dashboard Enhancement

## Status Summary

**Implementation Phase:** ✅ COMPLETE
**Testing Phase:** 🔄 IN PROGRESS (User will perform testing)
**Deployment Phase:** ⏳ PENDING

## Overview
This document outlines the tasks required to implement the Streamlit dashboard for monitoring Terraform drift detection and remediation activities based on the requirements and architecture specifications.

## Setup Tasks

### 1. Environment Preparation
- [ ] Activate the virtual environment for the dashboard application (venv) using .\.venv\Scripts\activate.ps1 (windows)
- [ ] Install required Python packages (Streamlit, PyGithub, requests)
- [ ] Configure environment variables for GitHub access token and webhook secret
- [ ] Verify network connectivity to GitHub API

### 2. Project Structure Setup
- [x] Create directory structure for dashboard application
- [x] Set up source code organization
- [x] Configure .gitignore file
- [x] Update the README.md with dashboard setup instructions
- [x] Update the required Python packages in requirements.txt

## Implementation Tasks

### 1. Dashboard Application Development
- [x] Create main Streamlit dashboard application file
- [x] Implement active drift view with filtering capabilities
- [x] Implement resolved drift view with historical data
- [x] Implement detailed drift view for individual records
- [x] Design summary metrics cards (total active, resolved, critical, high severity, average resolution time)
- [x] Create data display components for drift records

### 2. GitHub Integration Layer
- [x] Implement GitHub API client for retrieving issue data
- [x] Parse GitHub issue labels and metadata to determine drift properties
- [x] Create functions to extract drift ID, resource name, type, severity, description, timestamps
- [x] Implement GitHub issue status tracking (open/closed)
- [x] Add remediation status tracking (DETECTED, ISSUE_CREATED, NOTIFIED, REMEDIATION_RUNNING, VALIDATION_RUNNING, RESOLVED)

### 3. Webhook Integration
- [x] Create webhook endpoint for receiving GitHub events
- [x] Implement webhook secret validation
- [x] Handle issue opened, edited, closed, and reopened events
- [x] Implement automatic dashboard refresh on webhook receipt
- [x] Add error handling for webhook processing failures

### 4. Data Model Implementation
- [x] Define drift record data structure
- [x] Create functions to parse GitHub issues into drift records
- [x] Implement data mapping from GitHub issue fields to dashboard display fields
- [x] Ensure compatibility with existing Terraform Drift Analyzer issue format

### 5. Dashboard UI Components
- [x] Design responsive layout for dashboard views
- [x] Implement active drift filtering by severity levels
- [x] Create drill-down functionality for detailed view
- [x] Add visual indicators for drift status and severity
- [x] Implement real-time data refresh mechanism
- [x] Add loading states and error handling

## Testing Tasks

### 1. Unit Testing
- [ ] Test GitHub API client functions
- [ ] Test issue parsing and data extraction functions
- [ ] Test webhook validation logic
- [ ] Test drift record data structure mapping
- [ ] Test dashboard component rendering

### 2. Integration Testing
- [ ] Test end-to-end flow from GitHub issue creation to dashboard display
- [ ] Verify real-time updates through webhook events
- [ ] Test different severity levels in active drift view
- [ ] Test resolved drift view with historical data
- [ ] Validate detailed drift view functionality

### 3. User Acceptance Testing
- [ ] Verify all required fields are displayed in dashboard views
- [ ] Confirm filtering capabilities work correctly
- [ ] Validate summary metrics accuracy
- [ ] Test dashboard responsiveness and performance
- [ ] Ensure no manual refresh is required for updates

## Deployment Tasks

### 1. Application Deployment
- [ ] Deploy Streamlit dashboard application on the same VM as Terraform Drift Analyzer agent
- [ ] Configure application to run continuously (using Streamlit's server mode)
- [ ] Set up proper logging configuration
- [ ] Verify application startup and shutdown procedures

### 2. Webhook Configuration
- [ ] Configure GitHub repository webhook settings
- [ ] Test webhook delivery to dashboard endpoint
- [ ] Validate webhook event handling
- [ ] Ensure webhook secret is properly configured

### 3. Security Configuration
- [ ] Verify GitHub access token security (environment variables)
- [ ] Confirm webhook secret validation works correctly
- [ ] Test secure data handling practices
- [ ] Review application security posture

## Future Enhancement Tasks

### 1. HITL Approval Workflow Support
- [ ] Prepare architecture for future approval workflow implementation
- [ ] Add placeholder for AWAITING_APPROVAL status
- [ ] Design data model extensions for approval tracking

### 2. Performance Improvements
- [ ] Consider PostgreSQL integration for enhanced performance (future phase)
- [ ] Implement caching mechanisms for frequently accessed data
- [ ] Optimize API call frequency to GitHub

### 3. Additional Features
- [ ] Explore Grafana dashboard integration (future phase)
- [ ] Add automated Terraform execution from dashboard (future phase)
- [ ] Implement advanced analytics and reporting features

## Success Criteria Verification

- [ ] Drift issues appear automatically on the Streamlit dashboard
- [ ] Dashboard displays current GitHub issue status
- [ ] GitHub issue closure updates dashboard status automatically
- [ ] Dashboard refreshes based on GitHub webhook events
- [ ] Active and resolved drift views are available
- [ ] Summary metrics are displayed correctly
- [ ] Architecture supports future HITL approval workflows
\end{contents}