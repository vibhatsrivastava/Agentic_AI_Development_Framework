"""
cli.py — Command-line interface for AI Agent Builder.

Provides commands for project scaffolding, validation, and integration management.
"""

import re
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from .config import BASE_ARCHITECTURES, PROJECT_NAME_EXAMPLE, PROJECT_NAME_PATTERN
from .integrations import get_integration, list_integrations
from .scaffold import ProjectScaffolder
from .version import __version__

# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version=__version__, prog_name="ai-agent-builder")
def main():
    """
    ai-agent-builder — AI Agent project scaffolding and development tools.

    Accelerate AI Agent development with automated project generation,
    composable integration modules, and built-in best practices.
    """
    pass


@main.command()
@click.argument("project_name", required=False)
@click.option(
    "--architecture",
    "--arch",
    "-a",
    type=click.Choice(list(BASE_ARCHITECTURES.keys())),
    help="Base architecture (lcel, langgraph, custom)"
)
@click.option(
    "--integrations",
    "-i",
    help="Comma-separated integration names (e.g., 'pgvector,langfuse')"
)
@click.option(
    "--projects-dir",
    type=click.Path(),
    default="projects",
    help="Projects directory (default: projects)"
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Non-interactive mode (all options via flags)"
)
def new_project(
    project_name: Optional[str],
    architecture: Optional[str],
    integrations: Optional[str],
    projects_dir: str,
    non_interactive: bool
):
    """
    Create a new LangChain project from templates.

    EXAMPLES:

        \b
        # Interactive mode (recommended for first-time users)
        ai-agent-builder new-project

        \b
        # Non-interactive mode
        ai-agent-builder new-project 05_sentiment_analysis \\
            --architecture lcel \\
            --integrations langfuse

        \b
        # RAG project with pgvector + Langfuse
        ai-agent-builder new-project 06_rag_system \\
            --arch lcel \\
            -i pgvector,langfuse
    """
    # Find repo root (where .git directory is)
    repo_root = Path.cwd()
    while not (repo_root / ".git").exists() and repo_root != repo_root.parent:
        repo_root = repo_root.parent

    if not (repo_root / ".git").exists():
        click.secho("Error: Not inside a git repository", fg="red")
        sys.exit(1)

    projects_path = repo_root / projects_dir

    # Interactive mode
    if not non_interactive:
        click.echo(click.style("\n🚀 AI Agent Builder — Project Generator", fg="cyan", bold=True))
        click.echo()

        # Get project name
        if not project_name:
            click.echo(f"Project name pattern: {click.style(PROJECT_NAME_EXAMPLE, fg='yellow')}")
            project_name = click.prompt(
                "Enter project name",
                type=str,
                value_proc=lambda x: x.strip()
            )

        # Validate project name
        if not re.match(PROJECT_NAME_PATTERN, project_name):
            click.secho(
                f"Error: Project name must match pattern: {PROJECT_NAME_EXAMPLE}",
                fg="red"
            )
            sys.exit(1)

        # Get architecture
        if not architecture:
            click.echo("\nAvailable architectures:")
            for key, arch in BASE_ARCHITECTURES.items():
                click.echo(f"  {click.style(key, fg='green')}: {arch['description']}")

            architecture = click.prompt(
                "Select architecture",
                type=click.Choice(list(BASE_ARCHITECTURES.keys())),
                default="lcel"
            )

        # Get integrations
        if not integrations:
            available_integrations = list_integrations()

            click.echo("\nAvailable integrations:")
            by_category = {}
            for integration in available_integrations:
                if integration.category not in by_category:
                    by_category[integration.category] = []
                by_category[integration.category].append(integration)

            for category, integ_list in sorted(by_category.items()):
                click.echo(f"\n  {click.style(category.upper(), fg='cyan')}:")
                for integration in integ_list:
                    click.echo(f"    - {click.style(integration.name, fg='green')}: {integration.description}")

            integrations = click.prompt(
                "\nSelect integrations (comma-separated, or 'none')",
                type=str,
                default="none"
            )

    # Parse integrations
    integration_list = []
    if integrations and integrations.lower() != "none":
        integration_list = [i.strip() for i in integrations.split(",")]

    # Validate integrations exist
    available_names = [i.name for i in list_integrations()]
    for integ_name in integration_list:
        if integ_name not in available_names:
            click.secho(f"Error: Unknown integration '{integ_name}'", fg="red")
            click.echo(f"Available: {', '.join(available_names)}")
            sys.exit(1)

    # Create scaffolder
    scaffolder = ProjectScaffolder(
        projects_dir=projects_path,
        repo_root=repo_root
    )

    # Scaffold project
    click.echo()
    click.echo(click.style("📁 Creating project structure...", fg="cyan"))

    try:
        project_path = scaffolder.scaffold_project(
            project_name=project_name,
            architecture=architecture,
            integrations=integration_list
        )

        click.echo(click.style("✅ Project created successfully!", fg="green", bold=True))
        click.echo()
        click.echo(f"Location: {click.style(str(project_path.relative_to(repo_root)), fg='yellow')}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  1. cd {project_path.relative_to(repo_root)}")
        click.echo("  2. Activate the project venv:")
        click.echo("       Windows: .venv\\Scripts\\activate")
        click.echo("       Mac/Linux: source .venv/bin/activate")
        click.echo("  3. Ensure environment variables are set in repo-root .env")
        click.echo("  4. Run: python src/main.py")
        click.echo()

    except Exception as e:
        click.secho(f"Error creating project: {e}", fg="red")
        sys.exit(1)


