#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

rm -rf node_modules dist
npm install
npx electron-builder --linux AppImage --x64

echo "AppImage output:"
ls -la "$DIR"/dist/*.AppImage
