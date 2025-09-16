# Package Build and Distribution Guide

Complete guide for building, testing, and distributing the Game Translator package.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Package Structure](#package-structure)
- [Build Process](#build-process)
- [Testing Distribution](#testing-distribution)
- [Dependencies Management](#dependencies-management)
- [Publishing](#publishing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

Install the necessary build tools:

```bash
pip install setuptools wheel build twine
```

### Environment Setup

Ensure you have:
- Python 3.8+ installed
- Git repository initialized
- Virtual environment activated (recommended)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install build dependencies
pip install -r requirements-dev.txt
```

## Package Structure

The project follows standard Python package structure:

```
PythonProject_AI_Localisation/
├── setup.py                    # Package configuration
├── MANIFEST.in                 # Additional files inclusion rules
├── requirements.txt            # Core dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project documentation
├── LICENSE                     # License file
├── game_translator/            # Main package
│   ├── __init__.py            # Public API exports
│   ├── py.typed               # Type hints support marker
│   ├── core/                  # Core functionality
│   ├── providers/             # Translation providers
│   ├── importers/             # Data importers
│   └── exporters/             # Data exporters
├── game_translator_cli/        # CLI module
│   ├── __init__.py
│   └── main.py                # CLI entry point
├── tests/                     # Test suite
├── docs/                      # Documentation
└── examples/                  # Usage examples
```

## Build Process

### Step 1: Validate Configuration

Check package configuration for issues:

```bash
python setup.py check
```

**Expected output:**
```
running check
```

**Common warnings (safe to ignore):**
- License classifiers deprecation warning
- Missing optional files in MANIFEST.in

### Step 2: Clean Previous Builds

Remove old build artifacts:

```bash
# Remove build directories
rm -rf build/ dist/ *.egg-info/

# On Windows
rmdir /s build dist
del /s *.egg-info
```

### Step 3: Build Package

**Method 1: Classic setup.py approach**
```bash
python setup.py sdist bdist_wheel
```

**Method 2: Modern build tool (recommended)**
```bash
python -m build
```

### Step 4: Verify Build Output

Check the `dist/` directory:

```bash
ls -la dist/
```

**Expected files:**
```
dist/
├── game_translator-1.0.0.tar.gz          # Source distribution
└── game_translator-1.0.0-py3-none-any.whl # Wheel distribution
```

## Testing Distribution

### Local Installation Testing

**Test development installation:**
```bash
pip install -e .
```

**Test wheel installation:**
```bash
pip install dist/game_translator-1.0.0-py3-none-any.whl
```

### CLI Testing

**Test CLI commands:**
```bash
# Via Python module
python -m game_translator_cli.main --help

# Via entry points (if scripts directory in PATH)
game-translator --help
gt --help

# Via direct script
python cli.py --help
```

**Expected output:**
```
Usage: [command] [OPTIONS] COMMAND [ARGS]...

  Game Translator - AI-powered game localization tool

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  create-patterns  Create template file for custom validation patterns
  init             Initialize a new translation project
  status           Show project status and statistics
  translate        Translate pending entries using AI
  validate         Validate translations for quality and consistency
```

### Import Testing

**Test package imports:**
```python
# Test core imports
from game_translator import (
    TranslationProject,
    TranslationValidator,
    create_project,
    get_provider
)

# Test convenience functions
project = create_project("test", "en", "uk")
validator = create_validator()

# Test provider creation
mock_provider = get_provider("mock")
```

## Dependencies Management

### Core vs Optional Dependencies

The package uses a modular dependency approach:

#### Core Dependencies (requirements.txt)
```txt
click>=8.0.0          # CLI framework
rich>=10.0.0          # Enhanced console output
requests>=2.25.0      # HTTP requests for API calls
python-dotenv>=0.19.0 # Environment variables support
openai>=1.0.0         # Primary translation provider (OpenAI, OpenRouter, DeepSeek)
openpyxl>=3.0.0       # Excel file support for validation patterns and translations
```

#### Optional Dependencies (setup.py extras_require)
```python
extras_require = {
    "dev": [                            # Development tools
        "pytest>=6.0.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
        "mypy>=0.950",
        "pytest-cov>=3.0.0",
    ],
    "docs": [                           # Documentation tools
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "myst-parser>=0.17.0",
    ],
}
```

### Why OpenAI and Excel are Core Dependencies

**These libraries are included by default because:**

1. **OpenAI - Primary Translation Method:**
   - OpenAI API is the main translation provider
   - OpenRouter uses OpenAI client format
   - DeepSeek uses OpenAI-compatible API
   - Most users will use AI-based translation

2. **Excel - Validation and Translation Management:**
   - Custom validation patterns via Excel files
   - Translation review and correction workflows
   - Bulk import/export of translations
   - Professional localization workflows

3. **Flexible Provider Options:**
   ```python
   # Same client library for multiple providers
   from openai import OpenAI

   # OpenAI
   client = OpenAI(api_key="sk-...")

   # OpenRouter
   client = OpenAI(
       api_key="sk-or-...",
       base_url="https://openrouter.ai/api/v1"
   )

   # DeepSeek
   client = OpenAI(
       api_key="sk-...",
       base_url="https://api.deepseek.com/v1"
   )
   ```

4. **Installation Options:**
   ```bash
   # Standard installation (includes OpenAI & Excel)
   pip install game-translator

   # Development setup
   pip install game-translator[dev]

   # Documentation tools
   pip install game-translator[docs]
   ```

### User Installation Examples

**Standard installation (most users):**
```bash
pip install game-translator
# Includes: CLI, OpenAI/OpenRouter/DeepSeek support, Excel files, validation
```

**Development setup:**
```bash
pip install game-translator[dev]
# Adds: pytest, black, flake8, mypy, coverage
```

**Documentation building:**
```bash
pip install game-translator[docs]
# Adds: sphinx, sphinx-rtd-theme, myst-parser
```

## Publishing

### Test Repository (TestPyPI)

**Configure TestPyPI credentials:**
```bash
# ~/.pypirc
[distutils]
index-servers =
    testpypi
    pypi

[testpypi]
repository: https://test.pypi.org/legacy/
username: __token__
password: pypi-your-test-token

[pypi]
repository: https://upload.pypi.org/legacy/
username: __token__
password: pypi-your-production-token
```

**Upload to TestPyPI:**
```bash
twine upload --repository testpypi dist/*
```

**Test installation from TestPyPI:**
```bash
pip install --index-url https://test.pypi.org/simple/ game-translator
```

### Production Repository (PyPI)

**Upload to PyPI:**
```bash
twine upload dist/*
```

**Verify installation:**
```bash
pip install game-translator
```

## Troubleshooting

### Common Build Issues

**1. Import Errors During Build**
```
ImportError: cannot import name 'ClassName' from 'module'
```
**Solution:** Check all imports in `__init__.py` match actual class names.

**2. Missing Files in Distribution**
```
warning: no files found matching 'pattern' under directory 'path'
```
**Solution:** Update `MANIFEST.in` or ensure files exist.

**3. Entry Points Not Working**
```
bash: game-translator: command not found
```
**Solution:** Check `entry_points` in `setup.py` and ensure scripts directory is in PATH.

### Version Management

**Update version in multiple locations:**
1. `setup.py` - version parameter
2. `game_translator/__init__.py` - __version__
3. `game_translator_cli/__init__.py` - __version__

**Automated version bumping:**
```bash
# Using bump2version (optional)
pip install bump2version
bump2version patch  # 1.0.0 -> 1.0.1
bump2version minor  # 1.0.1 -> 1.1.0
bump2version major  # 1.1.0 -> 2.0.0
```

### Development Workflow

**Typical development cycle:**
```bash
# 1. Make changes
# 2. Update version numbers
# 3. Run tests
pytest

# 4. Clean and rebuild
rm -rf build/ dist/ *.egg-info/
python -m build

# 5. Test locally
pip install --force-reinstall dist/*.whl
python -m game_translator_cli.main --help

# 6. Upload to TestPyPI
twine upload --repository testpypi dist/*

# 7. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ game-translator

# 8. Upload to production PyPI
twine upload dist/*
```

### Security Best Practices

**1. Use API tokens instead of passwords:**
- Generate tokens at https://pypi.org/manage/account/token/
- Use `__token__` as username

**2. Environment variables for sensitive data:**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token
twine upload dist/*
```

**3. Verify package contents:**
```bash
# Check wheel contents
unzip -l dist/game_translator-1.0.0-py3-none-any.whl

# Check source distribution
tar -tzf dist/game_translator-1.0.0.tar.gz
```

This guide ensures reliable package building and distribution following Python packaging best practices.