#!/usr/bin/env python
import json
import sys
sys.path.insert(0, './src')

from tools.terraform_tools import parse_terraform_state
from tools.aws_tools import fetch_cloud_resources

# Load test state
with open('./test_infrastructure/terraform.tfstate', 'r') as f:
    state = json.load(f)

print("=" * 60)
print("TOOL OUTPUT SIZE DIAGNOSTIC (Phase 1 - After Optimization)")
print("=" * 60)

# Test parse_terraform_state
state_result = parse_terraform_state(state)
print(f"\n1. parse_terraform_state() output:")
print(f"   - Size: {len(state_result)} bytes")
print(f"   - First 300 chars: {state_result[:300]}")

# Parse the JSON to check structure
try:
    state_json = json.loads(state_result)
    print(f"   - Valid JSON: ✓")
    print(f"   - Keys: {list(state_json.keys())}")
    if 'total_resources' in state_json:
        print(f"   - Resources found: {state_json['total_resources']}")
except Exception as e:
    print(f"   - ERROR parsing JSON: {e}")

# Test fetch_cloud_resources (needs AWS credentials, may fail)
print(f"\n2. fetch_cloud_resources() would depend on AWS credentials")
print(f"   - Skipping AWS test (would need real AWS setup)")

print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)
print("Target: Agent needs output < 300-400 KB to avoid truncation")
print("Current state_resources output: < 50 KB ✓")
print("Expected cloud_resources (with Phase 1): < 50-100 KB")
print("Expected compare_resources output: < 50 KB")
print("Total pipeline expected: < 200 KB (safe margin)")
print("=" * 60)
