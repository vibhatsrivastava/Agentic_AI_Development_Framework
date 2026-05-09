# HashiCorp Vault Integration

This document explains how to use HashiCorp Vault for centralized secret management in Langchain Development Projects.

---

## Table of Contents

- [Overview](#overview)
- [Why Use Vault?](#why-use-vault)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Setting Up Vault](#setting-up-vault)
  - [Option 1: Local Development Server](#option-1-local-development-server)
  - [Option 2: Production Vault Server](#option-2-production-vault-server)
- [Storing Secrets in Vault](#storing-secrets-in-vault)
- [Configuring Your Project](#configuring-your-project)
- [How It Works](#how-it-works)
- [Testing Your Setup](#testing-your-setup)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

HashiCorp Vault integration provides **centralized secret management** for teams working on Agentic AI projects. Instead of each developer maintaining their own `.env` file with sensitive API keys, secrets are stored in Vault and retrieved automatically at runtime.

**Key Features:**
- **Centralized management**: Store `OLLAMA_API_KEY` once, accessible to all developers on the network
- **Automatic fallback**: If Vault is unreachable (offline, network issues), applications seamlessly fall back to `.env` files
- **Zero code changes**: Projects use `get_llm()` as before — credential retrieval is transparent
- **Backward compatible**: Vault is disabled by default; existing workflows continue unchanged

---

## Why Use Vault?

**Without Vault:**
- Each developer needs the API key manually shared
- Keys stored in `.env` files (risk of committing to Git)
- Key rotation requires updating every developer's `.env` file
- No audit trail of who accessed secrets

**With Vault:**
- Developers retrieve keys automatically from Vault
- No secrets in local files (unless Vault is unavailable)
- Rotate keys centrally — all developers get the new key immediately
- Vault audit logs track secret access

---

## Prerequisites

1. **HashiCorp Vault server** (local dev server or remote production instance)
   - Download: [https://www.vaultproject.io/downloads](https://www.vaultproject.io/downloads)
   - Or use managed Vault service (HCP Vault, AWS Secrets Manager with Vault adapter, etc.)

2. **Network access** to the Vault server (if using remote Vault)

3. **Python dependencies** (automatically installed):
   ```powershell
   uv pip install -r requirements-base.txt  # Includes hvac>=2.0.0
   ```

---

## Quick Start

**For developers joining an existing team with Vault already set up:**

1. Ask your team lead for:
   - Vault server URL (`VAULT_ADDR`)
   - Vault authentication token (`VAULT_TOKEN`)

2. Update your `.env` file at the repo root:
   ```env
   # Enable Vault
   VAULT_ENABLED=true
   VAULT_ADDR=http://vault.example.com:8200
   VAULT_TOKEN=hvs.your_token_here
   
   # Optional: customize secret path (if different from default)
   VAULT_SECRET_PATH=ollama
   VAULT_MOUNT_POINT=secret
   ```

3. **Run your project** — API keys are retrieved from Vault automatically:
   ```powershell
   python projects/01_hello_langchain/src/main.py
   ```

4. **Verify** in the logs:
   ```
   INFO | common.vault | Retrieved 'OLLAMA_API_KEY' from Vault (path: secret/ollama)
   ```

---

## Setting Up Vault

### Option 1: Local Development Server

**For individual developers or testing Vault integration:**

1. **Install Vault** (if not already installed):
   - Windows: Download from [https://www.vaultproject.io/downloads](https://www.vaultproject.io/downloads)
   - Extract `vault.exe` to a directory in your PATH

2. **Start Vault dev server**:
   ```powershell
   vault server -dev
   ```
   
   Output will show:
   ```
   Root Token: hvs.XXXXXXXXXXXXXXXXXXXXXXXX
   Unseal Key: ...
   Vault Address: http://127.0.0.1:8200
   ```

3. **Save the Root Token** — you'll need it for `VAULT_TOKEN` in `.env`

4. **Set environment variables** (for Vault CLI):
   ```powershell
   $env:VAULT_ADDR="http://127.0.0.1:8200"
   $env:VAULT_TOKEN="hvs.XXXXXXXXXXXXXXXXXXXXXXXX"
   ```

5. **Verify Vault is running**:
   ```powershell
   vault status
   ```

**⚠️ Warning:** Dev server stores secrets **in memory only** — data is lost on restart. Use production server for real deployments.

---

### Option 2: Production Vault Server

**For teams deploying Vault for multiple developers:**

1. **Install Vault on a server** accessible to all team members

2. **Initialize and unseal Vault**:
   ```bash
   vault operator init
   vault operator unseal
   ```
   
   Save the unseal keys and root token securely (use a password manager or secret sharing tool).

3. **Enable KV v2 secrets engine** (if not already enabled):
   ```bash
   vault secrets enable -version=2 kv
   ```
   
   Or if using custom mount point:
   ```bash
   vault secrets enable -path=secret -version=2 kv
   ```

4. **Create a policy for Ollama secrets**:
   ```bash
   vault policy write ollama-read - <<EOF
   path "secret/data/ollama" {
     capabilities = ["read"]
   }
   EOF
   ```

5. **Create tokens for developers**:
   ```bash
   vault token create -policy=ollama-read -ttl=720h
   ```
   
   Share the generated token with each developer for their `.env` file.

---

## Storing Secrets in Vault

### Using Vault CLI

1. **Authenticate with Vault**:
   ```powershell
   $env:VAULT_ADDR="http://vault.example.com:8200"
   $env:VAULT_TOKEN="hvs.your_root_or_admin_token"
   ```

2. **Store the Ollama API key**:
   ```powershell
   vault kv put secret/ollama OLLAMA_API_KEY="your_actual_api_key_here"
   ```

3. **Verify the secret was stored**:
   ```powershell
   vault kv get secret/ollama
   ```
   
   Output:
   ```
   ====== Data ======
   Key               Value
   ---               -----
   OLLAMA_API_KEY    your_actual_api_key_here
   ```

### Using Vault UI

1. Open your Vault server URL in a browser (e.g., `http://vault.example.com:8200/ui`)

2. Log in with your token

3. Navigate to **Secrets** → `secret/` → **Create secret**

4. Set:
   - **Path**: `ollama`
   - **Secret data**:
     - Key: `OLLAMA_API_KEY`
     - Value: `your_actual_api_key_here`

5. Click **Save**

---

## Configuring Your Project

### Update `.env` File

At the repo root, edit `.env`:

```env
# ─── HashiCorp Vault (Optional) ──────────────────────────────────────────────
VAULT_ENABLED=true
VAULT_ADDR=http://vault.example.com:8200
VAULT_TOKEN=hvs.your_vault_token_here
VAULT_SECRET_PATH=ollama
VAULT_MOUNT_POINT=secret

# ─── Ollama Server ────────────────────────────────────────────────────────────
OLLAMA_BASE_URL=http://10.0.0.15:11434
# OLLAMA_API_KEY is now fetched from Vault
# Keep this line as fallback if Vault is unreachable:
OLLAMA_API_KEY=your_fallback_api_key_here
```

**Configuration Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VAULT_ENABLED` | No | `false` | Set to `true` to enable Vault integration |
| `VAULT_ADDR` | Yes* | — | Vault server URL (e.g., `http://vault.example.com:8200`) |
| `VAULT_TOKEN` | Yes* | — | Authentication token for Vault |
| `VAULT_SECRET_PATH` | No | `ollama` | Path to secret in Vault (without mount point) |
| `VAULT_MOUNT_POINT` | No | `secret` | Vault mount point for KV secrets engine |

\* Required when `VAULT_ENABLED=true`

---

## How It Works

### Credential Retrieval Flow

```
┌─────────────────┐
│  Application    │
│  (get_llm())    │
└────────┬────────┘
         │
         │ Needs OLLAMA_API_KEY
         ▼
┌─────────────────────────────────────────┐
│  common/vault.py::get_secret()          │
│  ────────────────────────────────────   │
│  1. Check module-level cache            │
│     └─ If cached → return immediately   │
│                                          │
│  2. Check if VAULT_ENABLED=true         │
│     └─ If false → skip to step 4        │
│                                          │
│  3. Try to fetch from Vault             │
│     ├─ Success → cache & return         │
│     └─ Error → log warning, continue    │
│                                          │
│  4. Fallback to .env file               │
│     └─ os.getenv("OLLAMA_API_KEY")      │
│                                          │
│  5. Return default ("") if not found    │
└─────────────────────────────────────────┘
```

### Code Integration

**In `common/llm_factory.py` (line 26):**
```python
from common.vault import get_secret

_API_KEY = get_secret(
    vault_key="OLLAMA_API_KEY",
    env_fallback_key="OLLAMA_API_KEY",
    default=""
)
```

**In your project code:**
```python
# No changes needed! Just use the factory as before:
from common.llm_factory import get_llm

llm = get_llm()  # API key retrieved from Vault or .env transparently
```

---

## Testing Your Setup

### 1. Test Vault Connection

```powershell
# Verify Vault is accessible
$env:VAULT_ADDR="http://vault.example.com:8200"
$env:VAULT_TOKEN="hvs.your_token"
vault status
```

Expected output:
```
Sealed: false
...
```

### 2. Test Secret Retrieval

```powershell
vault kv get secret/ollama
```

Expected output:
```
====== Data ======
Key               Value
---               -----
OLLAMA_API_KEY    your_api_key_here
```

### 3. Test Application with Vault

Run a project and check logs for Vault retrieval:

```powershell
python projects/01_hello_langchain/src/main.py
```

**Expected log output (Vault enabled and working):**
```
INFO | common.vault | Successfully connected to Vault at http://vault.example.com:8200
INFO | common.vault | Retrieved 'OLLAMA_API_KEY' from Vault (path: secret/ollama)
INFO | __main__ | Initialising LLM...
```

### 4. Test Fallback Mechanism

**Simulate Vault being unavailable:**

1. Stop Vault server (or set incorrect `VAULT_ADDR`)
2. Ensure `OLLAMA_API_KEY` is set in `.env`
3. Run the project again

**Expected log output (Vault fallback to .env):**
```
ERROR | common.vault | Failed to initialize Vault client: ... Falling back to .env
INFO | common.vault | Using .env fallback for 'OLLAMA_API_KEY' (Vault unavailable or key not found)
INFO | __main__ | Initialising LLM...
```

---

## Troubleshooting

### Problem: "hvac library is not installed"

**Cause:** `hvac` package (Vault Python client) is missing.

**Solution:**
```powershell
uv pip install hvac>=2.0.0
# Or reinstall all dependencies:
uv pip install -r requirements-base.txt
```

---

### Problem: "VAULT_ADDR is not set"

**Cause:** `VAULT_ENABLED=true` but `VAULT_ADDR` is missing from `.env`.

**Solution:**
Add to `.env`:
```env
VAULT_ADDR=http://vault.example.com:8200
```

---

### Problem: "Vault authentication failed"

**Cause:** `VAULT_TOKEN` is invalid, expired, or has insufficient permissions.

**Solution:**
1. **Check token validity**:
   ```powershell
   vault token lookup $env:VAULT_TOKEN
   ```
   
2. **Renew token** (if renewable):
   ```powershell
   vault token renew
   ```
   
3. **Create new token** (if expired):
   ```powershell
   vault token create -policy=ollama-read
   ```

---

### Problem: "Key 'OLLAMA_API_KEY' not found in Vault secret"

**Cause:** Secret exists in Vault, but the key name doesn't match.

**Solution:**
1. **Check secret contents**:
   ```powershell
   vault kv get secret/ollama
   ```
   
2. **Add or fix the key**:
   ```powershell
   vault kv patch secret/ollama OLLAMA_API_KEY="your_key_here"
   ```

---

### Problem: "Vault secret path does not exist"

**Cause:** `VAULT_SECRET_PATH` points to a non-existent path in Vault.

**Solution:**
1. **List secrets**:
   ```powershell
   vault kv list secret/
   ```
   
2. **Create the secret**:
   ```powershell
   vault kv put secret/ollama OLLAMA_API_KEY="your_key_here"
   ```
   
3. **Or update `.env` to match existing path**:
   ```env
   VAULT_SECRET_PATH=your_existing_path
   ```

---

### Problem: Application still uses .env even when Vault is enabled

**Cause:** Vault fetch succeeded, but the key is not in the secret, triggering fallback.

**Solution:**
1. **Enable DEBUG logging** in `.env`:
   ```env
   LOG_LEVEL=DEBUG
   ```
   
2. **Run the application** and check logs:
   ```
   DEBUG | common.vault | Vault returned: {'OTHER_KEY': 'value'}
   WARNING | common.vault | Key 'OLLAMA_API_KEY' not found in Vault secret
   INFO | common.vault | Using .env fallback for 'OLLAMA_API_KEY'
   ```
   
3. **Add the missing key** to Vault (see above).

---

## Security Best Practices

### 1. Never Commit `.env` with Real Secrets

Even with Vault, `.env` should not contain production secrets:

```env
# ✅ Good: Fallback for offline development
OLLAMA_API_KEY=localhost-dev-key

# ❌ Bad: Production key in .env
OLLAMA_API_KEY=prod_ACtUaL_sEcReT_KeY
```

**Why:** `.env` fallback is for **local development** when Vault is unreachable.

---

### 2. Use Token TTL (Time-To-Live)

Create developer tokens with expiration:

```bash
vault token create -policy=ollama-read -ttl=720h  # 30 days
```

Forces periodic token renewal (enhances security).

---

### 3. Use Least-Privilege Policies

Grant **read-only** access to secrets:

```hcl
# ollama-read policy
path "secret/data/ollama" {
  capabilities = ["read"]
}
```

**Do not** give developers `write` or `delete` capabilities unless necessary.

---

### 4. Rotate Secrets Regularly

Change API keys in Vault periodically:

```powershell
vault kv put secret/ollama OLLAMA_API_KEY="new_rotated_key"
```

All developers get the new key on next app restart (no `.env` updates needed).

---

### 5. Monitor Vault Audit Logs

Enable Vault audit logging to track secret access:

```bash
vault audit enable file file_path=/var/log/vault_audit.log
```

Review logs for unauthorized access attempts.

---

## Advanced Configuration

### Using Different Mount Points

If your Vault uses a custom KV mount point:

```env
VAULT_MOUNT_POINT=custom-kv
```

Vault will read from `custom-kv/data/ollama` instead of `secret/data/ollama`.

---

### Storing Multiple Secrets

Store additional secrets in the same Vault path:

```powershell
vault kv put secret/ollama \
  OLLAMA_API_KEY="your_api_key" \
  OLLAMA_BASE_URL="http://remote-ollama:11434" \
  OTHER_SECRET="value"
```

**Extend `common/vault.py` to retrieve other secrets:**
```python
from common.vault import get_secret

# Retrieve additional secrets
base_url = get_secret("OLLAMA_BASE_URL", "OLLAMA_BASE_URL", default="http://localhost:11434")
```

---

### Using AppRole Authentication (Instead of Tokens)

For production environments, use **AppRole** instead of long-lived tokens:

1. **Enable AppRole**:
   ```bash
   vault auth enable approle
   ```

2. **Create AppRole**:
   ```bash
   vault write auth/approle/role/ollama-app \
     secret_id_ttl=1h \
     token_ttl=1h \
     token_policies=ollama-read
   ```

3. **Modify `common/vault.py`** to authenticate with AppRole:
   ```python
   # In _get_vault_client()
   role_id = os.getenv("VAULT_ROLE_ID")
   secret_id = os.getenv("VAULT_SECRET_ID")
   
   client = hvac.Client(url=vault_addr)
   client.auth.approle.login(role_id=role_id, secret_id=secret_id)
   ```

---

### Namespace Support (Vault Enterprise)

For multi-tenant Vault:

```env
VAULT_NAMESPACE=team-a
```

Update `common/vault.py` to set namespace when creating the client:
```python
client = hvac.Client(url=vault_addr, token=vault_token, namespace=vault_namespace)
```

---

## Summary

- **Enable Vault**: Set `VAULT_ENABLED=true` in `.env`
- **Configure connection**: Set `VAULT_ADDR` and `VAULT_TOKEN`
- **Store secrets**: Use `vault kv put secret/ollama OLLAMA_API_KEY="..."`
- **Run projects**: No code changes needed — keys retrieved automatically
- **Fallback works**: If Vault is unreachable, `.env` is used automatically
- **Disable anytime**: Set `VAULT_ENABLED=false` to use `.env` only

For questions or issues, see [Troubleshooting](#troubleshooting) or ask your team lead.