@main.group()
def integrations():
    """Manage and discover integration modules."""
    pass


@integrations.command("list")
@click.option(
    "--category",
    "-c",
    type=click.Choice(["vector_store", "cache", "observability", "loader"]),
    help="Filter by category"
)
def list_integrations_cmd(category: Optional[str]):
    """
    List all available integration modules.

    EXAMPLES:

        \b
        # List all integrations
        ai-agent-builder integrations list

        \b
        # List only vector stores
        ai-agent-builder integrations list --category vector_store
    """
    integrations_list = list_integrations(category=category)

    if not integrations_list:
        click.echo("No integrations available.")
        return

    click.echo(click.style("\n📦 Available Integrations", fg="cyan", bold=True))
    click.echo()

    # Group by category
    by_category = {}
    for integration in integrations_list:
        if integration.category not in by_category:
            by_category[integration.category] = []
        by_category[integration.category].append(integration)

    for cat, integ_list in sorted(by_category.items()):
        click.echo(click.style(f"{cat.upper()}:", fg="yellow", bold=True))
        for integration in integ_list:
            click.echo(f"  {click.style(integration.name, fg='green')} — {integration.description}")
        click.echo()


@integrations.command("info")
@click.argument("integration_name")
def integration_info(integration_name: str):
    """
    Show detailed information about an integration.

    EXAMPLES:

        \b
        # Get pgvector integration details
        ai-agent-builder integrations info pgvector
    """
    integration = get_integration(integration_name)

    if not integration:
        click.secho(f"Error: Integration '{integration_name}' not found", fg="red")
        sys.exit(1)

    click.echo()
    click.echo(click.style(f"📦 {integration.display_name}", fg="cyan", bold=True))
    click.echo(integration.description)
    click.echo()

    click.echo(click.style("Category:", fg="yellow"))
    click.echo(f"  {integration.category}")
    click.echo()

    click.echo(click.style("Dependencies:", fg="yellow"))
    for dep in integration.get_dependencies():
        click.echo(f"  - {dep}")
    click.echo()

    click.echo(click.style("Environment Variables:", fg="yellow"))
    for key, value in integration.get_env_vars().items():
        click.echo(f"  {key}={value}")
    click.echo()

    prereqs = integration.get_prerequisites()
    if prereqs:
        click.echo(click.style("Prerequisites:", fg="yellow"))
        for prereq in prereqs:
            click.echo(f"  - {prereq}")
        click.echo()

    click.echo(click.style("Generated Files:", fg="yellow"))
    for template_path, output_path in integration.get_template_files():
        click.echo(f"  {output_path}")
    click.echo()


@main.command()
@click.argument("project_path", type=click.Path(exists=True), required=False)
def validate(project_path: Optional[str]):
    """
    Validate project structure and configuration.

    EXAMPLES:

        \b
        # Validate current directory
        ai-agent-builder validate

        \b
        # Validate specific project
        ai-agent-builder validate projects/05_my_project
    """
    if not project_path:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)

    click.echo(click.style(f"\n🔍 Validating project: {project_path.name}", fg="cyan", bold=True))
    click.echo()

    issues = []

    # Check directory structure
    required_dirs = ["src", "tests"]
    for dir_name in required_dirs:
        if not (project_path / dir_name).exists():
            issues.append(f"Missing directory: {dir_name}/")

    # Check required files
    required_files = [
        "src/main.py",
        "tests/conftest.py",
        "requirements.txt",
        ".env.example",
        "README.md"
    ]
    for file_path in required_files:
        if not (project_path / file_path).exists():
            issues.append(f"Missing file: {file_path}")

    # Check .env file
    env_file = project_path / ".env"
    if not env_file.exists():
        issues.append("Missing .env file (copy from .env.example)")

    # Report results
    if issues:
        click.echo(click.style("⚠️  Issues found:", fg="yellow"))
        for issue in issues:
            click.echo(f"  - {issue}")
        click.echo()
    else:
        click.echo(click.style("✅ Project structure valid!", fg="green"))
        click.echo()


@main.command()
@click.argument("project_path", type=click.Path(exists=True), required=False)
@click.option("--coverage", is_flag=True, help="Run with coverage report")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def test(project_path: Optional[str], coverage: bool, verbose: bool):
    """
    Run project tests.

    EXAMPLES:

        \b
        # Run tests in current directory
        ai-agent-builder test

        \b
        # Run with coverage
        ai-agent-builder test --coverage

        \b
        # Run specific project tests
        ai-agent-builder test projects/05_my_project --coverage -v
    """
    if not project_path:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)

    click.echo(click.style(f"\n🧪 Running tests: {project_path.name}", fg="cyan", bold=True))
    click.echo()

    # Build pytest command
    pytest_cmd = ["pytest"]

    if coverage:
        pytest_cmd.extend(["--cov", "--cov-report=term-missing", "--cov-fail-under=90"])

    if verbose:
        pytest_cmd.append("-v")

    # Change to project directory and run
    import subprocess

    result = subprocess.run(
        pytest_cmd,
        cwd=project_path,
        capture_output=False
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
