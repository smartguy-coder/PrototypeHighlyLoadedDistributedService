# Prototype Highly Loaded Distributed Service Utils

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Shared utilities package for [PrototypeHighlyLoadedDistributedService](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService) microservices ecosystem.

## Installation

```bash
pip install prototype-highly-loaded-distributed-service-utils
```

## Usage

```python
from prototype_highly_loaded_distributed_service_utils import utils

# Your code here
```

## Features

- 🔧 Common utilities shared across microservices
- 📦 Single source of truth for shared functionality
- 🐍 Python 3.12+ support
- ✅ Fully typed with mypy strict mode

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService.git
cd PrototypeHighlyLoadedDistributedService/pypi_package_utils

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy .
```

## Building & Publishing

```bash
# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Vasyl Kartychak
