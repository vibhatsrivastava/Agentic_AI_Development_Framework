"""
token_counter.py — Token counting utilities for LLM usage tracking and cost estimation.

Provides tools to count tokens in prompts and responses, helping projects
monitor LLM usage and estimate costs. Supports multiple tokenization methods.
"""

import re
from typing import List, Dict, Optional, Union
from .exceptions import TokenCountError
from .utils import get_logger

logger = get_logger(__name__)


class TokenCounter:
    """
    Token counter for LLM prompts and responses.
    
    Uses a simple approximation based on whitespace and punctuation splitting.
    For more accurate counts, use tiktoken library (optional dependency).
    
    Example:
        counter = TokenCounter()
        
        prompt = "What is the capital of France?"
        token_count = counter.count_tokens(prompt)
        
        # Estimate cost (example pricing)
        cost = counter.estimate_cost(
            prompt_tokens=token_count,
            completion_tokens=50,
            model="gpt-oss:20b"
        )
    """
    
    # Approximate token costs per 1K tokens (USD)
    # These are example values - adjust based on your actual pricing
    MODEL_PRICING = {
        "gpt-oss:20b": {"prompt": 0.0001, "completion": 0.0003},  # Example OSS model
        "llama3.1:8b": {"prompt": 0.0, "completion": 0.0},  # Free local model
        "mistral:7b": {"prompt": 0.0, "completion": 0.0},  # Free local model
        "default": {"prompt": 0.0001, "completion": 0.0003}  # Fallback pricing
    }
    
    def __init__(self, use_tiktoken: bool = False):
        """
        Initialize token counter.
        
        Args:
            use_tiktoken: If True, use tiktoken library for accurate counting
                         (requires: pip install tiktoken)
        """
        self.use_tiktoken = use_tiktoken
        self._tiktoken_encoder = None
        
        if use_tiktoken:
            try:
                import tiktoken
                # Use cl100k_base encoding (GPT-3.5-turbo, GPT-4)
                self._tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
                logger.debug("Token counter initialized with tiktoken")
            except ImportError:
                logger.warning(
                    "tiktoken not installed. Falling back to approximate counting. "
                    "Install with: pip install tiktoken"
                )
                self.use_tiktoken = False
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Approximate token count
        
        Raises:
            TokenCountError: If counting fails
        """
        if not isinstance(text, str):
            raise TokenCountError(f"Expected str, got {type(text)}")
        
        if not text:
            return 0
        
        try:
            if self.use_tiktoken and self._tiktoken_encoder:
                return len(self._tiktoken_encoder.encode(text))
            else:
                # Approximate: split on whitespace and punctuation
                # Roughly 1 token = 4 characters for English text
                # More accurate: count words and add extra for punctuation
                words = len(re.findall(r'\b\w+\b', text))
                punctuation = len(re.findall(r'[^\w\s]', text))
                return words + (punctuation // 2)
        
        except Exception as e:
            raise TokenCountError(f"Failed to count tokens: {str(e)}")
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in a list of chat messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
        
        Returns:
            Total token count including message formatting overhead
        
        Example:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is AI?"}
            ]
            tokens = counter.count_messages(messages)
        """
        total_tokens = 0
        
        for message in messages:
            # Count message content
            content = message.get("content", "")
            total_tokens += self.count_tokens(content)
            
            # Add overhead for message formatting (approximate)
            # Each message has role, formatting tokens
            total_tokens += 4
        
        # Add conversation priming tokens
        total_tokens += 3
        
        return total_tokens
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "default"
    ) -> Dict[str, float]:
        """
        Estimate cost for a given number of tokens.
        
        Args:
            prompt_tokens: Number of input/prompt tokens
            completion_tokens: Number of output/completion tokens
            model: Model name for pricing lookup
        
        Returns:
            Dict with 'prompt_cost', 'completion_cost', 'total_cost' in USD
        
        Example:
            cost = counter.estimate_cost(
                prompt_tokens=100,
                completion_tokens=200,
                model="gpt-oss:20b"
            )
            print(f"Total cost: ${cost['total_cost']:.4f}")
        """
        # Get pricing for model (fallback to default if not found)
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["default"])
        
        # Calculate costs (pricing is per 1K tokens)
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        total_cost = prompt_cost + completion_cost
        
        return {
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
            "currency": "USD"
        }
    
    @staticmethod
    def add_custom_model_pricing(
        model: str,
        prompt_price_per_1k: float,
        completion_price_per_1k: float
    ) -> None:
        """
        Add custom pricing for a model.
        
        Args:
            model: Model name
            prompt_price_per_1k: Cost per 1K prompt tokens (USD)
            completion_price_per_1k: Cost per 1K completion tokens (USD)
        
        Example:
            TokenCounter.add_custom_model_pricing(
                model="custom-model:7b",
                prompt_price_per_1k=0.0002,
                completion_price_per_1k=0.0004
            )
        """
        TokenCounter.MODEL_PRICING[model] = {
            "prompt": prompt_price_per_1k,
            "completion": completion_price_per_1k
        }
        logger.info(f"Added pricing for {model}: ${prompt_price_per_1k}/${completion_price_per_1k} per 1K tokens")


# Module-level convenience functions

_default_counter: Optional[TokenCounter] = None


def get_token_counter(use_tiktoken: bool = False) -> TokenCounter:
    """
    Get the global token counter instance.
    
    Args:
        use_tiktoken: If True, use tiktoken for accurate counting
    
    Returns:
        Global TokenCounter instance
    """
    global _default_counter
    
    if _default_counter is None:
        _default_counter = TokenCounter(use_tiktoken=use_tiktoken)
    
    return _default_counter


def count_tokens(text: str) -> int:
    """
    Convenience function to count tokens in text.
    
    Args:
        text: Text to count tokens for
    
    Returns:
        Approximate token count
    """
    return get_token_counter().count_tokens(text)


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str = "default") -> Dict[str, float]:
    """
    Convenience function to estimate cost.
    
    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        model: Model name for pricing
    
    Returns:
        Cost breakdown dict
    """
    return get_token_counter().estimate_cost(prompt_tokens, completion_tokens, model)
