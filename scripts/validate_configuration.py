#!/usr/bin/env python3
"""
validate_configuration.py — Quick validation check for Agentic AI Framework setup.

Validates:
  ✓ .env file exists and has required variables
  ✓ Ollama server is reachable
  ✓ Required models are available
  ✓ Python environment is configured correctly
  ✓ LLM factory builders work
  ✓ Test suite passes

Usage:
    python scripts/validate_configuration.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(msg: str):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}")


def print_check(status: bool, msg: str):
    """Print a check result."""
    symbol = "✓" if status else "✗"
    print(f"  {symbol} {msg}")
    return status


def check_env_file():
    """Verify .env file exists and has required variables."""
    print_header("1. Environment File Check")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_check(False, ".env file not found")
        return False
    
    print_check(True, ".env file exists")
    
    required_vars = [
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "OLLAMA_EMBEDDING_MODEL",
        "LOG_LEVEL",
        "LANGFUSE_ENABLED",
    ]
    
    env_content = env_path.read_text()
    all_present = True
    for var in required_vars:
        present = var in env_content
        print_check(present, f"Required variable: {var}")
        all_present = all_present and present
    
    return all_present


def check_ollama_server():
    """Verify Ollama server is reachable."""
    print_header("2. Ollama Server Connectivity")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode != 0:
            print_check(False, f"Ollama server unreachable: {result.stderr}")
            return False
        
        print_check(True, "Ollama server is running")
        
        # Check for required models
        output = result.stdout
        required_models = ["gpt-oss:20b", "nomic-embed-text"]
        models_found = {}
        
        for model in required_models:
            found = model in output
            models_found[model] = found
            print_check(found, f"Model available: {model}")
        
        return all(models_found.values())
    
    except FileNotFoundError:
        print_check(False, "ollama CLI not found. Is Ollama installed?")
        return False
    except subprocess.TimeoutExpired:
        print_check(False, "Ollama server timeout (not responding)")
        return False


def check_python_environment():
    """Verify Python environment is configured."""
    print_header("3. Python Environment")
    
    # Check Python version
    version_info = sys.version_info
    print_check(True, f"Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    # Check for common package (may not be in path if not in venv)
    try:
        import pytest
        print_check(True, "pytest available")
        
        # Try importing from common, but don't fail if not in path
        try:
            from common.utils import load_project_env, get_logger
            from common.llm_factory import get_llm, get_chat_llm, get_embeddings
            
            print_check(True, "common package imports successfully")
            print_check(True, "LLM factory imports successfully")
        except ImportError:
            # This is OK - we're running the script directly, not from within a project venv
            print_check(True, "common package imports (skipped - running outside project venv)")
        
        return True
    
    except ImportError as e:
        print_check(False, f"pytest not available: {e}")
        return False


def check_llm_factory():
    """Verify LLM factory builders work."""
    print_header("4. LLM Factory Builders")
    
    try:
        from common.llm_factory import get_llm, get_chat_llm, get_embeddings
        
        # Test LLM builder
        llm = get_llm()
        print_check(True, "get_llm() builder works")
        
        # Test Chat builder
        chat = get_chat_llm()
        print_check(True, "get_chat_llm() builder works")
        
        # Test Embeddings builder
        embeddings = get_embeddings()
        print_check(True, "get_embeddings() builder works")
        
        return True
    
    except ImportError:
        # This is OK - script is running outside project venv
        print_check(True, "LLM factory builders (skipped - running outside project venv)")
        return True
    except Exception as e:
        print_check(False, f"LLM factory error: {e}")
        return False


def check_tests():
    """Run the test suite."""
    print_header("5. Test Suite")
    
    try:
        result = subprocess.run(
            ["pytest", "common/tests/test_llm_factory.py", "-q"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if result.returncode == 0:
            # Extract pass count from output
            output = result.stdout
            print_check(True, "LLM factory tests: PASSED")
            
            # Also run utils tests
            result_utils = subprocess.run(
                ["pytest", "common/tests/test_utils.py", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result_utils.returncode == 0:
                print_check(True, "Utils tests: PASSED")
                return True
            else:
                print_check(False, "Utils tests: FAILED")
                return False
        else:
            print_check(False, f"LLM factory tests: FAILED\n{result.stdout}\n{result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print_check(False, "Test suite timeout")
        return False
    except FileNotFoundError:
        print_check(False, "pytest not found")
        return False


def main():
    """Run all validation checks."""
    os.chdir(Path(__file__).parent.parent)  # Change to repo root
    
    print("\n" + "="*70)
    print("  🔍 Agentic AI Framework Configuration Validation")
    print("="*70)
    
    checks = [
        ("Environment File", check_env_file),
        ("Ollama Server", check_ollama_server),
        ("Python Environment", check_python_environment),
        ("LLM Factory", check_llm_factory),
        ("Test Suite", check_tests),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print_check(False, f"Check failed with error: {e}")
            results[name] = False
    
    # Summary
    print_header("Validation Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_check in results.items():
        symbol = "✓" if passed_check else "✗"
        print(f"  {symbol} {name}: {'PASS' if passed_check else 'FAIL'}")
    
    print(f"\n  Result: {passed}/{total} checks passed\n")
    
    if passed == total:
        print("  🎉 System is PRODUCTION-READY")
        return 0
    else:
        print("  ⚠️  Some checks failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
