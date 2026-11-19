#!/bin/sh
# OO batch corpus regression: run every tm*.c under prefix336 (base) or
# prefix336b (patched) and save per-file harness output for comparison.
cd /home/karin/Downloads/psp-tm
mode=$1
if [ "$mode" = base ]; then H="python3 tools/match.py"; D=build/regress/base
else H="python3 tools/match_oo.py"; D=build/regress/patched; fi
mkdir -p $D
for f in match/threadman/tm*.c; do
  b=$(basename $f .c)
  timeout 300 $H $f > $D/$b.txt 2>&1 || true
done
echo DONE_$mode
