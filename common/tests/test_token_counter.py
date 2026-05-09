"""
test_token_counter.py — Tests for common.token_counter module.
"""

import pytest
from common.token_counter import (
    TokenCounter,
    get_token_counter,
    count_tokens,
    estimate_cost
)
from common.exceptions import TokenCountError


class TestTokenCounter:
    """Test suite for TokenCounter class."""
    
    def test_initialize_counter(self):
        """Test token counter initialization."""
        counter = TokenCounter()
        assert counter.use_tiktoken is False
        assert counter._tiktoken_encoder is None
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        counter = TokenCounter()
        
        text = "Hello world"
        tokens = counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_empty_string(self):
        """Test counting tokens in empty string."""
        counter = TokenCounter()
        
        tokens = counter.count_tokens("")
        assert tokens == 0
    
    def test_count_tokens_with_punctuation(self):
        """Test counting tokens with punctuation."""
        counter = TokenCounter()
        
        # Text with punctuation should count words + punctuation
        text = "Hello, world! How are you?"
        tokens = counter.count_tokens(text)
        
        # Should count words (5) + punctuation (4) / 2 = 7
        assert tokens >= 5  # At least the number of words
    
    def test_count_tokens_long_text(self):
        """Test counting tokens in longer text."""
        counter = TokenCounter()
        
        text = "This is a longer sentence with many words that should result in more tokens."
        tokens = counter.count_tokens(text)
        
        # Should have roughly 15+ tokens
        assert tokens >= 10
    
    def test_count_tokens_invalid_input(self):
        """Test counting tokens with invalid input."""
        counter = TokenCounter()
        
        with pytest.raises(TokenCountError, match="Expected str"):
            counter.count_tokens(123)  # Not a string
    
    def test_count_messages_single_message(self):
        """Test counting tokens in a single message."""
        counter = TokenCounter()
        
        messages = [
            {"role": "user", "content": "What is AI?"}
        ]
        
        tokens = counter.count_messages(messages)
        
        # Should include message content + overhead
        assert tokens > counter.count_tokens("What is AI?")
    
    def test_count_messages_multiple_messages(self):
        """Test counting tokens in multiple messages."""
        counter = TokenCounter()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI stands for Artificial Intelligence."}
        ]
        
        tokens = counter.count_messages(messages)
        
        # Should be sum of all message contents plus overhead
        expected_min = (
            counter.count_tokens("You are a helpful assistant.") +
            counter.count_tokens("What is AI?") +
            counter.count_tokens("AI stands for Artificial Intelligence.") +
            (4 * 3) +  # 4 tokens per message overhead
            3  # Conversation priming
        )
        
        assert tokens >= expected_min
    
    def test_count_messages_empty_content(self):
        """Test counting messages with empty content."""
        counter = TokenCounter()
        
        messages = [
            {"role": "user", "content": ""}
        ]
        
        tokens = counter.count_messages(messages)
        
        # Should still have overhead tokens
        assert tokens > 0
    
    def test_estimate_cost_basic(self):
        """Test basic cost estimation."""
        counter = TokenCounter()
        
        cost = counter.estimate_cost(
            prompt_tokens=100,
            completion_tokens=200,
            model="gpt-oss:20b"
        )
        
        assert "prompt_cost" in cost
        assert "completion_cost" in cost
        assert "total_cost" in cost
        assert "currency" in cost
        
        assert cost["currency"] == "USD"
        assert cost["total_cost"] > 0
        assert cost["total_cost"] == cost["prompt_cost"] + cost["completion_cost"]
    
    def test_estimate_cost_default_model(self):
        """Test cost estimation with default model."""
        counter = TokenCounter()
        
        cost = counter.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="default"
        )
        
        # Default pricing: $0.0001 / 1K prompt, $0.0003 / 1K completion
        assert cost["prompt_cost"] == pytest.approx(0.0001, rel=1e-6)
        assert cost["completion_cost"] == pytest.approx(0.0003, rel=1e-6)
        assert cost["total_cost"] == pytest.approx(0.0004, rel=1e-6)
    
    def test_estimate_cost_free_model(self):
        """Test cost estimation with free local model."""
        counter = TokenCounter()
        
        cost = counter.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="llama3.1:8b"
        )
        
        # Free model should have zero cost
        assert cost["prompt_cost"] == 0.0
        assert cost["completion_cost"] == 0.0
        assert cost["total_cost"] == 0.0
    
    def test_estimate_cost_unknown_model_falls_back_to_default(self):
        """Test that unknown models use default pricing."""
        counter = TokenCounter()
        
        cost = counter.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="unknown-model:123"
        )
        
        # Should fall back to default pricing
        assert cost["prompt_cost"] == pytest.approx(0.0001, rel=1e-6)
        assert cost["completion_cost"] == pytest.approx(0.0003, rel=1e-6)
    
    def test_add_custom_model_pricing(self):
        """Test adding custom model pricing."""
        TokenCounter.add_custom_model_pricing(
            model="custom-model:7b",
            prompt_price_per_1k=0.0005,
            completion_price_per_1k=0.0010
        )
        
        counter = TokenCounter()
        cost = counter.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="custom-model:7b"
        )
        
        assert cost["prompt_cost"] == pytest.approx(0.0005, rel=1e-6)
        assert cost["completion_cost"] == pytest.approx(0.0010, rel=1e-6)
        assert cost["total_cost"] == pytest.approx(0.0015, rel=1e-6)


class TestGlobalTokenCounterFunctions:
    """Test suite for module-level convenience functions."""
    
    def test_get_token_counter(self):
        """Test getting global token counter."""
        counter = get_token_counter()
        
        assert counter is not None
        assert isinstance(counter, TokenCounter)
    
    def test_get_token_counter_singleton(self):
        """Test that get_token_counter returns same instance."""
        counter1 = get_token_counter()
        counter2 = get_token_counter()
        
        assert counter1 is counter2
    
    def test_count_tokens_convenience_function(self):
        """Test count_tokens convenience function."""
        text = "Hello world"
        tokens = count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_cost_convenience_function(self):
        """Test estimate_cost convenience function."""
        cost = estimate_cost(
            prompt_tokens=100,
            completion_tokens=200,
            model="default"
        )
        
        assert "total_cost" in cost
        assert cost["total_cost"] > 0
    
    def test_tiktoken_initialization_without_library(self):
        """Test that counter works without tiktoken library."""
        # This should work even if tiktoken is not installed
        counter = TokenCounter(use_tiktoken=True)
        
        # Should fall back to approximate counting
        text = "Hello world"
        tokens = counter.count_tokens(text)
        
        assert tokens > 0
