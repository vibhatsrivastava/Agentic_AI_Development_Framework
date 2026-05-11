"""
awx_wrapper.py — Unified entry point for executing AI agents from Ansible AWX.

This module provides a standardized interface for AWX to invoke any agent,
handling parameter extraction from environment variables and formatting
output as JSON for AWX parsing.

Usage (from AWX playbook):
    python -m common.awx_wrapper <project_name>
    
Example:
    python -m common.awx_wrapper 03_weather_reporting_agent
    
Environment Variables:
    Agent parameters are passed via environment variables (injected by AWX
    from credentials and survey responses). The wrapper extracts these and
    makes them available to the agent.

Output Format:
    {
        "status": "success" | "error",
        "result": <agent output>,
        "error": <error message if status=error>,
        "metadata": {
            "agent": <project_name>,
            "execution_time": <seconds>,
            "awx_job_id": <AWX job ID if available>
        }
    }
"""

import json
import os
import sys
import time
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional

from .awx_utils import extract_agent_params, format_awx_output, validate_project_structure
from .utils import get_logger

logger = get_logger(__name__)


def load_agent_module(project_name: str, repo_root: Path):
    """
    Dynamically load agent's main module.
    
    Args:
        project_name: Project directory name (e.g., "03_weather_reporting_agent")
        repo_root: Path to repository root
        
    Returns:
        Loaded module object
        
    Raises:
        ImportError: If agent module cannot be loaded
    """
    project_path = repo_root / "projects" / project_name
    main_module_path = project_path / "src" / "main.py"
    
    if not main_module_path.exists():
        raise ImportError(
            f"Agent main module not found: {main_module_path}\n"
            f"Expected path: projects/{project_name}/src/main.py"
        )
    
    # Load module dynamically
    spec = importlib.util.spec_from_file_location(
        f"{project_name}.main",
        main_module_path
    )
    
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load module spec for {main_module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    
    return module


def execute_agent(
    project_name: str,
    agent_params: Dict[str, str],
    repo_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Execute agent with provided parameters.
    
    Args:
        project_name: Project directory name
        agent_params: Agent-specific parameters extracted from environment
        repo_root: Repository root path (defaults to parent of common/ if not provided)
        
    Returns:
        Dict with agent execution results
        
    Raises:
        Exception: If agent execution fails
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    
    # Validate project structure
    validate_project_structure(project_name, repo_root)
    
    # Load agent module
    logger.info(f"Loading agent module: {project_name}")
    agent_module = load_agent_module(project_name, repo_root)
    
    # Check if module has a main() or run() function
    if hasattr(agent_module, "main"):
        main_func = agent_module.main
    elif hasattr(agent_module, "run"):
        main_func = agent_module.run
    else:
        raise AttributeError(
            f"Agent module {project_name} must define a main() or run() function"
        )
    
    # Execute agent
    logger.info(f"Executing agent: {project_name} with params: {agent_params}")
    start_time = time.time()
    
    try:
        # Call agent's main function
        # Agent should read parameters from environment variables
        result = main_func()
        
        execution_time = time.time() - start_time
        
        return {
            "status": "success",
            "result": result if result is not None else "Agent completed successfully",
            "metadata": {
                "agent": project_name,
                "execution_time": round(execution_time, 2),
                "awx_job_id": os.getenv("AWX_JOB_ID", ""),
            }
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "agent": project_name,
                "execution_time": round(execution_time, 2),
                "awx_job_id": os.getenv("AWX_JOB_ID", ""),
            }
        }


def main():
    """
    Main entry point for AWX wrapper.
    
    Expected usage:
        python -m common.awx_wrapper <project_name>
    
    Exit codes:
        0: Success
        1: Error (agent execution failed or invalid arguments)
    """
    # Parse command line arguments
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: python -m common.awx_wrapper <project_name>"
        }))
        sys.exit(1)
    
    project_name = sys.argv[1]
    
    try:
        # Extract agent parameters from environment variables
        agent_params = extract_agent_params()
        
        # Execute agent
        result = execute_agent(project_name, agent_params)
        
        # Format and output result as JSON
        output = format_awx_output(result)
        print(output)
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"AWX wrapper failed: {e}", exc_info=True)
        
        error_output = format_awx_output({
            "status": "error",
            "error": f"AWX wrapper error: {str(e)}",
            "metadata": {
                "agent": project_name,
                "awx_job_id": os.getenv("AWX_JOB_ID", ""),
            }
        })
        
        print(error_output)
        sys.exit(1)


if __name__ == "__main__":
    main()
