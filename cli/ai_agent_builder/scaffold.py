"""
scaffold.py — Project scaffolding orchestrator.

Creates project directory structure, renders templates, and generates files.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import BASE_ARCHITECTURES, PROJECT_STRUCTURE, get_project_number
from .env_manager import EnvManager
from .integrations import get_integration, list_integrations
from .template_renderer import TemplateRenderer, get_template_context


class ProjectScaffolder:
    """
    Orchestrates project scaffolding from templates.

    Responsibilities:
    - Create project directory structure
    - Render and write template files
    - Generate integration-specific files
    - Update root README.md with new project
    - Run post-generation hooks

    Example:
        scaffolder = ProjectScaffolder(
            projects_dir=Path("projects"),
            repo_root=Path(".")
        )

        project_path = scaffolder.scaffold_project(
            project_name="05_sentiment_analysis",
            architecture="lcel",
            integrations=["langfuse"]
        )
    """

    def __init__(
        self,
        projects_dir: Path,
        repo_root: Path,
        template_renderer: Optional[TemplateRenderer] = None,
        env_manager: Optional[EnvManager] = None
    ):
        """
        Initialize project scaffolder.

        Args:
            projects_dir: Path to projects directory (e.g., repo_root/projects)
            repo_root: Path to repository root
            template_renderer: TemplateRenderer instance (default: create new)
            env_manager: EnvManager instance (default: create new)
        """
        self.projects_dir = projects_dir
        self.repo_root = repo_root
        self.template_renderer = template_renderer or TemplateRenderer()
        self.env_manager = env_manager or EnvManager()

    def scaffold_project(
        self,
        project_name: str,
        architecture: str,
        integrations: List[str],
        **kwargs
    ) -> Path:
        """
        Scaffold a new project with the specified configuration.

        Args:
            project_name: Project name (e.g., "05_sentiment_analysis")
            architecture: Base architecture ("lcel", "langgraph", "custom")
            integrations: List of integration names
            **kwargs: Additional template context variables

        Returns:
            Path to created project directory

        Raises:
            ValueError: If project already exists or invalid parameters
            FileNotFoundError: If template files not found
        """
        # Validate parameters
        self._validate_project_name(project_name)
        self._validate_architecture(architecture)
        self._validate_integrations(integrations)

        # Create project directory
        project_path = self.projects_dir / project_name
        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists at {project_path}")

        # Build template context
        project_number = get_project_number(project_name)
        context = get_template_context(
            project_name=project_name,
            project_number=project_number,
            architecture=architecture,
            integrations=integrations,
            **kwargs
        )

        # Create directory structure
        self._create_directory_structure(project_path)

        # Render and write base files
        self._render_base_files(project_path, architecture, context)

        # Render and write integration files
        self._render_integration_files(project_path, integrations, context)

        # Generate .env.example
        self._generate_env_file(project_path, integrations)

        # Update root README.md
        self._update_root_readme(project_name, architecture, integrations)

        # Run post-generation hooks
        self._run_post_generate_hooks(project_path, integrations)

        # Set up isolated virtual environment with uv
        self._setup_project_environment(project_path)

        return project_path

    def _validate_project_name(self, project_name: str) -> None:
        """Validate project name matches pattern."""
        import re

        from .config import PROJECT_NAME_EXAMPLE, PROJECT_NAME_PATTERN

        if not re.match(PROJECT_NAME_PATTERN, project_name):
            raise ValueError(
                f"Invalid project name '{project_name}'. "
                f"Expected format: {PROJECT_NAME_EXAMPLE}"
            )

    def _validate_architecture(self, architecture: str) -> None:
        """Validate architecture is supported."""
        if architecture not in BASE_ARCHITECTURES:
            valid = ", ".join(BASE_ARCHITECTURES.keys())
            raise ValueError(
                f"Unknown architecture '{architecture}'. "
                f"Valid options: {valid}"
            )

    def _validate_integrations(self, integrations: List[str]) -> None:
        """Validate all integrations are available."""
        available = [i.name for i in list_integrations()]

        for integration_name in integrations:
            if integration_name not in available:
                raise ValueError(
                    f"Unknown integration '{integration_name}'. "
                    f"Available integrations: {', '.join(available)}"
                )

    def _create_directory_structure(self, project_path: Path) -> None:
        """Create project directory structure."""
        project_path.mkdir(parents=True, exist_ok=True)

        for dir_name in PROJECT_STRUCTURE["dirs"]:
            (project_path / dir_name).mkdir(exist_ok=True)

    def _render_base_files(
        self,
        project_path: Path,
        architecture: str,
        context: Dict[str, Any]
    ) -> None:
        """Render base template files for the project."""
        arch_dir = BASE_ARCHITECTURES[architecture]["template_dir"]

        for output_path, template_name in PROJECT_STRUCTURE["files"].items():
            # Construct template path (architecture-specific)
            template_path = f"{arch_dir}/{template_name}"

            # Render template
            content = self.template_renderer.render_template(template_path, context)

            # Write to file
            file_path = project_path / output_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    def _render_integration_files(
        self,
        project_path: Path,
        integrations: List[str],
        context: Dict[str, Any]
    ) -> None:
        """Render integration-specific files."""
        for integration_name in integrations:
            integration = get_integration(integration_name)
            if not integration:
                continue

            # Get template files for this integration
            template_files = integration.get_template_files()

            for template_path, output_path in template_files:
                # Add integration directory prefix
                full_template_path = f"integrations/{template_path}"

                # Render template
                content = self.template_renderer.render_template(
                    full_template_path,
                    context
                )

                # Write to file
                file_path = project_path / output_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

    def _generate_env_file(
        self,
        project_path: Path,
        integrations: List[str]
    ) -> None:
        """Generate .env.example file with integration-specific variables only.

        Skipped when no integrations are selected — all base variables live in
        the repo-root .env and are found automatically via load_dotenv().
        """
        if not integrations:
            return
        self.env_manager.write_env_example(project_path, integrations)

    def _update_root_readme(
        self,
        project_name: str,
        architecture: str,
        integrations: List[str]
    ) -> None:
        """Update root README.md with new project entry."""
        readme_path = self.repo_root / "README.md"

        if not readme_path.exists():
            return  # Skip if README doesn't exist

        # Read current README
        readme_content = readme_path.read_text(encoding="utf-8")

        # Build project description
        project_number = get_project_number(project_name)
        arch_name = BASE_ARCHITECTURES[architecture]["name"]
        integrations_str = ", ".join(integrations) if integrations else "None"

        project_entry = (
            f"- **[{project_number}_{project_name}](projects/{project_name}/README.md)** — "
            f"{arch_name} ({integrations_str})\n"
        )

        # Find insertion point (look for "## Projects" section)
        if "## Projects" in readme_content:
            # Insert after "## Projects" header
            lines = readme_content.split("\n")
            insertion_index = None

            for i, line in enumerate(lines):
                if line.startswith("## Projects"):
                    # Find first empty line after header
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() == "":
                            insertion_index = j + 1
                            break
                    break

            if insertion_index:
                lines.insert(insertion_index, project_entry)
                readme_path.write_text("\n".join(lines), encoding="utf-8")

    def _run_post_generate_hooks(
        self,
        project_path: Path,
        integrations: List[str]
    ) -> None:
        """Run post-generation hooks for integrations."""
        for integration_name in integrations:
            integration = get_integration(integration_name)
            if integration:
                integration.post_generate_hook(project_path)

    def _setup_project_environment(self, project_path: Path) -> None:
        """
        Create an isolated uv virtual environment for the project and install
        all dependencies:
          1. common/ package (editable) — brings runtime deps (langchain, etc.)
          2. requirements-base.txt — test/dev tooling (pytest, etc.)
          3. project requirements.txt — project-specific extras

        Requires uv to be installed globally. Prints a clear error if not found.
        """
        venv_path = project_path / ".venv"
        common_path = self.repo_root / "common"
        requirements_base = self.repo_root / "requirements-base.txt"
        project_requirements = project_path / "requirements.txt"

        try:
            # Verify uv is available before starting
            subprocess.run(
                ["uv", "--version"],
                check=True,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(
                "\n  ⚠️  uv is not installed. Skipping virtual environment setup."
                "\n      Install uv: https://docs.astral.sh/uv/getting-started/installation/"
                "\n      Then run manually inside the project directory:"
                "\n        uv venv .venv"
                f"\n        uv pip install -e {common_path}"
                f"\n        uv pip install -r {requirements_base}"
                "\n        uv pip install -r requirements.txt",
                file=sys.stderr,
            )
            return

        print("\n  🔧 Setting up virtual environment with uv...")

        try:
            # 1. Create venv
            subprocess.run(
                ["uv", "venv", str(venv_path)],
                check=True,
                capture_output=True,
            )
            print(f"     ✓ Created .venv at {venv_path.relative_to(self.repo_root)}")

            # 2. Install common/ as editable (pulls all runtime deps)
            subprocess.run(
                ["uv", "pip", "install", "--python", str(venv_path), "-e", str(common_path)],
                check=True,
                capture_output=True,
            )
            print("     ✓ Installed ai-agent-common (runtime deps)")

            # 2b. Fix editable install .pth file for flat-layout structure
            self._fix_editable_common_install(venv_path)
            print("     ✓ Fixed editable install path configuration")

            # 2c. Verify import works
            if self._verify_common_import(venv_path):
                print("     ✓ Verified 'import common' works correctly")
            else:
                print("     ⚠️  Warning: 'import common' verification failed")
                print("          Run manually: python -c \"import common\"")


            # 3. Install test/dev tooling
            if requirements_base.exists():
                subprocess.run(
                    [
                        "uv", "pip", "install",
                        "--python", str(venv_path),
                        "-r", str(requirements_base),
                    ],
                    check=True,
                    capture_output=True,
                )
                print("     ✓ Installed test/dev tooling (requirements-base.txt)")

            # 4. Install project-specific deps
            if project_requirements.exists():
                subprocess.run(
                    [
                        "uv", "pip", "install",
                        "--python", str(venv_path),
                        "-r", str(project_requirements),
                    ],
                    check=True,
                    capture_output=True,
                )
                print("     ✓ Installed project-specific deps (requirements.txt)")

        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
            print(
                f"\n  ❌  Environment setup failed: {exc.cmd}"
                f"\n{stderr}",
                file=sys.stderr,
            )

    def _fix_editable_common_install(self, venv_path: Path) -> None:
        """
        Fix editable install .pth file for common package.

        Due to flat-layout with name mismatch (project: ai-agent-common, import: common),
        uv creates a .pth file pointing to .../common/ but for 'import common' to work,
        we need the parent directory in sys.path.

        This method updates the .pth file to point to the repo root instead.
        """
        site_packages = venv_path / "Lib" / "site-packages"
        if not site_packages.exists():
            # Try Unix-style path
            site_packages = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

        if not site_packages.exists():
            return  # Can't find site-packages, skip

        # Find the editable .pth file created by uv/pip
        pth_files = list(site_packages.glob("_editable_impl_ai_agent_common.pth"))

        if not pth_files:
            # Fallback: create our own .pth file
            pth_file = site_packages / "ai_agent_common.pth"
        else:
            pth_file = pth_files[0]

        # Write repo root path (parent of common/) to .pth file
        repo_root_str = str(self.repo_root)
        pth_file.write_text(f"{repo_root_str}\n", encoding="utf-8")

    def _verify_common_import(self, venv_path: Path) -> bool:
        """
        Verify that 'import common' works in the project venv.

        Returns:
            True if import succeeds, False otherwise
        """
        python_exe = venv_path / "Scripts" / "python.exe"
        if not python_exe.exists():
            # Try Unix-style path
            python_exe = venv_path / "bin" / "python"

        if not python_exe.exists():
            return False

        try:
            result = subprocess.run(
                [str(python_exe), "-c", "import common"],
                check=True,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
