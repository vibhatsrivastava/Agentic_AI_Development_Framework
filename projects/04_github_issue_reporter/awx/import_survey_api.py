#!/usr/bin/env python3
"""
Import survey specification to AWX via REST API.
Alternative to awx CLI which has Python 3.13+ compatibility issues.
"""
import json
import os
import requests
from pathlib import Path
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
AWX_HOST = os.getenv("AWX_HOST", "https://awx.local")
AWX_TOKEN = os.getenv("AWX_TOKEN")  # Create in AWX UI: User Icon → Tokens
JOB_TEMPLATE_NAME = "<Name-of-Your-Job-Template>"  # Must match exactly

# Validate required environment variables
if not AWX_TOKEN:
    print("❌ Error: AWX_TOKEN environment variable is required")
    print("   Create a token in AWX: User Icon → Tokens → Add")
    print("   Then set it: $env:AWX_TOKEN = 'your_token_here'")
    exit(1)

# Load survey spec
survey_file = Path(__file__).parent / "survey.json"
with open(survey_file) as f:
    survey_spec = json.load(f)

# AWX API headers
headers = {
    "Authorization": f"Bearer {AWX_TOKEN}",
    "Content-Type": "application/json"
}

# Find job template by name
response = requests.get(
    f"{AWX_HOST}/api/v2/job_templates/",
    headers=headers,
    params={"name": JOB_TEMPLATE_NAME},
    verify=False  # Disabled for self-signed certs
)

if response.status_code == 401:
    print("❌ Authentication failed - invalid AWX_TOKEN")
    print("   Create a new token in AWX: User Icon → Tokens → Add")
    print("   Scope: Write")
    exit(1)

response.raise_for_status()
templates = response.json()["results"]

if not templates:
    print(f"❌ Job template '{JOB_TEMPLATE_NAME}' not found")
    exit(1)

template_id = templates[0]["id"]
print(f"✅ Found job template ID: {template_id}")

# Update survey spec (use POST to replace any existing survey)
response = requests.post(
    f"{AWX_HOST}/api/v2/job_templates/{template_id}/survey_spec/",
    headers=headers,
    json=survey_spec,
    verify=False
)

# If failed, print detailed error information
if response.status_code != 200:
    print(f"❌ Failed to upload survey spec (HTTP {response.status_code})")
    print(f"Response: {response.text}")
    try:
        error_detail = response.json()
        print(f"Error details: {json.dumps(error_detail, indent=2)}")
    except Exception:
        pass
    exit(1)

print("✅ Survey spec uploaded")

# Enable survey
response = requests.patch(
    f"{AWX_HOST}/api/v2/job_templates/{template_id}/",
    headers=headers,
    json={"survey_enabled": True},
    verify=False
)
response.raise_for_status()
print("✅ Survey enabled")

print("\n🎉 Survey successfully imported!")
