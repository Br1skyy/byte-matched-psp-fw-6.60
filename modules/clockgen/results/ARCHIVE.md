# clockgen results archive

Primary evidence archive, unedited grind results (the batch results file
and the working log). INTERNALS.md distills this. The individual files
were removed from this repo copy in favor of this single archive.

## index

- results: the clockgen batch results (final state, link,
  source-shape findings, module decode)
- LOG: the working log (tooling
  generalization, rounds, link calibration)

---

<!-- ==== results.md ==== -->

# clockgen grind results - batch CG (first pass, complete)

Module: kd/clockgen.prx (PSP firmware 6.60, owner console dump)
Harness: `python3 tools/match.py match/clockgen/cg.c match/clockgen/cg_asm.c --module clockgen`
Map: match/clockgen/clockgen-map.json (17 entries: 14 exports + 3 internals)

## Final state - 14 MATCH + 3 match(reloc), 0 DIFF (17/17 accepted)

| function | addr | words | state | notes |
|---|---|---|---|---|
| sceClockgenSetup | 0x00000 | 62 | *** MATCH *** | cg_asm transcription |
| sceClockgenSetSpectrumSpreading | 0x000F8 | 111 | *** MATCH *** | cg_asm transcription (ins word) |
| module_start | 0x002B4 | 27 | match (reloc) | cg.c pure C; 4 reloc words (3 stub jal + mutex-name string lo16) |
| module_reboot_before | 0x00320 | 30 | *** MATCH *** | cg_asm transcription (ins word) |
| sceClockgenInit | 0x00398 | 21 | match (reloc) | cg.c pure C; 4 reloc words (same shape as module_start) |
| sceClockgenEnd | 0x003EC | 19 | match (reloc) | cg.c pure C; 2 reloc words (DeleteMutex/Unregister jal) |
| sceClockgenSetProtocol | 0x00438 | 4 | *** MATCH *** | pure C (proven, match2.c) |
| sceClockgenGetRevision | 0x00448 | 3 | *** MATCH *** | pure C (proven, match2.c) |
| sceClockgenGetRegValue | 0x00454 | 10 | *** MATCH *** | pure C (proven, match2.c) |
| sceClockgenAudioClkSetFreq | 0x0047C | 16 | *** MATCH *** | cg_asm transcription (branchy form) |
| sceClockgenAudioClkEnable | 0x004BC | 8 | *** MATCH *** | cg_asm wrapper (exact jal 0x5DC) |
| sceClockgenAudioClkDisable | 0x004DC | 8 | *** MATCH *** | cg_asm wrapper |
| sceClockgenLeptonClkEnable | 0x004FC | 8 | *** MATCH *** | cg_asm wrapper |
| sceClockgenLeptonClkDisable | 0x0051C | 8 | *** MATCH *** | cg_asm wrapper |
| _sceClockgenSysEventHandler | 0x0053C | 40 | *** MATCH *** | internal; cg_asm (ins word) |
| _sceClockgenSetControl1 | 0x005DC | 41 | *** MATCH *** | internal; cg_asm |
| _cy27040_write_register | 0x00680 | 21 | *** MATCH *** | internal; cg_asm (daddu word) |

Words: 437 code words total (0x6D4 bytes / 4); 427 exact at harness level,
10 relocation-covered (the 3 pure-C functions). The link resolves all 10
(stub jal targets + the mutex-name string lo16) to retail values.

## Link result (tools/link/build_prx_cg.py)

```
python3 tools/link/build_prx_cg.py --no-retail
  functions linked: 17  (437 words exact, 0 reloc-site, 0 diff)
  ph1 RW image from cg.o .data initializers: 80 bytes
  ph2 relocation stream: 308 bytes, 126 records, byte-identical to retail: True
  wrote build/link-cg/clockgen-linked.prx (2836 bytes; identical to retail: True)
```

SHA1 of the from-scratch build (no retail bytes consumed; ph1 from the C
initializers, ph2 re-derived via the calibrated A1 codec, ELF from fields):

