# GitHub Gists Test Framework

## Description
- Automated tests for GitHub Gists written in Python (requests + pytest) with Allure reporting.
- Runs locally (uv) or in Docker. CI uses GitHub Actions.

## Requirements
- Python 3.12 (for local runs without Docker)
- Personal GitHub access token with the "gist" scope

## Configuration
- Copy .env.example to .env and set:
  - GITHUB_TOKEN=<your_token_with_gist_scope>
  - Optional: BASE_URL (default https://api.github.com), GITHUB_API_VERSION (default 2022-11-28)

## Setup and run tests

### Option A — Local with uv (recommended)
1. Install uv:
   - macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Windows (PowerShell):
     ```powershell
     iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
     ```
2. Create and activate venv with Python 3.12:
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate   # Windows: .venv/Scripts/activate
   ```
3. Install deps in editable mode:
   ```bash
   uv pip install -e '.[test]'
   ```
4. Configure env:
   ```bash
   cp .env.example .env
   # then set GITHUB_TOKEN in .env
   ```
5. Run tests:
   ```bash
   pytest -v
   ```
6. Allure raw results: temp/allure-results (see pytest.ini).
   - To view interactively, use Allure CLI:
     ```bash
     allure serve temp/allure-results
     ```

### Option B — Docker (no local Python needed)
1. Build image:
   ```bash
   docker build -t gists-tests .
   ```
2. Run tests (mount temp/ to collect raw Allure results):
   ```bash
   docker run --rm \
     -e GITHUB_TOKEN=$GITHUB_TOKEN \
     -e BASE_URL=https://api.github.com \
     -v "$(pwd)/temp/allure-report:/app/temp/allure-report" \
     gists-tests
   ```
   The container will run pytest and write Allure raw results to temp/allure-results.
3. Generate and open the Allure report on the host (optional):
   ```bash
   allure generate temp/allure-results -o temp/allure-report --clean
   allure open temp/allure-report
   # or open temp/allure-report/index.html in a browser
   ```

## CI
- GitHub Actions workflow: .github/workflows/ci.yml
- Add repository secret PERSONAL_GITHUB_TOKEN with gist scope
- CI installs with:
  ```bash
  pip install -e '.[test]'
  ```
  and uploads temp/allure-results as an artifact
