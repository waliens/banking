#!/bin/bash
set -euo pipefail

# Release script: create git tag, build & push Docker images, push tag to remote.
#
# Usage: ./scripts/release.sh <VERSION>
# Example: ./scripts/release.sh 4.0.0
#
# Steps:
#   1. Validate version format and check no newer tag exists on remote
#   2. Create local git tag
#   3. Build frontend & backend Docker images (tagged :latest and :VERSION)
#   4. Push images to the logged-in container registry
#   5. Push git tag to remote

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_IMAGE="rmormont/banking-v2-backend"
FRONTEND_IMAGE="rmormont/banking-v2-frontend"

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <VERSION>"
  echo "Example: $0 4.0.0"
  exit 1
fi

# Validate semver-like format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Error: VERSION must be in semver format (e.g. 4.0.0)"
  exit 1
fi

# Check for uncommitted changes
if ! git -C "$V2_DIR" diff --quiet HEAD 2>/dev/null; then
  echo "Error: there are uncommitted changes. Commit or stash before releasing."
  exit 1
fi

# Fetch latest tags from remote
echo "Fetching tags from remote..."
git -C "$V2_DIR" fetch --tags

# Check that no newer tag exists on the remote
LATEST_REMOTE_TAG=$(git -C "$V2_DIR" tag --sort=-v:refname | head -1)
if [ -n "$LATEST_REMOTE_TAG" ]; then
  # Compare versions: sort both and check which comes last
  HIGHEST=$(printf '%s\n%s' "$VERSION" "$LATEST_REMOTE_TAG" | sort -V | tail -1)
  if [ "$HIGHEST" != "$VERSION" ]; then
    echo "Error: remote already has a newer tag ($LATEST_REMOTE_TAG >= $VERSION)"
    exit 1
  fi
  if [ "$HIGHEST" = "$LATEST_REMOTE_TAG" ] && [ "$VERSION" = "$LATEST_REMOTE_TAG" ]; then
    echo "Error: tag $VERSION already exists"
    exit 1
  fi
fi

echo "==> Releasing version $VERSION"

# Create git tag
echo ""
echo "Creating git tag v$VERSION..."
git -C "$V2_DIR" tag "v$VERSION"

# Build images
echo ""
echo "Building backend..."
docker build \
  -t "$BACKEND_IMAGE:latest" \
  -t "$BACKEND_IMAGE:$VERSION" \
  "$V2_DIR/backend/"

echo ""
echo "Building frontend..."
docker build \
  -t "$FRONTEND_IMAGE:latest" \
  -t "$FRONTEND_IMAGE:$VERSION" \
  "$V2_DIR/frontend/"

# Push images
echo ""
echo "Pushing images..."
docker push "$BACKEND_IMAGE:latest"
docker push "$BACKEND_IMAGE:$VERSION"
docker push "$FRONTEND_IMAGE:latest"
docker push "$FRONTEND_IMAGE:$VERSION"

# Push git tag
echo ""
echo "Pushing tag v$VERSION to remote..."
git -C "$V2_DIR" push origin "v$VERSION"

echo ""
echo "Release $VERSION complete!"
echo "  - Images pushed: $BACKEND_IMAGE:$VERSION, $FRONTEND_IMAGE:$VERSION"
echo "  - Git tag pushed: v$VERSION"
