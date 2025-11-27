# Cachix Setup Guide for LLT Assistant Backend

This document explains how to set up Cachix binary cache for the LLT Assistant Backend project.

---

## Why Cachix?

Cachix is a binary cache service for Nix that provides:
- ✅ **5GB free storage** for open source projects
- ✅ **Unlimited bandwidth** on all plans
- ✅ **CloudFlare CDN** for fast global access
- ✅ **Long-term availability** (unlike Magic Nix Cache which will shut down in Feb 2025)
- ✅ **Automatic garbage collection** when storage limit is reached
- ✅ **Deduplication** (entries from cache.nixos.org don't count toward your quota)

---

## Setup Steps

### 1. Create Cachix Account

1. Go to [https://app.cachix.org](https://app.cachix.org)
2. Sign up using your GitHub account
3. Verify your email

### 2. Create a Binary Cache

1. After logging in, click **"Create binary cache"**
2. Enter cache name: `llt-assistant-backend`
3. Select visibility: **Public** (for open source) or **Private** (requires paid plan)
4. Click **"Create"**

### 3. Get Authentication Token

1. In Cachix dashboard, go to your cache: `llt-assistant-backend`
2. Click **"Settings"** tab
3. Scroll to **"Auth tokens"** section
4. Click **"Generate token"**
5. Copy the token (starts with `eyJ...`)

**Important:** Keep this token secure! It allows write access to your cache.

### 4. Add Token to GitHub Secrets

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/LLT-Assistant-Backend`
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `CACHIX_AUTH_TOKEN`
5. Value: Paste your Cachix token
6. Click **"Add secret"**

### 5. Verify Configuration

The workflow file `.github/workflows/nix-build.yml` is already configured to use Cachix:

```yaml
- name: Setup Cachix
  uses: cachix/cachix-action@v15
  with:
    name: llt-assistant-backend
    authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'
```

### 6. Test the Setup

1. Push a commit to the `dev` branch:
   ```bash
   git push origin dev
   ```

2. Go to **Actions** tab in GitHub
3. Watch the workflow run
4. Check for successful Cachix authentication in logs:
   ```
   Cachix: ... configured
   ```

5. After the build completes, verify in Cachix dashboard:
   - Go to `https://app.cachix.org/cache/llt-assistant-backend`
   - You should see new store paths uploaded

---

## Using the Cache Locally

To use the cache on your local machine:

```bash
# Install Cachix CLI
nix-env -iA cachix -f https://cachix.org/api/v1/install

# Use the cache (read-only, no auth needed for public caches)
cachix use llt-assistant-backend

# Now Nix will fetch from your cache automatically
nix build .
```

For private caches, authenticate first:
```bash
cachix authtoken <YOUR_AUTH_TOKEN>
cachix use llt-assistant-backend
```

---

## Cache Management

### View Cache Statistics

Visit: `https://app.cachix.org/cache/llt-assistant-backend`

You can see:
- Storage usage (out of 5GB free quota)
- Number of store paths
- Bandwidth usage
- Recent uploads

### Garbage Collection

Cachix automatically removes least recently used (LRU) entries when you reach 85% of storage limit. You'll receive a warning email at 85%.

### Manual Pin (Prevent Deletion)

To keep important store paths from being garbage collected:

```bash
cachix pin llt-assistant-backend <store-path>
```

---

## Troubleshooting

### Error: "Authentication failed"

**Cause:** `CACHIX_AUTH_TOKEN` secret is missing or incorrect

**Solution:**
1. Verify the secret exists in GitHub repository settings
2. Regenerate token in Cachix dashboard if needed
3. Update the GitHub secret with new token

### Error: "Cache 'llt-assistant-backend' not found"

**Cause:** Cache name mismatch or cache doesn't exist

**Solution:**
1. Verify cache exists in Cachix dashboard
2. Check cache name matches exactly in workflow file
3. Ensure cache visibility is set to "Public" for CI access

### Builds Not Using Cache

**Cause:** Cache not configured in Nix settings

**Solution:**
```bash
# Add to ~/.config/nix/nix.conf
substituters = https://cache.nixos.org https://llt-assistant-backend.cachix.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= llt-assistant-backend.cachix.org-1:...
```

Get your public key from Cachix dashboard → Settings → Public Key

---

## Cost Considerations

### Free Tier (5GB)

For this project, 5GB should be sufficient because:
- Nix deduplicates entries
- cache.nixos.org entries don't count
- Automatic garbage collection
- Typical project uses 1-2GB

### If You Need More Storage

Upgrade to paid plan if you consistently exceed 5GB:
- **Starter**: 50 GiB - ~$10-20/month
- **Standard**: 250 GiB - ~$40-50/month

---

## Migration from Magic Nix Cache

The workflow has been migrated from Magic Nix Cache to Cachix because:
- Magic Nix Cache will stop working on **February 1st, 2025** (GitHub is shutting down the API)
- Cachix is a long-term, reliable solution
- 5GB free tier is sufficient for most projects
- Better control over cache management

### Changes Made

1. Replaced `DeterminateSystems/nix-installer-action` with `cachix/install-nix-action@v27`
2. Replaced `DeterminateSystems/magic-nix-cache-action` with `cachix/cachix-action@v15`
3. Removed `permissions.id-token` requirement (Cachix doesn't need it)
4. Added `CACHIX_AUTH_TOKEN` secret requirement

---

## References

- [Cachix Documentation](https://docs.cachix.org/)
- [Cachix Pricing](https://www.cachix.org/pricing)
- [cachix/cachix-action on GitHub](https://github.com/cachix/cachix-action)
- [Nix Binary Cache Concepts](https://nix.dev/manual/nix/stable/package-management/binary-cache-substituter.html)

---

**Last Updated:** 2025-11-27
**Version:** 1.0
**Project:** LLT Assistant Backend
**Branch:** `feat/nix-poc`
