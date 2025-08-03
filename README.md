# Hounslow Bin Collection

Grab bin collection dates from the Hounslow Council website and make them available via MQTT and ICS for Home Assistant or elsewhere

## Features

- Modern Python package built with Python 3.11+
- Code quality with Ruff (formatting, linting, import sorting)
- Comprehensive test suite with pytest and coverage reporting
- YAML configuration support
- Documentation structure ready

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd hounslow_bin_collection

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .[dev]
```

## Usage

```python
import hounslow_bin_collection

# Your code here
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hounslow_bin_collection

# Run specific test file
pytest tests/test_example.py
```

### Code Quality

```bash
# Format code
ruff format

# Lint code
ruff check

# Fix auto-fixable issues
ruff check --fix
```

## Project Structure

```
hounslow_bin_collection/
├── src/hounslow_bin_collection/          # Main package
│   ├── __init__.py
├── tests/                     # Test suite
│   └── test_example.py
├── docs/                      # Documentation
├── config/                    # Configuration files
├── pyproject.toml             # Project configuration
├── README.md                  # This file
└── .gitignore                 # Git ignore rules
```

## License

MIT License - see LICENSE file for details.

## Author

ronschaeffer <ron@ronschaeffer.com>
