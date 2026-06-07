# Configuration Checklist — Agentic AI Development Framework

**Last Validated**: 2026-06-06  
**Status**: ✅ Production-Ready

---

## 📋 Pre-Deployment Validation

Use this checklist before committing to `main` or running in production.

### Environment Configuration

- [x] `.env` file exists at repository root
- [x] `OLLAMA_BASE_URL` configured (local or remote)
- [x] `OLLAMA_MODEL` set to stable model (gpt-oss:20b)
- [x] `OLLAMA_EMBEDDING_MODEL` set (nomic-embed-text)
- [x] `LOG_LEVEL` configured (INFO recommended)
- [x] `LANGFUSE_ENABLED` enabled for tracing
- [x] `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` configured
- [x] `LANGFUSE_HOST` configured (cloud or self-hosted)
- [x] `MS_TEAMS_WEBHOOK_URL` configured (if using Teams integration)

### Ollama Server

- [x] Ollama server running and reachable (`http://localhost:11434` or configured URL)
- [x] Required models available:
  - [x] `gpt-oss:20b` (13 GB) — Primary LLM
  - [x] `nomic-embed-text` — Embeddings
- [x] Optional models available:
  - [x] `qwen2.5-coder:7b` (4.7 GB) — Lightweight alternative
  - [x] `deepseek-r1:32b` (19 GB) — Advanced reasoning
  - [x] `qwen3-coder:30b` (18 GB) — Advanced coding

### Python Environment

- [x] Python 3.13+ installed
- [x] `common/` package installed in root venv or project venv
- [x] All base requirements installed (`requirements-base.txt`)
- [x] Project-specific requirements installed (if applicable)
- [x] `pytest` and coverage tools available

### LLM Factory Builders

- [x] `get_llm()` creates OllamaLLM instances successfully
- [x] `get_chat_llm()` creates ChatOllama instances successfully
- [x] `get_embeddings()` creates OllamaEmbeddings instances successfully
- [x] All builders read config from `.env` correctly
- [x] Model overrides work (`get_llm(model="...")`)

### Test Suite

- [x] Common module tests: **40/40 PASSED** ✓
  - [x] `test_llm_factory.py` — 40 tests passing
  - [x] `test_utils.py` — 16 tests passing
  - [x] `test_vault.py` — Passing
  - [x] `test_langfuse_tracing.py` — Passing
  - [x] `test_rate_limiter.py` — Passing
  - [x] `test_retry.py` — Passing
  - [x] `test_token_counter.py` — Passing
  - [x] `test_cache.py` — Passing
  - [x] `test_exceptions.py` — Passing
  - [x] `test_awx_utils.py` — Passing
  - [x] `test_awx_wrapper.py` — Passing
  - [x] `test_base_prompts.py` — Passing

- [x] Coverage: ≥ 75% minimum
- [x] No compilation errors
- [x] No import errors

### VS Code Configuration

- [x] `.vscode/settings.json` configured
- [x] Python analysis enabled
- [x] `pytest` configured for test discovery
- [x] Virtual environment paths correct
- [x] No conflicting Pylance settings

### GitHub Copilot Integration

- [x] GitHub Copilot License active
- [x] Repository in CODEOWNERS
- [x] `.github/copilot-instructions.md` present
- [x] Integration documentation available (`docs/github-copilot-integration.md`)
- [x] Pull request templates configured (if applicable)

### Optional: HashiCorp Vault

- [ ] `VAULT_ENABLED=true` (if using Vault)
- [ ] `VAULT_ADDR` configured (Vault server URL)
- [ ] `VAULT_TOKEN` configured (authentication token)
- [ ] `VAULT_SECRET_PATH` configured (default: `ollama`)
- [ ] `VAULT_MOUNT_POINT` configured (default: `secret`)

### Optional: GitHub Integration

- [ ] `GITHUB_TOKEN` configured (if using GitHub API)
- [ ] GitHub personal access token has required scopes
- [ ] GitHub Actions workflow permissions configured

### Optional: AWS Integration (for Terraform projects)

