# Quick Testing Guide - Terraform Drift Detector Optimizations

**Purpose**: Validate performance optimizations and verify functionality

---

## Prerequisites

1. **Rebuild vector store** (required for chunk size changes):
   ```bash
   cd projects/05_terraform_drift_detector
   python src/main.py check --workspace test \
     --state-file test_infrastructure/terraform.tfstate \
     --rebuild-vector-store
   ```

2. **Verify Langfuse is accessible**:
   - Open http://10.0.0.15:3000
   - Ensure `LANGFUSE_ENABLED=true` in `.env`

---

## Test 1: Basic Drift Check with Tracing

**Command**:
```bash
python src/main.py check --workspace production \
  --state-file test_infrastructure/terraform.tfstate
```

**Expected Output**:
```
================================================================================
## Drift Analysis Report — production

### Summary
- **Total Resources**: 3
- **Drifted**: 1
- **Compliant**: 2

**Severity Breakdown:**
- HIGH: 1

### Drifted Resources

#### 1. aws_instance.web_server
- **Resource ID**: `i-0123456789abcdef0`
- **Severity**: HIGH
- **Drift Type**: Tags Modified
...
================================================================================
```

**Verify**:
- ✅ Output is formatted markdown (not raw JSON)
- ✅ Summary section shows counts
- ✅ Drifted resources listed with details
- ✅ No errors in console

**Check Logs**:
```
INFO | RAG cache: X.XX% hit rate (X hits, X misses)
INFO | LLM cache: X.XX% hit rate (X hits, X misses)
```

---

## Test 2: Langfuse Tracing Verification

**After running Test 1**, access Langfuse:

1. **Open**: http://10.0.0.15:3000
2. **Navigate**: Sessions tab
3. **Filter**: Session ID = "production" (workspace name)

**Verify**:
- ✅ Trace appears with session_id="production"
- ✅ Tags include: `drift-detection`, `workspace:production`, `drift:true` (if drift detected)
- ✅ Metadata shows: `total_resources`, `drifted`, `severity_breakdown`
- ✅ Custom spans visible (if @observe decorators are working)

**Screenshot locations to check**:
- Dashboard → Sessions → Click on "production" session
- View trace timeline showing LLM calls, tool executions
- Check metadata panel for drift statistics

---

## Test 3: Cache Performance (Multiple Runs)

**Run 1** (cold cache):
```bash
python src/main.py check --workspace staging \
  --state-file test_infrastructure/terraform.tfstate
```

**Check Logs**:
```
DEBUG | RAG cache miss: abc123def456...
DEBUG | LLM cache miss: def789ghi012...
INFO | RAG cache: 0.00% hit rate (0 hits, 3 misses)
INFO | LLM cache: 0.00% hit rate (0 hits, 2 misses)
```

**Run 2** (warm cache - immediately after):
```bash
python src/main.py check --workspace staging \
  --state-file test_infrastructure/terraform.tfstate
```

**Check Logs**:
```
DEBUG | RAG cache hit: abc123def456...
DEBUG | LLM cache hit: def789ghi012...
INFO | RAG cache: 80.00% hit rate (4 hits, 1 misses)
INFO | LLM cache: 66.67% hit rate (4 hits, 2 misses)
```

**Verify**:
- ✅ Second run shows cache hits in logs
- ✅ Cache hit rate >60% on second run
- ✅ Second run completes faster (50-70% reduction expected)

---

## Test 4: Fix Mode with State Parsing Cache

**Run 1** (parse state):
```bash
python src/main.py fix --workspace production \
  --state-file test_infrastructure/terraform.tfstate \
  --resource i-0123456789abcdef0
```

**Check Logs**:
```
DEBUG | State parsing cache miss: test_infrastructure/terraform.tfstate
INFO | Parsed 3 resources from state file
```

**Run 2** (use cached state):
```bash
python src/main.py fix --workspace production \
  --state-file test_infrastructure/terraform.tfstate \
  --resource sg-abcdef0123456789
```

**Check Logs**:
```
DEBUG | State parsing cache hit: test_infrastructure/terraform.tfstate
```

**Verify**:
- ✅ Second run shows cache hit for state parsing
- ✅ State file parsing is instant (no "Parsed X resources" message)

---

## Test 5: Vector Store Optimization Verification

**After rebuilding vector store**, check logs during initialization:

```bash
python src/main.py check --workspace test \
  --state-file test_infrastructure/terraform.tfstate
```

**Check Logs**:
```
INFO | Loaded 4 policy documents
INFO | Loaded 1 documentation files
INFO | Split into 12 chunks  # Expected: ~12-15 (was ~30-40 with chunk_size=500)
INFO | Vector store created with 12 chunks
```

**Verify**:
- ✅ Chunk count is ~10-15 (down from ~30-40)
- ✅ teams.yaml not loaded (only 4 policy documents, not 5)
- ✅ No errors during indexing

