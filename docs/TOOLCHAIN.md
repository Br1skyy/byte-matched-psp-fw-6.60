# matching toolchain derivation

## Verdict

**GCC 3.3.6 (vanilla) configured `--target=mipsel-elf`, with:**

- Flags: **`-O3 -mips2 -G0 -mabi=eabi`**
- One local patch: **EABI stack alignment forced to 16 bytes**
  (`gcc/config/mips/mips.h`, `STACK_BOUNDARY`: drop `ABI_EABI` from the
  64-bit branch so EABI gets 128). Retail frames are always multiples
  of 16 and never reserve the o32 16-byte argument-home area.

This reproduces Sony's firmware codegen byte-for-byte on everything
tested that doesn't use Allegrex bitfield instructions.

## Evidence (all against retail 6.60 bytes extracted from EBOOT.PBP)

| Test | Result |
|---|---|
| Division idiom (`div; beqzl rt,+1; break 0x7`) - threadman fingerprint | byte-exact, zero `teq` |
| `sceClockgenSetProtocol` (clockgen 0x438) | byte-exact |
| `sceClockgenGetRevision` (0x448) | byte-exact |
| `sceClockgenGetRegValue` (0x454) | byte-exact |
| `sceClockgenAudioClk{Enable,Disable}` / `sceClockgenLeptonClk{Enable,Disable}` | byte-exact modulo the `jal` immediate (unlinked reloc placeholder; resolves when the callee is placed at its module offset) |

Versions eliminated: 2.95.2/2.95.3 (register allocation off), 3.2.3
(worse scheduling + wrong frames), 3.4.6 (emits `teq`, tail-calls).
Flags eliminated: `-O2` (scheduling differs), `-mno-abicalls`/`-G0` (no
effect on tested shapes - kept for PRX correctness), plain o32
(`-mabi=32` reserves the 16-byte arg home area → wrong frames).

## Known residual (Sony backend patches)

A minority of functions use `ins`/`ext` (SPECIAL3 bitfield, Allegrex
extension; e.g. clockgen 0x1a8, 0x344, 0x598). Vanilla GCC cannot emit
these - options: port the Allegrex `insv`/`extzv` patterns into 3.3.6's
mips.md, or emit via inline `asm(".word 0x7c...")` per site.

## Reproduce

Container: `etch386` (i386 debian/eol:etch; see tools/ scripts).

```
podman run --rm -v $PWD:/build:Z etch386 \
  /build/prefix336/bin/mipsel-elf-gcc -c -O3 -mips2 -G0 -mabi=eabi ...
```

- Build scripts: `tools/build-33.sh` (initial), `tools/build-336b.sh` (alignment patch, incremental)
- Toolchains: `toolchain-build/prefix336/` (primary), `prefix/`, `prefix2952/`, `prefix323/`, `prefix346/` (eliminated candidates)
- Match harness: `toolchain-build/matrix3.sh`, `matrix4.sh`
- Ground truth: `fw660/EBOOT/F0/kd/*.prx`, disassembly `toolchain-build/clockgen.dis`

## Method notes

- Source shape matters: retail uses tail-returns (`return f(...)` keeps
  callee result in v0) and single-call-site control flow; iterate source
  shapes until scheduling matches (standard decomp workflow).
- `sceClockgenAudioClkSetFreq` still needs source iteration (closest:
  nested `mode` variable form).
- To match `jal` immediates, compile whole-module source with functions
  in retail order and link with a script that reproduces the PRX layout.
