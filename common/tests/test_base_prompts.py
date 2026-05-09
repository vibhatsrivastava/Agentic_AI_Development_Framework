"""test_base_prompts.py — Tests for common/prompts/base_prompts.py."""

import pytest
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from common.prompts.base_prompts import QA_PROMPT, RAG_PROMPT, REACT_SYSTEM_PROMPT


class TestQAPrompt:
    def test_qa_prompt_is_prompt_template(self):
        """QA_PROMPT is a valid PromptTemplate."""
        assert isinstance(QA_PROMPT, PromptTemplate)

    def test_qa_prompt_accepts_question_variable(self):
        """QA_PROMPT can be formatted with a 'question' variable."""
        result = QA_PROMPT.format(question="What is 2+2?")
        assert "What is 2+2?" in result
        assert "Answer:" in result

    def test_qa_prompt_has_correct_input_variables(self):
        """QA_PROMPT requires exactly the 'question' input variable."""
        assert QA_PROMPT.input_variables == ["question"]


class TestRAGPrompt:
    def test_rag_prompt_is_chat_prompt_template(self):
        """RAG_PROMPT is a valid ChatPromptTemplate."""
        assert isinstance(RAG_PROMPT, ChatPromptTemplate)

    def test_rag_prompt_accepts_context_and_question(self):
        """RAG_PROMPT can be formatted with 'context' and 'question' variables."""
        messages = RAG_PROMPT.format_messages(
            context="Paris is the capital of France.",
            question="What is the capital of France?"
        )
        assert len(messages) == 2
        system_content = messages[0].content
        human_content = messages[1].content
        
        assert "Paris is the capital of France" in system_content
        assert "What is the capital of France?" in human_content

    def test_rag_prompt_has_correct_input_variables(self):
        """RAG_PROMPT requires 'context' and 'question' variables."""
        assert set(RAG_PROMPT.input_variables) == {"context", "question"}


class TestReActSystemPrompt:
    def test_react_prompt_is_string(self):
        """REACT_SYSTEM_PROMPT is a non-empty string."""
        assert isinstance(REACT_SYSTEM_PROMPT, str)
        assert len(REACT_SYSTEM_PROMPT) > 0

    def test_react_prompt_contains_key_concepts(self):
        """REACT_SYSTEM_PROMPT mentions tools and reasoning."""
        prompt_lower = REACT_SYSTEM_PROMPT.lower()
        assert "tool" in prompt_lower
        assert "assistant" in prompt_lower
