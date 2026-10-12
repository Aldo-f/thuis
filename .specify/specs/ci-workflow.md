# CI Workflow Specification

## File
`.github/workflows/ci.yml`

## Jobs

### lint-and-test
```yaml
name: CI
on:
  push:
    branches: [main, v4/*]
  pull_request:
    branches: [main, v4/*]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Run lint (ruff)
        run: uv run ruff check .
      
      - name: Run type check (mypy)
        run: uv run mypy src/thuis
      
      - name: Run tests
        run: uv run pytest tests/ -v --tb=short
      
      - name: Verify wrapper scripts
        run: |
          chmod +x thuis.sh
          ./thuis.sh --help
          # Verify it doesn't crash
```

### docker-build (optional)
```yaml
  docker-build:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t thuis:latest -f infra/Dockerfile .
```

## Requirements
- Python 3.11+
- uv for dependency management
- ruff for linting
- mypy for type checking
- pytest for testing

## Test Coverage
- All unit tests must pass
- Integration tests with mocked yt-dlp
- No network access in CI (mock all external calls)

## Artifacts
- Test results (JUnit XML)
- Coverage report (optional)