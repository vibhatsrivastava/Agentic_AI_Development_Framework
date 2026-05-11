"""
test_awx_wrapper.py — Unit tests for AWX wrapper module.

Tests the AWX wrapper that provides a unified entry point for
executing agents from Ansible AWX.
"""

import json
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from common.awx_wrapper import (
    load_agent_module,
    execute_agent,
    main as awx_wrapper_main,
)


class TestLoadAgentModule:
    """Test agent module loading."""
    
    def test_load_nonexistent_agent(self, tmp_path):
        """Test loading an agent that doesn't exist."""
        repo_root = tmp_path
        (repo_root / "projects").mkdir()
        
        with pytest.raises(ImportError, match="Agent main module not found"):
            load_agent_module("nonexistent_agent", repo_root)
    
    def test_load_agent_without_main_py(self, tmp_path):
        """Test loading an agent without main.py."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        src_path.mkdir(parents=True)
        
        with pytest.raises(ImportError, match="Agent main module not found"):
            load_agent_module("test_agent", repo_root)
    
    def test_load_valid_agent(self, tmp_path):
        """Test loading a valid agent module."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        src_path.mkdir(parents=True)
        
        # Create a minimal main.py
        main_py = src_path / "main.py"
        main_py.write_text("""
def main():
    return "Test agent executed"
""")
        
        # Should load successfully
        module = load_agent_module("test_agent", repo_root)
        assert hasattr(module, "main")
        assert callable(module.main)


class TestExecuteAgent:
    """Test agent execution."""
    
    def test_execute_agent_success(self, tmp_path):
        """Test successful agent execution."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        
        # Create a minimal main.py
        main_py = src_path / "main.py"
        main_py.write_text("""
def main():
    return "Agent executed successfully"
""")
        
        result = execute_agent("test_agent", {}, repo_root=repo_root)
        
        assert result["status"] == "success"
        assert result["result"] == "Agent executed successfully"
        assert "metadata" in result
        assert result["metadata"]["agent"] == "test_agent"
        assert "execution_time" in result["metadata"]
    
    def test_execute_agent_failure(self, tmp_path):
        """Test agent execution failure."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        
        # Create a main.py that raises an exception
        main_py = src_path / "main.py"
        main_py.write_text("""
def main():
    raise ValueError("Test error")
""")
        
        result = execute_agent("test_agent", {}, repo_root=repo_root)
        
        assert result["status"] == "error"
        assert "Test error" in result["error"]
        assert "metadata" in result
        assert result["metadata"]["agent"] == "test_agent"
    
    def test_execute_agent_no_main_function(self, tmp_path):
        """Test executing agent without main() or run() function."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        
        # Create a main.py without main() or run()
        main_py = src_path / "main.py"
        main_py.write_text("""
# No main() or run() function
pass
""")
        
        with pytest.raises(AttributeError, match="must define a main\\(\\) or run\\(\\) function"):
            execute_agent("test_agent", {}, repo_root=repo_root)
    
    def test_execute_agent_with_run_function(self, tmp_path):
        """Test executing agent with run() instead of main()."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        
        # Create a main.py with run() function
        main_py = src_path / "main.py"
        main_py.write_text("""
def run():
    return "Agent executed via run()"
""")
        
        result = execute_agent("test_agent", {}, repo_root=repo_root)
        
        assert result["status"] == "success"
        assert result["result"] == "Agent executed via run()"


class TestAwxWrapperMain:
    """Test AWX wrapper main entry point."""
    
    def test_main_no_arguments(self, capsys):
        """Test main() with no arguments."""
        with patch.object(sys, 'argv', ['awx_wrapper']):
            with pytest.raises(SystemExit) as exc_info:
                awx_wrapper_main()
            
            assert exc_info.value.code == 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["status"] == "error"
            assert "Usage" in output["error"]
    
    def test_main_with_nonexistent_agent(self, capsys):
        """Test main() with nonexistent agent."""
        with patch.object(sys, 'argv', ['awx_wrapper', 'nonexistent_agent']):
            with pytest.raises(SystemExit) as exc_info:
                awx_wrapper_main()
            
            assert exc_info.value.code == 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["status"] == "error"
    
    @patch('common.awx_wrapper.execute_agent')
    @patch('common.awx_wrapper.extract_agent_params')
    def test_main_success(self, mock_extract_params, mock_execute, capsys):
        """Test main() with successful execution."""
        mock_extract_params.return_value = {"city": "London"}
        mock_execute.return_value = {
            "status": "success",
            "result": "Agent executed",
            "metadata": {"agent": "test_agent", "execution_time": 1.23}
        }
        
        with patch.object(sys, 'argv', ['awx_wrapper', 'test_agent']):
            with pytest.raises(SystemExit) as exc_info:
                awx_wrapper_main()
            
            assert exc_info.value.code == 0
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["status"] == "success"
            assert output["result"] == "Agent executed"
    
    @patch('common.awx_wrapper.execute_agent')
    @patch('common.awx_wrapper.extract_agent_params')
    def test_main_agent_failure(self, mock_extract_params, mock_execute, capsys):
        """Test main() with agent execution failure."""
        mock_extract_params.return_value = {}
        mock_execute.return_value = {
            "status": "error",
            "error": "Agent failed",
            "metadata": {"agent": "test_agent", "execution_time": 0.5}
        }
        
        with patch.object(sys, 'argv', ['awx_wrapper', 'test_agent']):
            with pytest.raises(SystemExit) as exc_info:
                awx_wrapper_main()
            
            assert exc_info.value.code == 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["status"] == "error"
            assert output["error"] == "Agent failed"


class TestAwxWrapperIntegration:
    """Integration tests for AWX wrapper."""
    
    def test_awx_job_id_metadata(self, tmp_path, monkeypatch):
        """Test that AWX job ID is captured in metadata."""
        monkeypatch.setenv("AWX_JOB_ID", "12345")
        
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        
        main_py = src_path / "main.py"
        main_py.write_text("""
def main():
    return "Test"
""")
        
        result = execute_agent("test_agent", {}, repo_root=repo_root)
        
        assert result["metadata"]["awx_job_id"] == "12345"
