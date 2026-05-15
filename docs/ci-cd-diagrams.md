# CI/CD Pipeline Architecture Diagram

This document contains ASCII diagrams visualizing the CI/CD pipeline architecture.

## Complete Pipeline Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Repository                                   │
│                     vibhatsrivastava/Agentic_AI_Development_Framework        │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────────┐  ┌─────────────┐  ┌────────────────┐
        │   Test Workflow   │  │   Copilot   │  │    Deploy      │
        │    (test.yml)     │  │ Implement   │  │  (deploy.yml)  │
        │                   │  │(copilot-    │  │                │
        │ Trigger:          │  │implement.yml)│  │ Trigger:       │
        │ • Push to main    │  │             │  │ • Push to dev  │
        │ • Push to dev     │  │ Trigger:    │  │ • Push to main │
        │ • Pull Requests   │  │ • Issue     │  │ • Manual       │
        │                   │  │   comments  │  │                │
        └─────────┬─────────┘  │   with      │  └────────┬───────┘
                  │            │   /implement│           │
                  │            │   -plan or  │           │
                  │            │   /approved │           │
                  │            └──────┬──────┘           │
                  │                   │                  │
                  ▼                   ▼                  ▼
        ┌──────────────────┐  ┌─────────────┐  ┌────────────────┐
        │ Jobs:            │  │ 1. Validate │  │ Jobs:          │
        │ • Lint (ruff)    │  │    CODEOWNER│  │ • Build & Test │
        │ • Test (pytest)  │  │ 2. Parse    │  │ • Deploy       │
        │ • Coverage (75%) │  │    params   │  │   Staging      │
        │ • Matrix: Py     │  │ 3. Collect  │  │   (auto)       │
        │   3.13, 3.14     │  │    context  │  │ • Deploy       │
        │                  │  │ 4. Assign   │  │   Production   │
        │ Outputs:         │  │    issue    │  │   (manual)     │
        │ • Coverage report│  │ 5. Post     │  │                │
        │ • Test results   │  │    context  │  │ Outputs:       │
        │ • PR comments    │  │             │  │ • Deploy tag   │
        └──────────────────┘  └─────────────┘  │ • Notifications│
                                                └────────────────┘
```

## Copilot Implementation Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ISSUE CREATED                                                        │
│ • Developer creates issue with bug/feature request                  │
│ • Issue description, labels, attachments added                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ DISCUSSION & ANALYSIS                                                │
│ • Team discusses approach in comments                               │
│ • Agentic bot provides recommendations                              │
│ • CODEOWNERS review and provide feedback                            │
│ • Additional requirements or changes proposed                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CODEOWNER APPROVAL                                                   │
│ • CODEOWNER comments: /implement-plan [options]                     │
│ • Options:                                                           │
│   - branch=<branch-name>    (default: copilot/issue-N)             │
│   - model=<llm-model>       (default: gpt-oss:20b)                 │
│ • Alternative: /approved [options]                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ VALIDATION (copilot-implement.yml workflow)                         │
│                                                                      │
│ Step 1: Check CODEOWNER                                             │
│ ├─ Read CODEOWNERS file                                             │
│ ├─ Extract authorized users/teams                                   │
│ ├─ Compare with comment author                                      │
│ └─ Result: ✅ Authorized / ❌ Unauthorized                          │
│                                                                      │
│ Step 2: Parse Command                                               │
│ ├─ Check for /implement-plan or /approved                           │
│ ├─ Extract branch parameter (or use default)                        │
│ ├─ Extract model parameter (or use default)                         │
│ └─ Result: Command config object                                    │
│                                                                      │
│ Step 3: Collect Context                                             │
│ ├─ Fetch issue title & body                                         │
│ ├─ Fetch ALL issue comments (chronological)                         │
│ ├─ Fetch labels and metadata                                        │
│ ├─ Build comprehensive context JSON                                 │
│ └─ Save to issue-context.json                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
    ┌───────────────────┐            ┌──────────────────────┐
    │ IF UNAUTHORIZED   │            │ IF AUTHORIZED        │
    │                   │            │                      │
    │ • Post error      │            │ Step 4: Assign Issue │
    │   comment         │            │ ├─ Assign to copilot │
    │ • List CODEOWNERS │            │ ├─ Add labels:       │
    │ • Stop workflow   │            │ │  - copilot-        │
    └───────────────────┘            │ │    implementing    │
                                     │ │  - approved        │
                                     │ └─ Result: Issue     │
                                     │    updated           │
                                     │                      │
                                     │ Step 5: Post Context │
                                     │ ├─ Confirmation      │
                                     │ │  comment           │
                                     │ ├─ Implementation    │
                                     │ │  context comment   │
                                     │ ├─ Show config       │
                                     │ │  (branch, model)   │
                                     │ └─ Result: Comments  │
                                     │    posted            │
                                     └──────────┬───────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │ IMPLEMENTATION         │
                                   │                        │
                                   │ Manual Steps:          │
                                   │ 1. Developer uses      │
                                   │    GitHub Copilot      │
                                   │    Workspace on issue  │
                                   │ 2. Or manually creates │
                                   │    branch and          │
                                   │    implements          │
                                   │ 3. References context  │
                                   │    from workflow       │
                                   │                        │
                                   │ Automated (Future):    │
                                   │ • GitHub Copilot API   │
                                   │   integration          │
                                   │ • Auto-create branch   │
                                   │ • Auto-commit changes  │
                                   │ • Auto-create PR       │
                                   └────────────┬───────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │ PULL REQUEST           │
                                   │                        │
                                   │ • PR created against   │
                                   │   dev branch           │
                                   │ • CODEOWNERS auto-     │
                                   │   requested for review │
                                   │ • Tests run via        │
                                   │   test.yml workflow    │
                                   │ • Coverage checked     │
                                   └────────────┬───────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │ REVIEW & MERGE         │
                                   │                        │
                                   │ • CODEOWNERS review    │
                                   │ • Tests must pass      │
                                   │ • Coverage ≥75%        │
                                   │ • Merge to dev         │
                                   │ • Auto-deploy to       │
                                   │   staging              │
                                   └────────────────────────┘
```

