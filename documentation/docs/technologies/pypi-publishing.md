# PyPI Package Publishing

Publishing shared Python packages to PyPI (Python Package Index) for reuse across microservices.

---

## Table of Contents

1. [Overview](#overview)
2. [Build Tools](#build-tools)
3. [Package Structure](#package-structure)
4. [Configuration Files](#configuration-files)
5. [Authentication](#authentication)
6. [Publishing Workflow](#publishing-workflow)
7. [Make Commands](#make-commands)
8. [Versioning](#versioning)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

### Why Publish to PyPI?

When building a microservices architecture, you often need to share code between services:

- **Pydantic schemas** — Shared message contracts for Kafka
- **Utility functions** — Common helpers (validation, formatting, etc.)
- **Base classes** — Abstract producers, consumers, clients

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Package Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────────┐                      │
│                    │  PyPI (Public)      │                      │
│                    │  or Private PyPI    │                      │
│                    └──────────┬──────────┘                      │
│                               │                                 │
│              pip install package-utils                          │
│                               │                                 │
│         ┌─────────────────────┼─────────────────────┐           │
│         │                     │                     │           │
│         ▼                     ▼                     ▼           │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │  Service A  │      │  Service B  │      │  Service C  │      │
│  │  (Django)   │      │  (FastAPI)  │      │  (Worker)   │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
│                                                                 │
│  All services use the SAME version of shared schemas            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Our Package

| Field | Value |
|-------|-------|
| **Name** | `prototype-highly-loaded-distributed-service-utils` |
| **Location** | `pypi_package_utils/` |
| **PyPI URL** | [pypi.org/project/prototype-highly-loaded-distributed-service-utils](https://pypi.org/project/prototype-highly-loaded-distributed-service-utils/) |
| **Install** | `pip install prototype-highly-loaded-distributed-service-utils` |

---

## Build Tools

Python packaging relies on several tools to build and distribute packages.

### Wheel

**Wheel** is a built-package format for Python (PEP 427).

| Aspect | Description |
|--------|-------------|
| **What it is** | A `.whl` file — a ZIP archive with a special structure |
| **Purpose** | Pre-built distribution format (no compilation needed on install) |
| **File naming** | `package_name-version-py3-none-any.whl` |
| **Benefits** | Faster installation, no build dependencies required for users |

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source vs Wheel Distribution                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Source Distribution (sdist)          Wheel Distribution        │
│  ┌─────────────────────┐              ┌─────────────────────┐   │
│  │  package-1.0.tar.gz │              │  package-1.0.whl    │   │
│  │  • Raw source code  │              │  • Pre-built        │   │
│  │  • setup.py needed  │              │  • Ready to install │   │
│  │  • Build on install │              │  • No build step    │   │
│  └─────────────────────┘              └─────────────────────┘   │
│           │                                    │                │
│           ▼                                    ▼                │
│    pip install                          pip install             │
│    (runs setup.py,                      (just extracts,         │
│     compiles C code)                     ~10x faster)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Why we use wheel:**

- Pure Python packages install instantly
- No need for users to have build tools
- Consistent installation across platforms

```bash
# Build wheel with uv
uv build --wheel

# Result: dist/prototype_highly_loaded_...-0.1.1-py3-none-any.whl
```

### Twine

**Twine** is a utility for publishing packages to PyPI securely.

| Aspect | Description |
|--------|-------------|
| **What it is** | CLI tool for uploading distributions to PyPI |
| **Purpose** | Secure upload with HTTPS, verification, and authentication |
| **Key features** | Pre-upload validation, GPG signing support, API token auth |
| **Why not `setup.py upload`** | Legacy method is insecure (uses HTTP, plaintext passwords) |

**Twine workflow:**

```bash
# 1. Check package before upload (validates metadata, README)
uv run twine check dist/*

# 2. Upload to PyPI
uv run twine upload dist/*
# Enter: __token__ / your-api-token

# 3. Upload to TestPyPI (for testing)
uv run twine upload --repository testpypi dist/*
```

**What `twine check` validates:**

- Package metadata is complete
- README renders correctly on PyPI
- No duplicate files
- Correct file format

```
┌─────────────────────────────────────────────────────────────────┐
│                    Twine Upload Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Local Machine                           PyPI Server           │
│   ┌─────────────────┐                    ┌─────────────────┐    │
│   │  dist/          │    twine upload    │                 │    │
│   │  ├── .whl       │ ────────────────►  │  Package Index  │    │
│   │  └── .tar.gz    │    (HTTPS + Token) │                 │    │
│   └─────────────────┘                    └─────────────────┘    │
│                                                  │              │
│                                                  ▼              │
│                                          pip install pkg        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Build Tools Summary

| Tool | Role | Command |
|------|------|--------|
| **setuptools** | Build backend (reads pyproject.toml) | — |
| **wheel** | Creates `.whl` distribution format | `uv build --wheel` |
| **twine** | Uploads to PyPI securely | `twine upload dist/*` |
| **uv** | Fast package manager (runs all above) | `uv sync`, `uv build` |

---

## Package Structure

```
pypi_package_utils/
├── prototype_highly_loaded_distributed_service_utils/
│   ├── __init__.py              # Package exports, version
│   ├── py.typed                 # PEP 561 marker for type hints
│   ├── utils/
│   │   ├── __init__.py          # Utils exports
│   │   └── utils.py             # Utility functions
│   └── tests/
│       ├── __init__.py
│       └── test_utils.py        # Unit tests
├── pyproject.toml               # Build configuration (PEP 517/518)
├── setup.py                     # Legacy setup (optional)
├── README.md                    # Package documentation
├── LICENSE                      # MIT License
└── MANIFEST.in                  # Include non-Python files
```

### Key Files

#### `__init__.py` (Root)

```python
"""
Prototype Highly Loaded Distributed Service Utils.

Shared utilities for microservices ecosystem.
"""

__version__ = "0.1.1"
__author__ = "Vasyl Kartychak"

# Re-export public API
from prototype_highly_loaded_distributed_service_utils.utils import *  # noqa: F401, F403
```

#### `py.typed`

Empty file that marks the package as PEP 561 compliant (supports type hints).

```bash
touch prototype_highly_loaded_distributed_service_utils/py.typed
```

---

## Configuration Files

### pyproject.toml

Modern Python packaging uses `pyproject.toml` (PEP 517/518):

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "prototype-highly-loaded-distributed-service-utils"
version = "0.1.1"
description = "Shared utilities for PrototypeHighlyLoadedDistributedService microservices"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
authors = [
    {name = "Vasyl Kartychak", email = "your.email@example.com"}
]
dependencies = [
    "pydantic>=2.0",
]
keywords = [
    "microservices",
    "utilities",
    "distributed-systems",
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService"
Repository = "https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService"

[project.optional-dependencies]
dev = [
    "build>=1.0",
    "twine>=5.0",
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "mypy>=1.8",
    "ruff>=0.3",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["prototype_highly_loaded_distributed_service_utils*"]

[tool.pytest.ini_options]
testpaths = ["prototype_highly_loaded_distributed_service_utils/tests"]
pythonpath = ["."]
```

### MANIFEST.in

Include non-Python files in the distribution:

```
include LICENSE
include README.md
include pyproject.toml
recursive-include prototype_highly_loaded_distributed_service_utils py.typed
```

---

## Authentication

### PyPI API Token

PyPI requires authentication to publish packages. **API tokens are recommended** over passwords.

#### Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Verify your email
3. Enable 2FA (recommended)

#### Step 2: Generate API Token

1. Go to https://pypi.org/manage/account/token/
2. Click **"Add API token"**
3. Name: `prototype-utils-publish` (or any descriptive name)
4. Scope: **"Entire account"** (for first upload) or specific project
5. Copy the token (starts with `pypi-`)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PyPI Token Creation                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Token name:  prototype-utils-publish                           │
│  Scope:       Entire account (first time)                       │
│                                                                 │
│  ⚠️  Copy the token now! It won't be shown again.               │
│                                                                 │
│  Token: pypi-AgEIcHlwaS5vcmcCJGxxxxxxxxxxxxxxxxxxxxxxxx...      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Publishing Workflow

### Automated via Makefile

```bash
# One command does it all:
make pypi-publish

# What happens:
# 1. make pypi-test   → Run pytest
# 2. make pypi-build  → Build wheel with uv
# 3. twine check      → Validate package
# 4. twine upload     → Upload to PyPI (prompts for token)
# 5. make pypi-clean  → Clean artifacts
```

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make pypi-test` | Run tests with pytest |
| `make pypi-build` | Build wheel package |
| `make pypi-publish` | Full workflow: test → build → publish → clean |
| `make pypi-clean` | Remove build artifacts |

---

## Versioning

### Semantic Versioning

We follow [SemVer](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.0.0 → 1.0.1  (patch: bug fixes)
1.0.1 → 1.1.0  (minor: new features, backward compatible)
1.1.0 → 2.0.0  (major: breaking changes)
```

### Version Locations

Update version in **two places**:

1. `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.2"
   ```

2. `__init__.py`:
   ```python
   __version__ = "0.1.2"
   ```

### Pre-release Workflow

```bash
# 1. Update version in pyproject.toml and __init__.py
# 2. Commit changes
git add -A
git commit -m "Bump version to 0.1.2"

# 3. Tag the release
git tag v0.1.2
git push origin main --tags

# 4. Publish
make pypi-publish
```

---

## Troubleshooting

### "Version already exists"

```
HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
File already exists. See https://pypi.org/help/#file-name-reuse
```

**Cause:** You're trying to upload the same version that already exists on PyPI.

**Solution:** Increment the version number in `pyproject.toml` and `__init__.py`.

### "Invalid API token"

```
HTTPError: 403 Forbidden from https://upload.pypi.org/legacy/
Invalid or non-existent authentication information.
```

**Cause:** Wrong token or username.

**Solution:**
- Username must be `__token__` (with double underscores)
- Password is the full token including `pypi-` prefix
- if asked API-token, provide just it

### "Package not found after upload"

**Cause:** PyPI indexing delay (usually 1-5 minutes).

**Solution:**
```bash
# Wait a few minutes, then:
pip install --no-cache-dir package-name==version

# Or check directly:
curl -s https://pypi.org/pypi/package-name/json | python -c "import sys,json; print(list(json.load(sys.stdin)['releases'].keys()))"
```

### "Tests fail with import error"

```
ModuleNotFoundError: No module named 'prototype_highly_loaded_distributed_service_utils'
```

**Cause:** `pythonpath` not configured in pytest.

**Solution:** Check `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["prototype_highly_loaded_distributed_service_utils/tests"]
pythonpath = ["."]
```

### "twine check" warnings

```
warning: `long_description_content_type` missing
```

**Solution:** Ensure `README.md` is specified:
```toml
[project]
readme = "README.md"
```

---

## Best Practices

### 1. Always Run Tests Before Publishing

```bash
# Never skip tests!
make pypi-publish  # Runs tests automatically
```

### 2. Use Type Hints

```python
# ✅ Good: Typed functions
def format_phone(phone: str) -> str:
    """Format phone number to E.164."""
    return phone.strip().replace(" ", "")

# Include py.typed marker
```

### 3. Document Public API

```python
def example_utility() -> str:
    """Return a greeting string.

    Returns:
        A greeting message for testing purposes.

    Example:
        >>> from prototype_highly_loaded_distributed_service_utils import example_utility
        >>> example_utility()
        'Hello from prototype utils!'
    """
    return "Hello from prototype utils!"
```

### 4. Pin Major Versions in Dependencies

```toml
# ✅ Good: Flexible within major version
dependencies = [
    "pydantic>=2.0,<3.0",
]

# ❌ Bad: Too strict
dependencies = [
    "pydantic==2.5.3",
]
```

### 5. Keep Package Lightweight

```python
# ✅ Good: Minimal dependencies
dependencies = [
    "pydantic>=2.0",
]

# ❌ Bad: Heavy dependencies for a utils package
dependencies = [
    "django>=4.0",
    "celery>=5.0",
    "kafka-python>=2.0",
]
```

### 6. Gitignore Build Artifacts

```gitignore
# pypi_package_utils/.gitignore
dist/
build/
*.egg-info/
.pytest_cache/
__pycache__/
uv.lock
```

---

## TestPyPI (Optional)

For testing before real PyPI upload:

```bash
# Upload to TestPyPI first
uv run twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ package-name
```

Create `~/.pypirc` for TestPyPI:

```ini
[testpypi]
username = __token__
password = pypi-AgEXXXtestXXX...
```

---

## Further Reading

- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 517 – Build System](https://peps.python.org/pep-0517/)
- [PEP 518 – pyproject.toml](https://peps.python.org/pep-0518/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)

---

## Related Documentation

- [Technologies Overview](index.md)
- [Apache Kafka](kafka.md)
- [Tech Stack](../about/tech-stack.md)
