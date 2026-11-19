# threadman internals

Reference distilled from the batch decode reports (A through VV, archived in
results/ARCHIVE.md). All facts trace to a batch report or to the retail
disassembly. Retail virtual addresses are cited as @0xNNNNN.

Notation used throughout:

- **S** = the scheduler context block, a struct embedded in the module data
  block at module+0x40. Earlier batches called it "ctx"; offsets written
  "ctx+X" in the archive mean S+X, i.e. module+(0x40+X).
- **P** = the current thread's record (TCB). P = `*(u32 *)(module+0x40)` =
  *(S+0). The word at module+0x40 IS the current-thread-record pointer; batch
  C first read "current thread from ctx+0x08", which batch CC corrected
  (GetThreadKTLS loads base = `*(module+0x40)` directly, @0x11C68), and
  batches V/KK/SS byte-confirmed `P = *(module+0x40)` (@0x9A40 area, @0x12A1C).
- **TCB** = a thread control record, addressed through a UID-class view
  (see section 5). TCB offsets below are view offsets.
- **rec** = a UID class record; **hdr21** = the per-table view index byte at
  UID table header+0x15.

## contents

1. Overview
2. Boot sequence
3. Module data block map
4. Thread control block (TCB)
5. UID system
6. Scheduler
7. Wait machinery
8. IPC families
9. Callbacks
10. Timers
11. Exit and termination
12. Stacks
13. Error code catalog
14. Log msgno catalog
15. Quirks and shipped bugs

---

## 1. Overview

threadman.prx is sceThreadManager, the PSP kernel's scheduler. It owns
threads, the dispatcher, all inter-process communication objects (sema, event
flag, mutex, lwmutex, mbx, msgpipe, vpl, fpl, tlspl), callbacks, alarms,
vtimers, delay timers, kernel TLS, and the 64-bit system clock. Almost every
other kernel module sits on top of it.

Size and identity:

| item | value | evidence |
|---|---|---|
| internal name | "sceThreadManager" (SceModuleInfo) | VV |
| file size | 115864 bytes | PP, VV |
| text region | vaddr 0x0..0x1868C (99980 B) | PP |
| import veneer region | 0x1868C..0x18830 (53 two-word stubs, load-patched) | PP, SS |
| metadata + rodata | 0x18844..0x19EC4 | PP |
| RW data block (ph1) | vaddr 0x19F00, size 0x844, p_filesz = 0 (loader seeds it) | VV |
| ph2 relocation segment | 9432 B, 4215 A1 records | VV |
| functions reconstructed | 331 (24982 words, 99.95% of text; rest is zero padding) | UU, VV |
| export libraries | 3 (syslib, ThreadManForUser, ThreadManForKernel) | VV |
| located exports | 167 NIDs (149 user + 149 kernel func NIDs + kernel var NID 0x921B7ACD) | PP, VV |
| from-scratch SHA1 | 32e4457c8018af2f168bb931c07ab01b88b836af | VV |

Boot position: vaddr 0 is a 2-word bootstrap veneer `jal 0x18694; nop` into a
load-patched import (SS @0x0000). The ELF entry and module_start is
0x11F68 (PP, QQ). module_bootstart is 0x16B84 (syslib stub table, QQ).
The module creates the kernel's first three threads inside module_start
(section 2), so everything else in the system is scheduled by it.

Compiler: gcc 3.3.6, -O3 -mips2 -G0 -mabi=eabi, with two backend patches
(16-byte stack alignment EABI quirk; regrename leaf-vs-has-calls split, see
patches/). See docs/TOOLCHAIN.md.

## 2. Boot sequence

module_start @0x11F68 (400 words, QQ; syslib NID D3744BE0 = ELF entry).

Step order, all byte-verified (QQ unless noted):

1. **Enter critical and flush S**: `0x186AC` acquire (cookie to 92(sp));
   s8 = gp; caller sp saved to 96(sp) (thread 3 adopts it later);
   `0x18764(S, 0, 2052)` cache-range op over the whole 0x804-byte S block;
   `mfc0 a3,$22` saved to S+0x7C8; first subsystem init call @0x11FC8.
2. **13 subsystem init calls** @0x11FCC..0x12028: 0xC50, 0x16B40 (threads
   class, UU), 0x283C, 0x4FBC (sema, UU), 0x6120 (mutex, UU), 0x743C
   (lwmutex, UU), 0x84B4 (mbx, UU), 0x92F4 (msgpipe, UU), 0xB1B4, 0xC244
   (vpl/fpl, UU), 0xD474 (fpl/tlspl, UU), 0xE4EC (tlspl, UU), 0x1121C
   (timer classes, RR). Each registers its UID class table(s) via the
   0x18754/0x187CC import pair and pre-creates sentinel records.
3. **List and ring self-init** @0x1202C..0x120B8: five S-block list heads made
   self-referential (S+0x498 sleep queue, S+0x4A0 second wait queue, S+0x4A8
   dead list, S+0x4B0 suspend list, S+0x4B8 dead-handler list); the 128
   run-queue ring anchors at S+152+8*p (p = 0..127) self-linked; UID
   slot-table header at module+0x500 self-pointer + empty first link;
   S+0x20 = -1; S+0x38/S+0x5C/S+0x1C/S+0x7F8/S+0x7E4 zeroed.
4. **Boot-mode detection** @0x120B4..0x1210C + tails: imports 0x1872C(23),
   0x1872C(22), 0x1872C(26), 0x18734() decide the mode word at S+0x7E4
   (values 0..4):
   - profiler present (f23 != 0): sets *(0xBC000030) |= 0x300, prints
     "CPU Profiler enabled: " (string @0x196F4); f22 != 0 prints
     "Thread Mode" (@0x1971C), mode 1; else "Global Mode" (@0x1970C),
     mode 2.
   - no profiler: 0x18734() or f26 nonzero, mode 0 (silent); else f22
     nonzero, mode 3; f22 zero, mode 4.
5. **Private memory pool**: `0x1878C(1, 2048, 1, "SceThreadman")` creates a
   2KB SysMem pool, handle stored at S+0x7E0 (module+0x820). Every 320-byte
   thread context block and various small allocations come from it.
6. **The three birth threads**:
   - Thread 1 **"SceThreadmanIdle"** @0x1212C..0x12268: UID-created in the
     threads class; tid stored at TCB+8 and at the stack anchor data[0];
     priority 127 (also base at TCB+0xBA, ceiling 127 at TCB+0xBC); 256B
     stack block named "stack:SceThreadmanIdle"; entry at TCB+0xC0 =
     0x172C8 when mode != 0, else 0; state 2 (READY); context block via
     0x187EC(pool, 320, {8,64}) + 0x134A8 poison init, ctxblk+36 = 3,
     ctxblk+52 = 3, ctxblk+0xBC = 0x172DC (entry-return trampoline slot),
     ctxblk+56 = EPC = entry, sp/fp = stackData+256, +176 = gp;
     `0x127D0(TCB)` queues it on run queue 127. **S+0x50C = idle TCB**.
   - Thread 2 **"SceThreadmanCleaner"** @0x1226C..0x12388: same skeleton,
     entry 0x125A8 (the reaper loop), priority 1, 2048B stack, state 4
     (WAITING), parks immediately. **S+0x510 = cleaner TCB**; S+0x34
     (cleaner-wakeup flag) zeroed here.
   - Thread 3 **"SceThreadmanInit"** = the module_start CALLER adopted as a
     thread @0x1238C..0x12440: `0x187F4(saved_sp, sp+84, sp+88)` derives a
     pool from the caller's stack, `0x187DC(pool, desc56)` allocates the
     stack block from a 56-byte descriptor; TCB+0x2C = data, thread id
     written at data[0], TCB+0xC4 = size; priority 32; state 1 (RUNNING);
     context block via 0x187EC + 0x134A8; then `*(module+0x40) = TCB3` and
     S+4 = TCB3 (current and next both re-pointed), and the banked COP0
     registers re-pointed (ctc0 $14 = ctxblk, ctc0 $15 = 0, ctc0 $16 =
     &TCB3+0x24, k1 = 0). Thread 3 continues executing module_start.
7. **Dispatcher registration and plumbing** @0x1245C..0x12520:
   - `0x1870C(module+0x1100, 0x12828)`: registers the dispatch loop
     sub_12828 with the software-interrupt dispatch trampoline at
     module+0x1100.
   - `0xE5EC(...)`: timer/clock init installer (SS).
   - `0x186D4(0x41, 0, 0x125A0, 0, 0)` registers the 2-word
     `jr ra; li v0,-1` stub at 0x125A0 for interrupt 0x41, then
     `0x186BC(0x41)` enables it (the same interrupt sub_FE4 raises to
     defer dispatch).
   - `0x1869C(11, module+0x338)`: registers the sysstat table; later
     module_bootstart @0x16B84 re-registers it via 0x1868C(11, +0x338).
   - `ctc0 zero,$8` (BadVAddr clear).
   - Three syscall-template registrations via 0x18714 into S+0x7D4 =
     _sceKernelExitThread (0x16D34), S+0x7D8 =
     _sceKernelReturnFromChangeStack (0x14F10), S+0x7DC =
     _sceKernelReturnFromCallback (0x253C): the user-mode re-entry gadgets
     the callback thunk consumes (section 9).
   - `0x5138` = sceKernelCreateEventFlag("SceThreadmanSysStat", 512, 0,
     NULL), uid stored at S+0x7D0.
   - `0x18744(0x172A8, 3, 0)` registers the init-thread epilogue stub at
     0x172A8, which calls sceKernelExitDeleteThread(0): thread 3 ends by
     exiting and deleting itself.
   - Release cookie, `0x186A4()`, return 0.

Cleaner loop sub_125A8 @0x125A8 (65 words, never returns): enter critical,
walk the deferred-uid-free block chain at module+0x78 (block layout: +0 next,
+0x24 count, +4.. uids); per uid resolve against the threads table, on
failure run 0x155B8 (delete cleanup) else 0x1877C (uid free); free drained
non-head blocks back to the S+0x7E0 pool; when the chain is empty set state
= 4 (WAITING), S+4 = 0, and `0xFE4(1,1)` to park until the next deferred
free (sub_126AC sets S+0x34 = 1, which the dispatch core consumes to requeue
the cleaner).

sub_126AC uid free @0x126AC (73 words) is the deferred-release entry: it
appends the uid to the module+0x78 chain (duplicate scan, 8-slot blocks,
new 44-byte block from the pool on overflow) and arms S+0x34 = 1. Its four
callers (0xE9FC, 0xEDF8, 0xEF14, 0x179EC) all run in contexts that cannot
walk UID tables directly.

Timer bring-up (sub_E5EC @0xE5EC, SS): clock-source function pointers
installed at module+0x83C (sceKernelGetSystemTimeLow 0x10D28) and module+0x840
(sub_ECE4 64-bit clock reader); module+0x828 = USec2SysClock(100) low word,
module+0x82C = same << 1 (the scan bias); module+0x80C = 4 or 19 selected by
the config flag at module+0x808; SysTimer MMIO enable sequence
(0xBC60000C = 1, prescale 0xBC600008, 0xBC600010 = 0); sub_E80C registered as
the alarm interrupt handler; 32 timer nodes pre-created in the delay class
and pushed via 0xEEB0; rings at module+0x68 (delay free pool) and module+0xA8
(active queue) initialized; first deadline programmed to 0xBC600004;
exception vectors 0x112E0 / 0x112F8 / 0x1136C registered for line 24.

## 3. Module data block map

The grind originally modeled the data as one g_pad chain spanning
+0x000..+0x1784C. Batch VV proved the truth: ph1 has p_filesz = 0; the
runtime RW image is a 0x844-byte block at vaddr 0x19F00, seeded by the loader
from 913 addr_seg=1 relocations plus the ph0 rodata tail. Offsets at or below
0x844 are data; offsets above (0x1100, 0x196xx, 0x296E0, 0x17844) are text or
rodata addresses. All offsets below are module-relative (pre-relocation
image offsets, which is what the retail lui/addiu immediates encode).

Pre-S dwords (module+0x00..0x3F):

| offset | field | evidence |
|---|---|---|
| +0x00 | hardware counter shadow/seed, mirror of MMIO 0xBC600000; written at init and per tick | RR 0x1136C, sub_112F8; SS |
| +0x338 | sysstat table / exception-reentry dispatch vector (`jr v0` through this word); registered for vector 11 | SS @0x330 area; QQ |
| (0x0C0/+0x1100 etc.) | see text/rodata table at the end of this section | |

S block, S = module+0x40, 0x804 bytes (module+0x40..0x844). "S+X" equals the
"ctx+X" of the archive batches.