## Deployment Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CODE MERGED TO BRANCH                          │
└────────────────────────────┬───────────────┬────────────────────────┘
                             │               │
                    ┌────────┘               └────────┐
                    │                                 │
                    ▼                                 ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │  MERGED TO 'dev'          │    │  MERGED TO 'main'            │
    └───────────┬───────────────┘    └─────────────┬────────────────┘
                │                                   │
                ▼                                   ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │ Deploy Workflow Triggered │    │ Deploy Workflow Triggered    │
    │ (deploy.yml)              │    │ (deploy.yml)                 │
    └───────────┬───────────────┘    └─────────────┬────────────────┘
                │                                   │
                ▼                                   ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │ Job: build                │    │ Job: build                   │
    │ ├─ Checkout code          │    │ ├─ Checkout code             │
    │ ├─ Setup Python 3.13      │    │ ├─ Setup Python 3.13         │
    │ ├─ Install dependencies   │    │ ├─ Install dependencies      │
    │ ├─ Run linter (ruff)      │    │ ├─ Run linter (ruff)         │
    │ ├─ Run tests (pytest)     │    │ ├─ Run tests (pytest)        │
    │ └─ Upload coverage        │    │ └─ Upload coverage           │
    └───────────┬───────────────┘    └─────────────┬────────────────┘
                │                                   │
                ▼                                   ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │ Job: deploy-staging       │    │ Job: deploy-production       │
    │ needs: build              │    │ needs: build                 │
    │ environment: staging      │    │ environment: production      │
    │                           │    │                              │
    │ ✅ AUTOMATIC              │    │ ⏸️ MANUAL APPROVAL REQUIRED  │
    │                           │    │                              │
    │ Steps:                    │    │ Steps:                       │
    │ 1. Checkout code          │    │ 1. Wait for approval         │
    │ 2. Deploy to staging      │    │    • GitHub notification     │
    │    server/environment     │    │    • CODEOWNER reviews       │
    │ 3. Run smoke tests        │    │    • Click "Review           │
    │ 4. Post notification      │    │      deployments"            │
    │    to related PR          │    │    • Approve production      │
    └───────────┬───────────────┘    └─────────────┬────────────────┘
                │                                   │
                ▼                                   ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │ ✅ DEPLOYED TO STAGING    │    │ 2. Deploy to production      │
    │                           │    │    server/environment        │
    │ • Changes live in staging │    │ 3. Create deployment tag     │
    │ • Notification posted     │    │ 4. Run smoke tests           │
    │ • Ready for testing       │    │ 5. Post notification         │
    └───────────────────────────┘    └─────────────┬────────────────┘
                                                    │
                                                    ▼
                                     ┌──────────────────────────────┐
                                     │ ✅ DEPLOYED TO PRODUCTION    │
                                     │                              │
                                     │ • Changes live in production │
                                     │ • Deployment tag created     │
                                     │ • Notification posted        │
                                     │ • Audit trail logged         │
                                     └──────────────────────────────┘
```

## Branch Protection Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DEVELOPER CREATES PR                             │
│                  (from feature branch to main)                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BRANCH PROTECTION CHECKS (main branch)                              │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 1. Status Checks                                             │   │
│ │    ├─ test job (from test.yml) .................... ⏳      │   │
│ │    ├─ lint job (from test.yml) .................... ⏳      │   │
│ │    └─ build job (from deploy.yml) ................. ⏳      │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 2. Required Reviews                                          │   │
│ │    ├─ Number required: 1                                     │   │
│ │    └─ Review from Code Owners: Required ............. ⏳     │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 3. Conversation Resolution                                   │   │
│ │    └─ All conversations resolved: Required .......... ⏳     │   │
│ └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
    ┌──────────────────────┐        ┌───────────────────────┐
    │ ANY CHECK FAILS      │        │ ALL CHECKS PASS       │
    │                      │        │                       │
    │ • Merge button       │        │ • Merge button        │
    │   disabled           │        │   enabled             │
    │ • Developer must     │        │ • CODEOWNER can       │
    │   fix issues         │        │   merge to main       │
    │ • Re-run checks      │        │ • Triggers production │
    │                      │        │   deployment          │
    │ ❌ CANNOT MERGE      │        │                       │
    └──────────────────────┘        │ ✅ CAN MERGE          │
                                    └───────────────────────┘
```

