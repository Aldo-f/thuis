---
sidebar_position: 1
---

# What is thuis? (v2.0.0)

**thuis version 2.0.0** represents a major refactor that introduced the Python-based implementation, replacing the original PowerShell-only version.

This version laid the foundation for the modern thuis architecture with proper Python packaging, dependency management, and initial VRT MAX integration capabilities.

## Core Advancements in v2.0.0

- **Python-based implementation** - Moved from PowerShell/Batch to Python 3.8+
- **Proper package structure** - Introduced `src/thuis/` module organization
- **Dependency management** - Added `requirements.txt` for managed dependencies
- **Initial VERT MAX integration** - Basic framework for VRT MM authentication
- **Basic test suite** - Initial automated tests for core functionality
- **Cross-platform support** - Works on Windows, Linux, and macOS

## Key Features

- **Modular Python architecture** - Clean separation of concerns
- **Virtual environment support** - Isolated dependencies via venv
- **Pip-installable** - Can be installed via `pip install -r requirements.txt`
- **Basic CLI interface** - `python -m thuis.main <URL>` syntax
- **Logging system** - Basic logging to files and console
- **Test foundation** - Initial pytest test suite structure

## Limitations

This is an early version of the Python rewrite. While it established the foundation, many advanced features like comprehensive error handling, advanced logging, and full VRT MAX integration were still in development.

See the [usage guide](usage.md) for examples of how to use this version.
