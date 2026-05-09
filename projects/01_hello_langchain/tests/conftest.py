"""
Project-specific fixtures for 01_hello_langchain tests.

These fixtures supplement the global fixtures defined in common/tests/conftest.py.
"""

import pytest


@pytest.fixture
def sample_question():
    """
    Return a sample question for testing the main Q&A chain.
    
    Usage:
        def test_chain(sample_question):
            result = chain.invoke({"question": sample_question})
            assert len(result) > 0
    """
    return "What is LangChain and why is it useful for building AI agents?"


@pytest.fixture
def expected_keywords():
    """
    Return keywords expected in LLM responses about LangChain.
    
    Usage:
        def test_response_quality(mock_llm, expected_keywords):
            response = chain.invoke({"question": "..."})
            assert any(keyword in response for keyword in expected_keywords)
    """
    return ["LangChain", "framework", "AI", "agents", "chains"]


@pytest.fixture
def mock_llm_response():
    """
    Return a realistic mock response for LangChain questions.
    
    Usage:
        def test_with_realistic_response(mock_llm, mock_llm_response):
            mock_llm.invoke.return_value = mock_llm_response
            result = chain.invoke({"question": "..."})
            assert "LangChain" in result
    """
    return (
        "LangChain is a framework for developing applications powered by language models. "
        "It is useful for building AI agents because it provides tools for chaining together "
        "prompts, models, and data sources in a modular and composable way."
    )