```
56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199  clockgen-linked.prx
56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199  retail kd/clockgen.prx
```

Full-module reconstruction: every text word, the 10 import veneers, both
export entries, all three import entries, the NID tables, strings,
SceModuleInfo, the sdk-version word, the RW data image and the load
relocation stream are generated and land byte-identical on retail.

## What the retail compiler did that GCC 3.3.6 (-mips2) cannot

Three SPECIAL3 `ins`-with-$zero idioms (clearing low bits of a register,
Sony's compiler emitting `x &= ~7` / `x &= ~8` as ins rt,$0,pos,size):

- 0x1A8 `7C0A1004` ins t2,$0,0,3 - SetSpectrumSpreading, curReg[2] &= ~7
- 0x344 `7C081004` ins t0,$0,0,3 - module_reboot_before, curReg[2] &= ~7
- 0x598 `7C0318C4` ins v1,$0,3,1 - SysEventHandler, curReg[1] &= ~8 (LEPTON)

One MIPS III `daddu` used as a move:
- 0x6C0 `0044182D` daddu v1,a0,v0 (a0=0) - _cy27040_write_register return path

Also `movz` (0x0245300A @0x1D8, SetSpectrumSpreading ret mux): gas rejects
the mnemonic under -mips2, spliced as raw .word.

## Source-shape findings (GCC 3.3.6 -O3, verified on retail bytes)

- AudioClkSetFreq: `if (freq != 44100 && freq != 48000) return ...; call(x,
  freq == 48000)` (the match4.c shape) if-converts to xor/sltu - 10+ word
  DIFF. The branchy `if (freq == 44100) call(1,0); else if (freq == 48000)
  call(1,1); return 0x800001FE;` (uofw shape) matches retail's control flow;
  final transcription pins the jal and the deferred lui 0x8000.
- module_start inlines sceClockgenInit (static called twice, -O3 inlines
  into both callers) and hoists `g.protocol = 1` into the jal Setup delay
  slot; `sw v0,0(s0)` mutex store rides the RegisterSysEvent delay slot.
  Pure C reproduces it exactly except the call/string relocs.
- module_reboot_before inlines sceClockgenEnd the same way.
- Data model: RW segment ph1 (vaddr 0x8F0) = g_Cy27040 (+0, init mutex=-1)
  then g_ClockGenSysEv (+0x10, 0x40 bytes, init name=0x8D8 typeMask=
  0x00FFFF00 handler=0x53C). Both `.data` (initialized), so GCC keeps them
  adjacent - offsets 0/0x10 reproduce retail's lui 0/addiu {0,16} exactly.
- Import stubs 0x6D4..0x723 are 10 two-word veneers (jr ra; nop): TryLock,
  Unlock, Lock, Create, Delete mutex / TransmitReceive, SetClock, Transmit
  I2C / Register, Unregister SysEvent. jal targets to them from C are
  reloc-covered; transcriptions emit literal `jal 0x6XX` word-exact.

## Module decode (CY27040 register model, from the grind)

- reg0 (revision): GetRevision returns curReg[0]; SS ladder keys on
  `rev & 0xF` - revs {8,F,7,3,9,A} use thresholds 2/7/15/25 -> regSS
  0/1/2/4/6 (ret 0/5/10/20/30); rev 4 uses 2/7/12/17/22/27 -> 0/1/2/3/4/5/6
  (ret 0/5/10/15/20/25/30); other revs -> 0x80000104 NOT_SUPPORTED.
- reg1 (clock control): bit0 audio-freq (0=44.1k,1=48k), bit3 LEPTON DSP,
  bit4 audio enable. SetControl1(bus,mode) locks the mutex, computes
  `(regClk & bus) != 0` as return, forces the bit, writes only on change.
- reg2 (spread spectrum): low 3 bits hold the SS mode; SetSpectrumSpreading
  writes regSS|(cur&~7); mode < 0 restores oldReg[2]'s low bits and returns
  mode; equal old/new returns mode without touching the bus.
- I2C: slave address 0xD2; command = reg-128 for one register, 0 for the
  3-reg bulk read (recv[0]=count, values follow). Setup fills curReg+oldReg.
  SysEvent 0x10000 (suspend) TryLocks the mutex (spin block), 0x100000
  (resume) re-writes reg1 (LEPTON cleared) + reg2 and Unlocks.

<!-- ==== LOG.md ==== -->

# clockgen grind working log

## Session 1 (this file's session)

1. Tooling generalization:
   - tools/match.py: --module flag + MODULES table (threadman default,
     paths byte-identical to before). Regression: match/threadman/tm.c
     still prints 4 MATCH + 2 reloc; tools/link/build_prx.py --no-retail
     still emits SHA1 32e4457c8018af2f168bb931c07ab01b88b836af.
   - tools/prx.py: built-in SYSLIB_NIDS names for module_start et al.;
     export parser now accepts address 0 (sceClockgenSetup sits at vaddr 0)
     with a stricter nid_count >= fcount guard. Threadman map untouched.
   - Two harness bugs found via clockgen: name_map() dropped addr-0
     functions; parse_exports rejected 0-address entries. Both fixed
     without behavior change for threadman (its map has no zero addrs).
2. Map generated: 14 exports + internals section; all addresses equal the
   uofw //0x00000XXX comments (cross-checked 14/14).
3. Round 1 (pure C): SetProtocol/GetRevision/GetRegValue MATCH (proven
   match2.c contents ported verbatim); Init/module_start/End reloc-clean
   pure C on first try (delay-slot stores and the inlined static all
   reproduced). AudioClkEnable/Disable, LeptonClk* reloc via extern call.
   AudioClkSetFreq DIFF: match4.c's `!=` shape if-converts (xor/sltu);
   the branchy uofw shape fixes control flow. Setup DIFF: GCC generated
   65 words vs retail 62 (loop not fused the same way).
4. Round 2 (transcriptions, cg_asm.c): 12 functions transcribed
   word-for-word. gas findings: `movz` rejected under -mips2 (spliced
   .word), ins/daddu words spliced as .word, `li` small values emit addiu
   (matches retail), absolute `jal 0x6XX` word-exact no reloc. One
   transcription slip caught by diff (extra move in SetControl1 join),
   one label-forwarding error (j to local label instead of literal) -
   fixed; first clean compile gave 14 MATCH.
5. Iterations used: ~8 match.py runs total for the whole module.
6. Link (tools/link/build_prx_cg.py, new second script; threadman pipeline
   untouched): own object parser (reloc symbol names needed), symbol
   resolution map internals + 10 veneer addresses + .data offsets +
   .rodata anchor 0x8D8. ph2 via a calibrated A1 codec: reltab.decode of
   the retail stream gives the record order + class-index tables
   (clockgen uses a 6-entry flag table, unlike threadman's 8); every
   delta/lo16/class is re-derived from the generated image and the
   round-trip is byte-verified. Two rounds of fixes:
   - retail import strings are lowercase: sceSysEventForKernel,
     sceI2c_driver (the dis hex 7363 was misread as 'Sc' once).
   - delta-after-set-base convention: first record of a chain is relative
     to the set-base offset, not absolute (caught by round-trip diff).
   Final: --no-retail output byte-identical to retail, sha1
   56e3a4ed3f74b1e8c9c6fec2f093d6cfea2f3199, 0 differing bytes.

## Notes for future agents

- The etch386 podman run can transiently fail with /tc permission denied
  (volume relabel race when two pods start at once). Retry after a few
  seconds before debugging anything else.
- Branch targets in transcriptions: LOCAL labels for beq/bne/beqz/bnez/
  bltz/slti-branch forms (offsets are layout-preserved), LITERAL addresses
  for j/jal (word values are absolute module offsets). Never `j <label>`.
- Check the retail dis twice for branch targets at 0x180 vs 0x184 and
  0x188: SetSpectrumSpreading mixes all three (regSS-set / lock / lock-no-
  load entries) and the differences are semantically load-bearing.
