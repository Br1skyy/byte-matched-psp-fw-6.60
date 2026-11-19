# grind guide

You are grinding firmware functions to byte-exact C. Read this fully first.

## Ground truth

- Retail module: `orig/threadman.prx` (PSP firmware 6.60, from the owner's
  own console - decrypt/extract already done).
- Full retail disassembly (vaddr-aligned): `orig/threadman.dis`
  (26k lines). Function map (300 exports, name→addr): `orig/threadman-map.json`
- Already matched (do NOT redo): see PROGRESS.md.

## Environment (verified working - do not modify tools/ or the toolchain)

Everything compiles inside a podman container (`etch386`) using a
from-source GCC 3.3.6 configured `mipsel-elf` at
`../toolchain-build/prefix336`. The harness handles all of it:

```
cd /path/to/psp-tm
python3 tools/match.py match/threadman/tm.c        # compile + compare
python3 tools/match.py --list <substring>          # find function + addr
python3 tools/match.py --disas 0x10D28 6           # retail words at addr
grep -A12 ' 10d28:' orig/threadman.dis             # retail disasm context
```

Smoke test before you start: `python3 tools/match.py match/threadman/tm.c`
must print the six known results (4 MATCH + 2 reloc). If it errors, STOP and
report - do not try to fix tooling.

Toolchain facts (SETTLED - do not experiment with flags):
- GCC 3.3.6, `-O3 -mips2 -G0 -mabi=eabi`, 16-byte stack alignment patch.
- Endianness little. o32-ish EABI: args a0-a3, 8-byte returns in v0/v1.

## The loop (per function)

