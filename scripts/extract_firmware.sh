#!/bin/sh
# Extract modules from your own 6.60 EBOOT.PBP using pspdecrypt (containerized).
# Usage: ./scripts/extract_firmware.sh /path/to/EBOOT.PBP /path/to/output/dir
set -e
PBP="$1"; OUT="$2"
[ -f "$PBP" ] || { echo "usage: extract_firmware.sh EBOOT.PBP outdir"; exit 1; }
mkdir -p "$OUT"
docker=podman
$docker run --rm -v "$OUT:/work:Z" -v "$PBP:/data/EBOOT.PBP:ro,Z" \
  docker.io/library/alpine:3.19 sh -c \
  "apk add --no-cache libstdc++ libgcc zlib libcrypto3 >/dev/null 2>&1; \
   cd /work && cp /data/EBOOT.PBP . && /x/pspdecrypt -o /work EBOOT.PBP" || {
  echo "note: mount a dir containing the pspdecrypt binary at /x for this to work"
  echo "build it from github.com/John-K/pspdecrypt"
  exit 1; }
echo "extracted to $OUT (flash0 modules under EBOOT/F0/)"
