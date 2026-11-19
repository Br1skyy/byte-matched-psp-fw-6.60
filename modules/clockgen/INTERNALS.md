# clockgen internals

Reference distilled from the batch results (results/ARCHIVE.md) and the
matched sources in match/. All facts trace to a result file, the matched
source comments, or the retail disassembly. Retail virtual addresses are
cited as @0xNNNN.

## contents

1. Overview
2. Boot and init sequence
3. Module data block map
4. CY27040 register model
5. I2C framing
6. Spectrum spreading ladders
7. API semantics
8. Error code catalog
9. Quirks and toolchain notes

---

## 1. Overview

clockgen.prx is the clock generator driver: a CY27040 programmable clock
chip on I2C, behind a small export surface that sets bus clocks, audio
clock frequency, Lepton (DSP) clock, protocol, and spectrum spreading.

| item | value |
|---|---|
| file size | 2836 bytes |
| text | 0x000..0x6D3 (437 words in 17 functions) |
| import stubs | 0x6D4..0x723, 10 two-word veneers (load-patched) |
| export entries | 0x734 / 0x744 |
| import entries | 0x75C..0x798 |
| SceModuleInfo | 0x7A0 |
| rodata + strings + NID tables | .. 0x8E8 |
| RW data (ph1) | vaddr 0x8F0, 80 bytes |
| exports | 14 (plus 3 matched internals) |
| from-scratch SHA1 | 56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199 |

Imports (via the veneer table): threadman mutex Create/Delete/Lock/
TryLock/Unlock, I2c TransmitReceive/SetClock/Transmit, SysEvent
Register/Unregister.

## 2. Boot and init sequence

- module_start @0x2B4 (syslib entry, ELF e_entry, 27w): calls the inlined
  init, then `g_Cy27040.protocol = 1` (hoisted into the Setup call's
  delay slot), then sceClockgenSetup(); returns 0.
- clockgen_init (inlined into module_start and sceClockgenInit @0x398;
  -O3 inlines the static into both callers): `sceI2cSetClock(4, 4)`;
  `sceKernelCreateMutex("SceClockgen", 1, 0, 0)` -> g_Cy27040.mutexId
  (negative result returned verbatim); RegisterSysEventHandler
  (&g_ClockGenSysEv).
- sceClockgenEnd @0x3EC (also inlined into module_reboot_before
  @0x320): deletes the mutex when the id >= 0, resets the id to -1,
  unregisters the event handler.
- _sceClockgenSysEventHandler @0x53C (40w): suspend event 0x10000
  TryLocks the mutex (spin block, no handler thread); resume event
  0x100000 re-writes reg1 (LEPTON bit cleared) and reg2, then Unlocks.

## 3. Module data block map

RW segment (ph1, vaddr 0x8F0), 80 bytes, both objects initialized .data:

| offset (RW) | vaddr | field | evidence |
|---|---|---|---|
| +0x00 | 0x8F0 | Cy27040.mutexId (init -1) | cg.c |
| +0x04 | 0x8F4 | Cy27040.protocol | cg.c |
| +0x08 | 0x8F8 | curReg[3]: reg0 revision, reg1 clock control, reg2 spread | cg.c |
| +0x0B | 0x8FB | oldReg[3] (values to restore) | cg.c |
| +0x0E | 0x8FE | padding | cg.c |
| +0x10 | 0x900 | SceSysEventHandler.size = 0x40 | cg.c |
| +0x14 | 0x904 | .name = "SceClockgen" (@rodata 0x8D8) | cg.c |
| +0x18 | 0x908 | .typeMask = 0x00FFFF00 (suspend + resume) | cg.c |
| +0x1C | 0x90C | .handler = _sceClockgenSysEventHandler (0x53C) | cg.c |
| +0x20.. | 0x910.. | .gp, .busy, .next, reserved[9] | cg.c |

GCC keeps the two structs adjacent; the retail lui 0 / addiu {0,16}
literals land exactly on 0x8F0 and 0x900 (results). The register cache
struct IS g_Cy27040: every export reads or writes the chip through the
curReg/oldReg shadow copies, and the chip is only touched on the I2C bus
when a value actually changes.

## 4. CY27040 register model

| reg | meaning | bits |
|---|---|---|
| reg0 | revision (read-only) | GetRevision returns curReg[0] |
| reg1 | clock control | bit0 audio frequency (0 = 44.1 kHz, 1 = 48 kHz), bit3 Lepton DSP clock, bit4 audio clock enable |
| reg2 | spread spectrum | low 3 bits hold the SS mode |