## Workflow Interaction Matrix

```
┌─────────────┬──────────────┬───────────────┬─────────────────┐
│ Trigger     │ Test         │ Copilot       │ Deploy          │
│             │ (test.yml)   │ (copilot-     │ (deploy.yml)    │
│             │              │  implement    │                 │
│             │              │  .yml)        │                 │
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ Push to     │ ✅ Runs      │ ⬜ No         │ ⬜ No           │
│ feature     │              │               │                 │
│ branch      │              │               │                 │
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ Push to     │ ✅ Runs      │ ⬜ No         │ ✅ Runs         │
│ dev branch  │              │               │ • build         │
│             │              │               │ • deploy-staging│
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ Push to     │ ✅ Runs      │ ⬜ No         │ ✅ Runs         │
│ main branch │              │               │ • build         │
│             │              │               │ • deploy-prod   │
│             │              │               │   (manual)      │
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ PR opened   │ ✅ Runs      │ ⬜ No         │ ⬜ No           │
│ or updated  │              │               │                 │
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ Issue       │ ⬜ No        │ ✅ Runs       │ ⬜ No           │
│ comment:    │              │ (if CODEOWNER)│                 │
│ /implement  │              │               │                 │
│ -plan       │              │               │                 │
├─────────────┼──────────────┼───────────────┼─────────────────┤
│ Manual      │ ⬜ No        │ ⬜ No         │ ✅ Runs         │
│ workflow    │              │               │ (manual-deploy) │
│ dispatch    │              │               │                 │
└─────────────┴──────────────┴───────────────┴─────────────────┘
```

## Security & Access Control

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                               │
└─────────────────────────────────────────────────────────────────────┘

Layer 1: CODEOWNERS File
┌─────────────────────────────────────────────────────────────────────┐
│ • Defines authorized users/teams                                    │
│ • Controls who can trigger /implement-plan                          │
│ • Controls who can approve PRs                                      │
│ • Controls who can approve deployments                              │
└─────────────────────────────────────────────────────────────────────┘

Layer 2: Branch Protection (main)
┌─────────────────────────────────────────────────────────────────────┐
│ • Require PR reviews from CODEOWNERS                                │
│ • Require status checks (test, lint, build)                         │
│ • Require conversation resolution                                   │
│ • No direct pushes allowed                                          │
│ • No force pushes allowed                                           │
│ • No branch deletion allowed                                        │
└─────────────────────────────────────────────────────────────────────┘

Layer 3: Environment Protection (production)
┌─────────────────────────────────────────────────────────────────────┐
│ • Required reviewers: CODEOWNERS only                               │
│ • Deployment branches: main only                                    │
│ • Manual approval required before deployment                        │
│ • All deployments logged and auditable                              │
└─────────────────────────────────────────────────────────────────────┘

Layer 4: GitHub Actions Permissions
┌─────────────────────────────────────────────────────────────────────┐
│ • Read and write permissions for workflows                          │
│ • Limited to specific actions (create comments, assign, label)      │
│ • No deletion permissions                                           │
│ • Secrets accessible only by authorized workflows                   │
└─────────────────────────────────────────────────────────────────────┘

Access Matrix:
┌──────────────┬─────────────┬─────────────┬──────────────┬───────────┐
│ Action       │ Anyone      │ Contributor │ CODEOWNER    │ Admin     │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Create Issue │ ✅          │ ✅          │ ✅           │ ✅        │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Comment      │ ✅          │ ✅          │ ✅           │ ✅        │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Create PR    │ ✅          │ ✅          │ ✅           │ ✅        │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Trigger      │ ❌          │ ❌          │ ✅           │ ✅        │
│ /implement   │             │             │              │           │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Approve PR   │ ❌          │ ❌          │ ✅           │ ✅        │
│ to main      │             │             │              │           │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Merge to     │ ❌          │ ❌          │ ✅           │ ✅        │
│ main         │             │             │              │           │
├──────────────┼─────────────┼─────────────┼──────────────┼───────────┤
│ Approve      │ ❌          │ ❌          │ ✅           │ ✅        │
│ Production   │             │             │              │           │
│ Deployment   │             │             │              │           │
└──────────────┴─────────────┴─────────────┴──────────────┴───────────┘
```

---

*Diagrams last updated: 2026-05-15*
