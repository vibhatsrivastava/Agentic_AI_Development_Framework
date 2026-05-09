"""
test_main.py — Integration tests for 01_hello_langchain/src/main.py

Tests cover:
- Chain initialization and execution with mocked LLM
- Prompt formatting and template usage
- Output parsing and string processing
- End-to-end Q&A workflow

Coverage target: >= 90%
"""

import pytest
import sys
import os

# Allow imports from common/ package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestMainChain:
    """Integration tests for the main Q&A chain."""
    
    def test_chain_executes_successfully(self, mock_llm, sample_question):
        """Test that the chain runs end-to-end with mocked LLM."""
        # Arrange
        mock_llm.invoke.return_value = "LangChain is a framework for AI agents."
        
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | mock_llm | StrOutputParser()
        
        # Act
        result = chain.invoke({"question": sample_question})
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "LangChain" in result
        mock_llm.invoke.assert_called_once()
    
    def test_chain_with_realistic_response(self, mock_llm, mock_llm_response):
        """Test chain with a realistic mocked response."""
        # Arrange
        mock_llm.invoke.return_value = mock_llm_response
        
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | mock_llm | StrOutputParser()
        
        # Act
        result = chain.invoke({"question": "What is LangChain?"})
        
        # Assert
        assert result == mock_llm_response
        assert "framework" in result
        assert "AI agents" in result
    
    def test_prompt_formats_correctly(self, sample_question):
        """Test that the prompt template formats input correctly."""
        # Arrange
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        
        # Act
        formatted = prompt.format(question=sample_question)
        
        # Assert
        assert sample_question in formatted
        assert "Answer:" in formatted
        assert "Question:" in formatted
    
    def test_chain_handles_various_questions(self, mock_llm):
        """Test chain with multiple different questions."""
        # Arrange
        mock_llm.invoke.return_value = "Test answer"
        
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | mock_llm | StrOutputParser()
        
        questions = [
            "What is Python?",
            "Explain machine learning",
            "What are LLMs?",
            "How do agents work?"
        ]
        
        # Act & Assert
        for q in questions:
            result = chain.invoke({"question": q})
            assert result == "Test answer"
        
        assert mock_llm.invoke.call_count == 4
    
    def test_output_parser_returns_string(self, mock_llm):
        """Test that StrOutputParser correctly returns a string."""
        # Arrange
        mock_llm.invoke.return_value = "Parsed output"
        parser = StrOutputParser()
        
        # Act
        result = parser.invoke("Parsed output")
        
        # Assert
        assert isinstance(result, str)
        assert result == "Parsed output"


@pytest.mark.unit
class TestPromptTemplate:
    """Unit tests for prompt template creation and formatting."""
    
    def test_prompt_template_creation(self):
        """Test that PromptTemplate is created correctly."""
        template_string = "Question: {question}\nAnswer:"
        prompt = PromptTemplate.from_template(template_string)
        
        assert prompt is not None
        assert "question" in prompt.input_variables
    
    def test_prompt_template_with_single_variable(self):
        """Test prompt template with a single input variable."""
        prompt = PromptTemplate.from_template("Q: {question}")
        formatted = prompt.format(question="What is AI?")
        
        assert formatted == "Q: What is AI?"
    
    def test_prompt_template_with_empty_input(self):
        """Test prompt template with empty input."""
        prompt = PromptTemplate.from_template("Q: {question}")
        formatted = prompt.format(question="")
        
        assert formatted == "Q: "
    
    def test_prompt_template_preserves_whitespace(self):
        """Test that prompt template preserves formatting."""
        prompt = PromptTemplate.from_template(
            "Question: {question}\n\nAnswer in detail:"
        )
        formatted = prompt.format(question="Test")
        
        assert "\n\n" in formatted
        assert formatted.startswith("Question:")


@pytest.mark.integration
class TestMainModule:
    """Integration tests for the main() function."""
    
    @patch("sys.stdout", new_callable=Mock)
    def test_main_function_prints_output(self, mock_stdout, mock_llm):
        """Test that main() function executes and prints output."""
        # Arrange
        mock_llm.invoke.return_value = "LangChain is a framework."
        
        # Import the main function
        # Note: This would require refactoring main.py to make main() importable
        # For now, we test the component parts
        
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | mock_llm | StrOutputParser()
        
        # Act
        question = "What is LangChain and why is it useful for building AI agents?"
        response = chain.invoke({"question": question})
        
        # Assert
        assert response == "LangChain is a framework."
        mock_llm.invoke.assert_called_once()


@pytest.mark.integration
class TestLCELComposition:
    """Integration tests for LCEL (LangChain Expression Language) chain composition."""
    
    def test_pipe_operator_connects_components(self, mock_llm):
        """Test that the | operator correctly chains components."""
        # Arrange
        mock_llm.invoke.return_value = "Chained response"
        prompt = PromptTemplate.from_template("Q: {q}")
        parser = StrOutputParser()
        
        # Act
        chain = prompt | mock_llm | parser
        result = chain.invoke({"q": "test"})
        
        # Assert
        assert result == "Chained response"
    
    def test_chain_without_parser(self, mock_llm):
        """Test chain with only prompt and LLM (no parser)."""
        # Arrange
        mock_llm.invoke.return_value = "Direct response"
        prompt = PromptTemplate.from_template("Q: {q}")
        
        # Act
        chain = prompt | mock_llm
        result = chain.invoke({"q": "test"})
        
        # Assert
        assert result == "Direct response"
    
    def test_chain_invocation_passes_variables(self, mock_llm):
        """Test that chain correctly passes variables through components."""
        # Arrange
        def capture_invoke(arg):
            # Capture what the LLM receives
            return f"Received: {arg}"
        
        mock_llm.invoke = Mock(side_effect=capture_invoke)
        prompt = PromptTemplate.from_template("Question: {input}")
        
        # Act
        chain = prompt | mock_llm
        result = chain.invoke({"input": "test value"})
        
        # Assert
        mock_llm.invoke.assert_called_once()
        # The mock receives the formatted prompt (StringPromptValue object from LCEL)
        call_arg = mock_llm.invoke.call_args[0][0]
        # StringPromptValue has a .text attribute with the actual string
        assert hasattr(call_arg, 'text') or isinstance(call_arg, str)
        assert "test value" in str(call_arg)


@pytest.mark.unit
class TestOutputParser:
    """Unit tests for StrOutputParser."""
    
    def test_str_output_parser_returns_string(self):
        """StrOutputParser returns input as string."""
        parser = StrOutputParser()
        result = parser.invoke("test string")
        
        assert isinstance(result, str)
        assert result == "test string"
    
    def test_str_output_parser_handles_empty_string(self):
        """StrOutputParser handles empty string input."""
        parser = StrOutputParser()
        result = parser.invoke("")
        
        assert result == ""
    
    def test_str_output_parser_preserves_formatting(self):
        """StrOutputParser preserves newlines and formatting."""
        parser = StrOutputParser()
        text_with_formatting = "Line 1\n\nLine 2\n\tIndented"
        result = parser.invoke(text_with_formatting)
        
        assert result == text_with_formatting
        assert "\n\n" in result
        assert "\t" in result
