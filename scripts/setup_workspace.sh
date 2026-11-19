#!/bin/sh
# Set up a module workspace: symlink tools into the module dir so the
# harness (which expects tools/ and orig/ as siblings) works per module.
# Usage: ./scripts/setup_workspace.sh modules/<name>
set -e
MOD="$1"
[ -d "$MOD" ] || { echo "no such module dir: $MOD"; exit 1; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$MOD/orig" "$MOD/build" "$MOD/match"
for t in "$ROOT"/tools/*; do
  b=$(basename "$t")
  [ "$b" = "__pycache__" ] && continue
  [ "$b" = "link" ] && continue
  ln -sf "../../tools/$b" "$MOD/tools_$b" 2>/dev/null || true
done
ln -sfn ../../tools/link "$MOD/tools_link" 2>/dev/null || true
# the tools resolve ROOT from their own path, so give the module its own view
ln -sfn ../tools "$MOD/tools" 2>/dev/null || true
echo "workspace ready: $MOD  (put your decrypted .prx in $MOD/orig/)"