| S offset | module offset | field | evidence |
|---|---|---|---|
| +0x00 | +0x40 | P: current thread record pointer (the module_start thread-3 write @0x123xx; dispatch loop writes it at every switch @0x12A1C) | QQ, KK, V, SS |
| +0x04 | +0x44 | next/dispatch-target TCB; 0 = recompute. Zeroed before every dispatch request ("ctx+4 = 0" of H/L/R) | KK, L, H |
| +0x08 | +0x48 | threadman log handler (installed by sceKernelSetThreadmanLogHandler @0x16BD8). Batch CC first read this as a per-thread field of the current-thread record; after the S/P split was settled it is the global slot in S | KK @0x129F0; CC; GG |
| +0x0C | +0x4C | dispatch state: 0 running, 1 dispatch suspended, 2 suspended and current thread parked on suspend list, 3 suspended with termination pending. Every blocking entry gates on it (0x800201A7) | HH, K, L |
| +0x10 | +0x50 | global dispatch (context switch) counter | KK @0x1296C |
| +0x14 | +0x54 | same-thread re-dispatch generation counter | KK @0x12B08 |
| +0x1C | +0x5C | value compared against target TCB+0x20 in the 0x40000000 flag path of the dispatch loop; zeroed at init | KK; QQ |
| +0x20 | +0x60 | set to -1 at init | QQ |
| +0x24 | +0x64 | delay-timer free-pool COUNT | RR sub_10FAC |
| +0x28 | +0x68 | delay-timer free-pool ring HEAD (doubly-linked recycle list, refilled by 0xEEB0) | RR; SS init |
| +0x30 | +0x70 | pending-dispatch flag: written 1 by SuspendAllUserThreads (@0x3A08 `sw s1,48(s0)`), read by SignalSema's waiter gate (@0x4620 `lw v1,48(s4)`); while set, user-thread waiters are skipped in wake walks | HH; R; verified in dis |
| +0x34 | +0x74 | cleaner-wakeup flag: written 1 by deferred uid free sub_126AC, read by dispatch core sub_172F8 (@0x1730C `lw v1,52(t2)`) to requeue the cleaner; zeroed at cleaner creation | QQ; KK; verified in dis |
| +0x38 | +0x78 | deferred-uid-free block chain head (first block is static; blocks 44B: +0 next, +0x24 count, +4.. uids) | QQ, SS |
| +0x5C | +0x9C | zeroed at init | QQ |
| +0x60 | +0xA0 | sentinel uid slot: armed with rec+12 while an expiry dispatcher runs; CancelAlarm compares its argument against it (0x8002019F) | RR; G; J |
| +0x64 | +0xA4 | active-timer list head cache (the dword CancelAlarm compares/updates; batch G/J first called this "the list head", corrected by MM) | MM; RR |
| +0x68 | +0xA8 | active timer queue ring anchor {+0 first, +4 last}, self-referential when empty; links at node+0/+4, 64-bit expiry at +8/+12, ascending order | MM; SS |
| +0x70/+0x74 | +0xB0/+0xB4 | 64-bit dispatch timestamp (CPU-time deltas are now - this) | KK @0x12934; K; II |
| +0x78/+0x7C | +0xB8/+0xBC | 64-bit clock epoch base; ECE4 computes now = {+0xB8 lo, +0xBC hi} + counter(0xBC600000) | E; RR |
| +0x88..0x94 | +0xC8..0xD4 | run-queue bitmap, 4 words, bit 31-(p&31) of word p>>5 set when queue p non-empty (batch K first wrote "+0x80"; every real access is +0x88, Z) | Z; KK |
| +0x98..0x490 | +0xD8..0x4D0 | 128 run-queue ring anchors, 8 bytes each, at module+0xD8+8*p; anchor is a ring member, empty when self-linked | Z; KK; QQ |
| +0x490 | (none) | not documented (runq anchors end at +0x490 exclusive) | |
| +0x498 | +0x4D8 | sleep wait queue head (standalone ring head; links at TCB+0/+4) | L; Z |
| +0x4A0 | +0x4E0 | second thread wait queue (GetThreadmanIdList special types 64/65) | Z; delay cores use ctx+0x4E0 as the delay queue (L) |
| +0x4A8 | +0x4E8 | dead/dormant thread list (state 16 after plain exit; dormant threads park here from CreateThread) | Y; AA; NN |
| +0x4B0 | +0x4F0 | suspend/stop list (state 8) | K; LL |
| +0x4B8 | +0x4F8 | second dead list: dead-thread-handler list, state 32, exit status 0x800201A2 | NN; QQ |
| +0x4C0 | +0x500 | TEH ring sentinel (also holds the UID slot-table header self-pointer per QQ) | HH; UU; QQ |
| +0x4C8 | +0x508 | shared slot table (per-object wait view; section 5) | M; LL |
| +0x4CC | +0x50C | threads class table (type 1) | B; Z |
| +0x4D0 | +0x510 | semaphore class table (type 2) | M |
| +0x4D4 | +0x514 | event flag class table (type 3) | M |
| +0x4D8 | +0x518 | mutex class table (type 12) | Z; BB |
| +0x4DC | +0x51C | lwmutex class table (type 13) | Q |
| +0x4E0 | +0x520 | mbx class table (type 4) | N |
| +0x4E4 | +0x524 | msgpipe class table (type 7) | P; TT |
| +0x4E8 | +0x528 | vpl class table (type 5) | O |
| +0x4EC | +0x52C | fpl class table (type 6) | O |
| +0x4F0 | +0x530 | tlspl class table (type 14; batch Z first labeled it "queue-links") | CC; FF; Z |
| +0x4F4 | +0x534 | thread event handler class table (type 9) | B; UU |
| +0x4F8 | +0x538 | callback class table (type 8) | B; UU |
| +0x4FC | +0x53C | Timer base/link class table (20-byte link records) | RR; G; J |
| +0x500 | +0x540 | Delay-timer class table ("SceThreadmanDelay") | RR |
| +0x504 | +0x544 | Alarm class table (type 10) | RR; G |
| +0x508 | +0x548 | VTimer class table (type 11) | RR; J |
| +0x50C | +0x54C | idle thread TCB sentinel (DeleteThread rejects it) | QQ; Y |
| +0x510 | +0x550 | cleaner thread TCB sentinel (dispatch fallback thread) | QQ; Y; KK |
| +0x554 | | KTLS descriptor table, 16 x 24 bytes: +0 inUse, +4 refcount, +8 size, +12 destructor func, +16 arg, +20 validated gp | A; CC |
| +0x694 | +0x6D4 | Tlspl uid mirror, 16 words (mirror[idx] = patched uid) | CC; FF; II |
| +0x6A8..0x714 | | shared Refer* scratch region (108-byte ThreadInfo base ctx+0x668; 52/56-byte overlays at ctx+0x69C/0x6A0/0x6A8) | I; K; M |
| +0x6D4 | +0x714 | shared status-scratch template base (size word read by the 0x1880C copy-out min) | G; M; EE |
| +0x6D8 | +0x718 | mutex ceiling default word (scratch+4; CreateMutex reads it as the default ceiling) | BB |
| +0x6E4 | +0x724 | 0x187EC context-block descriptor {+0 = 8, +4 = 64} | AA |
| +0x6EC | +0x72C | 8-byte SceKernelThreadOptParam scratch {size, mpid} | AA |
| (module+0x734) | +0x734 | rodata string constant ("stack:..." name pool) used for stack block names | AA |
| +0x7C8 | +0x808 | CP0 $22 value saved at module_start entry (`sw a3,1992(s2)` @0x11FC8); the timer init later reads it as the config flag selecting module+0x80C = 4 or 19 | QQ; SS |
| +0x7CC | +0x80C | subinterrupt number programmed by the timer block | SS; RR |
| +0x7DC | +0x81C | syscall code-field dword: the callback gadget's 20-bit code is `(word << 6) & 0x3FFFFC0 \| 0xC` | MM |
| (module+0x810) | +0x810 | g_systemStatusFlag (sceKernelGetSystemStatusFlag target; round-1 model had 0x818, corrected by the link data image) | PP |
| +0x7E0 | +0x820 | threadman private SysMem pool handle | QQ; CC; SS |
| +0x7E4 | +0x824 | boot/mode word (0..4) from module_start step 4; profiler gate reads == 1 (0x17248 `lw v0,2020(S)`), VFPU-context selector (1 or 3 arms the 100-byte context alloc). Batch MM labeled this dword "programming margin"; the margin is actually read from +0x82C (see next row, raw words @0xEBA4/@0xEC24) | QQ; II; AA; MM |
| (module+0x828) | +0x828 | 100 us in SysClock units, low word (written at timer init) | SS |
| +0x7EC | +0x82C | timer margin/bias dword (= 2x the 100 us word): seeds the reprocess scan (added to head expiry @0xEBA4/0xEBC0) and is the margin window the deadline programming compares against (@0xEC24) | MM; SS; verified in dis |
| +0x7FC | +0x83C | clock-source function pointer: sceKernelGetSystemTimeLow (0x10D28) | SS |
| +0x800 | +0x840 | clock-source function pointer: sub_ECE4 (64-bit clock reader) | SS |
| +0x7F8 | +0x838 | dead-thread handler (sceKernelRegisterDeadThreadHandler; round-1 model had 0x834, corrected to 0x838 by the link data image) | NN; PP |

Corrections embedded above worth restating:

- The RW data block ends at +0x844. The old "+0x17844 config pair" of batch
  A is not data: 0x17844 is inside the text of sub_17844 (dead-thread
  dispatcher 2, UU); ThreadManForKernel_D366D35A @0x16B1C writes the pair
  {0x3E00008, 0} into that function's code at runtime (a patch site), per
  VV's re-audit of the data image.
- "ctx+0x64 alarm list head" (batches G/J) resolved into three distinct
  dwords: module+0x64 = S+0x24 delay-pool count, module+0xA4 = head cache,
  module+0xA8 = the real ring anchor (MM, RR).

Text and rodata constants referenced by code (not part of the data block):

| address | content | evidence |
|---|---|---|
| @0x1100 | software-interrupt dispatch trampoline (reads S+0x0C); registered with 0x1870C | QQ |
| @0x125A0 | `jr ra; li v0,-1` stub registered as interrupt 0x41 handler | QQ |
| @0x172A8 | init-thread epilogue stub (calls ExitDeleteThread(0)) | QQ |
| @0x172C8 | idle loop variant entry (DEAD SPIN: mfc0 $25, cache 0xa, madd, j self) | QQ; UU |
| @0x172DC | entry-return trampoline constant stored to ctxblk+0xBC for user threads | QQ; UU |
| @0x178C0, @0x13E80, @0x17844 | exit cores / start trampoline (section 11) | NN; UU |
| @0x19628 / @0x19638 | msg event / empty data descriptors for the msgno-0 log flavor | N |
| @0x196F4..0x197BC | boot strings and name pool ("SceThreadmanIdle"/"SceThreadmanCleaner"/"stack:..." with shared suffixes) | QQ |
| @0x19800 | panic string for the dispatcher's "no runnable thread" fatal | KK |
| @0x19B2C / @0x19BB0 / @0x19C34 / @0x19E34 | 33-entry thread-state jump tables (Suspend / Resume / SuspendAllUserThreads / IdList) | K; HH; Z |
| @0x29E88 | 15-case wait-type jump table for the debug status builder | NN |
| @0x19D58 | msgpipe class descriptor (method slots at +4/+0xC/+0x14/+0x1C) | TT |
| @0x19DD0/+0x19DE8/+0x19E00/+0x19E18 | Timer/Delay/Alarm/VTimer class descriptors (48 B + 20 B base) | RR |
| @0x29A44/0x29A60/0x29988/0x29A94 | 0x18724 panic strings of the exit/kill paths | NN |

## 4. Thread control block (TCB)

Every thread is a UID-class record in the threads table (module+0x50C). The
TCB view is rec + 4*hdr21(threads). Constructor: sceKernelCreateThread
@0x12CF8 (367 words, AA); the field map below merges AA (constructor), K
(StartThread), H/L/R (wake and wait), DD (stacks), Q/U (lwmutex), BB/NN
(mutex), CC (tls), II/NN (status builders), KK (dispatcher).

