"""Integration tests for main agent and CLI."""

import pytest
from unittest.mock import Mock, patch
from main import (
    validate_workspace,
    validate_state_file,
    create_agent,
    create_github_issues,
    send_teams_notifications,
    run_check_mode,
    run_fix_mode,
    main
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


def test_validate_state_file_windows_backslash_path(sample_state_file):
    """Test state file validation accepts Windows backslash paths."""
    path = validate_state_file(str(sample_state_file).replace('/', '\\'))

    assert path.exists()
    assert str(path).endswith(".tfstate")


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


def test_create_github_issues_per_resource_success(monkeypatch, mocker):
    """Test per-resource GitHub issue creation path."""
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_ISSUE_STRATEGY", "per-resource")

    json_data = {
        "resources": [
            {
                "id": "i-abc123",
                "type": "aws_instance",
                "name": "web-prod-01",
                "drift_type": "tags_modified",
                "severity": "HIGH",
                "drift_details": {"removed_tags": ["Environment"]},
                "policy_violations": [
                    {"policy": "policies/tags.yaml", "section": "prod.required_tags[0]", "impact": "Missing tag"}
                ],
                "remediation_command": "terraform apply -target=aws_instance.web-prod-01",
            }
        ]
    }

    mocker.patch("main.parse_teams_config", return_value={"resource_ownership": {"ec2": {"default_owner": "@team"}}})
    mocker.patch("main.get_resource_assignee", return_value="@team")
    mock_search = mocker.patch("main.search_existing_issues", return_value='{"found": false}')
    mock_create = mocker.patch(
        "main.create_github_issue",
        return_value='{"success": true, "issue_url": "https://github.com/test-owner/test-repo/issues/42"}',
    )

    created = create_github_issues(json_data, workspace="prod")

    assert created == ["https://github.com/test-owner/test-repo/issues/42"]
    mock_search.assert_called_once()
    mock_create.assert_called_once()


def test_create_github_issues_summary_success(monkeypatch, mocker):
    """Test summary GitHub issue creation path."""
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_ISSUE_STRATEGY", "summary")
    monkeypatch.setenv("GITHUB_ISSUE_ASSIGNEE", "platform-team")

    json_data = {
        "summary": {"total_resources": 2, "drifted": 1, "compliant": 1, "severity_breakdown": {"HIGH": 1}},
        "resources": [
            {
                "id": "i-abc123",
                "type": "aws_instance",
                "name": "web-prod-01",
                "severity": "HIGH",
                "drift_type": "tags_modified",
                "remediation_command": "terraform apply -target=aws_instance.web-prod-01",
            }
        ],
    }
    mock_create = mocker.patch(
        "main.create_github_issue",
        return_value='{"success": true, "issue_url": "https://github.com/test-owner/test-repo/issues/99"}',
    )

    created = create_github_issues(json_data, workspace="prod")

    assert created == ["https://github.com/test-owner/test-repo/issues/99"]
    mock_create.assert_called_once()


def test_send_teams_notifications_success(monkeypatch, mocker):
    """Test Teams summary notification dispatch."""
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")
    mock_send = mocker.patch("main.send_drift_summary_notification", return_value=True)

    send_teams_notifications(
        json_data={"summary": {"drifted": 1}},
        created_issues=["https://github.com/test-owner/test-repo/issues/1"],
        workspace="prod",
    )

    mock_send.assert_called_once()


def test_run_check_mode_creates_issues_and_sends_teams(
    mock_chat_llm,
    mock_vector_store,
    sample_state_file,
    mocker,
    monkeypatch,
):
    """Test run_check_mode JSON extraction and notification flow."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.vector_store_dir = "./vector_store"
    args.rebuild_vector_store = False

    monkeypatch.setenv("GITHUB_ISSUE_ENABLED", "true")
    monkeypatch.setenv("TEAMS_NOTIFICATION_ENABLED", "true")

    mocker.patch("main.initialize_vector_store", return_value=mock_vector_store)
    mocker.patch("main.get_retriever", return_value=Mock())
    mocker.patch("main.create_github_issues", return_value=["https://github.com/test/repo/issues/1"])
    mock_send_teams = mocker.patch("main.send_teams_notifications")

    mock_agent = Mock()
    msg = Mock()
    msg.content = """# Drift Report
```json
{"drift_detected": true, "summary": {"drifted": 1}, "resources": []}
```"""
    mock_agent.invoke.return_value = {"messages": [msg]}
    mocker.patch("main.create_agent", return_value=mock_agent)

    run_check_mode(args)

    mock_send_teams.assert_called_once()


def test_run_check_mode_vector_store_init_failure(sample_state_file, mocker, capsys):
    """Test run_check_mode exits when vector store initialization fails."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.vector_store_dir = "./vector_store"
    args.rebuild_vector_store = False
    mocker.patch("main.initialize_vector_store", side_effect=Exception("boom"))

    with pytest.raises(SystemExit) as excinfo:
        run_check_mode(args)

    assert excinfo.value.code == 1
    assert "Error initializing vector store" in capsys.readouterr().err


def test_run_fix_mode_vector_store_init_failure(sample_state_file, mocker, capsys):
    """Test run_fix_mode exits when vector store initialization fails."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.resource = "i-0123456789abcdef0"
    args.vector_store_dir = "./vector_store"
    mocker.patch("main.initialize_vector_store", side_effect=Exception("boom"))

    with pytest.raises(SystemExit) as excinfo:
        run_fix_mode(args)

    assert excinfo.value.code == 1
    assert "Error initializing vector store" in capsys.readouterr().err


def test_run_fix_mode_agent_failure(sample_state_file, mocker, capsys):
    """Test run_fix_mode exits when agent invocation fails."""
    args = Mock()
    args.workspace = "prod"
    args.state_file = str(sample_state_file)
    args.resource = "i-0123456789abcdef0"
    args.vector_store_dir = "./vector_store"
    mocker.patch("main.initialize_vector_store", return_value=Mock())
    mocker.patch("main.get_retriever", return_value=Mock())

    mock_agent = Mock()
    mock_agent.invoke.side_effect = RuntimeError("agent failed")
    mocker.patch("main.create_agent", return_value=mock_agent)

    with pytest.raises(SystemExit) as excinfo:
        run_fix_mode(args)

    assert excinfo.value.code == 1
    assert "Error generating remediation plan" in capsys.readouterr().err


def test_main_cli_routes_check_mode(monkeypatch, mocker):
    """Test CLI routing into check mode."""
    mock_run_check = mocker.patch("main.run_check_mode")
    monkeypatch.setattr("sys.argv", ["main.py", "--check", "--workspace", "prod"])

    main()

    mock_run_check.assert_called_once()


def test_main_cli_requires_resource_in_fix_mode(monkeypatch):
    """Test CLI parser error when --fix is used without --resource."""
    monkeypatch.setattr("sys.argv", ["main.py", "--fix", "--workspace", "prod"])

    with pytest.raises(SystemExit):
        main()
