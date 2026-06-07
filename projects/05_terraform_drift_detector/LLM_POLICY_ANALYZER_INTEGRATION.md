# LLM-Based Policy Violation Analysis Integration

## Overview

Replaced heuristic-based policy violation extraction with **intelligent LLM-based analysis** for enhanced impact assessment of Terraform drift.

### Changes Made

#### 1. **New Files Created**

**`src/llm_policy_analyzer.py`** (256 lines)
- `LLMPolicyAnalyzer` class: Core analyzer using Ollama LLM via `get_chat_llm()`
- Features:
  - Loads all policy YAML files from `policies/` directory
  - Uses LLM to analyze drift against actual policies
  - Structured prompt engineering with policy context
  - JSON output parsing via `JsonOutputParser`
  - Graceful fallback to heuristics if LLM fails
  - PolicyViolation dataclass with fields: policy, section, severity, impact, compliance_frameworks, remediation, confidence
  - Comprehensive error logging and recovery

**`src/impact_assessment_formatter.py`** (187 lines)
- `ImpactAssessmentFormatter` class: Formats violations for multiple output targets
- Features:
  - Console output with severity grouping (CRITICAL → HIGH → MEDIUM → LOW)
  - Markdown table export for reports
  - JSON export for APIs
  - Handles both dataclass and dict input formats
  - Emoji-based severity indicators
  - Detailed impact communication with remediation guidance

#### 2. **Modified Files**

**`src/main.py`**
- Added imports:
  ```python
  from typing import Optional
  from llm_policy_analyzer import LLMPolicyAnalyzer
  from impact_assessment_formatter import ImpactAssessmentFormatter
  ```

- Added lazy-loading initialization:
  ```python
  _policy_analyzer: Optional[LLMPolicyAnalyzer] = None
  _impact_formatter: Optional[ImpactAssessmentFormatter] = None
  
  def _get_policy_analyzer() -> LLMPolicyAnalyzer
  def _get_impact_formatter() -> ImpactAssessmentFormatter
  ```

- Replaced `_extract_policy_violations_from_drift()`:
  - Now calls `LLMPolicyAnalyzer.analyze_violations()` for intelligent analysis
  - Converts PolicyViolation objects to dicts for JSON serialization
  - Includes comprehensive error handling with heuristic fallback

- Added fallback function:
  - `_fallback_heuristic_violations()`: Original heuristic logic preserved as safety net

#### 3. **Architecture**

```
Drift Detection
    ↓
LLMPolicyAnalyzer.analyze_violations()
    ├─ Load policies from YAML files
    ├─ Create detailed prompt with policy context
    ├─ Query Ollama LLM for analysis
    ├─ Parse JSON response to PolicyViolation objects
    └─ Fallback: Heuristic extraction if LLM fails
    ↓
ImpactAssessmentFormatter
    ├─ Console output (color-coded by severity)
    ├─ Markdown reports
    └─ JSON export
    ↓
Output to user/Teams/GitHub
```

### Key Features

1. **Intelligent Analysis**
   - LLM reads actual policy files to understand compliance requirements
   - Analyzes drift against specific policy sections
   - Provides context-aware impact assessment

2. **Enhanced Impact Communication**
   - Detailed impact explanations beyond simple violation detection
   - Remediation guidance for each violation
   - Confidence scores from LLM analysis
   - Compliance framework mapping (SOC2, HIPAA, PCI-DSS, ISO27001, etc.)

3. **Resilience**
   - Graceful fallback to heuristics if LLM unavailable
   - Comprehensive error logging for debugging
   - Continues operation even if LLM analysis fails

4. **Backward Compatible**
   - All existing integration points work unchanged
   - Recovery path now uses LLM instead of heuristics
   - No breaking changes to data structures

### Data Flow

**Input to `_extract_policy_violations_from_drift()`:**
```python
{
    "resource_type": "aws_instance",
    "drift_type": "tags_modified",
    "severity": "HIGH",
    "changes": {
        "removed_tags": ["Environment"],
        "modified_tags": {"Owner": "old-team" → "new-team"}
    }
}
```

**Output (List of dicts):**
```python
[
    {
        "policy": "policies/tags.yaml",
        "section": "tag_compliance.required_tags",
        "severity": "HIGH",
        "impact": "Missing or modified required tags on aws_instance. Affects resource identification, cost tracking, compliance tracking, and operational automation.",
        "compliance_frameworks": ["AWS_TAGGING_POLICY", "SOC2", "ISO27001"],
        "remediation": "Apply required tags to aws_instance using Terraform or AWS Console",
        "confidence": 0.85
    }
]
```

### Integration Points (No Changes Required)

The following code paths automatically use LLM analysis:

1. **Line ~855**: Agent truncation recovery path
   - Rebuilds policy violations using LLM analyzer
   
2. **Line ~945**: Recovery drift from state file
   - Populates violations from LLM instead of heuristics

3. **Output formatting**: Console/Markdown/GitHub reports
   - Formatter can be used to enhance output presentation

### Dependencies

✅ **Already present in `requirements.txt`:**
- `pyyaml>=6.0` — Policy file parsing
- `langchain-chroma>=0.1.0` — LangChain ecosystem
- Base dependencies → LangChain, LangGraph, Ollama support

✅ **Available from `requirements-base.txt`:**
- `langchain_core` — LLM interface
- `ollama` support via Ollama base URL from `.env`

**No new dependencies required!**

### Testing Checklist

- [ ] Unit tests for `LLMPolicyAnalyzer` class
  - Mock LLM responses
  - Policy file loading
  - JSON parsing
  - Fallback logic

- [ ] Unit tests for `ImpactAssessmentFormatter` class
  - Console formatting
  - Markdown generation
  - JSON export
  - Severity grouping

- [ ] Integration tests
  - End-to-end flow with real Ollama
  - Policy file loading from actual directory
  - Recovery path with LLM analysis
  - Fallback behavior when LLM unavailable

- [ ] E2E manual testing
  - Run against test Terraform state file
  - Verify policy violations detected correctly
  - Check impact descriptions match policies
  - Validate output formatting

### Environment Requirements

Ensure `.env` has Ollama configuration:
```
OLLAMA_BASE_URL=http://localhost:11434  # or remote Ollama server
OLLAMA_MODEL=gpt-oss:20b               # or your chosen model
```

Optional Langfuse tracing (automatic):
```
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

### Troubleshooting

**Issue: LLM Analysis Returns Empty Violations**
- Check policy directory exists at `projects/05_terraform_drift_detector/policies/`
- Verify YAML files are properly formatted
- Check `OLLAMA_BASE_URL` and model accessibility

**Issue: LLM Timeouts**
- Increase timeout in `llm_policy_analyzer.py` if needed
- Check Ollama server is running and responsive
- Review model size (smaller models faster, larger models better analysis)

**Issue: Fallback Always Used**
- Check logs for LLM error messages
- Verify Ollama connectivity
- Try simpler model for debugging

### Next Steps

1. Run test suite (no code execution yet per requirements)
2. Validate with real Terraform drift detection
3. Monitor LLM response quality and latency
4. Fine-tune prompts based on real-world drift patterns
5. Consider caching policy analysis for improved performance

---

**Status**: ✅ Code ready for testing
**Files Modified**: 3
**New Dependencies**: 0
**Breaking Changes**: 0