| offset | field | evidence |
|---|---|---|
| +0x00/+0x04 | ring links (next/prev). A TCB is a node in exactly ONE ring at a time: ready queue, suspend list, dead list, sleep/delay queue, or an object wait queue. Same words always | LL; Z |
| +0x08 | thread id (SceUID) | D; K |
| +0x0C | state u32: 1 RUNNING, 2 READY, 4 WAITING, 8 SUSPENDED, 12 WAIT+SUSPENDED, 16 DORMANT, 32 dead-on-handler-list; >= 33 illegal | K; H; NN |
| +0x10 | current (run-queue) priority | K; Z |
| +0x14 | attr: bit 31 = user thread; bits 28..31 = user level class; bit 0x2000 = FPU-owning; bit 0x4000 = VFPU context | AA; D; SS |
| +0x18 | scratch, zeroed by the callback thunk on swap | MM |
| +0x1C | context block pointer (320-byte GPR/exception frame; validated by 0x186E4). Batch KK wrote this as +0x28; the raw dispatch-loop load is `lw a0,28(s0)` @0x12A30 = +0x1C | K; AA; MM; dis |
| +0x20 | compared against S+0x1C in the dispatch loop's 0x40000000 path | KK |
| +0x24 | exit-info block pointer: +0x18 = callback arg, +8 = user kernel-stack anchor, +0 = FPU-attach flags; bank16 gets its address at every switch-in (`ctc0 t7,$16`, t7 = TCB+0x24 @0x12A54) | A; DD; KK |
| +0x28 | final stack top / context word loaded into bank15 at switch-in (`lw t1,40(s0)` @0x12A4C); the callback thunk rewrites it with *(ctxblk+180) | K; MM; dis |
| +0x2C | kernel-stack data head (thread id stored at data[0]); +0x130 = its block handle; +0xC4 = its rounded size | D; DD; AA; II |
| +0x30 | user-stack data head (user threads); +0x134 = its block handle; +0xCC = its size (2048 user anchor) | D; DD; AA; II |
| +0x34/+0x38 | 64-bit CPU time accumulator (live delta added when rec == P) | I; K; II |
| +0x3C | FPU context block pointer (576 bytes: +0x10..+0x5F mirror VFPU MMIO 0xBC400000..+0x4F, +0x60 = ctrl/status word); 0 = no FPU context | KK; AA; DD |
| +0x40 | switch-frame pointer: FE4 sets it to +0x48 (kind 0) or +0x4C (kind != 0); *(frame) is the per-thread dispatch generation counter, bumped per switch | KK |
| +0x48/+0x4C | per-thread dispatch generation counters (FE4 frame slots) | KK |
| +0x44 | third frame variant (dead tail of sub_FE4) | KK |
| +0x50 | wakeupCount (pending wakeups; consumed by SleepThread, cancelled by CancelWakeupThread, donated by DonateWakeupThread) | H; L; T |
| +0x54 | exit status (rec+84; seeded 0x800201A4 by StartThread, overwritten by ExitThread before the exit core runs) | K; Y; AA |
| +0x58 | wait TYPE (the "gate" of early batches): 1 sleep, 2 delay, 3 sema, 4 evf, 5 mbx, 6 vpl, 7 fpl, 8 msgpipe, 9 thread-end, 12 mutex, 13 lwmutex, 14 tlspl | L; R; T; MM; BB; U; CC |
| +0x5C | waited-object record pointer (H/R first read it as a "cleanup flag"; LL proved it stores the rec passed to 0x1879C at teardown) | LL; H; R |
| +0x60 | wait arg / grant slot: sema wanted count, evf pattern, mbx out-slot ADDRESS, msgpipe cursor, requested block size, granted block or size on wake | R; N; V; O; Q |
| +0x64 | wait arg 2: evf mode (bit0 OR, 0x10/0x20 clears), msgpipe remaining, VPL requested size, lwmutex wanted count | R; V; O; Q |
| +0x68 | wait arg 3: evf result-out pointer, msgpipe size | R; V |
| +0x6C | msgpipe pSent/pRecv out pointer | V; W |
| +0x70 | msgpipe waitMode (0 wait-all, 1 wait-any) | V |
| +0x74 | msgpipe direction tag on the blocked waiter: 0 sender, 1 receiver | W |
| +0x78 | armed delay-timer uid (0x10FAC arm, 0x11104 cancel) | L; R; LL |
| +0x7C | timer teardown second arg (remaining-out pointer) | L; RR |
| +0x80 | waitResult, written by the waker; the wait core's return value IS this word. Doubles as the critical-cookie slot for the callback return trampoline (0x2DBC stores the cookie here) | L; LL; UU |
| +0x88 | gate: bit 8 = delete pending; nonzero = inside callback/exit machinery (blocks Delete/Exit/Start entry) | K; Y; NN |
| +0x90/+0x94 | per-thread callback queue ring anchor (next/prev) | M; MM |
| +0x98 | CB-notify arm flag: set by the sleeper, cleared by the waker; arms the "NotifyCallback may abort my wait" gate (H first read it as a "callbackQueue pointer", corrected by L) | L; H |
| +0x9C | notifyPending flag (set by NotifyCallback; the pumps test it) | H; L |
| +0xA0 | callback nesting depth (pump ++/--, read by the nesting query export) | DD; II; MM |
| +0xA4 | dispatch guard: current callback record while invoking (blocks DeleteCallback/CheckCallback) | M; DD |
| +0xA8 | owned-mutex ring sentinel (nodes are the mutex views themselves, links at view+0/+4) | BB; NN |
| +0xB0/+0xB4 | event-flag registrar link node (next/prev; registrar anchor at evf view+12/+16) | TT |
| +0xB8 | runStatus (s16) | K; NN |
| +0xBA | BASE priority (s16) | Z; BB; NN |
| +0xBC | EFFECTIVE priority ceiling imposed by held mutexes (word; 127 = unconstrained) | Z; BB; NN |
| +0xC0 | entry pointer (idle 0x172C8 / cleaner 0x125A8 / 0 when mode 0) | QQ |
| +0xC4 | kernel-stack rounded size (also the dispatch-suspension mirror slot inside the +0xDC block is at block+0xC4, not here) | AA; II; DD |
| +0xC8 | user stack fallback (thunk: user stack top when exit-info's is 0) | MM |
| +0xCC | user-stack size (2048 anchor) | AA; DD; II |
| +0xD0 | park-list head: chain of 16-byte frames parked ON the old stack during stack extension | DD |
| +0xD4 | park frame single anchor (ReturnFromChangeStack pops it) | DD |
| +0xDC | per-thread user block pointer (Tlspl block table; user frame area). Dispatch loop compares it against *(ctxblk+168); a per-thread dispatch-suspension mirror lives at block+0xC4. Batch K first read it as "user-mode frame base" | CC; HH; KK; K |
| +0xE0..+0x11C | 16-word KTLS value array (inline, no indirection) | CC |
| +0x120 | attr copy (StartThread moves it to +0x14) | AA; K |
| +0x124/+0x128 | argLen / stackTop when args were copied onto the stack | K; AA |
| +0x12C | SceKernelThreadOptParam pointer | AA |
| +0x130 | kernel-stack block handle (park uid for the extension machinery) | AA; DD |
| +0x134 | user-anchor block handle | AA; DD |
| +0x138 | partition id | AA |
| +0x13C | partition id (forced 1 for user attr) | AA |
| +0xD8 | entry copy handed to ctxblk+176 (0x172DC gets +0x188 for user threads at recycle) | K; UU |

### The k1 convention

k1 (register 27) carries the per-caller context at kernel entry: the thread
pointer/flags word of the caller. Its bit 20 is the user-mode flag.

- `sll k1,k1,11` lifts bit 20 into bit 31 (74 sites module-wide). The result
  is the kernel-address mask: sign tests on it are user/kernel mode tests
  (`bltz` = user caller).
- User-pointer gate: `((p \| p+len) & (k1<<11)) < 0` rejects a user-mode
  caller passing a kernel-space pointer, error 0x800200D3. Expected in every
  user-facing export that writes through a pointer (A @0x0ECB4).
- `srl rX,k1,31` recovers the original bit 20 as the user flag; `movz` grants
  kernel callers a bypass of every attr permission gate (B, F).
- The old k1 is saved in a callee-saved register (148 `move sX,k1` sites) and
  restored on every return path, including error paths.
- GetThreadKTLS additionally does the low-11-bit shuffle around the
  0x186AC stub (`move s5,k1; jal 0x186ac; sll k1,k1,11`), the callback-flag
  normalize (A).
- The log handler's a1 is the saved k1 keyword in the getter family only;
  other families pass other things (section 14).

## 5. UID system

Allocator and resolver are load-patched import veneers (0x1868C..0x18830
region, PP), so every `jal` to them is a literal word in retail.

**Class tables.** 16 class tables plus one shared slot table, contiguous in
the S block (see section 3 map). Type numbers are GetThreadmanIdType's
enumeration (Z @0x16784): threads 1, semas 2, event flags 3, mboxes 4, vpls
5, fpls 6, msgpipes 7, callbacks 8, TEHs 9, alarms 10, vtimers 11, mutexes
12, lwmutexes 13, tlspls 14; the Timer base class and the Delay class carry
no IdType number. The timer family registers itself as a class tree:
0x18754("Timer", 20, desc, 0, &S+0x4FC) then 0x187CC subclasses
"Delay"/"Alarm"/"VTimer" into S+0x500/S+0x504/S+0x508 (RR sub_1121C @0x1121C).

**Record layout** (common header):

| offset | field |
|---|---|
| +0/+4 | ring links (the class table's record ring) |
| +8/+12 | SceUID (rec+12 is the uid; create returns it) |
| +16 | name pointer |
| +22 | attr u16: permission bits tested with the movz kernel bypass: 0x1 refer, 0x2 operate/start/lock/signal, 0x4 wait/poll/receive, 0x8 cancel, 0x10 delete |
| +24+4*idx | per-object data (idx = hdr21) |

**The hdr21 view mechanism.** Each table header byte at +0x15 (hdr21) is a
per-table view index. Every object has multiple views onto the same record:
objView = rec + 4*hdr21(own class table) and slotView =
rec + 4*hdr21(shared slot table at module+0x508). The slot view carries the
shared wait machinery (slot+0 attr u32, slot+8 waiter count, slot+12 the
wait-ring anchor, slot+16 anchor prev; slot+4 = the msgpipe protected-head /
partial-handoff flag). Timer/alarm/vtimer objects have a third view: the
link view rec + 4*hdr21(S+0x4FC) whose +0/+4 are the active-queue links and
+8/+12 the 64-bit absolute expiry (G, J, RR).

**Allocator** 0x1875C(table, name, userByte, &rec): userByte =
(attr | userModeFlag) & 0xFF (family-wide rule, X). Returns error in v0;
rec+12 = the new uid. **Resolver** 0x18784(uid, table, &recOut): writes the
found record pointer to 0(sp), returns nonzero on failure (each family has
its own unknown-id error code). **Uid free**: 0x1877C(uid) for thread
context; sub_126AC appends to the deferred chain for contexts that cannot
walk tables (QQ). **View getter** 0x1876C(uid, table) -> view;
**membership test** 0x187FC(rec, table); **table-free resolve**
0x187C4(uid, &rec) (Z; the same veneer number also serves as a pool-handle
to SysMem-record resolver in CreateVpl, X). **Cancel-all-waiters**
0x1879C(rec, tag): tags 0x86D94883 (Cancel* family), 0x5BD49380 (sub_924
self-cleanup), 0x85FE2B4C (ReleaseWaitThread / sub_C30).

**SceUID bits 3-6 for Tlspl**: CreateTlspl patches the returned uid with
`ins s6,a0,3,4` so bits 3..6 carry the mirror-slot index; every Tlspl
operation does `ext uid,3,4` and cross-checks the 16-word mirror at
module+0x6D4 before resolving (CC @0xD880, FF, II @0xE288). The uid IS the
handle; the mirror check is a cheap validity gate that avoids the hot-path
resolve.

Sentinels: S+0x50C/S+0x510 hold the idle and cleaner TCBs; DeleteThread
refuses both with the unknown-thread error (Y @0x132B4).

## 6. Scheduler

**States**: 1 RUNNING, 2 READY, 4 WAITING, 8 SUSPENDED, 12 WAIT+SUSPENDED,
16 DORMANT, 32 dead-on-handler-list (jump tables @0x19B2C/@0x19BB0/@0x19C34,
33 entries each, cases driven by TCB+0x0C).

**Run queues**: one circular doubly-linked ring per priority 0..127. The
anchor at S+152+8*p (module+0xD8+8*p) is itself a ring member; empty iff
anchor->next == anchor. Bitmap: 4 words at S+0x88..0x94, bit 31-(p&31) of
word p>>5 set iff queue p non-empty (rotrv 0x80000000,p).

**The clz cascade** picks the most-urgent non-empty queue: r = clz(word0);
if word0 == 0 then clz(word1)+32; +64; +96; all zero gives 128. Allegrex
`clz` is SPECIAL funct 0x16 (12 such words module-wide, 3 cascades:
sub_14598 @0x147C8, RotateThreadReadyQueue @0x14A88, dispatch core
@0x173A4). All queues empty (128) is fatal: `0x18724(0x19800)` panic
(KK sub_172F8).

**Run-queue primitives**:

- sub_127D0(T) @0x127D0 (22w): insert T at the TAIL of ring[T->prio], set the
  bitmap bit. No state write; caller sets state.
- sub_16BF4(T, prio) @0x16BF4 (21w): unlink T; when the ring becomes empty
  (next == prev, next != T) clear the bitmap bit.
- sub_16C48(T, st) @0x16C48 (59w): make-ready with preemption decision. If
  T->prio < P->prio AND S+0x0C == 0 AND st != 0: requeue P at the tail of
  its own ring (P state 2), T state 1, S+4 = T, `sub_FE4(0, st)`. Else
  T state 2 (+ S+4 = 0 when st == 0, interrupt context) and sub_127D0(T).
  Insert side is the TAIL in both this and sub_127D0 (KK corrected Z's
  earlier "insert at front" reading).
- RotateThreadReadyQueue @0x14A3C: pure ring rotation, head thread moves to
  the back, bitmap untouched (Z).

**The dispatch loop** sub_12828 @0x12828 (247w, KK). Called from exactly one
place: sub_FE4+0xA8. It does NOT save or restore any GPR/k1/gp itself:

1. Return immediately if S+0x0C != 0 (only runs idle). P = *S.
2. Save the outgoing thread's FPU context MMIO 0xBC400000 -> block (if
   P+0x3C != 0), sync.
3. State gate: state 32 (dead) skips user-stack checks; user threads get
   release/anchor checks and up to three 0x177C4(P, 0/1, ptr) reports; the
   TCB+0xDC vs *(ctxblk+168) mismatch runs 0x17844(P).
4. Target selection: v0 = *(S+4); if 0 call the dispatch core sub_172F8;
   if target == current, bump S+0x14 and continue the refresh sequence.
5. CPU-time accounting: now = 0xECE4(); {P+0x34,P+0x38} += now -
   {S+0x70,S+0x74}; {S+0x70,S+0x74} = now; *(S+0x10)++; *(P->0x40 frame)++.
6. Log hook: if *(S+8) != 0, handler(msgno 1, a1 = 0, 2 = 5 extras:
   oldTid, oldPrio, newTid, flags...) via jalr.
7. The switch: if *(module+0) != 0 then *(*(module+0)) = *(target+0xDC)
   (Tlspl pointer cache); **\*(S) = target**; FPU restore loop
   (block -> MMIO) if target+0x3C != 0; optional `0x12C04(target)`
   interrupt-mask reprogram when *(ctxblk+52) & 0x40000000; then the four
   banked COP0 re-points (raw 0x40Cxxxxx words @0x12A2C..0x12A5C):
   ctc0 zero (perf bank), ctc0 a0 = *(target+0x1C) (the 320B context
   block), ctc0 t1 = *(target+0x28), ctc0 t7 = target+0x24. The exception
   stub reads these to find the new thread's register frame; k1/gp/sp/pc
   come from the 320B block at eret, outside this module.

**The dispatch core** sub_172F8 @0x172F8 (141w): deferred path first: if
*(S+0x34) != 0 (cleaner wakeup), S+4 = P, clear the flag, mark the cleaner
(S+0x510 thread) RUNNING, requeue P at its own tail if it was RUNNING.
Then the clz cascade; pick = dequeue HEAD of ring[best] with bitmap clear
when the ring empties; chosen state 1, S+4 = chosen. Preemption path (P
state 1): only when bestPrio < P->prio; dequeue the head AND requeue P at
the tail of its own ring (state 2).

**Reschedule request** sub_FE4(a0, a1) @0x00FE4 (87w): a1 == 0 (interrupt
context, cannot switch) raises a software interrupt: `ori v0,v0,0x200;
ctc0 v0,$13` + `0x186BC(0x41)`. Otherwise, if S+0x0C == 0, a cfc0 $25
hand-lock dance, `0x186E4(P+0x1C)`, then `sub_12828(s1)` and
`0x186C4(result)`. Its tail 0x1100..0x113C is dead code (no in-module
xrefs, KK).

**Preemption rules** collected: preempt only on a strictly more urgent
priority (slt, not sle); only from thread context; only when the dispatch
state is 0 and the resolver status is nonzero (StartThread @0x137B4);
ChangeThreadPriority defers to the core sub_14598 which re-runs the clz
scan and preempts only if newPrio >= scan result for the current thread.

**Dispatch lock** S+0x0C: 0 = running; 1 = dispatch suspended
(SuspendDispatchThread returns 1 iff it performed the 0->1 transition,
msgno 23); 2 = suspended with the current thread parked on the suspend list
(ResumeDispatchThread(2) re-inserts it and requests dispatch); 3 = suspended
with termination pending (written by the terminate core's self-kill-from-
interrupt path; ResumeDispatchThread(3) routes into the exit/terminate
cores). User threads keep a mirror at *(P+0xDC)+0xC4. Every blocking entry
gates on S+0x0C != 0 with 0x800201A7 (CAN_NOT_WAIT); the cookie==0-only
variant returns 0x80020066 (HH).

**Interrupt-context discipline**: cfc0 Cause != 0 makes blocking illegal
(0x80020064), cancels and refer-style reads stay legal, and wakers split:
woken == 1 in thread context dequeues and makes ready immediately
(0x16BF4 + 0x16C48); woken > 1 or interrupt context zeroes S+4 and requests
dispatch via 0xFE4 (R, EE, S dispatch tails).

## 7. Wait machinery

**The one-ring invariant** (LL): a TCB is a node in exactly one circular
doubly-linked ring at any moment; the links ALWAYS live at TCB+0x00/+0x04
and serve every queue in the module (ready rings, suspend ring, dead lists,
sleep/delay queues, object wait queues). Every move is unlink + insert. For
object waits the anchor is embedded in the slot view (view+12 = anchor.next,
view+16 = anchor.prev, empty iff anchor points at itself, view+8 = waiter
count, view+0 = attr with bit 0x100 = priority-ordered insert, view+4 = the
msgpipe protected-head flag). Sleep/delay queues are standalone head structs
(S+0x498 sleep, S+0x4E0 delay) whose own +0/+4 are the anchor.

**Wait types** (TCB+0x58): 1 sleep, 2 delay, 3 sema, 4 event flag, 5 mbx
receive, 6 vpl, 7 fpl, 8 msgpipe (send and receive share 8; TCB+0x74 tags
the direction), 9 thread-end, 12 mutex, 13 lwmutex, 14 tlspl. 10 and 11 are
not documented by any matched function.

**Going to sleep**, the generic object path (sub_680 @0x680, 118w, reached
through the 7-word veneer sub_908 which forwards rec/waitType/policyAttr/
deadline and clears the counter arg):

1. slotView = rec + 4*hdr21(slot table); timer handle TCB+0x78 = 0.
2. If a deadline was given: h = 0x10FAC(deadline, module+0xC8C template,
   TCB); on failure the error bubbles up; TCB+0x7C = arg2, TCB+0x78 = h.
3. If CB-armed AND notifyPending: disarm, cancel the timer, return
   0x800201AB without parking (the notify-abort is synthesized here too).
4. TCB+0x0C = 4 (WAITING), TCB+0x58 = waitType, TCB+0x80 = 0,
   TCB+0x5C = rec (the waited object), slotView+8++.
5. Insert into the ring: priority-ordered iff policyAttr & 0x100 (walk from
   the first, insert before the first node whose TCB+0x10 is numerically
   greater; a nonzero view+4 protects the head); else FIFO tail append.
6. Zero *(S+4), `sub_FE4(1, 1)`; the thread parks. The wait core's return
   value IS whatever the waker later writes into TCB+0x80.

Sleep/delay enqueue is sub_858 @0x858 (14w): tail-append onto the
standalone ring, state 4, TCB+0x5C = 0 (no object), then the core calls
FE4 itself. sub_890 @0x890 is the bare priority re-insert leaf (no
bookkeeping).

**The four wake paths**, all sharing the teardown invariant:

1. **Waker-driven release**: result -> waiter TCB+0x80, then sub_924.
2. **Direct handoff** (Vpl/Tlspl/MsgPipe grants): value -> head waiter's
   TCB+0x60, then sub_B08 -> sub_A08 on the head only.
3. **Timeout**: the timer core @0xC8C disarms the timer, sets
   TCB+0x80 = 0x800201A8, runs BOTH cancel tags (0x5BD49380 then
   0x85FE2B4C after the transition), then the sub_924 tail.
4. **Termination**: sub_B48(rec, exitStatus) walks the whole ring, each
   waiter gets TCB+0x80 = exitStatus plus sub_924. Queue destruction uses
   sub_C30 = `0x1879C(rec, 0x85FE2B4C)` instead.

**The teardown invariant**: whoever moves a waiting thread off its ring
must, in order: unlink via +0/+4; disarm the CB gate (+0x98); cancel the
+0x78 timer via 0x11104(handle, +0x7C) and zero both; notify the waited
object at +0x5C via 0x1879C(object, 0x5BD49380, tcb). sub_924, sub_A08,
sub_BC4 and the 0xC8C core implement exactly this sequence.

**sub_924** @0x924 (release-from-wait, 57w): killed (state 32) returns 0;
teardown as above; state 12 goes to the suspend ring (module+0x4F0) as
state 8 and returns 0; otherwise state 2 + sub_127D0, returns 1. The
return is the "transitioned to READY" bit every waker's dispatch tail
tests. **sub_A08** @0xA08 (wake-now, 64w): same skeleton, cause-aware
tail: thread context -> 0x16C48(tcb, status); interrupt context ->
0x127D0(tcb) + *(S+4) = 0. **sub_B08** @0xB08 (direct handoff, 16w):
stores the result into the head waiter's TCB+0x80 in the jal delay slot,
then sub_A08. **sub_BC4** @0xBC4 (27w): the teardown without unlink or
state change (caller owns the ring surgery).

**Sleep and delay specifics** (L, UU):

- SleepThread @0x2DF0: Cause gate, cookie, S+0x0C gate; consumes a pending
  wakeupCount without blocking if one exists; else sub_858(S+0x498, 1),
  FE4(1,1), returns TCB+0x80. msgno 48.
- SleepThreadCB @0x2EF0: same entry gates plus the callback loop: while
  notifyPending, pump (0x2170); after every wake with result 0x800201AB,
  re-pump and re-sleep; arms TCB+0x98 = 1 before parking. msgno 49.
- DelayThread/DelayThreadCB @0x3D78/@0x3D80, DelaySysClock(Thread)CB
  @0x3F9C..@0x3FA4: 2-word veneers `j core; li t3,cbFlag` (CB flag in t3,
  outside the o32 ABI). Cores 0x3D88 (usec, 133w) and 0x3FAC (SysClock,
  146w): build the absolute expiry (TCB+0x60/+0x64), arm the thread timer
  0x10FAC (template module+0x41F4, a different timer class from the object
  template module+0xC8C), TCB+0x78 = handle, sub_858(S+0x4E0, 2), FE4(1,1).
  Return 0, 0x800201A8 (timeout), or 0x800201AB (CB only).
- WakeupThread @0x3050 gate discipline: the wake-now branch fires only for
  wait TYPE 1 (sleep); a delayed thread (type 2) only gets its wakeupCount
  bumped, the timer keeps running (H, L, T). ReleaseWaitThread is
  wait-type-blind: it releases on STATE 4/12 and the teardown invariant
  cancels the delay timer (T @0x14C20).
- Wake-specific exports: CancelWakeupThread @0x3218 is the only tid==0
  means current member (returns the cancelled count);
  DonateWakeupThread @0x333C transfers the donor's pending count and
  self-sleeps.

## 8. IPC families

All families share the wrapper skeleton: k1 pointer gates (0x800200D3) ->
cfc0 Cause gate where blocking is possible (0x80020064) -> 0x186AC acquire
-> 0x18784 resolve (family unknown-uid error) -> attr16 permission gate with
the movz kernel bypass (0x800200D1) -> log -> body -> 0x186DC release ->
k1 restore. Wait veneers are 2-word `j core; li t3,cbFlag`. The three big
wait cores (sema 0x475C, evf 0x5740, mbx 0x8A78) follow the canonical
9-stage shape of batch TT: gate, enter+resolve, views, log, deadline,
CB-pump retry (0x2170 + re-resolve, 0x800201B5 when deleted while
pumping), family fast path, enqueue (0x908 -> 0x680), wake-result routing
from TCB+0x80 with the 0x800201AB retry only when CB-armed.

### semaphores (class table S+0x4D0)

Object view: +0 opt, +4 currentCount, +8 maxCount, +12 initCount snapshot.
Slot view: +0 attr. Legal attr mask 0x1FF. Waiter ordering: slot attr bit
0x100 = priority-ordered insert, default FIFO (the wait core passes the
slot attr as the policy arg).

- SignalSema @0x44D8: overflow PRE-CHECK walks the whole queue
  (current + signal - sum of wanted) against maxCount, 0x800201AE without
  touching the count; adds; wakes in queue order with head-of-line
  blocking (stops at the first waiter whose wanted count exceeds the
  remainder); while S+0x30 is set, user-thread waiters are skipped; count
  decremented per woken waiter.
- WaitSema/CB core @0x475C: fairness gate 0x4D68 first (a queued waiter
  that must be honored forces enqueue even when the count would satisfy);
  fast path consumes immediately when currentCount >= wanted.
- PollSema @0x4A34: same fairness gate, would-block is 0x800201AD; no
  Cause gate (interrupt-legal).
- CancelSema @0x4BCC: 0x1879C(rec, 0x86D94883) cancels all waiters, then
  currentCount = argument, or = initCount snapshot when the argument is
  negative (reset-to-init sentinel).

### event flags (class table S+0x4D4)

Object view: +0 opt, +4 currentPattern, +8 initPattern, +12 registrar
first-waiter pointer, +16 registrar count, +20/+24 registrar bookkeeping.
Waiter ordering: ALWAYS FIFO (the wait core passes selector 0; R).

- SetEventFlag @0x53C0: OR the pattern; full queue scan in FIFO order with
  no head-of-line stop; OR-mode matches any bit, AND-mode matches all;
  each match applies the waiter's OWN requested clears (mode bit 0x10 ->
  pattern = 0, bit 0x20 -> pattern &= ~waitPattern) and the scan continues
  with the updated pattern until the queue ends or the pattern is 0.