1. Read retail code: `grep -A<N> ' <addr>:' orig/threadman.dis`
2. Write C that would produce exactly that codegen into YOUR source file
   (one file per agent - never edit other agents' files or tm.c).
3. `python3 tools/match.py yourfile.c` - iterate until done.
4. Record result in `results/<batch>.md`.

Done states:
- `*** MATCH ***` - finished. Move on.
- `match (reloc)` - every differing word is relocation-covered (global
  base `lui` imm, or `jal` target to an extern you declared). This is a
  legitimate finish; note which relocs.
- Blocked - k1-dependent code you cannot emulate, `ins`/`ext` words
  (opcode 0x1F, e.g. `7c0a1004`), or unsolvable after ~20 iterations.
  Report the blocker honestly with evidence.

## Source-shape playbook (all empirically verified on retail bytes)

- Tail returns: `return f(x);` keeps callee result in v0, no `move v0,zero`.
- 8-byte values return in v0/v1 with no frame: `u64 f(u32 x){return x;}`
  → `move v0,a0; jr ra; move v1,zero`.
- MMIO: `return *(volatile u32*)0xBC600000;` → `lui v0,0xBC60; jr; lw`.
- Globals: retail addresses them `lui rX,0` + `addiu rX,rX,OFF` (module
  base + offset). Reproduce with TOP-LEVEL statics in declaration order,
  padding bytes so each lands at its retail offset:
  `static u8 padA[0x40]; static LogCtx g_logCtx; /* +0x40 */`
  Known offsets so far: logCtx +0x40 (handler at +8), systemStatusFlag
  +0x810, deadThreadHandler +0x838.
- Calls to module-internal functions: declare `extern s32 sub_xxxx(...);`
  (opaque). The `jal` word is then reloc-covered - fine.
- Branch-likely delay slots: gcc puts the taken-path side effect in the
  delay slot (`beqzl rs,rt,L; <delay = trap/store>`). Write the obvious
  source; gcc 3.3 reproduces it.
- Small constants via `li` = `ori/addiu r,zero`; 0x8000xxxx via
  `lui r,0x8000; ori r,r,lo`.
- Division: default flags produce the retail `div/beqzl/break 7` idiom.

## Register conventions seen in retail

- `k1` (reg 27) appears in many exports (GetThreadId etc.): the kernel
  keeps per-thread data at k1. Words with rs or rd = k1 (e.g. `0360f021
  move s8,k1`) mark these functions. A family of tiny 4-word exports
  (sceKernelWakeupThread @0x3050, sceKernelNotifyCallback @0x1CC0,
  sceKernelCancelCallback @0x1E74, sceKernelGetCallbackCount @0x1F78)
  look like tail-jumps - they may be matchable WITHOUT understanding k1
  (pattern-match the words). Try those first if assigned k1 work.

## Honesty rules

- Every claim in your report must be backed by actual command output.
- Never mark a function matched unless match.py printed MATCH/reloc for it.
- Report iteration counts and failed source shapes - they inform the next
  agent. Your partial progress notes are valuable; write them down.

## Wave-2 additions (verified by agents A/B/C - READ tm_c.c BEFORE k1 work)

- **k1 semantics**: packed keyword, bit 20 = user flag, bits 0-19 thread
  index. `sll rX,k1,0xB` promotes bit 20 -> bit 31 for pointer gates
  ((p|p+len)&(k1<<11) sign test -> 0x800200D3). Never dereferenced.
- **k1 recipe (C, proven)**: `.set noreorder` asm transcription with
  %hi/%lo relocs reproduces k1/cfc0 words exactly; 29/30-word function
  matched this way. tm_c.c is the reference implementation. This gas only
  accepts $sp/$ra/$fp aliases - all other registers numeric.
- **1-asm read trick (A)**: a single-instruction asm reading $27 keeps the
  rest of the function natural C (got USec2SysClock to 10/12 exact).
- **Register steering**: `register x asm("rN")` alone is IGNORED; bind the
  value in an asm-output operand to pin register + position.
- **Layout ceiling**: this GCC 8-aligns every static >= 8 bytes; retail
  globals at 4-mod-8 offsets (e.g. +0x17844) cap at LINK-MATCH. Don't
  burn iterations on them.
- **Context struct**: module+0x40 is a POINTER to the big context:
  ctx+0x08 current thread TCB, +0x24 inner block, +0x48 log handler,
  +0x80 callback arg slot, +0xE0 KTLS id table, +0x4CC UID type table,
  +0x554 KTLS descriptors (24B each). TCB: id +0x08, curPriority +0x10,
  attr +0x14 (bit31=user), exitInfo +0x24, gate +0x88.
- **Log handler dispatch**: `li a0,N; jalr` sites (N=29/30/37/38...) call
  the user log handler at ctx+0x48 as handler(N, original_k1, nextra,
  result) - 128 sites module-wide.

## Wave-2 final additions (agent E)

- `register x asm("$6")` syntax (this gcc rejects "r6"); pure-C pins are a
  net loss - transcription is the closure for allocator-blocked functions.
- sub_186ac returns a critical-section COOKIE captured in the next jal's
  delay slot and passed to sub_186dc - transcribe; no C shape expresses it.
- 0xECE4 = shared 64-bit system-clock reader (ctx+0x7C/+0x78 + MMIO
  0xBC600000); 0x113F0 = 64/32 divmod helper (divisor 10^6 = us scale).
- Log handler a1 = the syscall's first argument when one exists, else the
  saved k1. msgno catalog: 131 GetSystemTime, 132 GetSystemTimeWide,
  159 CancelCallback, 160 GetCallbackCount, 29/37/38/43 getters.

## Wave-3 additions (agents G/H/I)

- **Alarm family**: UID class table ctx+0x504 (+ dual-table header ctx+0x4FC,
  hdr21 byte at +0x15 selects record); active-alarm doubly-linked list head
  ctx+0x64 (alarm +0/+4 links, +8/+12 64-bit expiry, +16 state);
  user gates attr bit 0x10 (cancel) / 0x1 (refer); sentinel uid ctx+0x60;
  status scratch ctx+0x6D4; template module+0x714.
- **GOTCHA**: never hand-decode jal targets from hex - always verify with
  `--disas` or the .dis file (a 0C0045BD misread cost one iteration).
- Absolute `jal` to internal functions assembles word-exact (no reloc);
  only veneer jals are reloc-covered. Internal call sites worth knowing:
  0x924 (release-from-wait), 0xA08 (wake-now), 0xC30 (cleanup),
  0xFE4 (resched request), 0x116F4 (alarm core), 0x113F0 (64/32 divmod),
  0xECE4 (64-bit clock read), 0x1880C (bounded copy-out),
  0x18814 (name copy), 0x187AC (size validation).
- TCB additions from H: +0x0C state (4/0xC waiting, 0x10/0x20 dead),
  +0x50 wakeupCount, +0x58 wait gate, +0x5C cleanup flag, +0x80 waitResult,
  +0x98 callbackQueue, +0x9C notifyPending.

## Wave-4 additions (agents J/K/L/M)

- UID class map COMPLETE: +0x4C8 slot table, +0x4CC threads, +0x4D0 semas,
  +0x4D4 evflags, +0x4F4 TEH, +0x4F8 callbacks, +0x4FC queue-links,
  +0x504 alarms, +0x508 vtimers. 0x1875C = UID allocator (table, name,
  user u8, &rec), rec+12 = new SceUID.
- ins/ext/rotrv/cache/sync words: splice as raw .word under noreorder -
  nothing blocks transcription except data layout.
- Thread states: 1 RUNNING, 2 READY, 4 WAITING, 8 SUSPENDED, 12 W+S,
  16 DORMANT; 33-entry state jump tables @0x19B2C/0x19BB0; runq heads
  ctx+152+prio*8, bitmap ctx+128+(prio>>5)*4; preemption via sub_FE4(0,st).
- TCB+0x58 = wait TYPE (1 sleep, 2 delay); TCB+0x98 = CB-armed flag;
  TCB+0x00/+04 = wait-queue links; delay timer handle TCB+0x78.
- Shared-delay-slot traps (cost 2 iters): retail reuses a t9 loaded in a
  live j delay slot; verify branch targets against neighbour .dis lines,
  not the disassembler annotation.

## Wave-6 additions (S/T/U/V)

- **Internal-function diff**: use build/vdiff.py (V) or /tmp/cmp_internal.py
  method (U) - both import tools/match.py parsers; validate against a
  known match first. Intra-function `j` MUST use absolute retail targets
  (asm-local labels emit R_MIPS_26 relocs).
- **GOTCHA**: gas encodes `break 0x7` code in HIGH field (0x0007000D vs
  retail 0x000001CD) - raw .word. Two .dis annotation glitches exist in
  the 0x99xx-0x9Dxx range - raw words are authoritative over annotations.
- Wait types: 1 sleep, 2 delay, 3 sema, 4 evf, 5 mbx, 8 msgpipe-send,
  9 thread-end. Cancel-all tags: 0x86D94883 (cancel), 0x5BD49380
  (self-cleanup), 0x85FE2B4C (release-wait). ctx+0x00 = current TCB.
- New internals: 0xAFC0 ring write, 0x10D34 deadline builder, 0x16FA4
  kstack snapshot, 0xD2E4/0xD38C FPL ring push/pop, 0x9338 mbx insert,
  0xB08 direct-wake, 0x908 wait-enqueue (obj, type, attr, deadline).
- LwMutex: NO priority inheritance; queue order only (attr 0x100);
  delete strands waiters (no check).

## Wave-7 additions (W/X/Y/Z)

- **clz (SPECIAL funct 0x16) = the dispatcher's priority scan**: cascade
  over ctx+136..+148, clz(word)+32 per zero word, 128 = idle. Bitmap
  word actually at ctx+136+4*(p>>5), bit 31-(p&31) via rotrv.
- Ring anchors ctx+152+8p are themselves members of the circular TCB
  lists (empty <=> anchor->next == anchor). ChangeThreadPriority
  re-queues CURRENT at front of its own ring if preempted; prio==0 =
  "current's prio"; user range 8..119, kernel 1..126.
- UID class map COMPLETE (15 classes): +0x4D8 mutexes, +0x4F0 type-14,
  +0x498/+0x4A0 wait queues (types 64/65). 0x187c4 table-free resolver,
  0x187fc class-membership test.
- Exit paths: sub_178C0 never-return core; sub_B48 walks waiter list
  with exitStatus per waiter; TerminateThread is interrupt-legal.
- Exit/exit-delete twins log the acquire COOKIE as a1; SPECIAL2 filler
  0x70050024 exists in the twins.
- MsgPipe receiver priority bit is attr 0x1000 (send's is 0x100);
  receiver TCB+0x74=1 direction tag (send stores 0); 0xB094 ring read
  (pair of 0xAFC0 write); Try* would-block = 0x800201B3.
- Three more .dis annotation glitches at 0xA04C/0xA14C/0xA698 - raw
  words authoritative.

## STRUCTURAL CORRECTION (batch CC - read before using any "ctx" note above)

- module+0x40 ("P"/"ctx" in earlier notes) is the CURRENT THREAD'S RECORD
  pointer, NOT a global context struct. Fields ascribed to "ctx" are
  per-thread: P+0x00 = self/cur fields, P+0x48 = per-thread log handler
  slot, run queues/bitmap/UID tables hang off the REAL global block
  (module data) - re-read earlier notes with this lens. The "logCtx
  +0x40/+0x48" of round 1 is a thread record's fields.
- Tlspl mirror index is embedded in SceUID bits 3-6 (live ins/ext use);
  16-pool uid mirror at module+0x6D4; KTLS values inline threadRec+0xE0+4*id;
  Tlspl per-thread pointer at threadRec+0xDC.

## Wave-9 additions (GG)

- **HARNESS WARNING**: a symbolic `j <label>` emits R_MIPS_26 and the
  reloc mask ignores the target entirely - a WRONG-target j false-passes
  as "match (reloc)". Always literal `j 0xADDR`. Numeric asm labels leak
  across __asm__ blocks (all land in one .s) - unique label numbers only.
- Set-on-active vtimers RE-ARM: unlink, base = now - newTime (schedule
  elapses from immediately), 0xEAE0 re-insert, 0xEB7C reprocess. Wide
  variants return -1 (not SCE codes) on failure; handler-space rule:
  user threads register user-space handlers only (kernel: kseg) else
  0x800200D3. SetSysClockAlarm = thin 60w twin of SetAlarm via the same
  0x116F4 core. vt+0x14 userflag, vt+0x20 1873C-marker/gp.

## Finale additions (KK/LL/MM/NN/OO/PP)

- **THE LINKER EXISTS**: tools/link/build_prx.py builds threadman-linked.prx
  from all tm*.c - per-function word extraction, retail-address placement,
  full reloc resolution against ONE unified data image. Gap list:
  build/link/gaps.txt. New functions should be added to a tm_*.c and the
  linker picks them up automatically.
- **Toolchain v2 (prefix336b + tools/match_oo.py)**: two-mode regrename
  patch (has-calls → keep reg; leaf → vanilla). Use match_oo.py for
  functions containing calls; leaves compile identically. Vanilla
  prefix336/match.py untouched.
- Import-veneer region is 0x1868C..0x18830 contiguous; every 0x186AC-
  0x1881C callee is a load-patched stub (NEVER transcribe them - they
  are copied at link).
- gen_tm.py decoder bugs to carry: cfc0 rd field ($8/$13/$25 all occur),
  rotrv = srlv with sa=1, 2-operand bnel → bnezl.
- Dispatcher chain: 30 sites → 0xFE4 → 0x12828 (loop) → 0x172F8 (clz
  scan); contexts saved by kernel eret path from TCB+0x28 block; FPU via
  0xBC400000 MMIO loops; banked COP0 re-point words 0x40Cxxxxx.
