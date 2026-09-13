#!/usr/bin/env bash
#
# cleanup-ghcr-untagged.sh
# Safely bulk-deletes untagged image versions from GitHub Container Registry (ghcr.io).
#
# Usage:
#   # 1. Ensure your token has 'delete:packages' and 'read:packages' scope:
#   #    gh auth refresh -s delete:packages,read:packages
#   # 2. Run:
#   ./scripts/cleanup-ghcr-untagged.sh [owner] [package_name]
#
# Defaults:
#   owner: kreier
#   package_name: status

set -euo pipefail

OWNER="${1:-kreier}"
PACKAGE_NAME="${2:-status}"

echo "=== GHCR Untagged Version Cleanup ==="
echo "Target: ghcr.io/${OWNER}/${PACKAGE_NAME}"

# Verify gh CLI is installed
if ! command -v gh &>/dev/null; then
    echo "Error: GitHub CLI ('gh') is required. Install from https://cli.github.com"
    exit 1
fi

echo "Fetching package versions..."
# Determine if target is user or org
API_PATH="users/${OWNER}/packages/container/${PACKAGE_NAME}/versions"
if ! gh api "$API_PATH" --jq '.[0].id' &>/dev/null; then
    API_PATH="orgs/${OWNER}/packages/container/${PACKAGE_NAME}/versions"
fi

# Fetch untagged versions (per_page=100)
UNTAGGED_IDS=$(gh api "${API_PATH}?per_page=100" \
    --jq '.[] | select(.metadata.container.tags | length == 0) | .id')

if [ -z "$UNTAGGED_IDS" ]; then
    echo "No untagged versions found for ${OWNER}/${PACKAGE_NAME}."
    exit 0
fi

COUNT=$(echo "$UNTAGGED_IDS" | wc -l)
echo "Found ${COUNT} untagged version(s) in current page."

read -rp "Do you want to delete these ${COUNT} untagged version(s)? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

DELETED=0
for VID in $UNTAGGED_IDS; do
    echo -n "Deleting version ${VID}... "
    if gh api -X DELETE "${API_PATH}/${VID}" &>/dev/null; then
        echo "OK"
        ((DELETED++))
    else
        echo "FAILED"
    fi
done

echo "Deleted ${DELETED} of ${COUNT} untagged versions."
if [ "$DELETED" -eq 100 ]; then
    echo "Note: Re-run this script to delete remaining untagged versions (API paginates at 100)."
fi