- _sceClockgenSetControl1(bus, mode) @0x5DC (41w, internal): locks the
  mutex, computes `(regClk & bus) != 0` as the return value (the bit's
  previous state), forces the bus bit to `mode`, writes the register over
  I2C only when it changed, unlocks.
- The four 8-word wrappers (AudioClkEnable @0x4BC, AudioClkDisable
  @0x4DC, LeptonClkEnable @0x4FC, LeptonClkDisable @0x51C) are
  `jal 0x5DC` tail calls with constant arguments.
- GetRegValue @0x454: idx < 3 returns curReg[idx], else 0x80000102.
- SetSpectrumSpreading @0xF8 (111w): writes regSS | (curReg[2] & ~7); a
  negative mode restores oldReg[2]'s low bits and returns the mode
  unchanged; equal old/new returns without touching the bus.

## 5. I2C framing

- Slave address 0xD2.
- One-register write: command byte = reg-128; three-register bulk read:
  command 0, receive buffer recv[0] = count, values follow (Setup fills
  curReg and oldReg from a bulk read).
- _cy27040_write_register(idx, val) @0x680 (21w, internal): builds the
  two-byte transmit frame and calls sceI2cMasterTransmit.
- Setup @0x0 (62w): reads both current and old register sets through the
  two I2C read paths, then stores them into the cache.

## 6. Spectrum spreading ladders

The SS value written to reg2 comes from a revision-keyed threshold
ladder, selected by `rev & 0xF` (results):

- revisions {8, F, 7, 3, 9, A}: thresholds 2/7/15/25 map to regSS
  values 0/1/2/4/6 (returned 0/5/10/20/30).
- revision 4: thresholds 2/7/12/17/22/27 map to 0/1/2/3/4/5/6 (returned
  0/5/10/15/20/25/30).
- other revisions: 0x80000104 (not supported).

AudioClkSetFreq @0x47C (16w): accepts only 44100 and 48000; anything
else returns 0x800001FE. The branchy form (if 44100 call(1,0); else if
48000 call(1,1)) is what retail encodes; the `!=` shape if-converts and
diverges (results).

## 7. API semantics

| export | behavior |
|---|---|
| sceClockgenSetup @0x0 | bulk-read the chip into curReg/oldReg |
| sceClockgenSetProtocol @0x438 | store to g_Cy27040.protocol, return 0 |
| sceClockgenGetRevision @0x448 | return curReg[0] |
| sceClockgenGetRegValue @0x454 | idx < 3 -> curReg[idx], else 0x80000102 |
| sceClockgenAudioClkSetFreq @0x47C | 44100/48000 only, else 0x800001FE |
| AudioClk/LeptonClk Enable/Disable | SetControl1 tail calls |
| sceClockgenSetSpectrumSpreading @0xF8 | section 6 |
| sceClockgenInit @0x398 / End @0x3EC | section 2 |

## 8. Error code catalog

| code | meaning | function |
|---|---|---|
| 0x80000102 | illegal register index | GetRegValue |
| 0x80000104 | revision not supported (SS ladder miss) | SetSpectrumSpreading |
| 0x800001FE | unsupported audio frequency | AudioClkSetFreq |
| threadman/I2C codes | propagated verbatim from the imports | Init (CreateMutex), I2C calls |

## 9. Quirks and toolchain notes

- Retail uses three SPECIAL3 `ins`-with-zero words as bit clears:
  0x7C0A1004 @0x1A8 (curReg[2] &= ~7), 0x7C081004 @0x344 (same in
  module_reboot_before), 0x7C0318C4 @0x598 (curReg[1] &= ~8). GCC 3.3.6
  -mips2 cannot emit them; spliced as raw words in the transcription
  (results).
- One MIPS III `daddu v1,a0,v0` (a0 = 0) used as a move @0x6C0 in
  _cy27040_write_register; one `movz` @0x1D8. Both raw-word splices.
- The suspend handler blocks inside the kernel event callback via
  TryLock spin (no timeout path).
- SetControl1 returns the PREVIOUS bit state; the write happens only on
  change (silent bus otherwise).
- Link provenance: the 10 import veneers, both export entries, all three
  import entries, NID tables, strings, SceModuleInfo, the sdk-version
  word, the RW data image (from the C initializers) and the 308-byte
  ph2 relocation stream (126 records, calibrated A1 codec) are all
  generated; the from-scratch build is byte-identical to retail
  (results).
