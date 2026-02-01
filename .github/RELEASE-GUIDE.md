# Quick Release Guide

## Pre-Release Checklist

```bash
# 1. Ensure everything is up to date
git checkout main
git pull origin main

# 2. Run all checks
make check

# 3. Update version in pyproject.toml
# Edit: version = "1.0.0"

# 4. Update CHANGELOG.md
# Move items from [Unreleased] to [1.0.0]

# 5. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 1.0.0"
git push origin main
```

## Option 1: Release via GitHub UI (Recommended)

1. Go to: https://github.com/finnyb/beets-additionalfiles/releases/new
2. Click "Choose a tag" → Type: `v1.0.0` → Create new tag
3. Target: `main`
4. Release title: `v1.0.0`
5. Description: Copy from CHANGELOG.md
6. Click "Publish release"
7. GitHub Actions will automatically publish to PyPI

## Option 2: Release via Command Line

```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0

# Create GitHub release (requires gh CLI)
gh release create v1.0.0 \
  --title "v1.0.0" \
  --notes-file CHANGELOG.md
```

## Testing on TestPyPI First

```bash
# Create release candidate tag
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# Or trigger manually via GitHub Actions
# Go to: Actions → Publish to TestPyPI → Run workflow

# Test installation
pip install --index-url https://test.pypi.org/simple/ beets-additionalfiles
```

## Verify Release

```bash
# Check PyPI page
open https://pypi.org/project/beets-additionalfiles/

# Test installation
pip install --upgrade beets-additionalfiles

# Verify version
python -c "import beetsplug.additionalfiles; print('OK')"
```

## Rollback (if needed)

```bash
# Delete tag locally
git tag -d v1.0.0

# Delete tag remotely
git push origin :refs/tags/v1.0.0

# Delete GitHub release (via UI or gh CLI)
gh release delete v1.0.0

# Note: You CANNOT delete PyPI releases
# You must publish a new fixed version
```

## Common Issues

**Issue**: Workflow fails on "Publish to PyPI"
**Solution**: Ensure Trusted Publishing is configured on PyPI

**Issue**: "File already exists" error
**Solution**: Version already published, bump version number

**Issue**: Tests fail in workflow
**Solution**: Run `make check` locally, fix issues, push again

**Issue**: Can't create release
**Solution**: Ensure you have write permissions on the repository
