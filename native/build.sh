#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$DIR/build"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

cmake -S "$DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -- -j"$(nproc)"

echo "Binary: $BUILD_DIR/csvbench"
