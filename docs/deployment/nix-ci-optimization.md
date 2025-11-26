# Nix CI/CD Optimization Summary

## ⚠️ Important Update (2025-11-27)

**The workflow has been migrated from Magic Nix Cache to Cachix.**

- **Reason:** Magic Nix Cache will stop working on February 1st, 2025 (GitHub is shutting down the API)
- **New Solution:** Cachix with 5GB free tier for open source projects
- **Setup Required:** See [Cachix Setup Guide](./cachix-setup.md) for configuration instructions

---

## Overview

This document describes the optimization of the Nix-based CI/CD pipeline for the LLT Assistant Backend project. The optimization focuses on improving resource efficiency, reducing redundant operations, and implementing a fail-fast strategy.

## Changes Made

### 1. Job Dependencies (needs: keyword)

**Before:** 2 jobs running in parallel with no dependency
```yaml
jobs:
  nix-build:    # No dependencies
  nix-check:    # No dependencies
```

**After:** 4 jobs with clear dependency chain
```yaml
jobs:
  nix-check:         # Phase 1: Validate
  nix-build:         # Phase 2: Build (needs: nix-check)
  docker-build:      # Phase 3: Docker (needs: nix-build)
  integration-test:  # Phase 4: Test (needs: docker-build)
```

**Dependency Flow:**
```
nix-check (Phase 1: Validate flake)
    ↓
nix-build (Phase 2: Build Python app)
    ↓
docker-build (Phase 3: Build Docker image)
    ↓
integration-test (Phase 4: Run smoke tests)
```

### 2. Cachix Binary Cache Integration

**Changes:**
- Replaced `DeterminateSystems/nix-installer-action` with `cachix/install-nix-action@v27`
- Added `cachix/cachix-action@v15` in all jobs
- Removed `permissions.id-token` requirement (not needed for Cachix)

**Before (Magic Nix Cache - deprecated):**
```yaml
- uses: DeterminateSystems/nix-installer-action@main
- uses: DeterminateSystems/magic-nix-cache-action@main
```

**After (Cachix):**
```yaml
- uses: cachix/install-nix-action@v27
  with:
    nix_path: nixpkgs=channel:nixos-unstable
- uses: cachix/cachix-action@v15
  with:
    name: llt-assistant-backend
    authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'
```

