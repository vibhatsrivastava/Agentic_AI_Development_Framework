"""
vault.py — HashiCorp Vault integration with .env fallback
Provides centralized secret management for multi-developer teams.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Lazy import hvac to avoid hard dependency when Vault is disabled
try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

# Module-level cache for secrets (loaded once per process)
_SECRET_CACHE: Dict[str, str] = {}

# Module-level Vault client (initialized once)
_VAULT_CLIENT: Optional[Any] = None


def _get_vault_client() -> Optional[Any]:
    """
    Initialize and return a HashiCorp Vault client.
    
    Returns:
        hvac.Client instance if Vault is enabled and configured, None otherwise.
    """
    global _VAULT_CLIENT
    
    # Return cached client if already initialized
    if _VAULT_CLIENT is not None:
        return _VAULT_CLIENT
    
    # Check if Vault is enabled
    vault_enabled = os.getenv("VAULT_ENABLED", "false").lower() in ("true", "1", "yes")
    if not vault_enabled:
        logger.debug("Vault integration is disabled (VAULT_ENABLED=false)")
        return None
    
    # Check if hvac is installed
    if not HVAC_AVAILABLE:
        logger.warning(
            "Vault is enabled but hvac library is not installed. "
            "Install with: pip install hvac>=2.0.0"
        )
        return None
    
    # Get Vault configuration from environment
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    
    if not vault_addr:
        logger.warning("VAULT_ENABLED=true but VAULT_ADDR is not set. Falling back to .env")
        return None
    
    if not vault_token:
        logger.warning("VAULT_ENABLED=true but VAULT_TOKEN is not set. Falling back to .env")
        return None
    
    try:
        # Initialize Vault client
        client = hvac.Client(url=vault_addr, token=vault_token)
        
        # Verify authentication
        if not client.is_authenticated():
            logger.error("Vault authentication failed. Check VAULT_TOKEN. Falling back to .env")
            return None
        
        logger.info(f"Successfully connected to Vault at {vault_addr}")
        _VAULT_CLIENT = client
        return _VAULT_CLIENT
        
    except Exception as e:
        logger.error(f"Failed to initialize Vault client: {e}. Falling back to .env")
        return None


def _fetch_from_vault(vault_key: str) -> Optional[str]:
    """
    Fetch a secret from HashiCorp Vault.
    
    Args:
        vault_key: The key name within the Vault secret (e.g., "OLLAMA_API_KEY")
    
    Returns:
        Secret value from Vault, or None if not found or error occurred.
    """
    client = _get_vault_client()
    if client is None:
        return None
    
    # Get secret path from environment
    secret_path = os.getenv("VAULT_SECRET_PATH", "ollama")
    mount_point = os.getenv("VAULT_MOUNT_POINT", "secret")
    
    try:
        # Read secret from Vault (KV v2 engine)
        response = client.secrets.kv.v2.read_secret_version(
            path=secret_path,
            mount_point=mount_point
        )
        
        # Extract the secret data
        secret_data = response.get("data", {}).get("data", {})
        
        if vault_key in secret_data:
            logger.info(f"Retrieved '{vault_key}' from Vault (path: {mount_point}/{secret_path})")
            return secret_data[vault_key]
        else:
            logger.warning(
                f"Key '{vault_key}' not found in Vault secret at {mount_point}/{secret_path}. "
                f"Available keys: {list(secret_data.keys())}"
            )
            return None
            
    except hvac.exceptions.InvalidPath:
        logger.warning(f"Vault secret path '{mount_point}/{secret_path}' does not exist.")
        return None
    except hvac.exceptions.Forbidden:
        logger.error(f"Permission denied reading Vault secret at {mount_point}/{secret_path}")
        return None
    except Exception as e:
        logger.error(f"Error fetching secret from Vault: {e}")
        return None


def get_secret(vault_key: str, env_fallback_key: str, default: str = "") -> str:
    """
    Retrieve a secret from HashiCorp Vault with .env fallback.
    
    Strategy:
    1. Check module-level cache (for performance)
    2. Try to fetch from Vault (if enabled and reachable)
    3. Fall back to .env file
    4. Return default value if neither source has the secret
    
    Args:
        vault_key: The key name in Vault secret (e.g., "OLLAMA_API_KEY")
        env_fallback_key: The environment variable name to use as fallback (e.g., "OLLAMA_API_KEY")
        default: Default value if secret not found in Vault or .env (default: "")
    
    Returns:
        Secret value from Vault, .env, or default (in that priority order).
    
    Examples:
        >>> # Try Vault first, fallback to .env
        >>> api_key = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
        >>> 
        >>> # With custom default
        >>> api_key = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY", default="localhost-key")
    """
    # Check cache first
    cache_key = f"{vault_key}:{env_fallback_key}"
    if cache_key in _SECRET_CACHE:
        logger.debug(f"Using cached value for '{vault_key}'")
        return _SECRET_CACHE[cache_key]
    
    # Try to fetch from Vault
    vault_value = _fetch_from_vault(vault_key)
    if vault_value is not None:
        _SECRET_CACHE[cache_key] = vault_value
        return vault_value
    
    # Fall back to environment variable
    env_value = os.getenv(env_fallback_key)
    if env_value is not None:
        logger.info(f"Using .env fallback for '{env_fallback_key}' (Vault unavailable or key not found)")
        _SECRET_CACHE[cache_key] = env_value
        return env_value
    
    # Return default if neither source has the secret
    logger.debug(f"No value found for '{vault_key}' in Vault or .env. Using default: '{default}'")
    _SECRET_CACHE[cache_key] = default
    return default


def clear_cache() -> None:
    """
    Clear the secret cache.
    
    Useful for testing or forcing a refresh of secrets.
    In production, secrets are cached for the lifetime of the process.
    """
    global _SECRET_CACHE, _VAULT_CLIENT
    _SECRET_CACHE.clear()
    _VAULT_CLIENT = None
    logger.debug("Secret cache cleared")
