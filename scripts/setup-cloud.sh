#!/usr/bin/env bash
# Tested in this cloud image. Installs project dependencies without root.
set -euo pipefail
cd "$(dirname "$0")/.."
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/workspace/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/workspace/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/workspace/.local/share}"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" /workspace/tools
for tool in node npm cc kicad-cli chromium curl tar sha256sum; do
  command -v "$tool" >/dev/null || { echo "Missing base-image dependency: $tool" >&2; exit 1; }
done
/usr/bin/python3 -c 'import pcbnew'
python3 -c 'import ctypes,ctypes.util; ctypes.CDLL(ctypes.util.find_library("ngspice") or "libngspice.so.0")'
sdk_archive=/workspace/tools/wasi-sdk-25.0-x86_64-linux.tar.gz
sdk_dir=/workspace/tools/wasi-sdk-25.0-x86_64-linux
if [ ! -x "$sdk_dir/bin/clang" ]; then
  curl -fL --retry 2 https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-25/wasi-sdk-25.0-x86_64-linux.tar.gz -o "$sdk_archive"
  echo "52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c  $sdk_archive" | sha256sum -c -
  tar -xzf "$sdk_archive" -C /workspace/tools
fi
npm ci --ignore-scripts --cache /workspace/.cache/npm
python3 scripts/build.py
node scripts/bundle.mjs
