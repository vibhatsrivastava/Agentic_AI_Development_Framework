"""Tests for policy-based drift analysis tools."""

import json
from unittest.mock import Mock
from tools.policy_tools import create_policy_analysis_tool


def test_analyze_drift_with_policies_success(mock_chat_llm, sample_drift_summary):
    """Test successful policy analysis with RAG retrieval."""
    # Mock retriever
    mock_retriever = Mock()
    mock_retriever.get_relevant_documents.return_value = [
        Mock(
            page_content="Environment tag required for production",
            metadata={"source": "policies/tags.yaml"}
        )
    ]
    
    # Create tool
    analyze_tool = create_policy_analysis_tool(mock_retriever)
    
    # Invoke tool
    result_json = analyze_tool.invoke({"drift_summary": sample_drift_summary})
    result = json.loads(result_json)
    
    assert "error" not in result
    assert result["total_analyzed"] == 1
    assert len(result["enriched_drift_reports"]) == 1
    
    report = result["enriched_drift_reports"][0]
    assert report["resource"]["id"] == "i-0123456789abcdef0"
    assert "policy_analysis" in report
    assert len(report["retrieved_policies"]) > 0


def test_analyze_drift_with_policies_no_drift(mock_chat_llm):
    """Test policy analysis when no drift detected."""
    mock_retriever = Mock()
    
    no_drift_summary = json.dumps({
        "total_drifted": 0,
        "drifted_resources": []
    })
    
    analyze_tool = create_policy_analysis_tool(mock_retriever)
    result_json = analyze_tool.invoke({"drift_summary": no_drift_summary})
    result = json.loads(result_json)
    
    assert result["total_analyzed"] == 0
    assert "No drift detected" in result["analysis"]


def test_analyze_drift_with_policies_accepts_dict_input(mock_chat_llm):
    """Test policy analysis accepts dictionary input from tool chain."""
    mock_retriever = Mock()
    mock_retriever.get_relevant_documents.return_value = [
        Mock(page_content="Environment tag required", metadata={"source": "policies/tags.yaml"})
    ]

    drift_summary_dict = {
        "total_drifted": 1,
        "drifted_resources": [
            {
                "resource_id": "i-01e35bc38d1f134c2",
                "resource_type": "aws_instance",
                "resource_name": "drift_test",
                "drift_type": "tags_modified",
                "severity": "critical",
                "changes": {"removed_tags": ["Environment"]},
            }
        ],
    }

    analyze_tool = create_policy_analysis_tool(mock_retriever)
    result_json = analyze_tool.invoke({"drift_summary": drift_summary_dict})
    result = json.loads(result_json)

    assert "error" not in result
    assert result["total_analyzed"] == 1


def test_analyze_drift_with_policies_invalid_json():
    """Test handling of invalid JSON input."""
    mock_retriever = Mock()
    
    analyze_tool = create_policy_analysis_tool(mock_retriever)
    result_json = analyze_tool.invoke({"drift_summary": "{invalid json}"})
    result = json.loads(result_json)
    
    assert "error" in result


def test_analyze_drift_with_policies_error_from_previous_tool():
    """Test handling of error responses from compare_resources tool."""
    mock_retriever = Mock()
    
    error_drift_summary = json.dumps({"error": "Comparison failed"})
    
    analyze_tool = create_policy_analysis_tool(mock_retriever)
    result_json = analyze_tool.invoke({"drift_summary": error_drift_summary})
    result = json.loads(result_json)
    
    assert "error" in result


def test_analyze_drift_with_policies_llm_called(mock_chat_llm, sample_drift_summary):
    """Test that LLM is invoked with correct prompt structure."""
    mock_retriever = Mock()
    mock_retriever.get_relevant_documents.return_value = [
        Mock(page_content="Policy content", metadata={"source": "policies/test.yaml"})
    ]
    
    analyze_tool = create_policy_analysis_tool(mock_retriever)
    analyze_tool.invoke({"drift_summary": sample_drift_summary})
    
    # LLM should be invoked
    mock_chat_llm.invoke.assert_called_once()
    
    # Check that prompt contains expected sections
    call_args = mock_chat_llm.invoke.call_args[0][0]
    prompt_content = call_args[0].content
    
    assert "<drift_details>" in prompt_content
    assert "<relevant_policies>" in prompt_content
    assert "STRICT RULES" in prompt_content


def test_build_policy_query_tags_modified():
    """Test RAG query construction for tag modifications."""
    from tools.policy_tools import _build_policy_query
    
    drift = {
        "resource_type": "aws_instance",
        "drift_type": "tags_modified",
        "changes": {
            "removed_tags": ["Environment", "Backup"]
        }
    }
    
    query = _build_policy_query(drift)
    
    assert "aws_instance" in query
    assert "tags_modified" in query
    assert "Environment" in query
    assert "Backup" in query


def test_build_policy_query_attributes_changed():
    """Test RAG query construction for attribute changes."""
    from tools.policy_tools import _build_policy_query
    
    drift = {
        "resource_type": "aws_security_group",
        "drift_type": "attributes_changed",
        "changes": {
            "modified_attributes": {
                "ingress": {},
                "egress": {}
            }
        }
    }
    
    query = _build_policy_query(drift)
    
    assert "aws_security_group" in query
    assert "attributes_changed" in query
    assert "ingress" in query
    assert "egress" in query


def test_format_policy_documents():
    """Test formatting of retrieved policy documents for LLM prompt."""
    from tools.policy_tools import _format_policy_documents
    from langchain_core.documents import Document
    
    docs = [
        Document(
            page_content="Policy content 1",
            metadata={"source": "policies/tags.yaml"}
        ),
        Document(
            page_content="Policy content 2",
            metadata={"source": "policies/compliance.yaml"}
        )
    ]
    
    formatted = _format_policy_documents(docs)
    
    assert "Policy 1" in formatted
    assert "policies/tags.yaml" in formatted
    assert "Policy 2" in formatted
    assert "policies/compliance.yaml" in formatted
    assert "Policy content 1" in formatted


def test_format_policy_documents_empty():
    """Test handling of empty policy document list."""
    from tools.policy_tools import _format_policy_documents
    
    formatted = _format_policy_documents([])
    
    assert "No relevant policies found" in formatted
