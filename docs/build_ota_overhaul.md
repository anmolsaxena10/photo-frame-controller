# Build & OTA Overhaul Plan

## Problem

- Full OS image build takes 30-60 minutes via pi-gen on QEMU-emulated arm64
- Every code change triggers a full rebuild even when only app logic changed
- OTA updater is broken (no asset uploaded to releases, no pip install after update)
- No separation between infrastructure changes and application changes

## Strategy: Two-Track Releases

### Track 1: OTA App Update (fast, every tag)

A lightweight zip containing only the application code. Delivered to running devices via the OTA updater.

**Contents of OTA zip:**
- `app/`
- `web/`
- `config/`
- `requirements.txt`
- `post-update.sh` (optional hook for migrations)

**Build time:** ~10 seconds

### Track 2: Full OS Image (slow, only when needed)

Complete SD card image via pi-gen. Only needed when system-level dependencies change.

**Triggers (file-path based):**
- `image-builder/**`
- `service/**`
- `requirements.txt` (new native deps may need system libraries)
- `.github/workflows/build-image.yml`

**Build time:** 30-60 minutes (with caching)

## Workflow Design

```yaml
# On every tag v*.*.*:
#   1. Always build + upload OTA zip as release asset
#   2. Conditionally build full OS image if infra files changed
```

### File-path detection logic

Compare the tag's commit against the previous tag. If diff includes any infra file paths, trigger full image build. Otherwise, OTA zip only.

**Infra paths:**
- `image-builder/**`
- `service/**`
- `requirements.txt`
- `.github/workflows/build-image.yml`

**App-only paths (OTA sufficient):**
- `app/**`
- `web/**`
- `config/**`
- `docs/**`
- `README.md`

### Examples

| Change | What runs |
|--------|-----------|
| Bug fix in `app/controller/scheduler.py` | OTA zip only |
| New pip dependency in `requirements.txt` | OTA zip + full image |
| Updated `00-packages` in image-builder | OTA zip + full image |
| New web page in `web/` | OTA zip only |
| Changed systemd service file | OTA zip + full image |

## OTA Updater Changes

### Current behavior (broken)
1. Queries GitHub API for latest release
2. Looks for `.zip` asset → finds none (we only upload OS image artifact)
3. Falls back to `zipball_url` (entire source) → mostly works but no pip install

### Proposed behavior
1. Query GitHub API for latest release
2. Look for asset named `photo-frame-controller-v{version}.zip`
3. Download, extract, rsync into `/opt/photo-frame-controller/` excluding `data/`, `venv/`, `.git/`
4. Run `venv/bin/pip install -r requirements.txt` to update dependencies
5. Restart service

### Asset naming convention
```
photo-frame-controller-v1.2.3.zip
```

## Cache Key Fix

### Current (suboptimal)
```yaml
key: pigen-${{ runner.os }}-${{ hashFiles('image-builder/config', 'image-builder/stage-photo-frame/**') }}
```

This includes app code (copied into stage-photo-frame by build.sh), so any app change invalidates the rootfs cache.

### Proposed
```yaml
key: pigen-${{ runner.os }}-${{ hashFiles('image-builder/config', 'image-builder/stage-photo-frame/00-install/00-packages', 'image-builder/stage-photo-frame/00-install/00-run.sh', 'requirements.txt') }}
```

Only infrastructure files that affect the rootfs. App code gets copied fresh each time but doesn't invalidate the cached stages 0-2.

## Why We Keep Stage 2

Stage 2 ("Lite") provides:
- WiFi/Bluetooth stack (required by our app)
- NTP (needed for OTA version checks)
- dphys-swapfile (Pi Zero 2W has 512MB RAM — pip OOMs without swap)
- Python 3 (our runtime)
- User account setup + sudo
- Locale/timezone configuration

Removing it would require manually replicating all of this in the custom stage — more work, not faster.

## Implementation Checklist

- [ ] New workflow: `.github/workflows/release-ota.yml`
  - Builds OTA zip on every tag
  - Uploads as named release asset
- [ ] Modified: `.github/workflows/build-image.yml`
  - Add path-based conditional (compare against previous tag)
  - Fix cache key to exclude app code
  - Keep manual dispatch trigger for forcing full builds
- [ ] Modified: `app/controller/ota_updater.py`
  - Look for named asset `photo-frame-controller-v{version}.zip`
  - Run `pip install -r requirements.txt` after rsync
  - Add timeout and error handling for pip
- [ ] Optional: `post-update.sh` hook
  - Runs after rsync, before service restart
  - Can handle migrations, cache clearing, etc.
