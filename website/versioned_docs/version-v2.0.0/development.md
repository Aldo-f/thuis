---
sidebar_position: 5
---

# Development (v2.0.0)

## Setting Up the Development Environment

To contribute to thuis v2.0.0, follow these steps to set up your development environment:

### Prerequisites

- Python 3.8 or newer
- Git
- pip (comes with Python)

### Setup Steps

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/<your-username>/thuis.git
   cd thuis
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the virtual environment**
   - Linux/macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

4. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r dev-requirements.txt  # if exists
   ```

5. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Running Tests

To run the test suite:

```bash
python -m pytest tests/ -v
```

For specific test modules:

```bash
python -m pytest tests/classifier_test.py -v
```

To run tests with coverage:

```bash
python -m pytest tests/ --cov=src/thuis
```

## Project Structure

```
thuis/
├── src/
│   └── thuis/
│       ├── __init__.py
│       ├── main.py          # Main entry point
│       ├── core/            # Core functionality
│       ├── auth/            # Authentication handling
│       ├── downloader/      # Download logic
│       └── utils/           # Utility functions
├── tests/                   # Test suite
├── requirements.txt         # Production dependencies
├── dev-requirements.txt     # Development dependencies (if applicable)
├── thuis.sh                 # Linux wrapper script
├── thuis.bat                # Windows batch file
├── README.md                # Documentation
└── website/                 # Docusaurus documentation site
```

## Making Changes

When contributing to thuis v2.0.0:

1. **Create a feature branch** from `develop`
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

2. **Make your changes** in the appropriate modules

3. **Add or update tests** for your changes in the `tests/` directory

4. **Run the test suite** to ensure nothing is broken
   ```bash
   python -m pytest tests/ -v
   ```

5. **Follow code style guidelines** - The project follows PEP 8 with some exceptions

6. **Commit your changes** with descriptive messages
   ```bash
   git commit -m "feat: add new download format option"
   ```

## Logging System

v2.0.0 introduced a structured logging system:

- Logs are written to `logs/` directory
- Daily log files (e.g., `logs/2026-07-07.log`)
- Console logging can be enabled with `--log-level` parameter
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Example usage:
```bash
python -m thuis.main --log-level DEBUG https://example.com/video.mpd
```

## Configuration

Configuration in v2.0.0 is handled through:

1. **Command-line arguments** - Primary configuration method
2. **Environment variables** - For sensitive data like credentials
3. **.env file** - Optional file for environment variables (using python-dotenv)
4. **Hardcoded defaults** - Fallback values

## Credentials Handling

v2.0.0 introduced proper credentials management:

- Environment variables: `VRT_EMAIL` and `VRT_PASSWORD`
- .env file support via python-dotemp
- Secure credential handling (no logging of passwords)
- Fallback to built-in demo credentials for testing

## Building and Packaging

To create a distributable package:

```bash
# Ensure you have build tools installed
pip install build

# Build the package
python -m build

# The distribution files will be in the dist/ directory
```

## Testing Best Practices

- Write unit tests for new functionality in the `tests/` directory
- Use fixtures for common test setup
- Mock external dependencies (like network calls) when appropriate
- Follow the Arrange-Act-Assert pattern for test readability
- Ensure tests are deterministic and don't rely on external state