- ClearEventFlag @0x5618: `currentPattern &= argument`. The argument is a
  KEEP mask, not the documented "bits to clear" (R @0x56BC). No wake
  processing.
- PollEventFlag @0x5B70: mode must be subset of 0x31, both clear bits at
  once is 0x80020195, pattern 0 is 0x800201B1; single-waiter rule: unless
  slot attr bit 0x200 (multi-wait), the registrar must be empty or headed
  by the current thread ("poll from your own callback"), else
  0x800201B0; result = the PRE-clear pattern; miss = 0x800201AF.
- CancelEventFlag @0x5DB4: OVERWRITES the pattern (assignment), then the
  cancel-all tag; result count to the out pointer.
- The registrar (TT): what R called "a per-object single-waiter slot" is a
  counted registrar; the per-thread link node lives at TCB+0xB0/+0xB4.

### mailboxes (class table S+0x4E0)

Mbx view: +0 opt (raw), +4 numMessages, +8 tail pointer (newest; the head
is tail->next, the oldest). Slot view: +0 attr, +8 numWaitThreads, +12
first waiting thread. Messages are user blocks >= 8 bytes; msg+0 = next.

- Append helper 0x9338: empty ring self-loops the message; duplicate
  message pointer -> 0x800201C9; slot attr bit 0x400 selects a priority
  insert path (ordered by a byte at node+4); FIFO tail append otherwise.
