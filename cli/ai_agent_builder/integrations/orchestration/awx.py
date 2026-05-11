"""
awx.py — Ansible AWX orchestration integration module.

Enables scheduled and on-demand execution of AI agents via Ansible AWX.
When selected, scaffolds AWX-specific files (playbooks, surveys, credentials)
per-project for seamless AWX integration.

Usage:
    ai-agent-builder new-project 05_my_agent --integrations awx
"""

from pathlib import Path
from typing import Dict, List, Tuple

from ..base import IntegrationModule


class AwxIntegration(IntegrationModule):
    """
    Ansible AWX integration for orchestrating AI agents.

    Provides:
    - Ansible playbook templates for agent execution
    - AWX survey specifications for parameter input
    - Custom AWX credential type definitions
    - Per-project AWX setup documentation

    When selected during project creation, generates:
    - awx/playbook.yml      — Ansible playbook for this agent
    - awx/survey.json       — AWX survey spec with agent parameters
    - awx/credentials.yml   — Custom credential type definitions
    - awx/README.md         — AWX setup instructions for this agent
    """

    @property
    def name(self) -> str:
        """Integration name (must match CLI flag name)."""
        return "awx"

    @property
    def display_name(self) -> str:
        """Human-readable name for display."""
        return "Ansible AWX"

    @property
    def description(self) -> str:
        """Brief description of the integration."""
        return "Schedule and trigger agents via Ansible AWX with surveys and credentials"

    @property
    def category(self) -> str:
        """Integration category."""
        return "orchestration"

    @property
    def version(self) -> str:
        """Version when this integration was added."""
        return "0.2.0"

    def get_dependencies(self) -> List[str]:
        """
        Return list of pip dependencies required for AWX integration.

        Note: Ansible is typically installed on AWX control nodes, not in
        project venvs. These dependencies are for local playbook testing only.
        """
        return [
            "# AWX integration dependencies (for local playbook testing only)",
            "# ansible>=8.0.0  # Uncomment for local playbook testing",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        """
        Return dict of environment variables with example values.

        Note: AWX injects these at runtime via custom credential types.
        This is for reference only - actual values come from AWX credentials.
        """
        return {
            "# AWX Runtime Variables (injected by AWX, not stored in .env)": "",
            "# OLLAMA_BASE_URL": "http://ollama-server:11434",
            "# OLLAMA_API_KEY": "your_api_key_from_awx_credential",
            "# LANGFUSE_ENABLED": "true",
            "# LANGFUSE_PUBLIC_KEY": "pk-lf-from_awx_credential",
            "# LANGFUSE_SECRET_KEY": "sk-lf-from_awx_credential",
            "# LANGFUSE_HOST": "http://langfuse-server:3000",
        }

    def get_template_files(self) -> List[Tuple[str, str]]:
        """
        Return list of (template_path, output_path) tuples for file generation.

        Template paths are relative to cli/ai_agent_builder/templates/integrations/
        Output paths are relative to the project root.

        Generated files:
        - awx/playbook.yml      — Project-specific Ansible playbook
        - awx/survey.json       — AWX survey spec with agent parameters
        - awx/credentials.yml   — Custom credential type definitions
        - awx/README.md         — AWX setup instructions for this agent
        """
        return [
            ("awx/playbook.yml.j2", "awx/playbook.yml"),
            ("awx/survey.json.j2", "awx/survey.json"),
            ("awx/credentials.yml.j2", "awx/credentials.yml"),
            ("awx/README.md.j2", "awx/README.md"),
        ]

    def get_test_fixtures(self) -> str:
        """
        Return pytest fixtures for testing AWX integration.

        These fixtures mock AWX behavior for local testing without
        requiring an actual AWX instance.
        """
        return '''
@pytest.fixture
def mock_awx_credentials(monkeypatch):
    """Mock AWX credential injection via environment variables."""
    awx_creds = {
        "OLLAMA_BASE_URL": "http://mock-ollama:11434",
        "OLLAMA_API_KEY": "mock_api_key",
        "LANGFUSE_ENABLED": "false",  # Disable tracing in tests
    }
    for key, value in awx_creds.items():
        monkeypatch.setenv(key, value)
    return awx_creds


@pytest.fixture
def mock_awx_survey_vars(monkeypatch):
    """Mock AWX survey variables for agent parameters."""
    # Override with agent-specific parameters in test files
    survey_vars = {
        "agent_param_1": "test_value_1",
        "agent_param_2": "test_value_2",
    }
    for key, value in survey_vars.items():
        monkeypatch.setenv(key, value)
    return survey_vars


@pytest.fixture
def awx_output_parser():
    """Parse AWX wrapper JSON output for testing."""
    import json
    
    def parse(output: str) -> dict:
        """Parse JSON output from AWX wrapper."""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"status": "error", "error": "Invalid JSON output"}
    
    return parse
'''

    def get_readme_section(self) -> str:
        """
        Return markdown section to add to project README when AWX is selected.

        This section is appended to the project README to document AWX usage.
        """
        return """
## AWX Integration

This agent can be scheduled and triggered via Ansible AWX for automated execution.

### Setup

1. **Import Credential Types**: Import custom credential types from `awx/credentials.yml` into your AWX instance
2. **Create Credentials**: Create credentials in AWX using the imported types (Ollama API key, GitHub token, etc.)
3. **Create Project**: Add this repository as a project in AWX (SCM sync or manual)
4. **Create Job Template**:
   - Point to `awx/playbook.yml` in this project directory
   - Attach credentials created in step 2
   - Attach survey from `awx/survey.json`
5. **Configure Schedule** (optional): Add a schedule to the job template for periodic execution

### Usage

- **Manual Execution**: Launch job template from AWX UI, fill survey parameters
- **Scheduled Execution**: Job runs automatically based on configured schedule
- **Webhook Trigger**: Use AWX REST API to trigger job programmatically
- **Workflow Integration**: Include job template in AWX workflows for multi-agent orchestration

### Files

- `awx/playbook.yml` — Ansible playbook for this agent
- `awx/survey.json` — Survey specification for AWX UI
- `awx/credentials.yml` — Custom credential type definitions
- `awx/README.md` — Detailed AWX setup instructions

See `awx/README.md` for detailed setup instructions and troubleshooting.
"""