**Benefits:**
- ✅ 5GB free storage for open source projects
- ✅ Unlimited bandwidth with CloudFlare CDN
- ✅ Long-term availability (Magic Nix Cache shuts down Feb 2025)
- ✅ Better control over cache management
- ✅ Automatic garbage collection
- ✅ Deduplication (cache.nixos.org entries don't count)

### 3. Job Separation

**Before:** Single monolithic job doing everything
- nix-build: 11 steps (build + docker + test)
- nix-check: 2 steps (validation only)

**After:** Clear separation of concerns
- `nix-check`: Validate flake syntax and dependencies (2 steps)
- `nix-build`: Build Python application only (4 steps)
- `docker-build`: Build Docker image only (4 steps)
- `integration-test`: Run smoke tests only (8 steps)

**Benefits:**
- ✅ Clear responsibility boundaries
- ✅ Easier debugging (know which phase failed)
- ✅ Faster failure detection
- ✅ Can skip phases if needed

### 4. Artifacts for Build Outputs

**Artifacts created:**
1. `nix-app` artifact:
   - Contains: Built Python application (`result/`)
   - Retention: 1 day
   - Size: ~100 MB
   - Used by: Later inspection (optional)

2. `docker-image` artifact:
   - Contains: Docker image tarball
   - Retention: 1 day
   - Size: ~500 MB
   - Used by: `integration-test` job

**Implementation:**
```yaml
# In nix-build job
- name: Upload application artifact
  uses: actions/upload-artifact@v4
  with:
    name: nix-app
    path: result
    retention-days: 1

# In docker-build job
- name: Save Docker image to tarball
  run: cp result docker-image.tar.gz

- name: Upload Docker image artifact
  uses: actions/upload-artifact@v4
  with:
    name: docker-image
    path: docker-image.tar.gz
    retention-days: 1

# In integration-test job
- name: Download Docker image artifact
  uses: actions/download-artifact@v4
  with:
    name: docker-image
```

**Benefits:**
- ✅ Avoid rebuilding in subsequent jobs
- ✅ Docker image built once, tested separately
- ✅ Reduced computational overhead

## Performance Impact

### Estimated Time Comparison

**Before (parallel, no cache):**
| Job | First Run | Subsequent Runs |
|-----|-----------|-----------------|
| nix-check | 5 min | 5 min |
| nix-build (all) | 11 min | 11 min |
| **Total** | **11 min** (parallel) | **11 min** |

**After (sequential, with Magic Nix Cache):**
| Job | First Run | Subsequent Runs (Cached) |
|-----|-----------|--------------------------|
| nix-check | 5 min | 2 min (↓60%) |
| nix-build | 5 min | 2 min (↓60%) |
| docker-build | 3 min | 1.5 min (↓50%) |
| integration-test | 3 min | 3 min |
| **Total** | **16 min** (sequential) | **8.5 min** (↓47%) |

**Key Observations:**
- First run is **+5 min slower** due to sequential execution
- Subsequent runs are **-2.5 min faster** (47% improvement) due to caching
- Most projects will see cached runs more frequently

### Resource Savings

**Computational:**
- ✅ No redundant Nix installations (Magic Nix Cache optimizes this)
- ✅ Docker image built once per workflow run
- ✅ Python dependencies cached across jobs

**Runner Minutes:**
- ✅ Early failure detection saves runner time
  - Example: Flake syntax error stops at nix-check (5 min vs 16 min)
  - Example: Build failure stops at nix-build (10 min vs 16 min)

**GitHub Actions Costs:**
- ✅ Fail-fast reduces wasted runner minutes
- ✅ Caching reduces monthly usage
- ✅ Clearer logs reduce debugging time

## Fail-Fast Strategy

The optimized pipeline implements a fail-fast strategy:

```
❌ Flake syntax error → Stop at nix-check (save 11 min)
    ↓
❌ Build error → Stop at nix-build (save 6 min)
    ↓
❌ Docker build error → Stop at docker-build (save 3 min)
    ↓
❌ Integration test failure → Reported in integration-test
```

**Benefits:**
- ✅ Faster feedback loop (know immediately if flake is invalid)
- ✅ Reduced resource consumption (don't build if check fails)
- ✅ Clearer error messages (know exactly which phase failed)
- ✅ Developer time savings (fix issues earlier)

## Testing Recommendations

### Local Testing (Optional)

Before pushing, you can test the workflow locally using [act](https://github.com/nektos/act):

```bash
# Install act (macOS)
brew install act

# Test nix-check job
act -j nix-check

# Test entire workflow
act push
```

### Remote Testing

1. **Push to `feat/nix-poc` branch:**
   ```bash
   git push origin feat/nix-poc
   ```

2. **Monitor GitHub Actions:**
   - Navigate to: https://github.com/YOUR_ORG/LLT-Assistant-Backend/actions
   - Click on the latest workflow run
   - Observe job execution order

3. **Verify improvements:**
   - ✅ Jobs run sequentially (not parallel)
   - ✅ Each job shows "Setup Magic Nix Cache" step
   - ✅ Build times decrease in subsequent runs
   - ✅ Artifacts are created and downloaded correctly

4. **Test fail-fast behavior:**
   - Introduce a flake syntax error → Should stop at nix-check
   - Introduce a build error → Should stop at nix-build
   - Introduce a Docker error → Should stop at docker-build

## Troubleshooting

### Issue: "Actions artifact not found"

**Cause:** Artifact retention expired or job didn't complete successfully

**Solution:**
```yaml
# Increase retention if needed
retention-days: 7  # Instead of 1
```

### Issue: "Magic Nix Cache not working" or "FlakeHub registration required"

**Error message:**
```
FlakeHub registration required.
Unable to authenticate to FlakeHub.
```

**Cause:** Missing GitHub Actions permissions for Magic Nix Cache authentication

**Solution:**
The workflow already includes the required permissions at the top level:
```yaml
# Add permissions to workflow (at workflow level, not job level)
permissions:
  contents: read
  id-token: write  # Required for Magic Nix Cache authentication
```

**Important:** You do NOT need to register at FlakeHub.com for basic usage. The Magic Nix Cache is free for public repositories and only requires proper GitHub Actions permissions.

### Issue: "Docker load failed"

**Cause:** Artifact download may have corrupted the tarball

**Solution:**
```bash
# Verify tarball integrity in docker-build job
- name: Verify tarball
  run: |
    ls -lh result
    file result
```

## Future Improvements

### Potential Optimizations

1. **Parallel integration tests:**
   - Split smoke tests into multiple jobs
   - Run health check and API docs test in parallel

2. **Matrix builds:**
   - Test multiple Nix channels (stable, unstable)
   - Test multiple Python versions

3. **Cachix integration:**
   - Share cache across repositories
   - Faster builds for team members

4. **Conditional execution:**
   - Skip Docker build if no code changes
   - Use `paths` filter in workflow triggers

### Example: Parallel tests

```yaml
integration-test-health:
  needs: docker-build
  steps:
    - run: test health endpoint

integration-test-docs:
  needs: docker-build
  steps:
    - run: test docs endpoint
```

## References

- [Magic Nix Cache Documentation](https://github.com/DeterminateSystems/magic-nix-cache-action)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Nix Flake Check Command](https://nixos.org/manual/nix/stable/command-ref/new-cli/nix3-flake-check.html)
- [DeterminateSystems Nix Installer](https://github.com/DeterminateSystems/nix-installer-action)

## Version History

- **v1.0** (2025-11-26): Initial optimization with 4-phase pipeline and Magic Nix Cache
- Project: LLT Assistant Backend
- Branch: `feat/nix-poc`
- Workflow File: `.github/workflows/nix-build.yml`