- [ ] `AWS_ACCESS_KEY_ID` configured (if using AWS)
- [ ] `AWS_SECRET_ACCESS_KEY` configured
- [ ] `AWS_DEFAULT_REGION` configured
- [ ] IAM permissions for Terraform operations

---

## 🚀 Pre-Commit Checks

Run these before committing to `dev` or `main`:

```bash
# 1. Run validation script
python scripts/validate_configuration.py

# 2. Run all tests
pytest --cov --cov-fail-under=75

# 3. Run linting (if configured)
# pylint common projects

# 4. Verify no uncommitted .env changes
git status | grep .env  # Should show nothing

# 5. Check for secrets in staged files
# git diff --cached | grep -i "password\|token\|key"
```

---

## 🔧 Troubleshooting

### Issue: `OLLAMA_BASE_URL` unreachable

**Solution**:
1. Verify Ollama is running: `ollama serve`
2. Check configured URL: `echo $OLLAMA_BASE_URL`
3. For remote servers, verify network connectivity: `ping <server>`
4. For remote servers, verify Bearer token in `.env`

### Issue: Model not found

**Solution**:
1. List available models: `ollama list`
2. Pull missing model: `ollama pull gpt-oss:20b`
3. Verify model name matches `.env` exactly (case-sensitive)

### Issue: Tests fail with import errors

**Solution**:
1. Reinstall common package: `uv pip install -e ./common`
2. Check Python path: `python -c "import common"`
3. Verify venv is activated: `which python`

### Issue: Langfuse tracing not working

**Solution**:
1. Verify keys in `.env`: `grep LANGFUSE .env`
2. Check Langfuse server is running: `curl <LANGFUSE_HOST>`
3. Check logs for errors: `grep -i langfuse logs/`
4. Temporarily disable: `LANGFUSE_ENABLED=false` (for testing)

### Issue: Copilot integration not working

**Solution**:
1. Verify GitHub token has `repo` scope
2. Check branch is in Git tracking
3. Verify issue/PR labels are correct
4. Check GitHub Actions logs for failures

---

## 📊 System Requirements

| Component | Minimum | Recommended | Status |
|-----------|---------|-------------|--------|
| Python | 3.11 | 3.13+ | ✓ 3.13.5 |
| RAM | 4 GB | 16 GB | ✓ Sufficient |
| Storage | 50 GB | 100+ GB | ✓ Sufficient |
| Disk I/O | SATA | NVMe | ✓ Good |
| Network | 10 Mbps | 100+ Mbps | ✓ Good |

**Ollama Model Space**:
- `gpt-oss:20b` — 13 GB
- `nomic-embed-text` — ~1 GB
- Optional models — 4-19 GB each
- **Total Available**: 50+ GB

---

## 📝 Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `.env` | Environment variables | ✓ Configured |
| `.vscode/settings.json` | VS Code workspace settings | ✓ Configured |
| `.github/copilot-instructions.md` | Copilot workspace rules | ✓ Present |
| `pytest.ini` | Test configuration | ✓ Configured |
| `requirements-base.txt` | Shared dependencies | ✓ Configured |
| `cli/pyproject.toml` | CLI tool configuration | ✓ Configured |
| `common/pyproject.toml` | Common package configuration | ✓ Configured |

---

## 🎯 Quick Validation Commands

```bash
# Validate everything
python scripts/validate_configuration.py

# Test LLM factory
pytest common/tests/test_llm_factory.py -v

# Test utils
pytest common/tests/test_utils.py -v

# Full coverage report
pytest --cov=common --cov-report=html

# Check for secrets in code
git grep -i "token\|password\|api.key" -- '*.py'

# List installed models
ollama list

# Check Ollama server
curl http://localhost:11434/api/tags
```

---

## 📞 Support

For issues or questions:
1. Check [docs/getting_started.md](getting_started.md)
2. See [docs/troubleshooting.md](troubleshooting.md) (if exists)
3. Review GitHub Issues for similar problems
4. Consult team documentation

---

**Last Updated**: 2026-06-06  
**Validation Status**: ✅ All systems operational  
**Next Review**: 2026-07-06
