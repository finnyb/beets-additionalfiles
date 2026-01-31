# PyPI Publishing Guide

This project uses GitHub Actions to automate publishing to PyPI. There are three workflows configured:

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)
- **Trigger**: Push to `main` or `develop` branches, or pull requests
- **Purpose**: Run tests and linting on multiple Python versions
- **Actions**: Linting with ruff, tests with pytest, build verification

### 2. TestPyPI Workflow (`.github/workflows/publish-test.yml`)
- **Trigger**: Manual dispatch or tags like `v1.0.0-rc1`
- **Purpose**: Test publishing to TestPyPI before production
- **Actions**: Full test suite, build, publish to test.pypi.org

### 3. PyPI Workflow (`.github/workflows/publish.yml`)
- **Trigger**: GitHub Release is published
- **Purpose**: Publish production releases to PyPI
- **Actions**: Full test suite, build, publish to pypi.org

## Setup Instructions

### 1. Configure PyPI Trusted Publishing (Recommended)

Trusted Publishing is the modern, secure way to publish to PyPI without API tokens.

#### For PyPI:
1. Go to https://pypi.org/manage/account/publishing/
2. Add a new "pending publisher":
   - **PyPI Project Name**: `beets-additionalfiles`
   - **Owner**: `finnyb` (your GitHub username/org)
   - **Repository name**: `beets-additionalfiles`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

#### For TestPyPI:
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add a new "pending publisher" with the same details but:
   - **Workflow name**: `publish-test.yml`
   - **Environment name**: `testpypi`

### 2. Alternative: Use API Tokens (Legacy Method)

If you prefer API tokens instead of Trusted Publishing:

1. Generate API tokens:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

2. Add tokens to GitHub Secrets:
   - Go to repository Settings → Secrets and variables → Actions
   - Add secrets:
     - `PYPI_API_TOKEN` - Your PyPI token
     - `TEST_PYPI_API_TOKEN` - Your TestPyPI token

3. Modify workflows to use tokens instead of trusted publishing:
   ```yaml
   - name: Publish to PyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     with:
       password: ${{ secrets.PYPI_API_TOKEN }}
   ```

## Publishing Process

### Testing on TestPyPI

**Option 1: Manual Trigger**
1. Go to Actions → "Publish to TestPyPI"
2. Click "Run workflow"
3. Select branch and run

**Option 2: Release Candidate Tag**
```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```

**Verify Installation:**
```bash
pip install --index-url https://test.pypi.org/simple/ beets-additionalfiles
```

### Publishing to PyPI (Production)

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.0"
   ```

2. **Update CHANGELOG.md** with release notes

3. **Commit and push** changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 1.0.0"
   git push origin main
   ```

4. **Create a GitHub Release**:
   - Go to repository → Releases → Draft a new release
   - Create a new tag: `v1.0.0`
   - Target: `main` branch
   - Release title: `v1.0.0`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"

5. **Monitor the workflow**:
   - Go to Actions tab
   - Watch "Publish to PyPI" workflow
   - Check for any errors

6. **Verify publication**:
   - Check https://pypi.org/project/beets-additionalfiles/
   - Test installation:
     ```bash
     pip install beets-additionalfiles
     ```

## Release Checklist

Before creating a release:

- [ ] All tests pass locally (`make check`)
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] All changes committed and pushed
- [ ] (Optional) Tested on TestPyPI
- [ ] Create git tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub Release

## Workflow Details

### CI Workflow
```yaml
- Runs on: Push to main/develop, PRs
- Python versions: 3.10, 3.11, 3.12, 3.13
- Steps: Install deps → Lint → Test → Build check
```

### Publish Workflows
```yaml
- Runs on: GitHub Release (PyPI) or manual (TestPyPI)
- Python version: 3.11
- Steps: Install deps → Test → Lint → Build → Publish
- Uses: Trusted Publishing (no tokens needed)
```

## Troubleshooting

### "Project name not found" on PyPI
- Create the project manually on PyPI first, or
- Set up Trusted Publishing with "pending publisher"

### "Invalid or non-existent authentication"
- Verify Trusted Publishing is configured correctly
- Check repository name, workflow name, and environment name match exactly

### "File already exists"
- You cannot overwrite versions on PyPI
- Bump the version number in `pyproject.toml`

### Workflow fails on tests
- Run `make check` locally first
- Fix any failing tests or linting issues
- Commit and push fixes before retrying

### Build artifacts not found
- Ensure `uv build` runs successfully
- Check the build step output for errors

## Security Best Practices

✅ **Do:**
- Use Trusted Publishing (no tokens needed)
- Use environment protection rules in GitHub
- Review workflow runs before releases
- Keep dependencies updated

❌ **Don't:**
- Commit API tokens to git
- Share API tokens
- Skip testing before releases
- Publish from feature branches

## Additional Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publishing](https://github.com/marketplace/actions/pypi-publish)
- [Python Packaging Guide](https://packaging.python.org/)
