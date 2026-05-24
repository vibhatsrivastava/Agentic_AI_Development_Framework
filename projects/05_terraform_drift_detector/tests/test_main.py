"""Integration tests for main agent and CLI."""

import pytest
from unittest.mock import Mock, patch
from main import (
    validate_workspace,
    validate_state_file,
    create_agent,
    run_check_mode,
    run_fix_mode
)


def test_validate_workspace_success():
    """Test workspace name validation with valid names."""
    # Valid workspace names
    validate_workspace("prod")
    validate_workspace("staging")
    validate_workspace("dev-v2")
    validate_workspace("prod_backup_2023")


def test_validate_workspace_invalid():
    """Test workspace name validation rejects invalid names."""
    with pytest.raises(ValueError, match="Invalid workspace name"):
        validate_workspace("prod@123")  # Contains @
    
    with pytest.raises(ValueError, match="Invalid workspace name"):
        validate_workspace("prod space")  # Contains space
    
    with pytest.raises(ValueError, match="Invalid workspace name"):
        validate_workspace("prod/dev")  # Contains /


def test_validate_state_file_success(sample_state_file):
    """Test state file validation with valid file."""
    path = validate_state_file(str(sample_state_file))
    
    assert path.exists()
    assert str(path).endswith(".tfstate")


def test_validate_state_file_invalid_extension():
    """Test state file validation rejects non-.tfstate files."""
    with pytest.raises(ValueError, match="Invalid state file path"):
        validate_state_file("terraform.json")


def test_validate_state_file_path_traversal():
    """Test state file validation prevents path traversal."""
    with pytest.raises(ValueError, match="Invalid state file path"):
        validate_state_file("../../etc/passwd.tfstate")


def test_validate_state_file_not_found():
    """Test state file validation when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        validate_state_file("nonexistent.tfstate")


def test_create_agent(mock_chat_llm):
    """Test agent creation with tools."""
    mock_retriever = Mock()
    
    agent = create_agent(mock_retriever)
    
    # Agent should be created
    assert agent is not None


def test_run_check_mode_success(
    mock_chat_llm,
    mock_vector_store,
    mock_boto3_client,
    mock_env_vars,
    sample_state_file,
    mocker,
    capsys
):
    """Test check mode execution end-to-end."""
    # Mock argparse args
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.vector_store_dir = "./vector_store"
    args.rebuild_vector_store = False
    
    # Mock initialize_vector_store
    mocker.patch("main.initialize_vector_store", return_value=mock_vector_store)
    mocker.patch("main.get_retriever", return_value=Mock())
    
    # Mock agent.invoke to return a result
    mock_agent = Mock()
    mock_final_message = Mock()
    mock_final_message.content = "# Drift Report\n\nNo drift detected."
    mock_agent.invoke.return_value = {"messages": [mock_final_message]}
    mocker.patch("main.create_agent", return_value=mock_agent)
    
    # Run check mode
    run_check_mode(args)
    
    # Check stdout contains report
    captured = capsys.readouterr()
    assert "Drift Analysis Report" in captured.out
    assert "prod" in captured.out


def test_run_check_mode_invalid_workspace(capsys):
    """Test check mode with invalid workspace name."""
    args = Mock()
    args.workspace = "invalid@workspace"
    args.state_file = "terraform.tfstate"
    
    with pytest.raises(SystemExit) as excinfo:
        run_check_mode(args)
    
    assert excinfo.value.code == 1
    
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_run_check_mode_state_file_not_found(capsys):
    """Test check mode with missing state file."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = "nonexistent.tfstate"
    
    with pytest.raises(SystemExit) as excinfo:
        run_check_mode(args)
    
    assert excinfo.value.code == 1


def test_run_fix_mode_success(
    mock_chat_llm,
    mock_vector_store,
    mock_boto3_client,
    mock_env_vars,
    sample_state_file,
    mocker,
    capsys
):
    """Test fix mode execution end-to-end."""
    # Mock argparse args
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.resource = "i-0123456789abcdef0"
    args.vector_store_dir = "./vector_store"
    
    # Mock initialize_vector_store
    mocker.patch("main.initialize_vector_store", return_value=mock_vector_store)
    mocker.patch("main.get_retriever", return_value=Mock())
    
    # Mock agent.invoke to return a result
    mock_agent = Mock()
    mock_final_message = Mock()
    mock_final_message.content = "# Remediation Plan\n\nApply terraform to fix."
    mock_agent.invoke.return_value = {"messages": [mock_final_message]}
    mocker.patch("main.create_agent", return_value=mock_agent)
    
    # Run fix mode
    run_fix_mode(args)
    
    # Check stdout contains remediation plan
    captured = capsys.readouterr()
    assert "Remediation Plan" in captured.out
    assert "i-0123456789abcdef0" in captured.out


def test_run_fix_mode_invalid_resource_id(capsys):
    """Test fix mode with invalid resource ID format."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = "terraform.tfstate"
    args.resource = "invalid-resource-id!@#"
    
    # Mock validate_state_file to prevent FileNotFoundError
    with patch("main.validate_state_file"):
        with pytest.raises(SystemExit) as excinfo:
            run_fix_mode(args)
    
    assert excinfo.value.code == 1
    
    captured = capsys.readouterr()
    assert "Invalid AWS resource ID format" in captured.err


def test_system_prompt_contains_security_rules():
    """Test that SYSTEM_PROMPT includes security rules."""
    from main import SYSTEM_PROMPT
    
    # Should include security instructions
    assert "STRICT RULES" in SYSTEM_PROMPT
    assert "external input" in SYSTEM_PROMPT or "DATA ONLY" in SYSTEM_PROMPT
    assert "cite specific policy files" in SYSTEM_PROMPT.lower()


def test_agent_tools_integration(mock_chat_llm, mock_vector_store):
    """Test that all required tools are passed to agent."""
    mock_retriever = Mock()
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    # Mock create_react_agent to capture tools argument
    with patch("main.create_react_agent") as mock_create_react_agent:
        create_agent(mock_retriever)
        
        # Verify create_react_agent was called
        assert mock_create_react_agent.called
        
        # Get tools argument
        call_kwargs = mock_create_react_agent.call_args[1]
        tools = call_kwargs["tools"]
        
        # Should have 4 tools
        assert len(tools) == 4
        
        # Tool names should match expected tools
        tool_names = [tool.name for tool in tools]
        assert "parse_terraform_state" in tool_names
        assert "fetch_cloud_resources" in tool_names
        assert "compare_resources" in tool_names
        assert "analyze_drift_with_policies" in tool_names
