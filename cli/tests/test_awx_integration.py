"""
test_awx_integration.py — Unit tests for AWX integration module.

Tests the AwxIntegration class that provides AWX orchestration capabilities.
"""

import pytest
from pathlib import Path

from ai_agent_builder.integrations.orchestration.awx import AwxIntegration


class TestAwxIntegration:
    """Test suite for AwxIntegration class."""
    
    @pytest.fixture
    def awx_integration(self):
        """Fixture providing AwxIntegration instance."""
        return AwxIntegration()
    
    def test_integration_properties(self, awx_integration):
        """Test that integration properties are correctly defined."""
        assert awx_integration.name == "awx"
        assert awx_integration.display_name == "Ansible AWX"
        assert awx_integration.category == "orchestration"
        assert "schedule" in awx_integration.description.lower() or "trigger" in awx_integration.description.lower()
        assert awx_integration.version == "0.2.0"
    
    def test_get_dependencies(self, awx_integration):
        """Test that dependencies list is returned (may be empty or comments)."""
        deps = awx_integration.get_dependencies()
        assert isinstance(deps, list)
        # AWX dependencies are optional (for local testing only)
        # May be empty or contain commented-out ansible package
    
    def test_get_env_vars(self, awx_integration):
        """Test that environment variables dict is returned."""
        env_vars = awx_integration.get_env_vars()
        assert isinstance(env_vars, dict)
        # AWX injects vars at runtime, so this is for reference only
        # May contain comments explaining AWX runtime injection
    
    def test_get_template_files(self, awx_integration):
        """Test that template file mappings are correctly defined."""
        templates = awx_integration.get_template_files()
        assert isinstance(templates, list)
        assert len(templates) == 4  # playbook, survey, credentials, README
        
        # Verify expected template files
        template_names = [t[0] for t in templates]
        assert "awx/playbook.yml.j2" in template_names
        assert "awx/survey.json.j2" in template_names
        assert "awx/credentials.yml.j2" in template_names
        assert "awx/README.md.j2" in template_names
        
        # Verify expected output paths
        output_paths = [t[1] for t in templates]
        assert "awx/playbook.yml" in output_paths
        assert "awx/survey.json" in output_paths
        assert "awx/credentials.yml" in output_paths
        assert "awx/README.md" in output_paths
    
    def test_get_test_fixtures(self, awx_integration):
        """Test that test fixtures string is returned."""
        fixtures = awx_integration.get_test_fixtures()
        assert isinstance(fixtures, str)
        assert len(fixtures) > 0
        assert "mock_awx_credentials" in fixtures
        assert "mock_awx_survey_vars" in fixtures
        assert "awx_output_parser" in fixtures
    
    def test_get_readme_section(self, awx_integration):
        """Test that README section is returned."""
        readme = awx_integration.get_readme_section()
        assert isinstance(readme, str)
        assert len(readme) > 0
        assert "AWX Integration" in readme
        assert "Setup" in readme
        assert "Usage" in readme


class TestAwxIntegrationScaffolding:
    """Test AWX integration scaffolding behavior."""
    
    def test_template_file_paths_are_relative(self):
        """Test that template paths are relative to integrations template dir."""
        integration = AwxIntegration()
        templates = integration.get_template_files()
        
        for template_path, output_path in templates:
            # Template paths should start with awx/
            assert template_path.startswith("awx/")
            # Output paths should also start with awx/
            assert output_path.startswith("awx/")
            # Template paths should end with .j2
            assert template_path.endswith(".j2")
            # Output paths should not have .j2 extension
            assert not output_path.endswith(".j2")
    
    def test_integration_registered(self):
        """Test that AWX integration is registered in the system."""
        from ai_agent_builder.integrations import get_integration
        
        awx = get_integration("awx")
        assert awx is not None
        assert isinstance(awx, AwxIntegration)
    
    def test_integration_listed_in_orchestration_category(self):
        """Test that AWX appears in orchestration category listing."""
        from ai_agent_builder.integrations import list_integrations
        
        orchestration_integrations = list_integrations(category="orchestration")
        assert len(orchestration_integrations) > 0
        
        awx_found = any(i.name == "awx" for i in orchestration_integrations)
        assert awx_found, "AWX integration not found in orchestration category"
