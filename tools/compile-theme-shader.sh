#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/branding/shaders/recolor.frag"
OUTPUT="$ROOT/branding/shaders/recolor.frag.qsb"

if ! command -v qsb-qt6 >/dev/null 2>&1; then
  echo "Qt Shader Tools is required (Fedora package: qt6-qtshadertools-devel)." >&2
  exit 1
fi

test -s "$SOURCE"
qsb-qt6 -o "$OUTPUT" "$SOURCE"
test -s "$OUTPUT"
echo "Compiled LEOS accent shader: $OUTPUT"
