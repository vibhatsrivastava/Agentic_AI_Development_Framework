# CLI Editable Install Fixes

## Problem Summary

When projects were scaffolded using `ai-agent-builder new-project`, the `common` package was installed as an editable package, but imports failed with:
```
ModuleNotFoundError: No module named 'common'
```

## Root Cause

The issue stemmed from a mismatch between the project structure and Python packaging expectations:

1. **Package name vs. import name mismatch:**
   - Installable package name: `ai-agent-common`
   - Python import name: `common`
   - Hatchling couldn't auto-discover the package due to this mismatch

2. **Flat-layout structure:**
   ```
   common/
   ├── pyproject.toml         ← Build config here
   ├── __init__.py            ← Package root here
   ├── llm_factory.py
   └── cache/
       └── __init__.py
   ```

3. **Incorrect .pth file path:**
   - Editable install created: `.pth` pointing to `.../common/`
   - But for `import common` to work, need: `.../` (parent directory)

## Solutions Implemented

### 1. Fixed `common/pyproject.toml`

**Before:**
```toml
[tool.hatch.build.targets.wheel]
packages = ["common", "common/cache", "common/prompts"]
```

This was looking for `common/common/` which doesn't exist!

**After:**
```toml
[tool.hatch.build.targets.wheel]
# Note: Due to flat-layout with name mismatch (project: ai-agent-common, import: common),
# editable installs require manual .pth file creation. This is handled by the CLI scaffold.
packages = ["."]
```

### 2. Updated CLI Scaffold (`cli/ai_agent_builder/scaffold.py`)

Added automatic .pth file fix after editable install:

```python
def _fix_editable_common_install(self, venv_path: Path) -> None:
    """
    Fix editable install .pth file for common package.
    
    Due to flat-layout with name mismatch, uv creates a .pth file pointing to 
    .../common/ but for 'import common' to work, we need the parent directory 
    in sys.path.
    """
    # Find or create .pth file
    site_packages = venv_path / "Lib" / "site-packages"
    pth_file = site_packages / "_editable_impl_ai_agent_common.pth"
    
    # Write repo root path (parent of common/) to .pth file
    repo_root_str = str(self.repo_root)
    pth_file.write_text(f"{repo_root_str}\n", encoding="utf-8")
```

### 3. Added Import Verification

```python
def _verify_common_import(self, venv_path: Path) -> bool:
    """Verify that 'import common' works in the project venv."""
    python_exe = venv_path / "Scripts" / "python.exe"
    result = subprocess.run(
        [str(python_exe), "-c", "import common"],
        check=True,
        capture_output=True
    )
    return result.returncode == 0
```

## Installation Flow (Fixed)

When `ai-agent-builder new-project` is run, the CLI now:

1. ✅ Creates project directory structure
2. ✅ Creates `.venv` with `uv venv`
3. ✅ Installs `ai-agent-common` with `uv pip install -e .../common`
4. ✅ **Fixes .pth file** to point to repo root (not `common/` dir)
5. ✅ **Verifies import works** with test import
6. ✅ Installs `requirements-base.txt` (pytest, etc.)
7. ✅ Installs project `requirements.txt`

## Manual Fix for Existing Projects

If you have an existing project with the import error:

```powershell
cd projects\your_project
.venv\Scripts\Activate.ps1

# Fix the .pth file
$repoRoot = "C:\path\to\Agentic_AI_Development_Framework"
Set-Content -Path ".venv\Lib\site-packages\_editable_impl_ai_agent_common.pth" -Value "$repoRoot`n"

# Verify it works
python -c "import common; print('Success!', common.__file__)"
```

## Alternative Solutions Considered

### Option A: Rename Package (Breaking Change)
Rename `common/` to `ai_agent_common/` to match project name.
- ❌ Breaks all existing imports across all projects

### Option B: Move to src-layout (Recommended for Future)
```
common/
├── pyproject.toml
└── src/
    └── common/
        ├── __init__.py
        └── ...
```
- ✅ Follows modern Python packaging best practices
- ✅ Hatchling auto-discovery works
- ❌ Requires migration of existing projects

### Option C: Fix .pth File (Current Solution)
- ✅ Minimal changes to existing code
- ✅ Backward compatible
- ✅ Automated in CLI
- ⚠️  Slightly non-standard approach

## Testing

To test the fix works:

```powershell
# Create a new project
ai-agent-builder new-project 99_test_project --arch lcel -i none

# Activate venv
cd projects\99_test_project
.venv\Scripts\Activate.ps1

# Test import
python -c "from common.llm_factory import get_llm; print('Success!')"

# Run project
python src\main.py
```

## Future Improvements

1. **Migrate to src-layout** when next breaking change window opens
2. **Consider renaming** `common` → `ai_agent_common` for clarity
3. **Add automated tests** for CLI scaffolding process
4. **Document** this pattern in packaging best practices guide
