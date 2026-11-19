# byte-matched-psp-fw-6.60

PSP 6.60 kernel modules reconstructed from source that builds byte
identical to retail. no sony code in this repo, and the builds never read
retail bytes, the from scratch mode generates everything (code, tables,
relocations) from source derived material.

| module | functions | words | sha1 |
|---|---|---|---|
| threadman | 331 | 24982 | 32e4457c8018af2f168bb931c07ab01b88b836af |
| clockgen | 17 | 437 | 56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199 |

modules live under modules/<name>. each has match/ (source, split by
subsystem), map/, INTERNALS.md (the topic-organized decode reference),
results/ARCHIVE.md (unedited batch reports) and a PROGRESS.md. the
INTERNALS.md structure is the template in docs/INTERNALS-TEMPLATE.md.

## how

the firmware compiler was identified as gcc 3.3.6 with -O3 -mips2 -G0
-mabi=eabi plus two backend behaviors that were patched back in (see
patches/). every function is then diffed against retail until it matches.
build the toolchain with tools/build-toolchain.sh (needs podman), then per
module:

```
cd modules/threadman
python3 tools/match.py match/threadman/timer.c   # smoke test
python3 tools/link/build_prx.py --no-retail
sha1sum build/link/threadman-linked.prx
```

more detail in docs/. dont redistribute built prx files.