- Dequeue (Poll @0x8DC0, receive core @0x8A78): re-validates the oldest
  message AND its next pointer with the k1 gate on the way out (TOCTOU
  re-validation, 0x800200D3 on failure); a single-element ring requires
  count == 1 else 0x800201C9; unlink, count--, hand out the pointer.
- SendMbx @0x88BC: when receivers are queued, direct handoff writes the
  message pointer through the receiver's saved out-slot address
  (receiver's TCB+0x60 holds the `void ** out` argument) and wakes via
  sub_B08.
- ReceiveMbx/CB core @0x8A78: wait type 5; TCB+0x60 = out argument;
  deleted-while-pumping is 0x800201B5.
- CancelReceiveMbx @0x8FF0: cancel-all tag; count to the out pointer;
  interrupt-legal.

### message pipes (class table S+0x4E4)

Pipe view (field map CORRECTED by TT; batch P first read +8 read cursor,
+12 write cursor, +16 tail):

| offset | field |
|---|---|
| +0 | opt/5th argument pointer |
| +4 | wait direction: 0 none, 1 senders queued, 2 receivers queued |
| +8 | data BASE (block data head) |
| +12 | WRITE cursor |
| +16 | READ cursor |
| +20 | bufSize |
| +24 | usedBytes |
| +28 | SysMem block handle |

Slot view: +0 attr, +4 protected-head/partial-handoff flag, +8 waiter
count, +12 wait-ring anchor.

- Ring primitives: write 0xAFC0(pipe, src, n) and read 0xB094(pipe, dst,
  n), two-segment wrap copies around the base; callers guarantee n fits.
- Send core 0x97E0 (359w, V): receivers queued -> direct copy into each
  receiver's buffer (0x1880C into TCB+0x60 dst), wake on wait-any-progress
  or full need; senders queued -> FIFO discipline with a priority bypass
  (slot attr 0x100 AND no partial handoff in progress AND my prio beats
  the head's); buffer path writes via 0xAFC0 iff (wait-any and n > 0) or
  (wait-all and n == remaining); partial sends return SUCCESS with the
  count in pSentSize; blocks with TCB wait fields +0x60 src cursor,
  +0x64 remaining, +0x68 size, +0x6C pSent, +0x70 mode, +0x74 = 0
  (sender tag), wait type 8.
- Receive core 0xA1B4 (377w, W): mirror of the send core plus a
  ring-drain: the receiver pushes a blocked sender's remaining bytes into
  the ring itself under the same wait-any/wait-all discipline; partial
  sender stays queued with the protected-head flag set; receiver blocks
  with +0x74 = 1; its priority selector is (attr >> 4) & 0x100, i.e. slot
  attr bit 0x1000, which is why the receive-side bypass gate reads 0x1000
  while the send-side reads 0x100.
- TrySend @0x9D7C returns 0x800201B3 (full) iff it would block; a mode-0
  pre-scan adds every queued receiver's want to the free space before the
  fits test. TryReceive @0xA798 returns 0x800201B4 (empty). Both read
  Cause after resolve and never block: interrupt-legal.
- CancelMsgPipe @0xAC20: cancel-all tag; count routed to sendN or recvN by
  the pipe's direction; resets used = 0 and both cursors to the base;
  empties the pipe.
- SceKernelMsgPipeInfo 56 B: +0 size, +4 name[32], +36 attr, +40 bufSize,
  +44 freeSize, +48/+52 send/recv wait counts (routed by direction).

### mutexes (class table S+0x4D8)

Object view: +0/+4 owned-list links, +8 uid, +12 opt, +16 initCount,
+20 current count, +24 owner TCB (0 unlocked, -1 after an 0x800
exit-release), +28 ceiling priority (default from S+0x6D8 when nonzero
else the creator's current priority; kernel 1..126, user 8..119). Legal
attr mask 12 bits: 0x100 priority-ordered queue, 0x200 recursive, 0x400
priority ceiling, 0x800 persistent-across-exit.

**Priority ceiling, not inheritance.** The holder's priority is raised only
to the static ceiling at ACQUIRE time and re-evaluated at RELEASE time. No
code path raises a holder to a waiter's priority (BB, EE, NN):

- sub_6604(rec, TCB, count): count/owner stores; links the mutex into the
  owner's TCB+0xA8 ring (0x400 mutexes inserted SORTED by ascending
  ceiling); for 0x400 only: TCB+0xBC = min(TCB+0xBC, ceiling), and if that
  beat the run-queue priority, requeue via 0x14598.
- sub_7480(rec): full relinquish; when the ring empties, TCB+0xBC = 127
  and requeue at the s16 base; with 0x400 mutexes remaining, the FIRST
  (sorted) entry sets the ceiling and the requeue priority is
  min(ceiling, base). Textbook Immediate Priority Ceiling.
- sub_66F0(TCB) at exit/delete/terminate: walks the owned ring; 0x800
  mutexes keep their lock (owner = -1, waiters stranded); others count = 0,
  owner = 0, queue purged via 0xC30; resched iff boosted or waiters were
  cancelled.
- Lock core 0x6A7C (246w): block iff a candidate waiter exists AND (FIFO
  OR the caller does not strictly outrank it); user waiters are invisible
  to the fast path while S+0x30 is busy; the owner==0 fast acquire is only
  reachable after the queue objection test passes. Recursive path requires
  attr 0x200 (else 0x800201C8), overflow 0x800201C6.
- UnlockMutex @0x67F4: owner check 0x800201C5 before the underflow check;
  underflow is a strict `<` (equal-to-zero is legal), 0x800201C7; partial
  unlock (count still > 0) serves NOBODY; full unlock relinquishes, then
  hands off to exactly ONE waiter: 0x6604(rec, waiter, waiter's wanted
  count) applies the ceiling boost to the NEW owner, then sub_924;
  remaining waiters re-block on the new owner.
- TryLockMutex @0x6E54: NO fairness gate at all (contrast PollSema's
  0x4D68); owner==0 acquires regardless of queued waiters; any other owner
  is 0x800201C4.
- CancelMutex @0x705C: interrupt-legal iff newCount == 0; relinquish +
  cancel-all + optional re-acquire for the caller with a fresh ceiling
  boost ("kick everyone, hand it to me").
- ReferMutexStatus @0x7258: ownerId = owner tid; owner==0 maps to -1;
  owner==-1 (stranded 0x800 mutex) maps to -2.
- DeleteMutex @0x64F0: NO waiter walk and NO owner check; deleting a
  locked mutex leaves the owner's owned ring pointing into freed memory
  (see section 15).

### lightweight mutexes (class table S+0x4DC)

Not a UID handle API: calls pass a 32-byte SceLwMutexWorkArea embedded in
the caller's memory, tied to a kernel UID record at create time. Work
area: +0 lock count, +4 owner (thread ID uniformly; batch Q first read a
mixed pointer/id representation, resolved by U: create/trylock store
*(P+8) = the current thread's id, the wake handoff stores the waiter's
*(TCB+8)), +8 attr, +12 pad, +16 uid (Delete writes -1), +20..+28 zeros.
Record views: lwm view +8 uid, +12 pWork back-link, +16 name, +20
initCount; slot view as usual.

- The resolver runs on work+16; the back-link check (stored pWork must
  equal the caller's pointer) rejects cloned/stale work areas with
  0x800201CA (same code as an unresolvable uid).
- The work-area pointer itself is k1-gated; CreateLwMutex additionally
  ANDs the mask with a constant so user callers always fail:
  kernel-only (Q).
- Waiter ordering: queue order only, attr bit 0x100 priority-ordered
  insert via the same sub_680 selector as semaphores. **Neither ceiling
  nor inheritance**: no write to any holder priority anywhere in the
  family (U).
- Recursive counting gated on attr 0x200 (0x800201CF without,
  0x800201CD on overflow); count >= 2 also requires 0x200
  (0x800201BD).
- UnlockLwMutex @0x7A5C: not-owner is 0x800201CC, count underflow
  0x800201CE; full release hands off to the first waiter (count = its
  wanted count from TCB+0x60, owner = its tid, sub_924 wake pair).
- DeleteLwMutex @0x7908: frees the uid, writes -1 to work+16 and -1 (not
  0) to work+4; no waiter check, waiters strand (0x800201B5 on their
  next re-resolve).
- Lock core 0x7CE4 (236w): wait type 13; an inline slt pre-check
  short-circuits into the owner fast-path when the mutex is momentarily
  unlocked and the caller outranks the head waiter; no other bypass.

### variable pools (class table S+0x4E8)

Object view: +0 opt, +4 SysMem pool handle, +8 pool free size (queried at
create). Legal attr mask 0x43FF; user callers need a user-accessible
partition (0x187BC query, *(sp+12) & 3 == 3). The free list itself lives
in SysMem (imports 0x18774 alloc, 0x187A4 validate, 0x1878C create,
0x1874C free-size, 0x187E4 data head): not decodable from this module.
CreateVpl @0x0B44C rolls back the uid on pool failure; attr bit 0 tags
the SysMem record's attr16 with bit 1. Allocate core 0xB7E4: wait type 6,
FIFO with a head-priority bypass, direct grant when the pool satisfies.
FreeVpl @0x0BCB4: validates the block (0x800201B6), walks the waiter
queue granting each waiter a block of its requested size (0x18774,
written to TCB+0x60 in the wake jal's delay slot); slot attr 0x200 = skip
an unsatisfiable waiter and keep walking, otherwise the walk aborts.
CancelVpl @0xBEFC: cancel-all twin of CancelFpl.

### fixed pools (class table S+0x4EC)

Object view: +0 opt, +4 data base, +8 free-slot ring head, +12 free-index
table (allocated from the threadman pool when numBlocks >= 3, else inline
at +36), +16 numFreeBlocks, +20 blockSize, +24 numBlocks, +28 stride
(aligned blockSize), +32 SysMem block handle. Alignment from opt+4 must
be a power of two >= 4 (0x800200D2); 64-bit stride*count overflow is
0x800201B7; legal attr mask 0x41FF (attr bit 0x4000 selects a different
SysMem pool type).

- Free ring helpers: push 0xD2E4 (slots[idx] must be empty else -1) and
  pop 0xD38C (returns the index), the same pair the Tlspl family uses.
- Allocate core 0xC950 (179w): wait type 7; pop a free index, block =
  base + index*stride; empty pool blocks (CB retry loop as usual); grant
  lands in TCB+0x60.
- TryAllocateFpl @0xCC1C: empty pool is 0x80020190; direct pop, no
  fairness gate.
- FreeFpl @0xCDBC: inline block validation (base <= block <
  base+stride*n, exact stride multiple, free-table slot must be 0 ->
  0x800201B6); exactly ONE waiter woken per freed block via sub_B08 with
  the block in its TCB+0x60; no waiter -> push the index back.

### tls (two systems)

**Tlspl (user TLS, class table S+0x4F0 / module+0x530)**: at most 16 pools
(the 16-word uid mirror at module+0x6D4). CreateTlspl @0xD574: ONE SysMem
block for the whole pool (count * aligned blockSize, 64-bit overflow
check); uid patched with the mirror index in bits 3-6; pool view +0 opt,
+4 dataHead, +8 freeCount, +12 index table, +20 size, +24 count, +28
stride, +32 block, +36/+40 inline table. Per-thread association: the
thread record holds a block-table pointer at +0xDC; block pointer at
table+0x40+4*idx. AllocateTlspl @0xDC10: an existing block returns
directly; pool exhausted -> wait type 14 (priority insert iff slot attr
0x100), grant in TCB+0x60. FreeTlspl @0xDEC8: with waiters, the block is
handed DIRECTLY to the head waiter (TCB+0x60 + sub_B08); else memset and
push-back. DeleteTlspl @0xDA10: only when all blocks are free (or one
outstanding owned by the caller), else 0x800201D2. Thread exit walker
0xE0D4 returns the dying thread's blocks and serves sleeping allocators.

**KTLS (kernel TLS, descriptors at module+0x554)**: 16 global descriptors,
24 bytes each (inUse, refcount, size, destructor, arg, validated gp).
Values live INLINE in each thread record at +0xE0+4*id (no indirection).
GetThreadKTLS(id, tid, flag): id 0..15, NULL from interrupt context;
value already set -> returned (peek); unset and flag != 0 -> lazy
allocation from the threadman pool (module+0x820), zeroed, refcount++.
AllocateKTLS @0x11A24 takes the first free descriptor (0x800201C1 when
full); FreeKTLS @0x11B5C frees the DESCRIPTOR only, refused while any
thread still holds a value (0x800201C2). Exit walker 0x11E3C scans ids
15..0: runs the destructor INLINE (gp swap to the descriptor's gp) iff
the dying record is the current thread, frees the block, decrements the
refcount. GetKTLS @0x11F48 is the (id, 0, 1) veneer.

## 9. Callbacks

**Records** (class table S+0x4F8): view fields +0/+4 queue links, +8 uid,
+12 in-flight count, +16 deferred-delete marker, +20 owner TCB, +24
notifyCount, +28 notifyArg, +32 user flag, +36 function, +40 common,
+44 validated gp (0x1873C(func) result or the creator's gp). Create links
the view into the OWNER's callback queue ring at TCB+0x90/+0x94
(sceKernelCreateCallback @0x19D8, M).

**Notify path**: sceKernelNotifyCallback @0x1CC0 only records the pending
count/arg and notifies the owner: owner TCB+0x9C = 1, notifyCount++,
notifyArg stored; when the owner is currently waiting (state 4/12) its
wait is broken with the synthetic result 0x800201AB so a pump can run
(H). The count/arg live in the record at +24/+28 (offset by the view
index); CancelCallback zeroes them, GetCallbackCount returns them (F).

**The pump** sub_2170 @0x2170 (133w, MM/DD):

- Walks the current thread's queue ring from TCB+0x90; clears
  notifyPending (TCB+0x9C) in the branch delay.
- Per node: skip notifyCount == 0; skip nodes with the deferred-delete
  marker set; consume one notification (zero count and arg);
  TCB+0xA0 nesting++, TCB+0xA4 = the record (dispatch guard), node+12
  in-flight++; log msgno 7; then the invoke thunk.
- After invoke: guard restored, in-flight--, nesting--; a node whose
  deferred-delete is armed and whose in-flight count drained to 0 is
  unlinked and its waiters completed via sub_B48; a nonzero callback
  result with no deferred-delete auto-deletes the uid (0x1877C).
- Epilogue: dispatch-state fixup 0x14124(1, 0) when S+0x0C != 0; if any
  callbacks were deleted, S+4 = 0 and FE4(0). Returns the number executed.
- Entry points: sceKernelCheckCallback @0x2078 (returns TRUE iff the pump
  executed at least one; gates on Cause, TCB+0xA4, cookie, S+0x0C); the
  CB-variant wait cores run the pump on every notify-abort retry.
  sceKernelGetCallbackCount-family export 8672E3D0 @0x272C is the nesting
  query: returns *(P+0xA0) with no uid machinery at all (II).

**The invoke thunk** sub_2944 @0x2944 (126w, MM): the PSP's entire
usermode-callback mechanism. It never calls user code itself; it swaps the
thread's resume context:

1. Builds a 448-byte exception frame at a 64-byte-aligned sp
   (`ins s6,zero,0,6`); 0x134A8 poison-fills it: GPR slots
   frame+64..+188 = 0xdeadbeef, FPU area +192..+316 = 0x7F800001,
   +40 = 0xE00, +44/+48 = 0xdeadbeef/0, +52/+56/+60/+64 = 0.
2. Loads the resume registers: EPC (frame+56) = the callback function;
   a0/a1/a2 = (notifyCount, notifyArg, common); a3 = 0;
   gp (frame+176) = the callback's own gp from view+44 (the gp swap);
   Status (frame+52) = 19 (0x13: IE|EXL|UM, user-mode resume); cause
   word (frame+36) = 3.
3. Parks the kernel context on the thread record: validates the exit-info
   block pointer via 0x186E4(P+0x1C) (delay slot stores the old value at
   P+0x84), saves P+0x24/P+0x28/P+0x18, detaches the FPU context
   (clears attr bit 0x4000 while the callback runs).
4. Return-address arming, by flavor:
   - kernel callback (user flag 0): ra (frame+188) = the in-module
     trampoline 0x2DBC = `cookie = 0x186AC(); P = *(S);
     *(P+0x80) = cookie; jal 0x28C0`.
   - user callback: picks the user stack top, subtracts 64, and WRITES A
     `syscall` INSTRUCTION THERE: code field from the module dword
     module+0x81C as `(word << 6) & 0x3FFFFC0 | 0xC`; zeroes the
     following 12 bytes; flushes icache (`cache 0x1b`, `cache 0x8`,
     `sync`); sets sp = fp = ra = the gadget address. The callback runs
     on a 64-byte scratch below the user stack top and its `jr ra` fires
     the gadget.
5. Hands off: `ctc0 *(P+0x28),$15; ctc0 frame,$14`, then
   `0x186C4(frame)` (the real context restore lives in another module).
   Returns 0 to the pump.

**Reentry**: the patched syscall (or the 0x2DBC trampoline) lands in
_sceKernelReturnFromCallback @0x253C / sub_28C0: re-enter critical, P =
current, restore the swapped P-fields, re-check the Status bit 0x4000 and
the FPU attach dance, `0x186C4(*(P+0x84))` restores the kernel context.
The syscall templates registered at module_start (S+0x7D4/0x7D8/0x7DC)
are exactly these re-entry gadgets (QQ).

**Nesting and guards**: TCB+0xA0 counts nesting; TCB+0xA4 holds the
running record and blocks CheckCallback/DeleteCallback (0x80020064);
the in-flight count (view+12) makes DeleteCallback/CancelCallback safe
while an invocation is live; the deferred-delete marker (view+16)
completes the delete after the last invocation drains (auto-delete on
nonzero callback result only when no delete is armed).

## 10. Timers

**Hardware model** (RR): SysTimer MMIO at 0xBC600000:

| register | meaning |
|---|---|
| 0xBC600000 | counter (read = overflow ack) |
| 0xBC600004 | compare/deadline |
| 0xBC600008 | prescale (48) |
| 0xBC60000C | enable (1) |
| 0xBC600010 | mode / irq-clear (0) |

**Clock read** sub_ECE4 @0xECE4 (16w): now64 = {module+0xB8 lo,
module+0xBC hi} + counter. module+0x00 is the counter SHADOW: seeded at
init, refreshed every tick. GetSystemTimeLow @0x10D28 reads the MMIO counter
directly.

**The deadline channel**: every deadline reaches the hardware through
module+0xC0/+0xC4. The reprocess scan sub_EB7C @0xEB7C walks the active
queue (anchor module+0xA8) for the soonest entry (seeded with the
module+0x82C bias added to the head expiry), reads now, and programs:
winner already passed or within the module+0x82C margin -> deadline =
now + margin, else the winner's expiry; stores it to module+0xC0/+0xC4
and mirrors the LOW word to 0xBC600004, then sync (MM).

**The 0xF0000000 kick**: the tick fixup sub_112F8 @0x112F8 refreshes the
shadow `*(module+0) = counter` inside the 0x18704 ack delay slot, then
checks delta = deadline_lo - shadow: if delta == 0 or delta >u 0xF0000000
(the wrap window), it forces shadow = deadline_lo - 1, so the next
re-program kicks an immediate interrupt and forces queue reprocessing
when the programmed deadline can no longer fire on time (RR).

**Queue discipline**: sorted ascending insert sub_EAE0 @0xEAE0 into the
module+0xA8 ring (64-bit expiry at link+8/+12); cancel paths unlink with
a beql head fixup against the head cache module+0xA4. sub_1136C is the
cold-start/full reprogram (enable + prescale + seed + compare + subint
enable 0x186BC). Interrupt handler sub_E80C (registered at init): copies
the deadline to module+0xB8/0xBC (it becomes the new epoch), walks the
ring, fires expired entries, reprocesses (SS).

**Delay timers**: class S+0x500 ("SceThreadmanDelay"). Arm sub_10FAC
@0x10FAC: recycles from the free pool (S+0x24 count / S+0x28 head),
falls back to a fresh class record; link expiry = the caller's absolute
deadline; timer view +0 = arg2, +4 = TCB. Cancel sub_11104 @0x11104:
computes the remaining time for the caller's out pointer (via the 64/32
divmod 0x113F0), unlinks, pushes the record back to the pool via 0xEEB0,
reprocesses. The delay cores store the handle at TCB+0x78 and the
remaining-out at TCB+0x7C; the wait teardown cancels it.

**Alarms**: class S+0x504. Create core 0x116F4 (80w): expiry = argument64
+ now64 (BOTH SetAlarm @0x10DF4 and SetSysClockAlarm @0x10EBC are
relative); alarm view +0 user byte, +4 handler, +8 common, +12 validated
gp or raw gp, +16 state (1 = cancel in progress); the link view carries
the expiry. Expiry dispatcher sub_1147C (62w): arms the S+0x60 sentinel
uid, logs msgno 5, swaps gp to the stored one, calls the handler OUTSIDE
the critical section in thread context (re-acquire after), or defers via
0x186EC in interrupt context; recycles the node. CancelAlarm @0xED24
checks the sentinel uid first (0x8002019F), unlinks the active-list
entry, then the thread-context 0x1877C or interrupt-context 0x126AC
delete, then reprocesses. ReferAlarmStatus @0xEF24 builds the 20-byte
SceKernelAlarmStatus in the shared scratch (module+0x714 is the master
template, G).

**Vtimers**: class S+0x508. Object view: +0 active, +4/+8 64-bit time
face (base while running = schedule-relative, elapsed while stopped),
+0xC/+0x10 64-bit schedule, +0x14 user flag, +0x18 handler, +0x1C common,
+0x20 gp marker (Wide setters store gp directly). Start @0xFDB4:
elapsed -> base, expiry = sched + base inserted into the active queue
when a handler is armed; Stop @0xFFBC unlinks. Set-on-active re-arms the
queue: SetVTimerTime recomputes the base so the new schedule elapses
from now, unlinks and reinserts (GG); SetVTimerHandler swaps handler/
schedule/common and re-arms immediately; CancelVTimerHandler disarms
without reinserting. The expiry dispatcher sub_11574 (96w) mirrors the
alarm one (msgno 6, 16-byte remaining-time frame handed to 0x186EC in
interrupt context). Sentinel uid (S+0x60) checked by Start/Stop/
HandlerSetters: 0x800201BF. GetVTimerBase/Wide: a STOPPED timer's base
reads as {0,0} (retail quirk, DD); GetVTimerTime computes now - base
while running. SetVTimerTimeWide error paths return -1/-1, not SCE
codes (GG).

## 11. Exit and termination

**Exit cores.** sceKernelExitThread @0x139C8 and sceKernelExitDeleteThread
@0x13AC4 are thin (63 words each, Y): Cause and TCB+0x88 gates; negative
status replaced with 0x800200D2; the status is stored to TCB+0x54 in the
log branch's delay slot (BEFORE the log and BEFORE the core); msgno 19/20;
then the never-return core sub_178C0(deleteFlag, cookie, status).

**sub_178C0 @0x178C0** (85w, NN): asserts S+0x0C == 0 (a nonzero state is
force-cleared with a 0x18724 panic and the kill continues); deleteFlag
sets TCB+0x88 bit 8; TEH dispatch class 4 (0x1580); the teardown chain:
0x11E3C (KTLS walker), sub_B48(rec, status) (type-9 waiter completion),
0x60D4, 0x66F0 (mutex mass-release), 0x26CC (callback purge), 0xE0D4
(Tlspl walker). Plain exit: insert into the dead list at S+0x4A8 (state
16), S+4 = 0, FE4(1,1). Delete leg: TEH class 8, state 0, deferred uid
free 0x126AC(id), same FE4 tail. Both legs then hit a 0x18724 panic +
break loop: the caller NEVER resumes (the thread is off-CPU from the
FE4).

**The entry-return trampoline** 0x13E80 (109w, UU): StartThread installs
it at ctxblk+56; when a thread's entry function RETURNS, control lands
here. It dispatches TEH class 2, poison-refills the context block,
ctxblk+36 = 3 (runStatus), ctxblk+84 = 0x800201AC, ctxblk+188 = 0x172DC
(user) / TCB+200 (kernel), re-points entry/stack/gp, and the thread is
recycled onto the dormant list rather than freed. 0x172DC is the
exit-with-status path the trampoline slot holds for user threads.

**The terminate core** sub_17A14 @0x17A14 (296 words, one function; the
live-kill path @0x17B68 is an internal block, NN). Exported pair:
sceKernelTerminateThread @0x13BC0 is legal FROM AN INTERRUPT handler
(validates 0x187AC then continues); TerminateDeleteThread is not (the
core rejects deleteFlag && cause with 0x80020064). Entry: target == self
in thread context 0x80020197; state 0 0x80020198; dead target: plain
Terminate 0x800201A2, TerminateDelete runs the full delete cleanup.

The live-kill protocol (NN):

1. Gate/park: killing myself from an interrupt with dispatch suspended
   sets S+0x0C = 3 and returns 0 (deferred to ResumeDispatchThread(3)).
   Target gate (TCB+0x88) & 0xC set: already exiting, plain Terminate
   0x800201A2, TerminateDelete just arms gate bit 8. Clean target:
   exitStatus = 0x800201AC. A nonzero S+0x0C is force-cleared (panic
   print, kill continues).
2. Teardown prep (0x2570 TEH refcount--, 0x27B4 callbacks, KTLS walker);
   the 0x25FC gate may run the FULL inline teardown immediately.
3. State analysis: state 4/8/12 unlinked from its queue (wait states also
   cancel the timer via sub_BC4 and purge the object queue via 0xC30).
4. **The retarget**: the victim's context block is rewritten so that when
   it is next scheduled it "falls out" of its entry function straight into
   the exit core: ctxblk+56 = 0x178C0 (the slot StartThread fills with
   0x13E80), runStatus 3, exit status 0x800201AC, the entry/stack/gp
   fields rebuilt. State set to 2 and 0x127D0(view) dispatches it.
5. Completion: interrupt context returns immediately (the retargeted
   victim exits when dispatched); TerminateDelete in interrupt context
   does the inline delete (TEH class 8, unlink, 0x155B8, uid free).
   Thread context: **the terminator enqueues ITSELF as a type-9 waiter on
   the victim and blocks** (0x908(rec, 9, 0, 0, 0)); the victim's exit
   completes it with 0x800201AC. TerminateThread is synchronous.
6. Dead-list tail: user threads without a user frame go straight to the
   list; runnable/queued threads unlinked by state (state 2 clears the
   runq bitmap bit); dead list = S+0x4A8, state 16.

**DeleteThread** @0x132B4 (125w, Y): requires the target dead (state 0x10
or 0x20, else 0x800201A4); rejects the two sentinel records; TCB+0x88
gate; TEH class 8 (0x1580(8, rec, cookie, tid)); teardown A/B 0x60D4 +
0x66F0; unlink; state = 0; 0x155B8 final cleanup; uid free. NO waiter
handling: a deletable thread is already dead, its type-9 waiters were
completed at exit time. The tid==0 path has the 0x1A4 quirk (section 15).

**The dead lists and handlers**: plain exit parks at S+0x4A8 (state 16,
deletable by DeleteThread). sub_1752C @0x1752C (166w, contains the
deferred 0x177AC block) is the shared post-exit teardown: unlinks from
whatever list holds it (runq bitmap cleared when the ring emptied),
sub_B48 with 0x800201AC, the 8-callee chain, a death report via 0x18724,
and insertion into the SECOND dead list at module+0x4F8 (state 32,
exitStatus 0x800201A2) where the registered dead-thread handler
(module+0x838, RegisterDeadThreadHandler @0x17138) gets invoked with the
uid; DeleteThread's state test accepts BOTH lists. Dispatchers 0x177C4
and 0x17844 feed records into sub_1752C (NN, UU).

## 12. Stacks

**Per-thread stacks**: a kernel stack block (CreateThread, >= 512 bytes,
0x80020194 below) and, for user threads, an extra 2048-byte user anchor
block in partition 1 (rec+0x30 data head, +0x134 handle, +0xCC size). The
thread id is stored at the data head's first word (the anchor-word
convention, StartThread and module_start).

**Extension mechanism** (DD): the old stack is never moved.

- sceKernelExtendKernelStack @0x152C0 (190w): kernel-only; allocates a new
  block named from the string pool; inside the critical section builds a
  16-byte frame ON THE OLD STACK at sp+0..12: frame[0] = previous park
  head (TCB+0xD0), frame[4/8/12] = the old {data head, block handle,
  size} triple (kernel or user variant by attr sign); pushes the frame as
  the new park-list head (TCB+0xD0 = sp); stores the new values into the
  TCB slots; switches `sp = data + size` around SPECIAL2 barrier words;
  runs the function; restores sp; pops the frame (restore the triple,
  TCB+0xD0 = frame[0]); frees the block. attr bit 0x20 adds cache-range
  ops (0x18764) on both ends.
- sceKernelExtendThreadStack @0x1512C (101w): the thin sibling; delegates
  to the stack-switch runner sub_17EB4 @0x17EB4 (126w: 64-byte parked
  frame on the target stack, FPU poison table 0x3F80xxxx, cache flushes,
  0x186B4 finish). **On success it returns 0xDEADBEEF** (lui/ori
  dead/beef; the function result in s0 is discarded). Same marker from
  the user temp-stack runner 28BFD974 @0x1502C (II).
- _sceKernelReturnFromChangeStack @0x14F10: pops the SINGLE frame at
  TCB+0xD4 (the runner's anchor), restores the triple plus three words
  into the exit-info block, frees the parked block, returns
  [TCB+0x24]+0x18. Cause != 0 or an empty anchor breaks (0x0003FFCD).
- Exit-side cleanup: 0x156BC walks both park anchors (TCB+0xD0/+0xD4)
  freeing parked blocks; 0x18504 (delete teardown) frees the kernel/user
  anchor blocks.

**Stack queries**: CheckThreadKernelStack @0x17044 and CheckThreadStack
@0x157C8 return sp - anchor (kernel +0x2C, user +0x30, or the parked
user anchor via [TCB+0x24]+8), with a 64-byte overflow threshold that
triggers the report path (0x186AC / 0x186E4(P+0x1C) / 0x177C4 / FE4).
GetThreadStackFreeSize @0x15928 and GetThreadKernelStackFreeSize
@0x15A8C scan the 0xFFFFFFFF fill from the stack top and return the
untouched bytes.

## 13. Error code catalog

| code | meaning | function(s) |
|---|---|---|
| 0x80020064 | illegal context (interrupt) | all blocking entries |
| 0x80020066 | cannot dispatch (cookie == 0 variant, release(0)) | Suspend/ResumeDispatchThread, SuspendAllUserThreads, RegisterTEH |
| 0x800200D1 | illegal permission (attr16 gate) | all families |
| 0x800200D2 | illegal alignment / bad id | CreateFpl opt, GetThreadmanIdType, IdOwner; ExitThread negative status |
| 0x800200D3 | illegal address (k1 pointer gate) | all pointer arguments |
| 0x80020190 | allocation failed | CreateThread, CreateVpl, pool creators, TryAllocateFpl, timer arm |
| 0x80020191 | illegal attr (family mask) | all creators, ChangeCurrentThreadAttr, RegisterTEH mask |
| 0x80020192 | illegal entry pointer (alignment) | CreateThread |
| 0x80020193 | illegal priority (user 8..119, kernel 1..126) | CreateThread, ChangeThreadPriority, RotateThreadReadyQueue, CreateMutex ceiling |
| 0x80020194 | illegal stack size (< 512) | CreateThread, ExtendThreadStack/KernelStack, 28BFD974 |
| 0x80020195 | illegal mode (msgpipe waitMode; evf mode mask) | msgpipe cores, Poll/WaitEventFlag |
| 0x80020196 | illegal event-handler mask | RegisterThreadEventHandler |
| 0x80020197 | illegal thread id / context (tid == 0, self-ops) | Wakeup, Suspend, Resume, Start, Terminate, WaitEnd, uid==0 refer |
| 0x80020198 | unknown thread id / duplicate deferred uid | thread ops, DeleteThread, cleaner |
| 0x80020199 | unknown semaphore id | sema family |
| 0x8002019A | unknown event flag id | evf family |
| 0x8002019B | unknown mbx id | mbx family |
| 0x8002019C | unknown vpl id | vpl family |
| 0x8002019D | unknown fpl id | fpl family |
| 0x8002019E | unknown msgpipe id | msgpipe family |
| 0x8002019F | unknown alarm id / alarm busy (sentinel or active cancel) | alarm family |
| 0x800201A0 | unknown thread-event-handler id | TEH release |
| 0x800201A1 | unknown callback id | callback family |
| 0x800201A2 | thread is dead/dormant-illegal / default exit status of the dead list | Wakeup, Suspend, Start, Delete, Terminate, ChangePriority; seeded at create/start |
| 0x800201A3 | already suspended | SuspendThread (state 8/12) |
| 0x800201A4 | not dormant / DeleteThread dead-path default | StartThread, DeleteThread (also the 0x1A4 quirk) |
| 0x800201A5 | not suspended | ResumeThread |
| 0x800201A6 | not waiting | ReleaseWaitThread (state not 4/12) |
| 0x800201A7 | cannot wait (CAN_NOT_WAIT: cookie 0 or dispatch suspended) | sleep/delay/wait cores, CheckCallback, deletes |
| 0x800201A8 | wait/delay timeout | delay cores, timeout core |
| 0x800201AA | wait released (ReleaseWaitThread result) | ReleaseWaitThread |
| 0x800201AB | wait aborted by notify (callback pump retry) | NotifyCallback, sub_680, all CB wait loops |
| 0x800201AC | thread terminated | terminate core exit status |
| 0x800201AD | poll semaphore failed / would block | PollSema, sema wait core |
| 0x800201AE | semaphore overflow (count + waiters > max) | SignalSema, sema wait |
| 0x800201AF | event flag no match | PollEventFlag |
| 0x800201B0 | event flag busy (registrar held by another thread) | PollEventFlag |
| 0x800201B1 | event pattern is zero | Poll/WaitEventFlag |
| 0x800201B2 | mbx no message | PollMbx |
| 0x800201B3 | msgpipe full (TrySend would block) | TrySendMsgPipe |
| 0x800201B4 | msgpipe empty (TryReceive would block) | TryReceiveMsgPipe |
| 0x800201B5 | object deleted while waiting (CB re-resolve) | all CB wait cores, LwMutex delete |
| 0x800201B6 | illegal free block (pool validation) | FreeVpl, FreeFpl, FreeTlspl |
| 0x800201B7 | illegal size / overflow | CreateVpl/Fpl/Tlspl, VPL/FPL allocate |
| 0x800201BB | illegal id type | GetThreadmanIdType/List |
| 0x800201BC | illegal size (msgpipe bufSize < request; refer size verify) | msgpipe family, ReferThreadStatus |
| 0x800201BD | illegal count (count <= 0, or >= 2 without recursive attr) | mutex/lwmutex create/lock/poll, sema wait |
| 0x800201BE | unknown vtimer id | vtimer family |
| 0x800201BF | vtimer sentinel uid | vtimer Start/Stop/HandlerSetters |
| 0x800201C0 | KTLS id not in use | FreeKTLS |
| 0x800201C1 | KTLS descriptor table full | AllocateKTLS |
| 0x800201C2 | KTLS descriptor busy (refcount) | FreeKTLS |
| 0x800201C3 | unknown mutex id | mutex family |
| 0x800201C4 | try-lock would block | TryLockMutex |
| 0x800201C5 | not mutex owner | UnlockMutex |
| 0x800201C6 | mutex recursive count overflow | lock cores |
| 0x800201C7 | mutex count underflow (strict <) | UnlockMutex |
| 0x800201C8 | mutex not recursive | lock cores |
| 0x800201C9 | message already queued / ring count mismatch | mbx append/dequeue |
| 0x800201CA | unknown lwmutex id or back-link mismatch | lwmutex family |
| 0x800201CB | bad id for owner query | GetThreadmanIdOwner |
| 0x800201CC | lwmutex not owner | UnlockLwMutex |
| 0x800201CD | lwmutex recursive count overflow | lwmutex cores |
| 0x800201CE | lwmutex count underflow | UnlockLwMutex |
| 0x800201CF | lwmutex not recursive | TryLock/lock core |
| 0x800201D0 | unknown tlspl id (mirror mismatch) | tlspl family |
| 0x800201D1 | tlspl mirror table full (16 pools) | CreateTlspl |
| 0x800201D2 | tlspl busy (outstanding blocks) | DeleteTlspl |

## 14. Log msgno catalog

Handler signature: `TmLogHandler(msgno, a1, nextra, ...)`; extra words flow
a3, then t0, t1, t2. a1 conventions vary BY FAMILY, the main source of
cross-batch confusion:

- **a1 = saved k1 keyword**: the no-argument getters (29, 37, 38, 43, 48
  is module base, 131/132 vary), DeleteCallback (157), ReleaseTEH (46).
- **a1 = first syscall argument** when one exists: out pointer (131
  GetSystemTime, 164 ReferSystemStatus), uid (140, 141, 165), cbid (159),
  pWork (lwmutex family 82-87), func (138 SetAlarm).
- **a1 = &S**: Cancel/GetCallbackCount (159/160), the wait-no-arg entries
  (55/56 WaitThreadEnd, 93-95 mbx, 100-class msgpipe send receivers
  vary), Refer* (64, 73), 23/24 dispatch, 162 CheckCallback.
- **a1 = record/TCB/data pointer**: WakeupThread (50, the TCB), Notify
  (158, cb record), CreateSema/EventFlag/Mbx (the opt), CreateVpl/Fpl
  (the obj view), 67 SetEventFlag (slot view), sema/mutex ops (61, 59,
  62-63, 74-81), 106/121/129/130 body pointers, 113 is a STALE register
  (see section 15).
- **a1 = acquire cookie**: Terminate pair (21/22).
- **a1 = status**: Exit pair (19/20).
- **a1 = scratch buffer**: 64/73 and the Refer* msgnos when the log fires
  after the build (81).
- **msgno 0 flavor**: mbx Poll/dequeue events pass a0 = 0 with a3 = a
  data-descriptor pointer (0x19628 message / 0x19638 empty), not an
  argument (N).

| msgno | event | a1 | extras |
|---|---|---|---|
| 1 | context switch (dispatch loop @0x12AF8) | 0 | 5: oldTid, oldPrio, newTid, flags, ... |
| 5 | alarm expiry dispatch | alarm view | 3 |
| 6 | vtimer expiry dispatch | vtimer view | 5 (incl. remaining pair) |
| 7 | per-callback invoke (pump @0x2268) | node | 5: uid, common, func, count, notifyArg |
| 16 | CreateThread | module base in s8 | 2: entry |
| 17 | DeleteThread | rec | 1: tid |
| 18 | StartThread | | 3: tid, argLen, argp |
| 19 | ExitThread | status | 1: status |
| 20 | ExitDeleteThread | status | 1: status |
| 21 | TerminateThread | cookie | 1: state |
| 22 | TerminateDeleteThread | cookie | 1: state |
| 23 | SuspendDispatchThread | &S | 0 |
| 24 | ResumeDispatchThread | cookie | 1: state |
| 25 | ChangeCurrentThreadAttr | | |
| 26 | ChangeThreadPriority | prio | 2: tid, prio (t0 dup) |
| 27 | RotateThreadReadyQueue | prio | 1 (a3 = prio) |
| 28 | ReleaseWaitThread | tid | 1: tid |
| 29 | GetThreadId | k1 | 0 |
| 31 | GetThreadExitStatus | &S | 2: scratch, status |
| 32 | CheckThreadStack | data base | 0 |
| 33 | GetThreadStackFreeSize | tid | 1 |
| 34 | ReferThreadStatus | rec | 2: tid, info |
| 35 | ReferThreadRunStatus | tid | 2 |
| 36 | ReferThreadDebugStatus | tid | 2 |
| 37 | GetUserLevel | k1 | 1: level (a3 = computed value) |
| 38 | IsUserModeThread | k1 | 1: user flag |
| 40 | RunOnTempStack (28BFD974) | k1 | 3: orig a0, a1 |
| 41 | ExtendThreadStack | block | 3: size, func, arg |
| 43 | CheckThreadKernelStack | k1 | 0 |
| 44 | GetThreadKernelStackFreeSize | tid | 1 |
| 45 | RegisterTEH | view | 5: tid, mask, handler, common, uid |
| 46 | ReleaseTEH | k1 | 1: uid |
| 47 | ReferTEHStatus | scratch | 2 |
| 48 | SleepThread | module base | 0 |
| 49 | SleepThreadCB | stale s8 (section 15) | 0 |
| 50 | WakeupThread | TCB | 1: tid |
| 51 | CancelWakeupThread | rec | 1: tid |
| 52 | DonateWakeupThread | target | 2: tid, count |
| 53 | SuspendThread | | |
| 54 | ResumeThread | | |
| 55/56 | WaitThreadEnd / CB | &S | 1: tid |
| 58 | DeleteSema | uid | 1: uid |
| 59 | SignalSema | stale s8 (section 15) | 2: semaid, count |
| 60/61 | WaitSema / CB | | 61 known |
| 62 | PollSema | semaobj | 2 |
| 63 | CancelSema | semaobj | 3: semaid, count, pCount |
| 64 | ReferSemaStatus | scratch | 2: slot, info |
| 66 | DeleteEventFlag | uid | 1 |
| 67 | SetEventFlag | slot view | 2: uid, pattern |
| 68 | ClearEventFlag | &S | 2: uid, mask |
| 69/70 | WaitEventFlag / CB | | |
| 71 | PollEventFlag | evfobj | 4 |
| 72 | CancelEventFlag | evfobj | 3 |
| 73 | ReferEventFlagStatus | scratch (a3 dup) | 2 |
| 74 | CreateMutex | uid | 1 |
| 75 | DeleteMutex | uid | 1 |
| 76 | UnlockMutex | mutexobj | 2: uid, count |
| 77/78 | LockMutex / CB | mutexobj | 2: uid, count |
| 79 | TryLockMutex | count (the only one) | 2 |
| 80 | CancelMutex | newCount (t0) | 3: uid, count, pWaiters |
| 81 | ReferMutexStatus | scratch | 2 |
| 82 | CreateLwMutex | pWork | 1 |
| 83 | DeleteLwMutex | pWork | 1: uid |
| 84 | UnlockLwMutex | pWork | 2: uid, count |
| 85/86 | LockLwMutex / CB | pWork | 2: uid, count |
| 87 | TryLockLwMutex | pWork | 2 |
| 89 | ReferLwMutexStatus | rec | 2: uid, info |
| 90 | CreateMbx | opt | 1: uid |
| 91 | DeleteMbx | uid | 1 |
| 92 | SendMbx | slot obj | 2: uid, msg |
| 93/94 | ReceiveMbx / CB | &S | 2: uid, out |
| 95 | PollMbx | &S | 2: uid, out |
| 96 | CancelReceiveMbx | pCount | 2 |
| 97 | ReferMbxStatus | stale s8 (section 15) | 2 |
| 98 | CreateMsgPipe | 0 (v0) | 1: uid |
| 99 | DeleteMsgPipe | uid | 1 |
| 100/101 | SendMsgPipe / CB | stale s8 | 4: uid, buf, size |
| 102 | TrySendMsgPipe | stale s8 | 4 |
| 103/104 | ReceiveMsgPipe / CB | stale s8 | 4 |
| 105 | TryReceiveMsgPipe | stale s8 | 4 |
| 106 | CancelMsgPipe | recvN pointer | 3: uid, sendN, recvN |
| 107 | ReferMsgPipeStatus | &S | 2: uid, info |
| 108 | CreateVpl | obj view | 1: uid |
| 109 | DeleteVpl | uid | 1 |
| 110/111 | AllocateVpl / CB | 0x800201AB preset | 1 |
| 112 | TryAllocateVpl | size | 3 |
| 113 | FreeVpl | STALE s8 (section 15) | 2: uid, block |
| 114 | CancelVpl | count ptr | 2 |
| 115 | ReferVplStatus | uid | 2: uid, info |
| 116 | CreateFpl | obj view | 1 |
| 117 | DeleteFpl | rec view | 1 |
| 118/119 | AllocateFpl / CB | &S | 1: uid |
| 120 | TryAllocateFpl | obj view | 2 |
| 121 | FreeFpl | block | 2 |
| 122 | CancelFpl | count ptr | 2 |
| 123 | ReferFplStatus | uid | 2 |
| 124 | CreateTlspl | mirror idx | 1: patched uid |
| 125 | DeleteTlspl | &P | 1: uid |
| 126 | AllocateTlspl | timeout | 1 |
| 129 | FreeTlspl | block | 2 |
| 130 | ReferTlsplStatus | slot view | 2 |
| 131 | GetSystemTime | out pointer | 2 (a3 = hi) |
| 132 | GetSystemTimeWide | saved k1 | 1 |
| 134/135 | DelayThread / CB | | 1 (usec) |
| 136/137 | DelaySysClock / CB | | 2 (lo, hi) |
| 138 | SetAlarm | handler | 4 |
| 139 | SetSysClockAlarm | handler | 5 |
| 140 | CancelAlarm | uid | 1 |
| 141 | ReferAlarmStatus | &S | 2: uid, info |
| 142 | CreateVTimer | k1 | |
| 143 | DeleteVTimer | uid | 1 |
| 144 | GetVTimerBase | base ptr | 3 |
| 145 | GetVTimerBaseWide | | |
| 146 | SetVTimerTime | vt | 3: uid, hi, lo |
| 149 | SetVTimerHandler | vt | 5 |
| 150 | CancelVTimerHandler | vt | 1 |
| 151/152 | GetVTimerTime/Wide | | |
| 153 | SetVTimerTimeWide | vt | 2 |
| 154 | SetVTimerHandlerWide | vt | 4 |
| 155 | ReferVTimerStatus | vt | 2: scratch, info |
| 156 | CreateCallback | view | 3: func, common, uid |
| 157 | DeleteCallback | k1 | 1: cbid |
| 158 | NotifyCallback | view | 2: cbid, arg |
| 159 | CancelCallback | &S | 1: cbid |
| 160 | GetCallbackCount | &S | 2: cbid, count |
| 161 | GetCallbackNestingLevel (8672E3D0) | k1 | 2: 0, result |
| 162 | CheckCallback | k1 | 1: result |
| 163 | ReferCallbackStatus | scratch | 2 |
| 164 | ReferSystemStatus | user pointer st | 1: cookie |
| 165 | GetThreadmanIdList | 66 | |
| 166 | GetThreadmanIdType | uid | 1 |
| 167 | AllocateKTLS | desc | 4 |
| 168 | FreeKTLS | id | 1 |
| 170 | GetThreadKTLS | value-or-block | 4 |

Wide twins of timer getters (147/148, 151/152/153) follow the same family
patterns (DD, GG). GetVTimerTime/Wide, SetVTimerTimeWide and
SetVTimerHandlerWide pairs share msgno families 144..155.

## 15. Quirks and shipped bugs

Everything in this section is retail behavior, reproduced verbatim by the
byte-exact reconstruction.

**Shipped bugs (state corruption or stranded waiters)**:

- **DeleteMutex corruption** @0x64F0: no waiter walk, no owner check.
  Deleting a locked mutex leaves the owner's TCB+0xA8 owned ring pointing
  into freed memory and strands all waiters (BB).
- **Strand-forever 0x800 mutexes**: the exit mass-release (sub_66F0) sets
  owner = -1 on attr-0x800 mutexes and leaves them locked forever;
  ReferMutexStatus maps that owner to -2, a distinguishable
  "locked by a dead thread" state (BB, NN, EE).
- **DeleteLwMutex strands waiters** @0x7908: no waiter check; stranded
  waiters see 0x800201B5 on re-resolve; work+4 gets -1, not 0 (U).
- **DeleteThread(0) returns 0x1A4** @0x132B4: the tid==0 branch jumps into
  a shared error tail whose `ori v0,v0,0x1a4` delay slot executes with
  v0 = 0, so the function returns the positive value 0x000001A4 instead
  of 0x800201A4 (Y @0x132F8-0x13460).
- **Keep-mask ClearEventFlag** @0x5618: `currentPattern &= argument` with
  no complement; the argument is a KEEP mask, contradicting the
  documented "bits to clear" (R @0x56BC).

**Stale-register log sites** (the handler reads a register before the
function ever wrote it; transcribed literally):

- SignalSema msgno 59: a1 = s8 as left by the caller (@0x4530 area, R).
- SleepThreadCB msgno 49: a1 = s8 before s8 is loaded (L @0x2ECC+).
- ReferMbxStatus msgno 97: a1 = s8 set only by the later walk (N).
- MsgPipe send/receive/Try msgnos 100-105: a1 = s8 residue (V, W, FF).
- FreeVpl msgno 113: a1 = s8 uninitialized at log time (S).

**PollMbx TOCTOU window** @0x8DC0/@0x8A78: the dequeue re-validates the
oldest message and its next pointer with the k1 gates on the way out, but
the message contents stay user-controlled between validation and handout;
the single-element ring also re-checks the count (0x800201C9) (N).

**Dead code sites** (reconstructed because they are inside the compared
extents):

- sub_FE4 tail 0x1100..0x113C: an unused switch-completed probe with no
  in-module xrefs (KK).
- ExitThread twins: SPECIAL2 filler 0x70050024 writes its result to $0;
  the following `beqz a1` is provably dead (Y).
- CreateFpl: `ext s7,s6,14,1` computed, result register never read
  (FF).
- Live shift-by-zero no-ops (`sll r,r,0`, `srl r,r,0`) at RunStatus
  0x16098/0x16144, Tlspl resolver, vtimer cores (II, MM).
- GetSystemTime @0x10C50: a dead load in the bnezl delay slot (E).
- CreateThread: `ins v0,zero,27,24` dead (AA).

**Other documented quirks**:

- 0xDEADBEEF success returns: ExtendThreadStack @0x1512C and the user
  temp-stack runner 28BFD974 @0x1502C return 0xdeadbeef in v0 (and v1 for
  the latter); the function result is discarded (AA, DD, II).
- SysClock2USec @0x10A74: a NULL lo out-pointer skips the division and
  copies the clock's low word into the HI out-pointer (E).
- GetVTimerBaseWide: a stopped vtimer's base reads {0,0} (DD).
- Wide vtimer setters return -1/-1 on error, not SCE codes (GG).
- Delete* family discards the 0x1877C result and hardcodes 0 via the v1
  route (X, II).
- SuspendAllUserThreads sets S+0x30; while it is set, SignalSema's wake
  walk skips user-thread waiters entirely (they stay queued until a
  dispatch happens) (HH, R).
- The msgpipe receive core's `bnezl a1` targeting the fall-through
  address: the delay-likely store executes only when taken, which is the
  same effect as always (N @0x8994).
- SceKernelMbxInfo+48 keeps stale scratch data when the box is empty (the
  zero loop does not cover the last word) (N).
- WaitThreadEnd returns the target's exit status immediately for dead
  targets without blocking; the CB variant re-resolves the uid after
  every callback batch (0x800201B5) (T, MM).
- CancelWakeupThread is the only member of the wake family where tid == 0
  means the current thread (T).
- The dispatcher's "no runnable thread" fatal calls 0x18724 with the
  string at module+0x19800 (KK).
- 2-word wait veneers pass the CB flag in t3, a register outside the o32
  ABI; 5th/6th syscall arguments arrive in t0/t1 (L, O, V).
- Numeric-label and delay-slot-schedule artifacts of the Sony backend
  (lazy callee-saves in branch delay slots, register double-life such as
  s6 reused for the 0x800201AB constant) are documented in the archive
  batches and reproduced by the transcription method.
