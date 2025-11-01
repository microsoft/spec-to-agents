# CI/CD Pipeline Setup

This repository is now configured with a comprehensive CI/CD pipeline that runs on every Pull Request and push to the main branch.

## What runs on every PR:

### 🔍 **Code Quality Checks**
- **Linting**: `ruff check .` - Ensures code follows style guidelines
- **Formatting**: `ruff format --check .` - Verifies code is properly formatted
- **Type Checking**: `mypy .` - Checks type annotations for correctness

### 🧪 **Testing**
- **Unit Tests**: `pytest --verbose --cov` - Runs all tests with coverage reporting
- **Coverage Reporting**: Generates HTML and XML coverage reports
- **Matrix Testing**: Tests on Python 3.11 and 3.12

### 🔒 **Security**
- **Dependency Audit**: `pip-audit` - Scans for known vulnerabilities in dependencies

## Local Development Commands

Before submitting a PR, run these commands locally to ensure CI will pass:

```bash
# Install/sync dependencies
GIT_LFS_SKIP_SMUDGE=1 uv sync --dev

# Run all quality checks
uv run ruff check . --fix        # Fix linting issues
uv run ruff format .             # Format code
uv run mypy .                    # Type checking
uv run pytest --cov=src/spec_to_agents --cov-report=html -v  # Run tests with coverage

# Security audit
uv run pip-audit
```

## Coverage Reports

- **HTML Report**: Generated in `htmlcov/` directory after running tests with coverage
- **XML Report**: Generated as `coverage.xml` for CI integration
- **Coverage uploaded to Codecov**: Automatic upload on Python 3.11 jobs

## Dependabot Configuration

Automatic dependency updates are configured for:
- **Python dependencies**: Weekly updates
- **GitHub Actions**: Weekly updates

## PR Template

A PR template is provided that includes:
- Description checklist
- Testing requirements
- Code quality checklist
- Type of change categories

## Files Added/Modified:

1. **`.github/workflows/ci.yml`** - Main CI pipeline
2. **`.github/dependabot.yml`** - Automated dependency updates
3. **`.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`** - PR template
4. **`pyproject.toml`** - Added dev dependencies and coverage config:
   - `pytest-cov` for coverage reporting
   - `pip-audit` for security scanning
   - `ruff` for linting/formatting
   - Coverage configuration

## Status Badges

Add these to your README.md to show CI status:

```markdown
[![CI](https://github.com/microsoft/spec-to-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/spec-to-agents/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/microsoft/spec-to-agents/branch/main/graph/badge.svg)](https://codecov.io/gh/microsoft/spec-to-agents)
```

## Next Steps

1. **Set up Codecov**: Create account at codecov.io and configure repository
2. **Configure branch protection**: Require CI checks to pass before merging
3. **Add reviewers**: Update dependabot.yml with actual reviewer team names
4. **Custom rules**: Add any project-specific linting or testing rules

The CI pipeline will now automatically run on every PR, ensuring code quality and preventing broken code from being merged.