---

## Test 6: JSON Output Quality

**Run drift check and capture output**:
```bash
python src/main.py check --workspace production \
  --state-file test_infrastructure/terraform.tfstate 2>&1 | tee output.log
```

**Manually verify markdown report includes**:
- Summary section with counts
- Severity breakdown
- Per-resource details
- Policy violations (if any)
- Remediation commands

**Parse JSON from agent** (check logs):
```
INFO | Successfully parsed JSON data from agent output
```

**Verify JSON structure** (internally used for GitHub issues):
- drift_detected: bool
- summary: {total_resources, drifted, compliant, severity_breakdown}
- resources: array with all required fields

---

## Test 7: GitHub Issue Creation (if enabled)

**Prerequisites**:
- Set `GITHUB_ISSUE_ENABLED=true` in `.env`
- Configure `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`

**Run**:
```bash
python src/main.py check --workspace production \
  --state-file test_infrastructure/terraform.tfstate
```

**Verify**:
- ✅ GitHub issues created (check GitHub repo)
- ✅ Issue titles include workspace name
- ✅ Issue bodies have drift details
- ✅ Labels applied correctly (severity-*, workspace-*)

---

## Test 8: Teams Notifications (if enabled)

**Prerequisites**:
- Set `TEAMS_NOTIFICATION_ENABLED=true` in `.env`
- Configure `TEAMS_WEBHOOK_URL`

**Run**:
```bash
python src/main.py check --workspace production \
  --state-file test_infrastructure/terraform.tfstate
```

**Verify**:
- ✅ Teams notification sent
- ✅ Message includes drift summary
- ✅ Links to GitHub issues (if created)

---

## Performance Comparison

### Before Optimizations
- **Total latency**: ~20-30 seconds (example)
- **LLM output tokens**: ~2000-3000 tokens
- **RAG queries**: 5 chunks × N resources = 15-25 queries
- **LLM API calls**: N resources × 1 = 3-5 calls

### After Optimizations (Expected)
- **Total latency**: ~6-12 seconds (50-70% reduction)
- **LLM output tokens**: ~700-1000 tokens (65% reduction)
- **RAG queries**: 1-2 unique queries (70-90% reduction via caching)
- **LLM API calls**: 1-2 unique calls (40-60% reduction via caching)

**Measure actual times**:
```bash
# Timing command (PowerShell)
Measure-Command { python src/main.py check --workspace prod --state-file test_infrastructure/terraform.tfstate }
```

---

## Troubleshooting

### Issue: No cache hits on second run
**Cause**: Cache expired (TTL=3600s), process restarted, or different drift patterns  
**Solution**: Run tests within 1 hour, reuse same workspace/state file

### Issue: Langfuse traces not appearing
**Cause**: `LANGFUSE_ENABLED=false`, missing API keys, or Langfuse unreachable  
**Solution**: Check `.env` configuration, verify http://10.0.0.15:3000 is accessible

### Issue: Chunk count still high after rebuild
**Cause**: Vector store not rebuilt, or using cached vector store  
**Solution**: Delete `./vector_store` directory and run with `--rebuild-vector-store`

### Issue: JSON parsing failed
**Cause**: LLM returned markdown instead of pure JSON  
**Solution**: Check logs for "No JSON block found", verify `format="json"` in `get_chat_llm()`

### Issue: Policy citations missing
**Cause**: k=2 too low for complex drift, or teams.yaml still indexed  
**Solution**: Verify teams.yaml excluded, check retrieved policy sources in logs

---

## Success Criteria

**All tests pass if**:
- ✅ Drift checks complete without errors
- ✅ Markdown output is formatted correctly
- ✅ Langfuse traces appear with session grouping
- ✅ Cache hit rates >60% on second run
- ✅ Chunk count reduced to ~10-15
- ✅ JSON output has all required fields
- ✅ GitHub issues and Teams notifications work (if enabled)
- ✅ Total latency reduced by 50-70%

---

## Next Steps After Testing

1. **Monitor production performance** over multiple drift checks
2. **Analyze Langfuse traces** to identify any remaining bottlenecks
3. **Tune cache TTLs** if policies change frequently (current: 1 hour)
4. **Adjust k value** if policy citations are missing (try k=3)
5. **Collect user feedback** on JSON-only output quality
6. **Document baseline metrics** for future comparison

---

## Quick Reference

**Langfuse Dashboard**: http://10.0.0.15:3000  
**Vector Store**: `./vector_store/`  
**Cache TTL**: 3600 seconds (1 hour)  
**RAG k value**: 2 (down from 5)  
**Chunk size**: 1500 (up from 500)  
**Prompt size**: ~180 words (down from ~830)  

**Cache Statistics Location**: Check logs for lines starting with:
```
INFO | RAG cache: ...
INFO | LLM cache: ...
```
