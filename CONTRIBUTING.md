# Contributing to **thuis**

Thank you for considering contributing to this project! Below are the steps to get you up and running, add a new feature, write tests, and submit a pull request.

## Prerequisites

- **Python 3.8+** installed.
- **Git** installed and configured.
- A fork of the repository on GitHub (click the *Fork* button on the repo page).
- (Optional) Install the [pre‑commit](https://pre-commit.com/) hooks to keep the codebase tidy:
  ```bash
  pip install pre-commit
  pre-commit install
  ```

## Getting the Code

```bash
# Clone your fork
git clone https://github.com/<your‑username>/thuis.git
cd thuis

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Test Suite

The project uses **pytest**. To run all tests:

```bash
pytest
```

You can also run a single test file, e.g.:

```bash
pytest tests/classifier_test.py
```

If you need a quick check while developing, use the `-x` flag to stop on the first failure:

```bash
pytest -x
```

## Adding a New Feature

1. **Create a new branch** from `main` (or the current development branch):
   ```bash
   git checkout -b my‑feature‑name
   ```
2. **Implement the feature** in the appropriate module under `src/thuis/`.
3. **Add tests** for the new functionality in the `tests/` directory. Follow the existing naming convention (`*_test.py`).
4. **Run the test suite** to ensure everything passes.
5. **Update documentation** if your feature changes the CLI usage. Edit `README.md` or add a new section.

## Code Style & Linting

- The project follows **PEP 8**. Run `flake8` to check style:
  ```bash
  flake8 src tests
  ```
- If you have `pre‑commit` installed, it will automatically run formatting tools on each commit.

## Submitting a Pull Request

1. **Commit your changes** with clear, concise messages:
   ```bash
   git add .
   git commit -m "Add feature X and accompanying tests"
   ```
2. **Push the branch** to your fork:
   ```bash
   git push origin my‑feature‑name
   ```
3. Open a **Pull Request** on GitHub:
   - Base repository: `thuis/thuis`
   - Base branch: `main`
   - Compare: your feature branch.
   - Provide a descriptive title and a brief description of what the PR does.
   - Mention any related issues using `#<issue‑number>`.
4. The CI will automatically run the test suite. Ensure all checks pass before merging.

## Troubleshooting

- **Missing dependencies**: Ensure you are inside the virtual environment (`which python` should point to `.venv`).
- **Tests failing**: Run `pytest -vv` to get detailed output and check the failing test case.
- **CI failures**: Look at the GitHub Actions logs for the exact error. Fix any linting or test failures before requesting a review.

---

Happy coding! 🎉

## Versioning Release Checklist

When a new release is tagged, follow these steps to add a Docusaurus version:

1. **Create the tag**: `git tag v<major>.<minor>.<patch>` and push: `git push origin v<major>.<minor>.<patch>`
2. **Create/update the branch**: If not exists, create `v<major>/main` from the tag: `git checkout -b v<major>/main v<major>.<minor>.<patch>` and push.
3. **Generate versioned docs**: Check out `v4/main`, then run:
   ```bash
   cd website
   npx docusaurus docs:version v<major>.<minor>.<patch>
   ```
4. **Update the config**: Edit `website/docusaurus.config.ts` to add the new version to the `versions` block.
5. **Build and verify**: Run `cd website && npx docusaurus build` to confirm it builds successfully.
6. **Commit and push**: Commit the changes to the `v<major>/main` branch with message `docs: add versioned docs for v<major>.<minor>.<patch>`.

The versioned docs are generated from the current `website/docs/` folder. If the release predates the Docusaurus website, the current docs content will be used as a baseline.
