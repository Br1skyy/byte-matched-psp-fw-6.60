#!/bin/sh
# Reproduce the matching toolchain from scratch (idempotent).
# Requires: podman. Produces: ../toolchain-build/prefix336/bin/mipsel-elf-gcc
# (run from anywhere; operates on the sibling toolchain-build directory)
set -e
W=$(cd "$(dirname "$0")/../.." && pwd)
TB=$W/toolchain-build
mkdir -p $TB/src $TB/prefix
[ -f $TB/src/gcc-3.3.6.tar.bz2 ] || curl -sL -o $TB/src/gcc-3.3.6.tar.bz2 \
    https://ftp.gnu.org/gnu/gcc/gcc-3.3.6/gcc-3.3.6.tar.bz2
[ -f $TB/src/binutils-2.16.1.tar.bz2 ] || curl -sL -o $TB/src/binutils-2.16.1.tar.bz2 \
    https://ftp.gnu.org/gnu/binutils/binutils-2.16.1.tar.bz2
cat > $TB/rebuild.sh <<'EOS'
set -e
export PATH=/build/prefix/bin:$PATH
cd /build/src
[ -d binutils-2.16.1 ] || tar xjf binutils-2.16.1.tar.bz2
if [ ! -x /build/prefix/bin/mipsel-elf-as ]; then
  mkdir -p b-binutils && cd b-binutils
  ../binutils-2.16.1/configure --target=mipsel-elf --prefix=/build/prefix --disable-nls > /dev/null 2>&1
  make -j4 > /build/bu.log 2>&1 && make install > /dev/null 2>&1
  cd ..
fi
[ -d gcc-3.3.6 ] || tar xjf gcc-3.3.6.tar.bz2
# Sony-equivalent stack alignment: EABI frames 16-byte
sed -i 's@mips_abi == ABI_32 || mips_abi == ABI_O64 || mips_abi == ABI_EABI@mips_abi == ABI_32 || mips_abi == ABI_O64@' \
  gcc-3.3.6/gcc/config/mips/mips.h
mkdir -p b-gcc336 && cd b-gcc336
../gcc-3.3.6/configure --target=mipsel-elf --prefix=/build/prefix336 \
    --enable-languages=c --disable-nls --disable-shared --disable-threads \
    --with-newlib --without-headers --with-gnu-as --with-gnu-ld > /dev/null 2>&1
mkdir -p /build/prefix336/mipsel-elf/bin
for t in as ar ld nm ranlib objdump; do ln -sf /build/prefix/bin/mipsel-elf-$t /build/prefix336/mipsel-elf/bin/$t; done
make -j4 all-gcc MAKEINFO=true > /build/gcc.log 2>&1
make install-gcc MAKEINFO=true > /dev/null 2>&1
/build/prefix336/bin/mipsel-elf-gcc --version | head -1
EOS
podman pull --arch i386 docker.io/debian/eol:etch >/dev/null 2>&1 || true
IMG=$(podman images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | awk '$1=="debian/eol:etch"{print $2}' | head -1)
podman tag $IMG etch386
printf '#include <unistd.h>\nint main(int c,char**v){syscall(136,8);execvp(v[1],v+1);return 1;}\n' > /tmp/sa32.c
podman run --rm -v $TB:/build:Z -v $W/tools:/tools:Z etch386 sh -c \
  "echo 'deb http://archive.debian.org/debian etch main' > /etc/apt/sources.list; \
   apt-get update >/dev/null 2>&1; apt-get install -y --force-yes -qq build-essential bzip2 patch >/dev/null 2>&1; \
   gcc -o /tmp/sa32 /tmp/sa32.c 2>/dev/null || { printf '#include <unistd.h>\\nint main(int c,char**v){syscall(136,8);execvp(v[1],v+1);return 1;}\\n' > /tmp/sa32.c; gcc -o /tmp/sa32 /tmp/sa32.c; }; \
   /tmp/sa32 sh /build/rebuild.sh"
