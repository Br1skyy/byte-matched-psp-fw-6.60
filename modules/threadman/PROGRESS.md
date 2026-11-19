# progress

threadman is done. build_prx.py --no-retail builds all 115864 bytes from
source derived material and the sha1 matches retail. details per function
below.

## Matched (6)

| Addr | Size | Function | Status |
|---|---|---|---|
| 0x10A60 | 2w | `_sceKernelReturnFromTimerHandler` | ✅ |
| 0x10A68 | 3w | `sceKernelUSec2SysClockWide` | ✅ |
| 0x10D28 | 3w | `sceKernelGetSystemTimeLow` | ✅ (MMIO `0xBC600000`) |
| 0x16BD8 | 7w | `sceKernelSetThreadmanLogHandler` | ✅ |
| 0x16E24 | 30w | `sceKernelGetThreadCurrentPriority` | ✅ (retro-upgraded to full match via literal back-edge word) |
| 0x1712C | 3w | `sceKernelGetSystemStatusFlag` | 🔗 |
| 0x17138 | 4w | `sceKernelRegisterDeadThreadHandler` | 🔗 |

| 0x11F48 | 8w | `sceKernelGetKTLS` | 🔗 (jal reloc only, 1 iter; target GetThreadKTLS now matched by CC) |
| 0x16B1C | 9w | `ThreadManForKernel_D366D35A` | 🔗 (2 LO16 words; global lands +0x17848 vs retail +0x17844) |

| 0x16DAC | 30w | `sceKernelGetThreadId` | ✅ (1 iter) |
| 0x16E9C | 34w | `sceKernelGetUserLevel` | ✅ (1 iter) |
| 0x16F24 | 32w | `sceKernelIsUserModeThread` | ✅ (1 iter) |
| 0x17044 | 58w | `sceKernelCheckThreadKernelStack` | ✅ (1 iter) |

| 0x1E74 | 65w | `sceKernelCancelCallback` | 🔗 (batch F, 3 iters: 60/65 exact; only 5 jal-veneer words reloc-covered, veneers kept extern) |
| 0x1F78 | 64w | `sceKernelGetCallbackCount` | 🔗 (batch F: 59/64 exact; same 5 jal relocs) |

| 0x0ECB4 | 12w | `sceKernelUSec2SysClock` | ✅ (batch E: transcription of A's decode, 0 relocs) |
| 0x10A74 | 47w | `sceKernelSysClock2USec` | ✅ (batch E, literal jal/j targets) |
| 0x10BE0 | 46w | `sceKernelGetSystemTime` | ✅ (batch E) |
| 0x10C98 | 36w | `sceKernelGetSystemTimeWide` | ✅ (batch E) |

| 0x3050 | 114w | `sceKernelWakeupThread` | 🔗 (batch H, 2 iters: 107/114 exact; 7 jal-veneer words reloc; full decode in results/H.md) |
| 0x1CC0 | 109w | `sceKernelNotifyCallback` | 🔗 (batch H: 104/109 exact; 5 jal-veneer words reloc; wait-break/dispatch path decoded) |

| 0x2384 | 110w | `sceKernelReferCallbackStatus` | ✅ (1 iter, 0 relocs) |
| 0x1800 | 118w | `sceKernelReferThreadEventHandlerStatus` | ✅ (1 iter, 0 relocs) |
| 0x14E10 | 64w | `sceKernelGetThreadExitStatus` | ✅ (1 iter, 0 relocs) |

| 0x10B30 | 44w | `sceKernelSysClock2USecWide` | ✅ (batch G, 1 iter) |
| 0x10DF4 | 50w | `sceKernelSetAlarm` | ✅ (batch G, 1 iter) |
| 0x0ED24 | 99w | `sceKernelCancelAlarm` | ✅ (batch G, 1 iter) |
| 0x0EF24 | 104w | `sceKernelReferAlarmStatus` | ✅ (batch G, 1 iter) |

| 0x0F0C4 | 68w | `sceKernelCreateVTimer` | ✅ (batch J, 1 iter) |
| 0x0F1D4 | 69w | `sceKernelDeleteVTimer` | ✅ (batch J, 1 iter) |
| 0x0F2E8 | 90w | `sceKernelGetVTimerBase` | ✅ (batch J, 1 iter) |
| 0x0FDB4 | 130w | `sceKernelStartVTimer` | ✅ (batch J, 1 iter) |
| 0x0FFBC | 118w | `sceKernelStopVTimer` | ✅ (batch J, 1 iter) |
| 0x10828 | 142w | `sceKernelReferVTimerStatus` | ✅ (batch J, 3 iters: shared-delay-slot address misattribution) |

| 0x0F874 | 182w | `sceKernelSetVTimerTime` | ✅ (batch GG, 0 relocs) |
| 0x0FB4C | 154w | `sceKernelSetVTimerTimeWide` | ✅ (batch GG, 0 relocs) |
| 0x10194 | 169w | `sceKernelSetVTimerHandler` | ✅ (batch GG, 0 relocs) |
| 0x10438 | 160w | `sceKernelSetVTimerHandlerWide` | ✅ (batch GG, 0 relocs) |
| 0x106B8 | 92w | `sceKernelCancelVTimerHandler` | ✅ (batch GG, 0 relocs) |
| 0x10EBC | 60w | `sceKernelSetSysClockAlarm` | ✅ (batch GG, 0 relocs) |

| 0x04DF0 | 115w | `sceKernelReferSemaStatus` | ✅ (batch M, 1 iter) |
| 0x05F10 | 113w | `sceKernelReferEventFlagStatus` | ✅ (batch M, 3 iters: 1 gas movn wrap + 1 j-target typo) |
| 0x019D8 | 106w | `sceKernelCreateCallback` | ✅ (batch M, 1 iter) |
| 0x01B80 | 80w | `sceKernelDeleteCallback` | ✅ (batch M, 1 iter) |

| 0x8650 | 86w | `sceKernelCreateMbx` | ✅ (batch N, 1 iter, 0 relocs) |
| 0x87A8 | 69w | `sceKernelDeleteMbx` | ✅ (batch N, 1 iter, 0 relocs) |
| 0x88BC | 107w | `sceKernelSendMbx` | ✅ (batch N, 1 iter, 0 relocs) |
| 0x8A68 | 2w | `sceKernelReceiveMbx` | ✅ (batch N; `j 0x8A78; li t3,0`) |
| 0x8A70 | 2w | `sceKernelReceiveMbxCB` | ✅ (batch N; `j 0x8A78; li t3,1`) |
| 0x8DC0 | 140w | `sceKernelPollMbx` | ✅ (batch N, 1 iter, 0 relocs) |
| 0x9128 | 115w | `sceKernelReferMbxStatus` | ✅ (batch N, 1 iter, 0 relocs) |

| 0x2DF0 | 64w | `sceKernelSleepThread` | ✅ (batch L, 3 iters, 0 relocs) |
| 0x2EF0 | 88w | `sceKernelSleepThreadCB` | ✅ (batch L, 3 iters, 0 relocs) |
| 0x3D78 | 2w | `sceKernelDelayThread` | ✅ (batch L; `j 0x3D88; li t3,0`) |
| 0x3D80 | 2w | `sceKernelDelayThreadCB` | ✅ (batch L; `j 0x3D88; li t3,1`) |
| 0x3F9C | 2w | `sceKernelDelaySysClockThread` | ✅ (batch L; `j 0x3FAC; li t3,0`) |
| 0x3FA4 | 2w | `sceKernelDelaySysClockThreadCB` | ✅ (batch L; `j 0x3FAC; li t3,1`) |

| 0x15C04 | 211w | `sceKernelReferThreadStatus` | ✅ (batch K, 1 iter, 0 relocs - the batch-I "monster") |
| 0x0357C | 133w | `sceKernelSuspendThread` | ✅ (batch K, 2 iters: one delay-slot transcription typo) |
| 0x03790 | 125w | `sceKernelResumeThread` | ✅ (batch K, 1 iter) |
| 0x1351C | 299w | `sceKernelStartThread` | ✅ (batch K, 1 iter - ins/rotrv/cache/sync raw-word splices) |

| 0x09468 | 148w | `sceKernelCreateMsgPipe` | ✅ (batch P, 1 iter, 0 relocs) |
| 0x096BC | 69w | `sceKernelDeleteMsgPipe` | ✅ (batch P, 1 iter) |
| 0x097D0 | 2w | `sceKernelSendMsgPipe` | ✅ (batch P, veneer `j 0x97e0; li t3,0`) |
| 0x0A1A4 | 2w | `sceKernelReceiveMsgPipe` | ✅ (batch P, veneer `j 0xa1b4; li t3,0`) |
| 0x0ADD0 | 124w | `sceKernelReferMsgPipeStatus` | ✅ (batch P, 2 iters: OR rt operand is live a1 not saved s2) |

| 0x076D8 | 140w | `sceKernelCreateLwMutex` | ✅ (batch Q, 2 iters, 0 relocs) |
| 0x08094 | 139w | `_sceKernelTryLockLwMutex` | ✅ (batch Q, 1 iter, 0 relocs) |
| 0x07CD4 | 2w | `_sceKernelLockLwMutex` | ✅ (batch Q bonus: `j 0x7CE4; li t3,0` veneer) |
| 0x07CDC | 2w | `_sceKernelLockLwMutexCB` | ✅ (batch Q: `j 0x7CE4; li t3,1` veneer) |
| 0x082C0 | 125w | `sceKernelReferLwMutexStatusByID` | ✅ (batch Q, 2 iters, 0 relocs - no cfc0 check) |
| 0x07A5C | 158w | `_sceKernelUnlockLwMutex` | ✅ (batch Q, 1 iter, 0 relocs) |
| 0x07CE4 | 236w | `sub_07CE4` - shared LwMutex lock core (INTERNAL) | ✅ (batch U, 2 iters, 0 relocs - internal-compare script) |
| 0x07908 | 85w | `sceKernelDeleteLwMutex` | ✅ (batch U, 1 iter, 0 relocs) |

| 0x044D8 | 157w | `sceKernelSignalSema` | ✅ (batch R, 0 relocs; 7w over budget, matched as batch centerpiece) |
| 0x0474C | 2w | `sceKernelWaitSema` | ✅ (batch R; `j 0x475C; li t3,0` veneer) |
| 0x053C0 | 150w | `sceKernelSetEventFlag` | ✅ (batch R, 0 relocs) |
| 0x05618 | 70w | `sceKernelClearEventFlag` | ✅ (batch R; arg = KEEP mask, cur &= arg) |
| 0x05B70 | 145w | `sceKernelPollEventFlag` | ✅ (batch R, 0 relocs) |
| 0x05DB4 | 87w | `sceKernelCancelEventFlag` | ✅ (batch R; sub_1879C(rec, 0x86D94883) all-waiter cancel) |

| 0x0B6C0 | 69w | `sceKernelDeleteVpl` | ✅ (batch O, 1 iter, 0 relocs) |
| 0x0B7D4 | 2w | `sceKernelAllocateVpl` | ✅ (batch O veneer `j 0xB7E4; li t3,0`) |
| 0x0B7DC | 2w | `sceKernelAllocateVplCB` | ✅ (batch O veneer `li t3,1`) |
| 0x0BB14 | 104w | `sceKernelTryAllocateVpl` | ✅ (batch O, 2 iters, 0 relocs) |
| 0x0C034 | 114w | `sceKernelReferVplStatus` | ✅ (batch O, 2 iters, 0 relocs) |
| 0x0D118 | 115w | `sceKernelReferFplStatus` | ✅ (batch O, 2 iters, 0 relocs) |

| 0x0AC20 | 108w | `sceKernelCancelMsgPipe` | ✅ (batch S, 1 iter, 0 relocs) |
| 0x0BCB4 | 146w | `sceKernelFreeVpl` | ✅ (batch S, 1 iter, 0 relocs) |
| 0x0CDBC | 137w | `sceKernelFreeFpl` | ✅ (batch S, 2 iters: gas `break` field-encoding) |
| 0x0BEFC | 78w | `sceKernelCancelVpl` | ✅ (batch S, 1 iter, 0 relocs) |
| 0x0CFE0 | 78w | `sceKernelCancelFpl` | ✅ (batch S, 1 iter, 0 relocs) |

| 0x3AC0 | 2w | `sceKernelWaitThreadEnd` | ✅ (batch T; veneer `j 0x3AD0; li t3,0`) |
| 0x3AC8 | 2w | `sceKernelWaitThreadEndCB` | ✅ (batch T; veneer `li t3,1`) |
| 0x3218 | 73w | `sceKernelCancelWakeupThread` | ✅ (batch T, 1 iter, 0 relocs) |
| 0x333C | 144w | `sceKernelDonateWakeupThread` | ✅ (batch T, 1 iter, 0 relocs) |
| 0x14C20 | 124w | `sceKernelReleaseWaitThread` | ✅ (batch T, 1 iter, 0 relocs) |

| 0x097E0 | 359w | `sub_097E0` - MsgPipe send core (INTERNAL, behind 0x97D0/0x97D8 veneers) | ✅ (batch V, 2 iters, 0 relocs; P's 361w figure off by 2 - TrySend starts @0x9D7C) |

| 0x0A1B4 | 377w | `sub_0A1B4` - MsgPipe receive core (INTERNAL, behind 0xA1A4/0xA1AC veneers) | ✅ (batch W, 364/377 -> clean, 0 relocs; P's 379w figure off by 2 again - TryReceive starts @0xA798) |
| 0x09D7C | 266w | `sceKernelTrySendMsgPipe` | ✅ (batch W, 262/266 -> clean, 0 relocs) |

| 0x04248 | 95w | `sceKernelCreateSema` | ✅ (batch X, 1 iter, 0 relocs - relaunch: dead agent's work lost, redone) |
| 0x043C4 | 69w | `sceKernelDeleteSema` | ✅ (batch X, 1 iter, 0 relocs) |
| 0x05138 | 93w | `sceKernelCreateEventFlag` | ✅ (batch X, 1 iter, 0 relocs) |
| 0x052AC | 69w | `sceKernelDeleteEventFlag` | ✅ (batch X, 1 iter, 0 relocs) |
| 0x0B44C | 157w | `sceKernelCreateVpl` | ✅ (batch X, 1 iter, 0 relocs; O.md decode closed - sema/evf UID-create family + 0x187C4 pool-record resolver in results/X.md) |

| 0x132B4 | 125w | `sceKernelDeleteThread` | ✅ (batch Y, 3 iters, 0 relocs; retail quirk: tid==0 returns 0x000001A4) |
| 0x139C8 | 63w | `sceKernelExitThread` | ✅ (batch Y, 3 iters, 0 relocs; noreturn into 0x178C0 core) |
| 0x13AC4 | 63w | `sceKernelExitDeleteThread` | ✅ (batch Y, 3 iters, 0 relocs) |
| 0x13BC0 | 94w | `sceKernelTerminateThread` | ✅ (batch Y, 3 iters, 0 relocs; legal from interrupt ctx) |
| 0x13D38 | 82w | `sceKernelTerminateDeleteThread` | ✅ (batch Y, 3 iters, 0 relocs) |

| 0x14854 | 122w | `sceKernelChangeThreadPriority` | ✅ (batch Z, 2 iters, 0 relocs) |
| 0x14A3C | 121w | `sceKernelRotateThreadReadyQueue` | ✅ (batch Z, 2 iters, 0 relocs - Allegrex clz cascade raw .word) |
| 0x0143C | 81w | `sceKernelReleaseThreadEventHandler` | ✅ (batch Z, 1 iter, 0 relocs) |
| 0x15928 | 89w | `sceKernelGetThreadStackFreeSize` | ✅ (batch Z, 2 iters, 0 relocs) |
| 0x16784 | 122w | `sceKernelGetThreadmanIdType` | ✅ (batch Z, 1 iter, 0 relocs) |

| 0x0DA10 | 128w | `sceKernelDeleteTlspl` | ✅ (batch CC, 3 iters, 0 relocs) |
| 0x0DC10 | 174w | `_sceKernelAllocateTlspl` | ✅ (batch CC, 4 iters, 0 relocs) |
| 0x0DEC8 | 131w | `sceKernelFreeTlspl` | ✅ (batch CC, 2 iters, 0 relocs) |
| 0x11A24 | 78w | `sceKernelAllocateKTLS` | ✅ (batch CC, 2 iters, 0 relocs) |
| 0x11B5C | 67w | `sceKernelFreeKTLS` | ✅ (batch CC, 1 iter, 0 relocs) |
| 0x11C68 | 116w | `sceKernelGetThreadKTLS` | ✅ (batch CC, 1 iter, 0 relocs; closes A's LINK-MATCH via its veneer GetKTLS 0x11F48) |

| 0x04A34 | 102w | `sceKernelPollSema` | ✅ (batch BB, 0 relocs; NO cfc0; 0x4D68 fairness gate → 0x800201AD) |
| 0x04BCC | 103w | `sceKernelCancelSema` | ✅ (batch BB, 0 relocs; NO cfc0; count<0 resets to initial) |
| 0x06284 | 155w | `sceKernelCreateMutex` | ✅ (batch BB, 0 relocs; attr 0x400 = priority ceiling) |
| 0x064F0 | 69w | `sceKernelDeleteMutex` | ✅ (batch BB, 0 relocs; NO owner/waiter check) |
| 0x06A6C | 2w | `sceKernelLockMutex` | ✅ (batch BB; `j 0x6A7C; li t3,0` veneer) |
| 0x06A74 | 2w | `sceKernelLockMutexCB` | ✅ (batch BB; `li t3,1` veneer) |
| 0x0705C | 127w | `sceKernelCancelMutex` | ✅ (batch BB, 0 relocs; intr-legal iff newCount==0) |

| 0x14F10 | 71w | `_sceKernelReturnFromChangeStack` | ✅ (batch DD, 0 relocs; pops TCB+0xD4 frame, returns [TCB+0x24]+0x18) |
| 0x1512C | 101w | `sceKernelExtendThreadStack` | ✅ (batch DD, 0 relocs; runs via 0x17EB4; **success returns 0xdeadbeef**) |
| 0x152C0 | 190w | `sceKernelExtendKernelStack` | ✅ (batch DD, 0 relocs; parks old stack fields in a frame chained via TCB+0xD0, sp switch w/ SPECIAL2 barriers) |
| 0x157C8 | 88w | `sceKernelCheckThreadStack` | ✅ (batch DD, 0 relocs; 3 delta paths, 64B threshold, same 0x177C4 report tail) |
| 0x02078 | 62w | `sceKernelCheckCallback` | ✅ (batch DD, 0 relocs; returns (pump 0x2170 result != 0); pump decoded in DD.md) |
| 0x14308 | 164w | `sceKernelChangeCurrentThreadAttr` | ✅ (batch DD, 0 relocs; attr bit 0x4000 lazily allocates 576B FPU ctx) |
| 0xF450 | 75w | `sceKernelGetVTimerBaseWide` | ✅ (batch DD bonus, 0 relocs; stopped timer returns {0,0}) |
| 0xF57C | 104w | `sceKernelGetVTimerTime` | ✅ (batch DD bonus, 0 relocs; 2 out slots a1/a1+8, mask stays in k1) |
| 0xF71C | 86w | `sceKernelGetVTimerTimeWide` | ✅ (batch DD bonus, 0 relocs; 0xECE4()-base borrow chain) |

| 0x12CF8 | 367w | `sceKernelCreateThread` | ✅ (batch AA, 1 iter, 0 relocs - biggest export yet; authoritative TCB constructor map + K.md rec+192/196 correction in results/AA.md) |

| 0x0C408 | 265w | `sceKernelCreateFpl` | ✅ (batch FF, 0 relocs - FPL family COMPLETE; full decode in results/FF.md) |
| 0x0D574 | 295w | `sceKernelCreateTlspl` | ✅ (batch FF, 0 relocs - Tlspl family COMPLETE; CC's decode-only member closed 1:1, SceUID bits 3-6 INS byte-confirmed) |
| 0x0A798 | 290w | `sceKernelTryReceiveMsgPipe` | ✅ (batch FF, 0 relocs - would-block error is 0x800201B4 MPF_EMPTY, NOT B3; 290w not 288) |

| 0x05730 | 2w | `sceKernelWaitEventFlag` | ✅ (batch HH; veneer `j 0x5740; li t3,0`) |
| 0x05738 | 2w | `sceKernelWaitEventFlagCB` | ✅ (batch HH; veneer `li t3,1`) |
| 0x04754 | 2w | `sceKernelWaitSemaCB` | ✅ (batch HH; veneer `j 0x475C; li t3,1`) |
| 0x14034 | 60w | `sceKernelSuspendDispatchThread` | ✅ (batch HH, 2 iters, 0 relocs) |
| 0x14240 | 50w | `sceKernelResumeDispatchThread` | ✅ (batch HH, 2 iters, 0 relocs) |
| 0x03984 | 79w | `sceKernelSuspendAllUserThreads` | ✅ (batch HH, 2 iters, 0 relocs) |
| 0x16D34 | 30w | `_sceKernelExitThread` | ✅ (batch HH, 1 iter, 0 relocs) |
| 0x01140 | 191w | `sceKernelRegisterThreadEventHandler` | ✅ (batch HH, 1 iter, 0 relocs) |

| 0x17230 | 19w | `sceKernelReferThreadProfiler` | ✅ (batch II, 1 iter, 0 relocs; perf readout, *(module+0x7E4)==1 gate, raw SPECIAL3 word) |
| 0x1727C | 11w | `sceKernelReferGlobalProfiler` | ✅ (batch II, 1 iter; *(module+0x824)==2 gate) |
| 0x097D8 | 2w | `sceKernelSendMsgPipeCB` | ✅ (batch II; veneer `j 0x97E0; li t3,1`) |
| 0x0A1AC | 2w | `sceKernelReceiveMsgPipeCB` | ✅ (batch II; veneer `j 0xA1B4; li t3,1`) |
| 0x0C940 | 2w | `sceKernelAllocateFpl` | ✅ (batch II; veneer `j 0xC950; li t3,0`) |
| 0x0C948 | 2w | `sceKernelAllocateFplCB` | ✅ (batch II; `li t3,1` veneer - the 178w shared core @0xC950 still undecoded) |
| 0x0272C | 34w | `ThreadManForKernel_8672E3D0` | ✅ (batch II, 1 iter; NID unnamed even in psplibdoc - semantics: GetCallbackNestingLevel, returns *(P+0xA0), no uid/acquire, msgno 161) |
| 0x17148 | 58w | `sceKernelReferSystemStatus` | ✅ (batch II, 1 iter; NEW callee 0x183ec builds the status block, msgno 164) |
| 0x1502C | 64w | `ThreadManForUser_28BFD974` | ✅ (batch II, 1 iter; NID unnamed - semantics: user-mode temp-stack runner, 0x187dc(pool=0,desc56) alloc + 0x17eb4 switch, >=512 gate 0x80020194, returns 0xdeadbeef, msgno 40) |
| 0x0C82C | 69w | `sceKernelDeleteFpl` | ✅ (batch II, 1 iter; msgno 117, return 0 via v1) |
| 0x08FF0 | 78w | `sceKernelCancelReceiveMbx` | ✅ (batch II, 1 iter; 0x1879c(rec,0x86D94883) cancel-all, optional count out via bnezl, err 0x8002019B, msgno 96) |
| 0x15A8C | 94w | `sceKernelGetThreadKernelStackFreeSize` | ✅ (batch II, 1 iter; 0xFFFFFFFF-fill word scan, kernel stack fields rec+48/+204 vs user rec+44/+196, msgno 44) |
| 0x0CC1C | 104w | `sceKernelTryAllocateFpl` | ✅ (batch II, 1 iter; 0xd38c ring pop, block = base+idx*stride, empty -> 0x80020190, msgno 120) |
| 0x1696C | 108w | `sceKernelGetThreadmanIdOwner` | ✅ (batch II, 1 iter; type-dispatch via resolvers 0xc1fc/0xd42c/0xb16c/0xe4a4 -> types 5/6/7/14 + threads-ring wait-queue walk, err 0x800201CB) |
| 0x161EC | 125w | `sceKernelReferThreadDebugStatus` | ✅ (batch II, 1 iter; NEW callee 0x180ac, 244B status, cause-gated 0x80020197, SPECIAL2 0x7013xxxx nop pads, msgno 36) |
| 0x0E23C | 122w | `sceKernelReferTlsplStatus` | ✅ (batch II, 1+1 iters; uid-mirror cross-check -> 0x800201D0, SceUID bits 3-6 live `ins` word 0x7E1418C0, 60B info, msgno 130) |
| 0x15F50 | 167w | `sceKernelReferThreadRunStatus` | ✅ (batch II, 1 iter; 48B status, live CPU-time fixup 0xece4 - {P+0x70/+0x74}, Sony sll-by-0 no-ops, msgno 35) |

| 0x067F4 | 158w | `sceKernelUnlockMutex` | ✅ (batch EE, 3 iters, 0 relocs; ONE waiter served per full release, ceiling boost applied to new owner via 0x6604, partial unlock serves nobody) |
| 0x06A7C | 246w | `sub_06A7C` - shared mutex lock core (INTERNAL, behind BB's 2w veneers) | ✅ (batch EE, 1 iter, 0 relocs - build/vdiff.py; fast-acquire gate + CB machinery decoded) |
| 0x06E54 | 130w | `sceKernelTryLockMutex` | ✅ (batch EE, 1 iter, 0 relocs; NO fairness gate - jumps queued waiters, unlike PollSema's 0x4D68; msgno 79 a1=count) |
| 0x07258 | 121w | `sceKernelReferMutexStatus` | ✅ (batch EE, 1 iter, 0 relocs; no cfc0; ownerId −1 unlocked / −2 dead-0x800-owner sentinel; full 56B info map) |

| 0x163E0 | 233w | `sceKernelGetThreadmanIdList` | ✅ (batch JJ: last export, generated+matched by vdiff-free harness run) |
| 0x0253C | 13w | `_sceKernelReturnFromCallback` | ✅ (batch OO: pure C, `tools/match_oo.py` = prefix336b, 2 jal relocs; LAST BLOCKED EXPORT CLOSED - GCC regrename patch, see results/OO.md) |

| 0x0680 | 118w | `sub_0680` - wait-queue insert core (INTERNAL: timer arm + priority/FIFO ring insert + FE4 away; returns waitResult) | ✅ (batch LL, vdiff, 1 iter, 0 relocs) |
| 0x0858 | 14w | `sub_0858` - sleep-queue tail append (INTERNAL; L's sleep core, byte-confirmed) | ✅ (batch LL, 0 relocs) |
| 0x0890 | 30w | `sub_0890` - bare priority re-insert leaf (INTERNAL; JJ's 0x890 identified) | ✅ (batch LL bonus, 0 relocs) |
| 0x0908 | 7w | `sub_0908` - wait-enqueue veneer → sub_680, li t1,0 (INTERNAL) | ✅ (batch LL, 0 relocs) |
| 0x0924 | 57w | `sub_0924` - release-from-wait: unlink+timer cancel+object notify+ready/suspend (INTERNAL) | ✅ (batch LL, 0 relocs) |
| 0x0A08 | 64w | `sub_0a08` - wake-now, cause-aware dispatch tail (INTERNAL) | ✅ (batch LL, 0 relocs) |
| 0x0B08 | 16w | `sub_0b08` - direct-wake handoff to HEAD waiter (INTERNAL) | ✅ (batch LL, 0 relocs) |
| 0x0B48 | 31w | `sub_0b48` - exit-waiter walk: waitResult+sub_924 per waiter (INTERNAL) | ✅ (batch LL, 0 relocs) |
| 0x0BC4 | 27w | `sub_0bc4` - wait-machinery cancel, NO unlink/state (INTERNAL) | ✅ (batch LL bonus, 0 relocs) |
| 0x0C30 | 8w | `sub_0c30` - cleanup 0x1879C(inherited a0, 0x85FE2B4C) (INTERNAL) | ✅ (batch LL, 0 relocs) |

| 0x1752C | 166w | `sub_1752C` - deferred-exit teardown (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs; 0x177AC = deferred block inside) |
| 0x178C0 | 85w | `sub_178C0` - never-return exit core (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |
| 0x17A14 | 296w | `sub_17A14` - terminate core + live-kill 0x17B68 (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs; live-kill decoded) |
| 0x6604 | 59w | `sub_6604` - mutex acquire+ceiling boost (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |
| 0x66F0 | 65w | `sub_66F0` - mutex exit mass-release (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |
| 0x7480 | 55w | `sub_7480` - mutex relinquish+restore (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |
| 0x180AC | 208w | `sub_180AC` - ThreadDebugStatus builder (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |
| 0x183EC | 34w | `sub_183EC` - SystemStatus builder (INTERNAL) | ✅ (batch NN, 1st compile, 0 relocs) |

| 0x2170 | 133w | `sub_2170` - callback pump (INTERNAL) | ✅ (batch MM via build/vdiff.py, 1 iter, 0 relocs; DD's decode byte-locked + corrected, thunk ABI in results/MM.md) |
| 0x2944 | 126w | `sub_2944` - user-callback invoke thunk (INTERNAL) | ✅ (batch MM, 2 iters; THE usermode-callback re-entry ABI: exception frame, gp swap, patched-syscall gadget) |
| 0x3AD0 | 170w | `sub_3AD0` - WaitThreadEnd core (INTERNAL) | ✅ (batch MM, 2 iters; T's decode byte-locked, wait type 9) |
| 0xC950 | 179w | `sub_C950` - FPL allocate core (INTERNAL, behind 0xC940/48 veneers) | ✅ (batch MM, 1 iter; **wait type 7 = FPL**, msgnos 118/119, FPL family COMPLETE) |
| 0x116F4 | 80w | `sub_116F4` - alarm create core (INTERNAL) | ✅ (batch MM, 1 iter; expiry = arg64 + now64, SetAlarm/SetSysClockAlarm share it) |
| 0xEAE0 | 39w | `sub_EAE0` - timer-queue insert (INTERNAL) | ✅ (batch MM, 1 iter; **anchor = module+0xA8** 8B ring, ascending-expiry sorted insert) |
| 0xEB7C | 78w | `sub_EB7C` - timer-queue reprocess (INTERNAL) | ✅ (batch MM, 1 iter; programs MMIO 0xBC600004, new dwords module+0x824/+0x82C) |

| 0x00FE4 | 87w | `sub_FE4` - resched-request entry (INTERNAL; 31 jal sites) | ✅ (batch KK, 2 iters, 0 relocs) |
| 0x127D0 | 22w | `sub_127D0` - make-ready tail-append, no preempt (INTERNAL) | ✅ (batch KK, 0 relocs) |
| 0x12828 | 247w | `sub_12828` - **THE DISPATCH LOOP** (INTERNAL) | ✅ (batch KK, 0 relocs - FPU MMIO ctx, banked-reg re-point, msgno-1 log hook) |
| 0x16BF4 | 21w | `sub_16BF4` - runq dequeue + bitmap clear (INTERNAL) | ✅ (batch KK, 0 relocs) |
| 0x16C48 | 59w | `sub_16C48` - make-ready + preempt handshake (INTERNAL) | ✅ (batch KK, 0 relocs) |
| 0x172F8 | 141w | `sub_172F8` - **THE DISPATCH CORE**, 3rd clz cascade @0x173A4 (INTERNAL) | ✅ (batch KK, 0 relocs) |

| 0x11F68 | 400w | `sub_11F68` - **module_start** (the ELF entry; syslib NID D3744BE0 → 0x18A10) | ✅ (batch QQ via match_oo.py + build/vdiff.py, 0 relocs; first compile) |
| 0x125A8 | 65w | `sub_125A8` - thread-2 entry: "SceThreadmanCleaner" deferred-uid-free reaper loop (INTERNAL) | ✅ (batch QQ, 0 relocs; first compile) |
| 0x126AC | 73w | `sub_126AC` - uid free = DEFERRED release append (module+0x78 chain) (INTERNAL) | ✅ (batch QQ, 0 relocs; first compile) |

| 0x0475C | 182w | `sub_0475C` - sema wait core (INTERNAL, behind WaitSema/CB veneers 0x474C/0x4754) | ✅ (batch TT via match_oo.py + vdiff, 0 relocs) |
| 0x05740 | 268w | `sub_05740` - evf wait core (INTERNAL, behind WaitEventFlag/CB veneers) | ✅ (batch TT, 0 relocs) |
| 0x08A78 | 210w | `sub_08A78` - mbx receive core (INTERNAL, behind ReceiveMbx/CB veneers) | ✅ (batch TT, 0 relocs) |
| 0x0AFC0 | 53w | `sub_0AFC0` - msgpipe ring write (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B094 | 54w | `sub_0B094` - msgpipe ring read (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B16C | 18w | `sub_0B16C` - msgpipe-class uid ring resolver (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B1B4 | 17w | `sub_0B1B4` - msgpipe-class registration (INTERNAL; QQ's module_start calls it) | ✅ (batch TT, 0 relocs) |
| 0x0B1F8 | 10w | `sub_0B1F8` - class uid getter via 0x1876c (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B220 | 32w | `sub_0B220` - class delete helper w/ block free (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B2A0 | 73w | `sub_0B2A0` - queued-sender drain walker (INTERNAL) | ✅ (batch TT, 0 relocs) |
| 0x0B3C4 | 34w | `sub_0B3C4` - waiter-leave direction/count cleanup (INTERNAL) | ✅ (batch TT, 0 relocs) |

| 0x10FAC | 86w | `sub_10FAC` - delay timer arm (INTERNAL; ctx+0x500 "SceThreadmanDelay" class, free pool ctx+0x24/+0x28, EAE0+EB7C) | ✅ (batch RR via match_oo.py + vdiff, 0 relocs) |
| 0x11104 | 70w | `sub_11104` - delay timer cancel (INTERNAL; remaining usec via 0x10A74, unlink + 0xEEB0 pool push + 0xEB7C) | ✅ (batch RR, 0 relocs) |
| 0x1121C | 49w | `sub_1121C` - timer UID-class registration (INTERNAL; 0x18754 base "Timer"/20B @ctx+0x4FC + 3x 0x187CC Delay/Alarm/VTimer 48B @0x500/0x504/0x508) | ✅ (batch RR, 0 relocs) |
| 0x112E0 | 4w | `sub_112E0` - SysTimer OVF IRQ ack leaf (INTERNAL; read 0xBC600000, raw eret) | ✅ (batch RR, 0 relocs) |
| 0x112F0 | 2w | `sub_112F0` - empty stub (INTERNAL; jr ra;nop) | ✅ (batch RR, 0 relocs) |
| 0x112F8 | 29w | `sub_112F8` - timer tick fixup (INTERNAL; module+0 counter shadow, 0xF0000000 window kick, 0x18704 ack) | ✅ (batch RR, 0 relocs) |
| 0x1136C | 33w | `sub_1136C` - timer hw init/program (INTERNAL; prescale 48→0xBC600008, counter←module+0, compare←module+0xC0→0xBC600004) | ✅ (batch RR, 0 relocs) |
| 0x113F0 | 35w | `sub_113F0` - 64/32 divmod helper (INTERNAL; 4-digit loop, divu $0 + break 0x0007000D) | ✅ (batch RR, 0 relocs) |
| 0x1147C | 62w | `sub_1147C` - alarm expiry dispatcher (INTERNAL; ctx+0x60 sentinel uid, gp swap, msgno 5) | ✅ (batch RR, 0 relocs) |
| 0x11574 | 96w | `sub_11574` - vtimer expiry dispatcher (INTERNAL; same skeleton + 0x186FC/0x186EC deferred-call frame, msgno 6) | ✅ (batch RR, 0 relocs) |
| 0x0ECE4 | 16w | `sub_ECE4` - 64-bit system clock read (INTERNAL; module+0xB8/+0xBC epoch base + 0xBC600000 counter) | ✅ (batch RR, 0 relocs) |

| 0x0000 | 2w | `sub_0000` - module entry veneer `jal 0x18694` (import) (INTERNAL) | ✅ (batch SS, 1 iter, 0 relocs) |
| 0x0008 | 30w | `sub_0008` - idle park loop: cache flush + 0xBC200000 dance, 20 embedded nop words (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0080 | 78w | `sub_0080` - VFPU/COP2 ctx SAVE (32x sdc2 16B-stride, the 576B FPU block) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x01B8 | 68w | `sub_01B8` - VFPU/COP2 ctx RESTORE (ldc2 mirror) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x02C8 | 12w | `sub_02C8` - FPU ctrl reset (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0300 | 169w | `sub_0300` - exception reentry: module+0x338 jr-vector, lazy FPU owner switch, eret (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x05A4 | 44w | `sub_05A4` - per-thread FPU save, ctc0 $8 clear in delay (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E424 | 32w | `sub_E424` - Tlspl pool-block validate → index / 0x800201B6 (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E4A4 | 18w | `sub_E4A4` - Tlspl uid resolver (class-14 ring walk, returns rec+12) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E4EC | 17w | `sub_E4EC` - uid-table create wrapper (jal 0x187CC w/ rodata names) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E530 | 10w | `sub_E530` - jal 0x1876C passthrough, returns *(a0+12) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E558 | 37w | `sub_E558` - Tlspl pool destroy helper (187A4 validate + 187B4 block free) (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E5EC | 136w | `sub_E5EC` - MODULE INIT: timer config, clock fn-ptr pair module+0x83C/+0x840, 32 pre-created alarm nodes, registers sub_E80C (INTERNAL) | ✅ (batch SS, 0 relocs) |
| 0x0E80C | 181w | `sub_E80C` - alarm expiry interrupt handler (module+0xA8 ring, handlers invoked OUTSIDE critical, 0xEB7C rearm) (INTERNAL) | ✅ (batch SS, 0 relocs) |

| 0x156BC | 67w | `sub_156BC` - reg init: park-list block frees (TCB+0xD0/+0xD4, pool module+0x820) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x134A8 | 29w | `sub_134A8` - ctxblk poison init (deadbeef GPRs + 0x7F800001 FPU) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x2570/0x27B4 | 35/34w | teardown-prep pair: TEH/callback uid-view release (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x25FC | 52w | `sub_25FC` - inline-vs-retarget gate (TEH class/tid scan, -1/-8/-16 rules) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x26CC | 24w | `sub_26CC` - callback ring purge + uid free (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x283C/0x743C/0x4FBC/0x6120/0x84B4/0xC244/0x92F4/0xC50/0x16B40 | 15-33w ea | static-init family x9 (name tables + class tbls via 0x187CC/0x18754) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x28C0 | 33w | `sub_28C0` - kernel-callback trampoline (P+0x84 frame, 0x186C4 resume, break 0x3,0x3ff) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x2B3C/0x2C7C/0x5000/0x5028/0x6208/0x755C/0x84F8/0xC288/0x9420/0x9448/0x11834/0x1185C/0x1187C/0x118A4/0x118C4/0x11A04/0xD4B8 | 8-10w ea | uid-resolve twins x17 (0x1876C -> view+12) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x2B64/0x2CA4 | 70w ea | wait-type-10/11 TEH-class enqueue twins (errs 0x800201A0/A1) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x2DBC | 13w | `sub_2DBC` - callback return trampoline (cookie->P+0x80, jal 0x28C0) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x4D68 | 34w | `sub_4D68` - sema fairness gate (INTERNAL) | ✅ (batch UU, 0 relocs - BB decode byte-locked) |
| 0x5048/0x60D4/0x6164/0x6230/0x7584/0x75E4 | 19-61w ea | sema/mutex walk+bookkeeping cores x6 (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x8520/0x855C/0x85A8 | 15/19/42w | LwMutex unlink/refcount/waiter-walk trio (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x9338 | 58w | `sub_9338` - mbx insert (prio-ordered attr 0x400, k1 user gates) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0xC1FC/0xC2B0/0xC32C | 18/31/55w | VPL ring-search/delete/waiter-walk (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0xC8C | 79w | `sub_C8C` - timeout core, 4th wake path (INTERNAL) | ✅ (batch UU, 0 relocs - LL decode byte-locked) |
| 0xDC8/0xE20/0xF10/0xFBC/0xFC4 | 22/60/43/2/8w | view reset / cancel-all B5 / cancel-all A9 / ret-0 / refcount-- x5 (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0xD2E4/0xD338/0xD38C/0xD3DC | 21/21/20/20w | FPL/Tlspl free-ring push/pop quartet (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0xD42C/0xD4E0 | 18/37w | FPL uid ring search / FPL+Tlspl delete-free (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x14124 | 71w | `sub_14124` - resume-dispatch core (INTERNAL) | ✅ (batch UU, 0 relocs - HH decode byte-locked) |
| 0x14598 | 175w | `sub_14598` - requeue/preempt core (INTERNAL) | ✅ (batch UU, 0 relocs - Z decode byte-locked, rotrv/clz raw) |
| 0x155B8 | 65w | `sub_155B8` - delete cleanup (cache ops + stack-block walk) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x10D34/0x10D8C | 22/26w | deadline builders (now64 + usec / +64-bit arg) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x172A8/0x172C8/0x172DC | 8/5/7w | exit-delete-self / DEAD SPIN (mfc0 $25+cache+madd) / exit-with-status slot (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x16B84/0xEEB0 | 21/29w | early-exit panic helper / TEH slot alloc (ctx+0x4FC) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x12C04 | 61w | `sub_12C04` - post-attr-change IMASK reprogram 0xBC000044 (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x16FA4/0xE0D4 | 40/90w | kstack snapshot / Tlspl exit walker (INTERNAL) | ✅ (batch UU, 0 relocs - CC decode byte-locked) |
| 0x17EB4 | 126w | `sub_17EB4` - stack-switch runner (INTERNAL) | ✅ (batch UU, 0 relocs - DD decode byte-locked) |
| 0x1580 | 160w | `sub_1580` - THE TEH DISPATCH (ring ctx+0x4C0; kernel-inline jalr vs user 0x2944 thunk) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x118EC/0x119B8 | 51/19w | vtimer delete (queue unlink + EB7C) / view init (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x13E80 | 109w | `sub_13E80` - THREAD START TRAMPOLINE (ctxblk fill; +188 = 0x172DC user / TCB+200 kernel) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x3D88/0x3FAC/0x41F4 | 133/146/21w | the DELAY CORES + cancel walker behind 3D78/3D80/3F9C/3FA4 veneers (k1 dance, 0x10FAC arm) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0xB7E4 | 204w | `sub_B7E4` - VPL allocate core behind B7D4/B7DC veneers (wait type 6) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x177C4/0x17844 | 32/31w | dead-thread dispatchers (state 0x20 tail into 0x1752C) (INTERNAL) | ✅ (batch UU, 0 relocs) |
| 0x18474/0x18504 | 36/98w | fresh uid-view ring init / delete teardown (0x17A14 + 0x156BC + block frees) (INTERNAL) | ✅ (batch UU, 0 relocs) |

## Blocked (none)

All mapped exports are closed. (0x0253C was the last: resolved batch OO by
patching GCC 3.3.6's `-O3` regrename pass in `../toolchain-build/prefix336b`
- retail keeps the raw allocator's registers in functions with calls but
renames in leaf functions; full analysis and 0-regression corpus proof in
results/OO.md.)

## Notes

- **Batch UU 90/90 MATCH, 3473/3473 words exact, 0 relocs beyond the %lo set
  (the named-internals sweep - TEXT REGION COMPLETE)**: tm_uu.c generated by
  /tmp/gen_uu.py (gen_tm.py decoder + fixes: mfc0 rs=0; cfc0/ctc0 with live
  rd field - gas accepts `cfc0 $9,$8`/`mfc0 $2,$25` directly, no raw .word;
  sllv/srlv/srav gated on sa==0 so Allegrex rotrv falls to raw .word;
  beqzl/bnezl 2-operand forms), compared via build/vdiff.py. 3 compiles for
  90 functions (one decoder mnemonic bug bez->beqz, one %lo site off-by-one
  0x1780C vs 0x17810). **Coverage: text region 0..0x1868C is 99.95%
  (99928/99980); the only remaining bytes are 52 B of verified all-zero
  alignment padding (0x2F8-0x300, 0x654-0x680) - every real instruction word
  in the text region is now reconstructed byte-exact** (331 functions
  linked, 24982 words, 0 diff, whole-ph0 94.11%). Key decodes (full table in
  results/UU.md): 0x1580 = THE TEH DISPATCH (ring ctx+0x4C0, sentinel
  module+0x500, kernel handlers INLINE via jalr node+8 vs user via 0x2944
  thunk, in-flight node+12 ++/--, auto-delete 0x1877C, event clear P+0x88);
  0x13E80 = THREAD START TRAMPOLINE (TEH class 2, ctxblk+36=3, +84=
  0x800201AC, **+188 slot = 0x172DC for USER threads / TCB+200 for kernel**,
  +176/+180 entry, +168 gp, +52 = 19 user / 3); 0x3D88/0x3FAC = the delay
  cores (k1 save/sll-0xB/restore, deadline 0x10D34/0x10D8C, arm 0x10FAC,
  queue module+0x4E0, enqueue 0x858 type 2); 0xB7E4 = VPL allocate core
  (wait type 6, 0x18774 grants, attr 0x100/0x200 bypass rules); the
  uid-resolve twins (17x) are 0x1876C(uid,table) -> view+12; the static-init
  family (9x, 15-33w) registers name tables + class tables via 0x187CC;
  0x172C8 is a DEAD SPIN (mfc0 $25 + cache + madd + self-j) - first mfc0 in
  the module. GOTCHA: compute word counts PROGRAMMATICALLY - three
  hand-computed boundaries were wrong (0x26CC 24w not 48w, 0x2B64/0x2CA4 70w
  not 116w) and the generator's branch-leaves-function WARN caught all
  three pre-compile. 0x1873C itself is an import veneer (all 6 callers
  already matched) - nothing to transcribe.

- **Batch SS 14/14 EXACT, 834/834 words exact, 0 relocs (THE TWO WAVE-11
  CORNERS: module head 0x0-0x680 + the SysMem-adjacent block 0xE424-0xEAE0
  - 3388 B closed)**: tm_ss.c generated by /tmp/gen_ss.py (gen_tm.py clone
  with the guide's decoder fixes: full cfc0/ctc0/mfc0/mtc0 rd fields, raw
  .word for rotrv/break/eret/cache/SPECIAL2/SPECIAL3/0x48xx-VFPU, 2-op
  bnel→bnezl), compared with build/vdiff.py + full link. 3 compiles: (1)
  branch-to-own-start label + gas `divu` MACRO, (2) two function-size
  arithmetic slips (78w/68w not 54w/70w for the VFPU pair - left a 24w
  tail gap), (3) clean. **WHAT LIVES AT THE MODULE'S VERY START (the
  syscall entry story)**: vaddr 0 is a 2-word VENEER tail-calling import
  stub 0x18694 (the ELF entry/module_start is 0x11F68); 0x8 = the IDLE
  THREAD park loop (infinite, cache 0xa flushes + 0xBC200000 int dance,
  20 literal nop words inside, no xrefs); 0x80/0x1B8 = the VFPU/COP2
  ctx SAVE/RESTORE pair (32x sdc2/ldc2 16B-stride + 0x48xx COP1 ctrl
  transfers = DD/AA's 576B FPU block; callers = sub_12C04 + 0x18224,
  the still-open switch cluster); 0x2C8 = FPU ctrl reset; **0x300 = the
  EXCEPTION REENTRY path ending in eret** (wait-lock node decrement +
  ring unlink, jr through the module+0x338 LOAD-PATCHED dispatch vector,
  Cause bit0 spin, lazy FPU owner switch: *(P+20)&0x2000 gate, owner
  byte ctx+36, swc1 $f0-$f31 at ctx+192..316, sb 0xE00 attach flag);
  0x5A4 = per-thread FPU save. 0x2F8-0x300 + 0x654-0x680 are all-zero
  alignment pads - copied-at-link, NOT transcribed. **THE RESOLVER
  BLOCK**: sub_E424 pool-block validate (range/stride/free-table checks
  → index or 0x800201B6); sub_E4A4 Tlspl uid resolver (rec = node -
  4*hdr21 semantics); sub_E4EC/sub_E530 uid-table create/teardown
  wrappers (0x187CC/0x1876C, rodata name ptrs); sub_E558 pool destroy
  (validates free-index table via 187A4 iff NOT the inline one at
  view+36, frees the ONE SysMem block via 187B4 - CC's ownership model
  byte-locked); **sub_E5EC = MODULE INIT** (USec2SysClock(100) seeds
  module+0x828/+0x82C (MM's scan bias), +0x830/+0x834 = 1, **the clock
  fn-ptr pair module+0x840 = &0xECE4 / +0x83C = &0x10D28**, MMIO
  0xBC60000C/8/10 enable, registers sub_E80C via 0x186D4(val,1,0xE80C,
  base,0) + 0x186F4(val,2), empties rings module+0x68/+0xA8, sentinel
  record (0xF0000000 marker, deadline slots module+0xC0/C4), **32
  pre-created alarm nodes** (0x1875C on *(module+0x540) + jal 0xEEB0
  each), arms 0xBC600004, three 0x186CC/0x18824/0x1882C(24,0x112E0/
  0x112F8/0x1136C) vector registrations); **sub_E80C = THE ALARM
  EXPIRY INTERRUPT HANDLER** (walks module+0xA8 ring, 64-bit expiry
  compare vs 0xECE4 now, unlink + 0x187FC alarm-class test: members
  INVOKE handler(arg) via jalr *(view+0) OUTSIDE the critical section
  then recycle via 0xEEB0; non-members branch to the 0xE994 block = ONE
  function (0xE900 beqzl crosses the "gap") - vtimer members rearm via
  0xEAE0/0x11574, delay-timers route to QQ's 0x126AC deferred-release
  chain (module+0x78, zeroed at init); tail = 0xEB7C reprocess +
  module+0xA4=0 + return -1). UID-table map reconciled: wave-4's
  +0x4FC/+0x504/+0x508 are module+0x40-RELATIVE (absolute +0x53C/
  +0x540/+0x548), matching FF/CC's absolute +0x530 Tlspl. NEW GOTCHAs:
  gas -mips2 REJECTS the `eret` and `cache` mnemonics (raw .word;
  `sync` assembles to 0x0000000F fine); gas macro-expands 2-op
  `div`/`divu` - write `divu $0,$7,$3` (explicit rd=$0) for the raw
  word; branches to the function's own first word need a label on the
  entry symbol (gen_tm.py's a!=addr guard drops it); `.set noat`
  required where retail uses $at; the .dis file contains literal `...`
  ellipsis lines - pull words via --disas only. Full decode in
  results/SS.md.

- **Batch RR 11/11 MATCH, 482/482 words exact, 0 relocs (THE TIMER BLOCK
  0x10FAC-0x116F4, 1864 B - delay timer arm/cancel, hw deadline programmers,
  64/32 divmod, alarm + vtimer expiry dispatchers - plus the 64 B clock
  reader 0xECE4)**: tm_rr.c generated by /tmp/gen_rr.py (gen_kk decoder clone
  + gen_mm %lo-table mechanics; only the bnezl decoder fix fired in this
  block), compiled with tools/match_oo.py, compared via build/vdiff.py
  (validated on tm_mm.o sub_EB7C 78/78 first). 10/11 first-compile; the 1
  fix was the register-field hand-copy class again ($21-vs-$23 in a %lo
  override, 5th recurrence). **Text coverage 76.56% → 82.72%**
  (82700/99980 B exact; 227 functions, 20675 words exact, 0 diff - linked
  prx byte-identical to retail); gaps 0x10FAC-0x116F4 and 0x0ECE4-0x0ED24
  both closed (0xECD4 was already covered as batch E's USec2SysClock tail).
  **THE TIMER PROGRAMMING MODEL (deliverable)**: deadlines reach MMIO
  0xBC600004 exclusively through **module+0xC0** - 0xEB7C (margin
  *(module+0x824), scan bias *(module+0x82C)) stores the 64-bit deadline
  there and mirrors the low word to 0xBC600004 + sync; **sub_1136C** is the
  cold-start/reprogram path (enable 1→0xBC60000C, prescale 48→0xBC600008,
  0→0xBC600010, counter 0xBC600000 ← **module+0 (counter shadow/seed)**,
  compare ← module+0xC0, 0x186BC(*(module+0x80C)) subint-enable);
  **sub_112F8** refreshes the shadow each tick (inside the 0x18704 ack delay
  slot) and KICKS: if deadline−shadow is 0 or >u 0xF0000000 (lui 0xf000, NOT
  0xF000), shadow = deadline−1 so the reprogram fires an immediate compare;
  **sub_112E0** = the SysTimer OVF handler (read counter = ack, raw eret);
  0x112F0 = 2w stub. **UID class map FINAL**: ctx+0x4FC = base "Timer" class
  (20 B link records, 0x18754-registered by sub_1121C) with children
  **ctx+0x500 "SceThreadmanDelay"** (the missing 16th class - delay-timer
  records), ctx+0x504 "Alarm", ctx+0x508 "VTimer" (48 B each, 0x187CC);
  class-create callbacks 0x118A4/0x119B8/0x11A04 live in the NEXT gap
  0x11834-0x11A24 (prime next pick). **Delay-timer free pool: ctx+0x24 count
  / ctx+0x28 head** (module+0x64/+0x68 - resolves MM's unplaced dword;
  three timer dwords now pinned: +0x64 pool count, +0xA4 head-cache, +0xA8
  ring anchor), refilled by 0xEEB0. sub_10FAC(deadline64*, arg, tcb): pool
  pop else 0x1875C(ctx+0x500) (fail → 0x80020190), link+8/+12 = expiry,
  timer+0 = arg / +4 = tcb, EAE0 + EB7C, returns rec+12 uid;
  sub_11104(uid, remainingUsec*): resolve, expiry−now clamped ≥0 via 0x10A74
  SysClock2USec, unlink + ctx+0x64 cache fixup, 0xEEB0 push, 0xEB7C, ret 0.
  Expiry dispatchers arm the **ctx+0x60 sentinel uid** (rec+12), swap gp
  (alarm view+12 / vtimer view+32), jalr handler(view+0/+24, common), log
  **msgno 5 (alarm) / 6 (vtimer)**, and the vtimer one has an
  interrupt-context variant via 0x186FC + 16 B frame at result−16 →
  0x186EC(uid, frame, frame+8, common). divu transcription: `divu $0,rs,rt`
  bare form confirmed; this block's break words are the 0x0007000D
  (HIGH-field) encoding - raw .word as usual. Full decode + string/descriptor
  dump ("Timer"/"Delay"/"Alarm"/"VTimer"/"SceThreadmanSysTimerOVF" @
  0x196C0-0x196D8, descriptors @0x19DD0-0x19E48) in results/RR.md.

- **Batch TT 11/11 MATCH, 951/951 words exact, 0 relocs (THE THREE WAIT
  CORES behind the 2-word veneers - 2640 B - plus the ENTIRE msgpipe ring
  pair/class gap 0x0AFC0-0x0B44C, 1164 B)**: tm_tt.c generated by
  /tmp/gen_tt.py (gen_kk decoder + gen_ll %lo-table mechanics; decoder
  fixes carried: cfc0 rd, rotrv guard, beqzl/bnezl), compiled with
  tools/match_oo.py (all have calls), verified via build/vdiff.py; 2
  compiles (run 1: one %lo-override typo $2 vs retail $6 @0xB170 - LL's
  one-slip class). All four gap entries GONE from build/link/gaps.txt;
  3804 B of text closed (functions.tsv 11x EXACT; text coverage contribution
  +3.81 points of the 74.83->82.72% jump QQ also reports - the two batches
  ran concurrently). **THE CANONICAL WAIT-CORE SHAPE (deliverable, byte-
  confirmed in all three)**: gate (k1 pointer gates on every user ptr arg
  -> 0x800200D3; cfc0 -> 0x80020064; per-family arg validation) -> enter
  0x186ac + dispatch-busy S+0x0C -> 0x800201A7 -> 0x16fa4 snapshot ->
  0x18784 resolve (199/19A/9B) -> attr16 bit 4 -> 0x800200D1 -> views
  (objView + slotView via hdr21) -> log (plain/CB msgno pairs 60/61, 69/70,
  93/94; a1 = S, a3 = uid) -> 0x10d34(sp,*timeout) deadline -> CB pump
  retry (0x2170 + RE-RESOLVE, deleted -> 0x800201B5) -> family test /
  fast path -> TCB park (+0x60 arg, +0x64 mode, +0x68 out, +0x98 CB) ->
  0x908(rec, type 3/4/5, policyArg, deadline, tmo) -> **wake result routed
  from TCB+0x80 through 0x908's return** (0x800201AB retried only when
  CB-armed). Sema core facts: count<=0 -> **0x800201BD** (new), fairness
  0x4d68 nonzero => enqueue unconditionally (no fast-path steal past
  waiters), else currentCount>=wanted consumes without parking. Evf core:
  R.md's "single-waiter slot" is a COUNTED REGISTRAR (objView+12 first,
  +16 count, +20/+24 links; per-thread node at **TCB+0xB0**); match path
  writes *result = PRE-clear pattern, applies waiter's own 0x10/0x20
  clears. Mbx core: N.md's decode byte-locked (k1 re-validation of oldest
  msg on dequeue, 0x800201C9). **Ring pair field-map CORRECTION**: pipe
  +8 = data BASE, +12 = WRITE cursor, +16 = READ cursor, +20 = bufSize,
  +24 = usedBytes (P.md's "+8 read/+12 write/+16 tail" was wrong); each is
  a two-segment wrap copy via 0x1880c. Same gap also held the msgpipe
  UID-CLASS cluster: 48B descriptor at rodata 0x19D58 (methods 0xB3C4/
  0xB2A0/0xB1F8/0xB220) registered at init by 0xB1B4 (QQ's module_start
  calls it) via 0x187cc into **module+0x524 = the msgpipe class-table
  ptr (S+0x4E4)**; 0xB2A0 = standalone queued-SENDER drain (the receive
  core's inline loop factored out), 0xB3C4 = waiter-leave hook (partial
  flag re-derive, count--, direction reset at zero), 0xB16C = table-free
  uid ring resolver (IdOwner's msgpipe leg). Full decode in results/TT.md.

- **Batch QQ 3/3 MATCH, 538/538 words exact, 0 relocs (THE module_start
  BLOCK - the single largest gap 0x11F68-0x127D0, 2152 B)**: tm_qq.c generated
  by /tmp/gen_qq.py (gen_kk.py decoder + NEW mfc0/ctc0 rd-field decode -
  this block's COP0 words are REAL mfc0/ctc0 (rs=0/6), gas assembles them
  natively, no raw .word needed), compiled with tools/match_oo.py (all three
  have calls), verified via build/vdiff.py (control: tm_kk.o sub_FE4 87/87)
  and the linker (3x EXACT in functions.tsv; gap range GONE from
  build/link/gaps.txt; text coverage 74.83% -> 82.72%, of which 2152 B is
  this batch - the rest of the jump is concurrent tm_rr/tm_tt batches).
  **THE BLOCK = 3 functions**: sub_11F68 (400w, module_start; the mode tails
  0x12558-0x125A4 + the 2-word `jr ra; li v0,-1` stub @0x125A0 passed as
  int-0x41 handler arg belong to it), sub_125A8 (65w, thread-2 body), and
  sub_126AC (73w, uid free). **module_bootstart is NOT here** - syslib stub
  table 0x18A00 says module_bootstart = 0x16B84 (the 0x16B40 gap). **What
  module_start builds (full decode in results/QQ.md)**: cache-flush of the
  2052B S block + mfc0 $22 -> S+0x7C8; 13 per-family init calls (0xC50,
  0x16B40, 0x283C, 0x4FBC, 0x6120, 0x743C, 0x84B4, 0x92F4, 0xB1B4, 0xC244,
  0xD474, 0xE4EC, 0x1121C - each anchors one of the remaining gaps); 5
  S-block list heads + ALL 128 runq anchors self-linked; boot-mode detect
  via imports 0x1872C(22/23/26)+0x18734 -> mode word S+0x7E4 (prints
  "CPU Profiler enabled: "/"Thread Mode"/"Global Mode", ORs 0x300 into
  0xBC000030 on the f23 path); then THE THREAD POOL: 2KB pool
  0x1878C(1,2048,1,"SceThreadman") -> S+0x7E0; **thread 1
  "SceThreadmanIdle"** prio 127, 256B stack, entry 0x172C8 (the perf-counter
  idle spin) iff mode!=0, state 2, queued 0x127D0, -> sentinel slot S+0x50C;
  **thread 2 "SceThreadmanCleaner"** prio 1, entry 0x125A8, state 4 ->
  KK's dispatch-fallback slot S+0x510; **thread 3 "SceThreadmanInit" = the
  CALLER ADOPTED** (0x187F4(saved caller sp) + 0x187DC 56B stack desc),
  prio 32, state 1, *(module+0x40)/S+4 = TCB3 + ctc0 $14/$15/$16 re-point +
  k1=0 - S->current is born HERE. Then dispatcher registration:
  0x1870C(module+0x1100, 0x12828-the dispatch loop) + 0xE5EC (unmatched),
  0x186D4(0x41,0,stub_125A0,0,0) + 0x186BC(0x41) for the SW-int,
  0x1869C(11, module+0x338) (module_bootstart later does 0x1868C(11,
  module+0x338)), syscall templates S+0x7D4/0x7D8/0x7DC =
  _sceKernelExitThread/_sceKernelReturnFromChangeStack/
  _sceKernelReturnFromCallback, internal evflag "SceThreadmanSysStat" ->
  S+0x7D0, 0x18744(0x172A8,3,0) = init-thread ExitDeleteThread epilogue;
  returns 0. **sub_125A8** = infinite reaper: walks the module+0x78
  deferred-free block chain (0x18784 resolve / 0x155B8 cleanup / 0x1877C
  free / 0x187A4 pool-free), then parks P->state=4 + FE4(1,1).
  **sub_126AC** = DEFERRED uid release: append to module+0x78 chain (8
  slots/block, 40B blocks, dup -> 0x80020198, alloc fail 0x80020190), arms
  S+0x34=1 + S+4=0. GOTCHA: `j 0x12100` lands ON the jal (shared delay
  slot stores the mode) - KK's class; delay-slot `addiu s5,v0,64` uses
  PRE-call v0 - transcribe operands verbatim, never "fix".

- **Batch KK 6/6 MATCH, 577/577 words exact, 0 relocs (THE DISPATCHER
  CLUSTER - the heart of the module, all internals)**: tm_kk.c generated by
  /tmp/gen_kk.py (gen_tm.py word-decoder + 2 decoder fixes); vdiff
  validated on tm_v.o/tm_ee.o first. **Where the dispatcher is**: the
  switch/dispatch LOOP is **sub_12828 @0x12828** (247w, called only by
  sub_FE4); the brief's clz cascade over ctx+136..+148 is a **THIRD
  cascade @0x173A4-0x173CC** inside **sub_172F8 @0x172F8** (141w, called
  only by the loop at 0x12B14; Z's "8 clz words, 2 cascades" is really 12
  words / 3 cascades). Chain: 30 switch-away sites -> jal 0xFE4 -> jal
  0x12828 -> jal 0x172F8. **Context-switch semantics (the deliverable)**:
  NO GPR/k1/gp is saved in threadman - the 320B ctx block at TCB+0x28 is
  the exception frame (filled/reloaded by the kernel stub at eret); the
  loop only re-points FOUR banked COP0 regs (rs=3 raw words 0x40Cxxxxx @
  0x12A2C-0x12A5C): bank6 = TCB+0x3C FPU-block ptr (0 if none), bank14 =
  &FPU ctrl word, bank30 = TCB+0x28 ctx block, bank0 = &TCB+0x24; FPU
  registers are MMIO at 0xBC400000 (block+0x10..+0x5F = regs, +0x60 =
  ctrl; two 16B-stride copy loops w/ sync do save/restore-on-switch).
  S->current (module+0x40) = target @0x12A1C; *(S+0x70/+0x74) = dispatch
  TIMESTAMP (CPU-time deltas = now - it); *(P->0x40 switch frame)+1 per
  dispatch; **msgno 1 = context-switch log event** via jalr *(S+8) (the
  SetThreadmanLogHandler slot, module+0x48) with 5 extras (oldTid,
  oldPrio, newTid, flags). **sub_FE4(a0 kind, a1 st)**: a0 picks the
  switch-frame variant P+0x48/P+0x4C; a1==0 (interrupt ctx) = defer via
  CP0 Cause bit 9 (`cfc0/ori 0x200/ctc0 $13`) + jal 0x186BC(0x41);
  dispatchState (S+0xC) != 0 -> return; else cfc0 $25 handlock node (+8
  0/1 state, sync-guarded), jal 0x186E4(P+0x1C) gate, then the loop.
  **sub_172F8**: S+0x34 pending flag path requeues current (state RUNNING)
  at TAIL of its own ring else S+4 = *(S+0x510 idle); clz scan -> best
  prio; preempt only if bestPrio < current->prio (current requeued at
  TAIL, state 2, target state 1, S+4 = target); 128 = PANIC jal
  0x18724(0x19800). **sub_16C48(T,st)** = preempt handshake (target more
  urgent + dispatchState 0 + thread ctx: requeue P, T state 1, S+4 = T,
  jal FE4(0,st); else 127D0 append); **sub_127D0(T)** = plain tail-append
  + bitmap bit; **sub_16BF4(T,prio)** = unlink + clear bit iff ring
  empties (Z's decode confirmed 1:1). 0x12C04(T) (DD's helper) is part of
  switch-in: per-thread interrupt-mask reprogram (0xBC000044) when
  ctxblk+52 & 0x40000000. GOTCHAs: gas rejects 2-operand `bnel` (use
  bnezl); gen_tm.py decoder bugs - cfc0 hardcodes $13 (also $25/$8 exist)
  and Allegrex rotrv (= srlv with sa=1) silently decodes as srlv dropping
  bit 6; both fixed in /tmp/gen_kk.py. sub_FE4 0x1100-0x113C is DEAD CODE
  (no xrefs module-wide) - transcribed anyway. Full decode + TCB/S field
  table in results/KK.md.

- **Batch MM 7/7 MATCH, 805/805 words exact, 0 relocs (user-callback
  machinery + remaining family cores - ALL INTERNALS)**: tm_mm.c generated
  by /tmp/gen_mm.py (gen_tm.py word-decoder; vdiff validated on tm_v.o
  first). 5 of 7 first-compile; 2 fixes: gen_tm's COP0 decoder hardcodes
  `cfc0 r,$13` (the thunk's `40464000` = **cfc0 a2,$8 BadVaddr** needs a
  raw-word override) and 2 rt-field typos ($22 vs $18). **THE USERMODE
  CALLBACK MECHANISM (deliverable)**: pump 0x2170 walks the current
  thread's callback ring (anchor P+0x90), consumes notifyCount/notifyArg
  (node+24/+28), sets nesting P+0xA0++/guard P+0xA4=record, and calls
  **invoke thunk 0x2944(userFlag, func, count, notifyArg, common, 0, gp)**.
  The thunk builds a 64-byte-aligned EXCEPTION FRAME (init 0x134A8: GPR
  r0-r31 @+64..+188 deadbeef-poisoned, FPU @+192.., then sets): **EPC@+56 =
  the user callback function**, a0/a1/a2 = (count, notifyArg, common)
  (PSPSDK signature confirmed), **gp@+176 = the callback's own gp (obj+44
  = 0x1873C(func) or creator gp - the GP SWAP)**, Status@+52 = 19
  (IE|EXL|UM, user-mode resume), k0@+168 = P+220. It parks the kernel
  context by swapping P+36/+40/+132/+24 (restored by the error path /
  return trip), clears TCB attr bit 0x4000 (FPU detach, ins 7C187384), and
  for USER callbacks **patches a `syscall` instruction onto the user stack
  top** (code = *(module+0x81C), icache flush via cache 0x1b/0x8 + sync),
  pointing frame sp/fp/ra (r29/r30/r31) at it; KERNEL callbacks get ra =
  module+0x2DBC (in-module return trampoline: cookie→P+128, sub_28C0).
  Then `ctc0 *(P+40),$15 / ctc0 s6,$14` + `jal 0x186C4(frame)` (import
  stub) and RETURNS 0 - the callback is NOT called inline: the next
  dispatch resumes the thread IN USER MODE at the callback; `jr ra` fires
  the patched syscall → _sceKernelReturnFromCallback (0x253C, the blocked
  13w export - its full call graph 0x28C0/0x2DBC/P-field swap now decoded)
  swaps the kernel context back. **Pump decode corrections**: the skip
  flag node+16 = deferred-delete marker (Delete/Cancel arm it; node+12 =
  in-flight ++/−− counter; drain-to-zero → unlink + 0xB48(rec,0));
  auto-delete = result!=0 && node+16==0 (uid at node+8, 0x1877C); log
  msgno **7**. WaitThreadEnd core: T.md exact (msgnos 55/56, exit status
  = target+84, 0x800201AB CB retry). **FPL core**: wait type **7**, log
  msgnos 118/119, 0xD38C ring pop, block = base+idx*stride, grant via
  P+0x60 - FPL family COMPLETE. Alarm core 116F4: 0x1875C(alarm tbl,
  name 0x296E0, userbyte, &rec); expiry = arg64 + now64 (BOTH SetAlarm
  and SetSysClockAlarm relative); alarm obj +0 user/+4 handler/+8 common/
  +12 1873C-or-gp; returns rec+12 uid. Timer queue: **anchor = module+0xA8
  (8-byte ring {first,last}; G/J's "ctx+0x64" = module+0xA4 is CancelAlarm's
  head-cache, module+0xA0 = sentinel uid)**; links +0/+4, 64-bit expiry
  +8/+12, ascending sorted insert; reprocess 0xEB7C scans soonest, adds
  margin *(module+0x824) when past/near, stores deadline module+0xC0/+0xC4
  and mirrors to MMIO 0xBC600004 + sync (scan bias *(module+0x82C)).
  Register double-life is systemic here: s6 in 0xC950 (user-flag → then
  0x800201AB constant), s5 in 0x3AD0, s0 in the pump's unlink block -
  always transcribe from the LAST write of a callee-saved reg.

- **Batch NN 8/8 MATCH, 968/968 words exact, 0 relocs (the teardown cores
  + mutex bookkeeping trio + status builders - ALL INTERNALS)**: tm_nn.c
  generated by /tmp/gen_nn.py (tools/gen_tm.py word-decoder method: every
  retail word decoded independently, branch/jump targets from RAW offset
  fields, 22 module-data %hi/%lo sites hand-listed), compared via
  build/vdiff.py (validated on tm_v.o first). **First compile, zero
  iterations, zero diffs** - the generator method is now 3-for-3 (II, LL,
  NN). Sizing corrections: **0x17A14 is ONE 296-word function**
  (0x17A14-0x17EB0; "live-kill 0x17B68" is an internal block, not a
  separate function); **0x177AC is a block inside sub_1752C** (166w). **The
  LIVE-KILL PROTOCOL (decoded)**: terminate on a live target REBUILDS the
  victim's ctxblk (0x134A8; runStatus 3, exit status 0x800201AC, ctxblk+56
  = 0x178C0 as the exit TRAMPOLINE - the slot StartThread fills with
  0x13E80) so the victim falls out of its entry function into the exit
  core when dispatched; the TERMINATOR then sleeps as a type-9 (thread-end)
  waiter on the victim via 0x908 - synchronous terminate; interrupt-ctx
  plain terminate returns immediately (no wait), terminate-delete runs the
  delete inline; self-kill from interrupt with dispatch suspended sets
  **ctx+0x0C = 3** (writer of HH's state 3, deferred via
  ResumeDispatchThread); already-exiting target (gate&0xC): plain →
  0x800201A2, delete → gate|=8 + return 0; dispatch-busy (ctx+0x0C!=0) is
  FORCE-CLEARED with a 0x18724 warning and the kill proceeds (both 0x17A14
  and 0x178C0 and 0x1752C do this force-clear). **Mutex ceiling arithmetic
  (exact)**: acquire = effective(TCB+188) = MIN(effective, ceiling) +
  requeue iff effective < runq prio (0x14598); release: ring empty OR
  non-0x400 head → effective = 127, requeue at BASE (s16 `lh` TCB+186);
  0x400 head → effective = head ceiling, requeue at min(ceiling, base);
  mass-release 0x66F0 rescheds iff boosted OR 0xC30 cancelled any waiters
  (counts accumulate in a j delay slot); attr 0x800 → owner = -1, count
  untouched (locked forever). **Second dead list @module+0x4F8** (state
  0x20, exitStatus 0x800201A2) with the registered dead-thread handler at
  module+0x838 - sub_1752C inserts there and jalr's the handler(uid,
  ctxblk); distinct from the exit core's ctx+0x4A8 (module+0x4E8) list
  (state 16). 0x1752C = the 0x178C0 chain factored out (B48 with
  0x800201AC + 8 callees) - _sceKernelExitThread's callee. SystemStatus
  builder 0x183EC: 28B, mode = 4 (interrupt) / 3 (a1==0) / 0 / 1 by
  ctx+0x0C, fields from the SENTINEL record ctx+0x50C. ThreadDebugStatus
  builder 0x180AC: 244B map + wait-type union at +144..+160 via `jr` jump
  table @0x29E88 (TCB+0x58-indexed), badvaddr cfc0/ctc0 pair, halfword→
  word write-back at ctxblk+36. GOTCHA for generators: gen_tm.py's cfc0
  decode ignores the CP0 rd field - only rd==13 (Cause) decodes to the gas
  mnemonic; cfc0/ctc0 of badvaddr (0x40504000/0x40D04000) must be raw
  .word (fix applied in /tmp/gen_nn.py, tools/ untouched). Unresolved new
  callee: 0x25FC(view) - live-kill inline-teardown gate. Still unassigned
  in the region: 0x177C4/0x17844 (31w dead-thread dispatchers tailing into
  0x1752C), 0x18474 (36w), 0x18504.

- **Batch LL 10/10 MATCH, 0 relocs (the wait-queue machinery - every IPC
  family's shared cores)**: tm_ll.c via gen_tm.py-style decoder script,
  compared with build/vdiff.py (validated 19/19 on tm_ii.o + 359/359 on
  tm_v.o first). 2 compiles: run 1 had ONE diff - my %lo override typed
  $2 for retail a2=$6 at 0x998. Full decode + the canonical invariants in
  results/LL.md. The cores: **0x680** = full wait primitive (slotView =
  rec+4*hdr21(*(module+0x508)); arms timer 0x10FAC(deadline, module+0xC8C,
  tcb) with handle→TCB+0x78/arg2→TCB+0x7C; REFUSES to block with
  0x800201AB if CB-armed+notify-pending - the enqueue-time twin of
  NotifyCallback's abort; stamps state=4/gate=type/TCB+0x5C=rec/waitResult=0,
  bumps view+8, inserts priority (attr&0x100, key=TCB+0x10, protected
  head via view+4) or FIFO tail, zero *(module+0x44), FE4(1,1); RETURNS
  TCB+0x80 - the waker's word). **0x858** = tail append on standalone
  sleep/delay head structs (+0x5C=0). **0x890** = the bare priority
  re-insert (a0=any tcb). **0x924** = release: unlink → disarm +0x98 →
  0x11104(TCB+0x78,TCB+0x7C)+zero pair → 0x1879C(TCB+0x5C, 0x5BD49380,
  tcb) → state 12→suspend ring (module+0x4F0) as 8 / else state 2 +
  0x127D0; returns 1 iff READY. **0xA08** = wake-now with cause-aware
  tail (thread ctx 0x16C48(tcb,status); intr ctx 0x127D0 +
  *(module+0x44)=0). **0xB08** = direct handoff: result into HEAD
  waiter's +0x80 in the jal delay slot, then A08. **0xB48** = full-ring
  exit walk (per waiter +0x80=status + 924, next-load in jal delay slot,
  returns count). **0xBC4** = teardown-without-unlink. **0xC30** =
  0x1879C(INHERITED a0, 0x85FE2B4C). **TCB+0x5C = the waited-OBJECT
  pointer** (closes H/R's "cleanup flag"); *(module+0x40) word+0 is a
  conditional waiter-refcount (t1 arg); timeout core @0xC8C (decoded
  only) is the 4th wake path: waitResult=0x800201A8 + both 0x1879C tags.

- **Batch II 17/17 MATCH, 0 relocs (refer/misc sweep - first DECODER-SCRIPT
  batch)**: tm_ii.c, full decode + both unnamed-NID identifications in
  results/II.md. 16 of 17 first-compile; ReferTlsplStatus 1 fix (hand
  override typo). NEW METHOD: /tmp/gen_ii.py decodes each retail word
  independently and emits the noreorder asm - branch/jump targets computed
  from RAW offset fields, never .dis annotations; only the module-data
  %hi/%lo sites are hand-listed. 1 typo in 1406 words (vs 4-6 in hand
  batches). **Import stub table discovery**: 0x18790-0x18830 is a 2-word
  `jr ra;nop` veneer table patched at load - jal words there are
  word-exact; 0x183ec (SystemStatus builder) and 0x180ac (ThreadDebugStatus
  builder, 244B) are REAL internal functions. **0x187dc (import) =
  stack-block allocator `(pool, desc56)`: desc[0]=size; fills desc+40=data,
  desc+44=blockSize** (also used by CreateThread's 320B ctx block).
  Unnamed NIDs: 8672E3D0 = GetCallbackNestingLevel (returns *(P+0xA0),
  msgno 161, no uid machinery); 28BFD974 = user-mode temp-stack runner
  (0x187dc + 0x17eb4, >=512B else 0x80020194, returns 0xdeadbeef, msgno
  40) - both unnamed in the authoritative psplibdb threadman.csv.
  IdOwner = type-dispatch (sema/vpl/mbx/tlspl resolvers → out types
  5/6/7/14) + threads-ring wait-queue walk, err 0x800201CB. New msgnos
  35/36/40/44/96/117/120/130/161/164; errors 0x80020190/94/9B/CB/D0.
  Sony emits live shift-by-0 no-ops (`sll r,r,0` - transcribe verbatim).
  AllocateFpl/CB veneer into the still-undecoded 178w core @0xC950.

- **Batch HH 8/8 MATCH, 0 relocs (wait-family stragglers + the dispatch-
  suspension pair)**: tm_hh.c, full decode in results/HH.md. 2 compile
  iterations (run 1: one forward beqzl needed its label ON the next branch
  word, not the block head - 5/8 matched; run 2: 8/8 after fixing three
  `bnez v1` copied as `bnez v0`, the cfc0 cause lives in v1 in this
  family). **The dispatch pair decoded**: SuspendDispatchThread gates
  cause/cookie (0x80020064/0x80020066), logs msgno 23, returns 1 iff it
  transitioned ctx+0x0C 0→1 (0 if already suspended - the saved state for
  ResumeDispatchThread(state) to feed back); USER threads also set a
  per-thread mirror *(P+0xDC)+0xC4 = 1. ResumeDispatchThread takes the
  SAVED STATE as arg a0, logs msgno 24, delegates to new internal
  **sub_14124(state,a1,cookie)**: state 0 = suspend-side (same mirror
  logic, returns 0); nonzero = resume - clears ctx+0x0C and the mirror,
  old==2 re-parks current on the suspend list (module+0x4B0, FE4(1,0)),
  old==3 routes into sub_17A14 (terminate-pending) / 0x178C0 never-return
  when a2 nonzero. **ctx+0x0C state catalog (K refined)**: 0 run, 1
  suspended, 2 suspended+current-parked, 3 suspended+terminate-pending -
  this is the field every wait entry gates with CAN_NOT_WAIT 0x800201A7
  (L), i.e. the scheduler lock; the +0xC4 mirror is the per-user-thread
  side the callback family consults. **SuspendAllUserThreads (79w) is the
  writer of ctx+0x30 = 1** (the pending-dispatch flag R saw gate
  SignalSema's user-thread wakes): walks the thread UID ring via a THIRD
  33-entry state jump table @0x19C34 - runnable→dequeue+suspend-list
  (state 8), waiting→state 12, kernel threads and state>=33 skipped.
  **_sceKernelExitThread (30w)**: status = [P+0x24]+0x18, calls Y's
  matched sceKernelExitThread 0x139C8 AND KEEPS ITS RETURN VALUE, then
  sub_1752C(P − 4*hdr21) = the factored-out post-exit teardown (B48 with
  0x800201AC + the 8-callee chain Y saw inline in 0x178C0; deferred
  variant 0x177AC when ctx+0x0C!=0) - it RETURNS, the only exit path
  that does. **RegisterThreadEventHandler (191w)**: k1 gates on
  name+handler (D3), user requires kernel-class handler; mask 4 bits
  (ins raw 0x7C091804, else 0x80020196); special tids −1/−8/−16 (kernel
  bypass, user only if == self tid, else 0x80020198); tid 0 requires
  mask==4 (0x80020191) and targets the current thread; resolves + attr
  bit 2 (D1) + attr>>28 class match for user; UID-create via
  0x1875C(TEH tbl ctx+0x4F4, name, userByte, &rec); TEH VIEW layout +8
  uid, +0x14 target, +0x18 user, +0x1C mask, +0x20 handler, +0x24 common,
  +0x28 gp (0x1873C); ring anchor **ctx+0x4C0**; log msgno **45** with 5
  extras (tid, mask, handler, common, uid), a1 = TEH view. The three
  wait veneers close R's set: WaitEventFlag/CB `j 0x5740; li t3,0/1`,
  WaitSemaCB `j 0x475C; li t3,1` - CB flag in t3 as everywhere.
  New error: **0x80020066** = cookie==0 alone (the 0x800201A7 of L/K
  batches was the ctx+0x0C gate; 66 is the pure acquire-fail flavor).
  GOTCHA: mid-sequence label targets - a forward beqzl can target the
  very next branch word; put the label there, not on the "block head".

- **Batch FF 3/3 MATCH, 0 relocs (the last big creators + TryReceive)**:
  tm_ff.c, full decode in results/FF.md. 850 words in 2 fix passes (first
  compile rejected on movz/movn needing `.set mips4`; then 9 word diffs,
  all one-pass transcription slips: 7 register-field typos + 2 LABEL
  off-by-ones). **CreateFpl 0xC408 (265w)**: O.md's decode closed - same
  skeleton as CreateVpl/CreateTlspl (name/opt k1 gates, attr & ~0x41FF,
  opt align power2>=4 else 0x800200D2, 64-bit stride*count overflow ->
  0x800201B7, 0x187BC partition user gate &3==3, 0x18794(partition, name,
  attr&0x4000?4:3, align, total) one-block pool, obj+4 = 0x187E4 dataHead,
  0x1875C UID create returns 0-on-success with uid at rec+12, numBlocks>=3
  -> index table from pool *(module+0x820) else inline obj+36, free ring
  via 0xD2E4, msgno 116). **CreateTlspl 0xD574 (295w)**: CC's decode-only
  member byte-confirmed - mirror scan FIRST (module+0x6D4, full ->
  0x800201D1), raw `ins s6,a0,3,4` patches the mirror idx into SceUID bits
  3-6, mirror[idx] = patched uid stored in the bnez LOG-TEST delay slot
  (both paths), pool tbl *(module+0x530), free ring via 0xD338 (not
  0xD2E4), msgno 124 (a1 = idx). **TryReceiveMsgPipe 0xA798 (290w)**:
  W.md's guide decoded with 2 corrections - the would-block error is
  **0x800201B4 (MPF_EMPTY; TrySend's B3 = MPF_FULL - the brief's B3 was
  wrong)** and the size is 290w (no +2 skew). Receive core minus blocking:
  `ins t2,zero,0,1` waitMode mask BEFORE enter-critical, cookie never
  spilled (captured at 12(sp) in the 0x18784 jal DELAY slot = pre-call v0,
  same shared-delay-slot capture as the creators' dataHead), mode0 prescan
  adds ALL queued senders' rem to available, direct handoff + ring-drain
  0xAFC0 mirror of the core, bypass = slot attr 0x1000 && slot+4==0 &&
  prio win, cfc0 only gates the final FE4 dispatch, msgno 105 (a1 = s8
  residue). New recipe facts: INS rd field is MSB (size = msb-lsb+1, so
  0x7C9630C4 = ins s6,a0,3,4); INS with rs=zero is a bit-CLEAR (mask);
  the mid-sequence error-tail `j` (j 0xC5C4/j 0xD770 landing on a j whose
  delay is the error ori, lui preloaded in the gate branch delay) is the
  standard create-family shape, present in BOTH creators. Families: FPL
  COMPLETE, Tlspl COMPLETE; MsgPipe has only CancelMsgPipe @0xAC20 (108w)
  left.

- **Batch EE 4/4 MATCH, 0 relocs (mutex family COMPLETION - Unlock + lock
  core + TryLock + Refer)**: tm_ee.c, full decode in results/EE.md. 3
  exports via match.py, the 246w internal core 0x6A7C via build/vdiff.py
  (validated on tm_v.o first). **UnlockMutex handoff protocol**: full
  release (new count <= 0) = 0x7480 relinquish (releaser's ceiling
  restored FIRST) then a waiter walk serving **exactly ONE waiter** -
  0x6604(rec, waiterTCB, waiter->TCB+0x60 wanted) applies the ceiling boost
  to the NEW owner, then 0x924; 0x924>0 -> 0x16bf4+0x16c48 dispatch tail.
  Partial unlock (count still > 0) stores the count, NO waiter walk.
  Underflow 0x800201C7 = strict currentCount < unlockCount; owner !=
  current -> 0x800201C5 checked BEFORE underflow. **Lock core fast-acquire
  gate**: block iff a candidate waiter exists AND (slot attr 0x100 == 0
  [FIFO] OR my prio >= candidate's); queue-pass + owner==0 -> acquire;
  ctx+0x30 busy hides USER waiters from the gate. TryLockMutex has NO
  fairness gate at all (jumps waiters, contrast PollSema 0x4D68); would-
  block = 0x800201C4. ReferMutexStatus: no cfc0, 56B info {size,name[32],
  attr@+0x24, init@+0x28, cur@+0x2C, ownerId@+0x30, waitCount@+0x34},
  ownerId = 0 -> -1, owner == -1 (0x800 mutex stranded by sub_66F0) -> -2.
  Log msgnos 76/79/81 (79's a1 = count, unique in family). NEW GOTCHA
  class: branch-likely targets landing on ANOTHER branch's delay slot -
  compute target = branch+4+offset*4 with the raw word, never eyeball the
  .dis (cost 2 of Unlock's 3 iters).

- **Batch AA 1/1 MATCH, 0 relocs (sceKernelCreateThread - the TCB
  constructor)**: tm_aa.c, full decode + the authoritative thread-record
  constructor map in results/AA.md. 367w, the project's largest matched
  export, FIRST COMPILE. (ExtendThreadStack 0x1512C was also matched
  here but DD owns it concurrently - duplicate removed from tm_aa.c, its
  decode stays in AA.md.) **Gates**: name/entry/option k1 gates → D3;
  cause!=0 or current->gate → 64; attr & 0x070F9F00 → 191; USER-CALLER
  attr sanitize: attr &= 0x07FFFFFF, then bit 0x00800000 clear → attr |=
  (current->attr & 0xFF) [inheritance] else attr |= 0x80000000; user prio
  8..119 + attr |= 0xFF on the OK path; entry&3 → 192; size<512 → 194.
  **TCB fields written**: +16 prio, +20/+288 attr, +192 ENTRY (K.md's
  "rec+196 entry" is really stackSize+255 - stackTop = rec+44 +
  (rec+196&~1)), +184/+186 prio s16, +188=127, +196 stackSize+255,
  +216 = 0x1873C(entry) or gp, +300 option, +304 stack block, +312/+316
  partition (mpid else attr<0?2:1), +44 stack data head, user attr
  extras +48/+204/+308 = 2048B kernel-part anchor block, +60 = 100B FPU
  ctx {0xBC400000,1,1} iff ctx+0x7E4 ∈ {1,3}, +28 = 320B ctx blk (attr
  0x4000 → +32 = 576B FPU ctx), +12 state 16 DORMANT, +84 0x800201A2,
  links into ctx+0x4A8 dormant list. **New callees**: 0x1881c
  name-copy variant (dst,31,0x197C0/0x197CC/0x197D8,src), 0x187ec ctx
  alloc (pool ctx+0x7E0, size, desc@module+0x724{8,64}), 0x18764 stack
  handoff (rec+44|+48, -1, size), 0x17eb4 stack-switch runner (Extend).
  Log msgno 16; TEH dispatch 0x1580(rec, class 1); returns rec+12 uid.
  INS field decode (rd=size-1, sa=pos) now confirmed on 6 words.

- **Batch CC 6/6 MATCH, 0 relocs (BOTH TLS SYSTEMS - Tlspl + KTLS)**: tm_cc.c,
  full decode + the two-systems contrast in results/CC.md. CreateTlspl
  0xD574 (295w) DECODED ONLY (>200w rule): pools own ONE SysMem block
  (0x18794, total = alignUp(size,align)*count, opt at template
  module+0x714); the free-slot index is EMBEDDED INTO the SceUID (INS
  bits 3-6 at 0xD880, `ext uid,3,4` everywhere = `(uid>>3)&0xF`) and
  cross-checked against the 16-word uid mirror table **module+0x6D4**
  (16 pools max, full -> 0x800201D1). Per-thread block table =
  `*(threadRec+0xDC)+0x40+4*idx`; Allocate returns an existing block
  without realloc, enqueues **wait type 14** (0x908, deadline 0x10D34)
  when none, grant lands in TCB+0x60; Free hands the block DIRECTLY to
  the head waiter (waiterTCB+0x60 + 0xB08 wake) or memset + 0xD338
  push-back (0xD3DC pops at alloc); Delete needs freeCount==count (or
  count-1 with the one outstanding block reclaimed from the CURRENT
  thread via 0xE424) else 0x800201D2. KTLS: 16 descriptors
  module+0x554 {+0 inUse, +4 refcount(per-THREADS holding), +8 size,
  +12 dtor, +16 arg, +20 gp}; values INLINE at `threadRec+0xE0+4*id`;
  GetThreadKTLS(id,tid,flag) lazily allocates+zeroes per-thread blocks
  from sysmem pool `*(module+0x820)` when flag!=0 and bumps desc+4;
  FreeKTLS frees the DESCRIPTOR only (refcount must be 0 ->
  0x800201C2). Exit walkers 0x11E3C (KTLS: inline dtor with GP SWAP iff
  dying rec == *(module+0x40), else deferred; frees block via
  0x187A4, clears slot, refcount--) and 0xE0D4 (Tlspl: returns all 16
  slots' blocks, serves sleeping allocators via 0xB08) - **proving
  P = *(module+0x40) IS the CURRENT THREAD'S RECORD** (the walker
  compares thread records against it; supersedes the round-1 "global
  ctx" reading - log handler at P+0x48 is a per-thread field).
  New: module+0x4C dispatch-busy gate (0x800201A7), module+0x530 =
  Tlspl class-14 UID table (Z's +0x4F0, base-relative), 0xE424
  pool-block validate->index, 0x18804 zero-init, 0x1873C dtor
  validate. Msgnos 124/125/126/129, 167/168/170; errors 1D0/1D1/1D2,
  1C0/1C1/1C2, 1B7, 190. GOTCHAs: 4 forward/backward label typos (the
  family floor - check EVERY Xf/Xb against target direction); tail
  gate `j 0xDC80` lands ON the ORI of the error build (delay slot
  supplies the lui) - j targets can be mid-instruction-sequence, not
  just labels; non-likely bnez delay slots carry both-paths side
  effects (mirror store 0xD8F4, refcount reload 0x11DB8).

- **Batch DD 9/9 MATCH, 0 relocs (stack machinery + callback pump gate + 3
  vtimer getters)**: tm_dd.c, full decode + the stack-extension mechanics
  deliverable in results/DD.md. 3 compiles total. **The park mechanism**:
  ExtendKernelStack builds a 16B frame ON THE OLD STACK
  ({old TCB+0xD0 head, +0x2C/+0x30 data, +0x130/+0x134 uid, +0xC4/+0xCC
  size}) and threads it through TCB+0xD0 as a linked park list; switches
  sp = data + size+255 between SPECIAL2 raw-word barriers (0x7013xxxx),
  calls func(arg), restores. TCB+0xD4 (212) is a SEPARATE single frame
  anchor - _sceKernelReturnFromChangeStack pops IT, restores the same
  three fields + writes frame {+0x10/+0x18/+0x14} into [TCB+0x24]+4/+8/+C,
  frees the parked block (TCB+0x130 via 0x187B4), returns [TCB+0x24]+0x18;
  Cause!=0/no frame -> break 0x3,0x3ff (raw 0x0003FFCD). ExtendThreadStack
  is the thin user sibling delegating to 0x17EB4(uid,data,size,func,arg) -
  **returns 0xdeadbeef on success** (func result discarded, retail quirk).
  CheckCallback = gates (Cause, TCB+0xA4 guard, cookie, ctx+0x0C==0 →
  0x80020064/0x800201A7) then `0x2170(cookie)` - the PUMP (decoded, 132w
  @0x2170): walks TCB+0x90 callback queue, per armed node consumes
  notifyCount/Arg, sets TCB+0xA0 nesting++ + TCB+0xA4 = record, calls
  **0x2944(arg, func, count, notifyArg, common, 0, gp)** invoke thunk;
  result!=0 && attr==0 → 0x1877C auto-delete; attr!=0 && count==0 →
  unlink + 0xB48(rec,0) + FE4(0) iff deletions; returns executed count -
  CheckCallback returns (count != 0). ChangeCurrentThreadAttr: both args
  ins-masked bits 14..28 (else 0x80020191); bit 0x4000 = FPU: lazily
  0x187EC(&ctx+0x7E0, 576, {8,64}) allocs a 576B FPU ctx (128 regs
  0x7F800001 countdown-fill + 0x3F80xxxx control block, fail → attr
  revert + 0x80020190), mirrors bit into [TCB+0x1C]+52 and [TCB+0x24]+0,
  flips CP0 Status bit 14, 0x12C04(TCB). New internals: 0x1881C name
  builder (2 adjacent str constants 0x197C8/0x197D4), 0x187EC FPU ctx
  alloc, 0x2944 user-callback invoke thunk, 0x12C04, 0x14124(1,0);
  **0x18764(ptr, mode, size) = cache-range op** (3 call-site shapes now:
  (data,-1,size), (data,0,size), (TCB+0x2C,0,TCB+0xC4)). VTimer getters
  add msgnos 145/151/152; GetVTimerBase of a STOPPED timer returns {0,0}
  (the field holds elapsed then). GOTCHAs: k1 restore can read a
  different saved copy (`move k1,s1` @0x154A8 - s1 was re-pointed at the
  save @0x15458); countdown loops may put the decrement at the loop HEAD
  (dropped word → every later branch offset -1, N vs N-1 signature).

- **Batch BB 7/7 MATCH, 0 relocs (FULL Mutex family + Poll/CancelSema - the
  priority-inheritance answer)**: tm_bb.c, full decode in results/BB.md.
  **The scheduler-semantics deliverable: the full mutex does PRIORITY
  CEILING (attr 0x400), NOT priority inheritance** - no code path raises a
  holder to a waiter's priority (sub_680 wait-enqueue never touches the
  holder); without 0x400 the ceiling is 127 and it behaves exactly like the
  LwMutex (queue order only, attr 0x100). Mechanism: **TCB+0xBA base prio,
  TCB+0xBC effective ceiling, TCB+0xA8 owned-mutex ring (links mutexobj+0/+4,
  sorted by ceiling for 0x400)**; `0x6604(rec,TCB,count)` acquire+boost
  (ceiling < effective → store + 0x14598 requeue; mutexobj: +8 uid, +12 opt,
  +16 init, +20 count, +24 owner TCB, +28 ceiling), `0x7480(rec)` relinquish
  (count/owner = 0, unlink, re-evaluate remaining head's ceiling, requeue at
  min(base, ceiling), empty → 127/base), `0x66F0(TCB)` exit mass-release
  (4 call sites in delete/exit/terminate cores; attr 0x800 mutexes go
  permanently locked with owner = -1, others count=0/owner=0 + 0xC30 purge).
  UnlockMutex handoff re-applies the boost to the new owner via 0x6604.
  **Wait type 12 = full mutex**; errors C3/C4/C5/C6/C8 mutex, 1AD poll-failed;
  msgnos 62/63/74/75/77/78/80. PollSema + CancelSema have NO cfc0 gate
  (interrupt-legal); PollSema's new internal `0x4D68(slot)` = fairness check
  (FIFO queue nonempty or head waiter prio <= mine → refuse with 0x800201AD);
  CancelSema count<0 resets currentCount to the create initial. Remaining
  unassigned: lock core 0x6A7C (246w), UnlockMutex 0x67F4 (158w), TryLock
  0x6E54 (~130w) - all decoded in results/BB.md. GOTCHA recurrences: t7=$15
  (3rd time), log-rejoin j lands on a delay slot (0x4B70 → 0x4AEC).

- **Batch W 2/2 MATCH, 0 relocs (MsgPipe RECEIVE CORE 0xA1B4 internal +
  TrySendMsgPipe 0x9D7C)**: tm_w.c, full decode + semantics in results/W.md.
  643/643 words exact via build/vdiff.py (re-validated on tm_v.o first).
  **Receive core is 377w, not P's 379w** (P's +2 skew again). **Receive
  semantics**: attr bit 4 = receive; ring read via NEW callee **0xB094**
  (pipe, dst, n) - 0xAFC0's read counterpart; pipe+4==2 (senders queued)
  prio bypass = slot attr **0x1000** && slot+4==0 && prio win; blocked
  senders served by direct handoff 0x1880c(my dst, sTCB+0x60 src, n) PLUS
  a ring-drain 0xafc0(pipe, sSrc, min(free,sRem)) iff **(sMode==1 && n2>0)
  || (sMode==0 && free>=sRem)** (mirror of send's ring-write gate);
  *pSent = sSize-sRem updated; **sender wake 0x924 iff (sMode==1 && copied)
  || sRem==0**, else slot+4=1 and the walk STOPS; partial receive returns
  0 with *pRecvSize = size-rem (mode1 after any progress, mode0 only at
  rem==0); block = pipe+4=2, TCB wait fields (+0x60 dst, +0x64 want,
  +0x68 size, +0x6C pRecv, +0x70 mode, **+0x74 = 1** - direction tag, send
  stores 0, +0x98 CB), 0x908(rec, wait type **8 shared with send**,
  **(slotattr>>4)&0x100** = attr bit 0x1000 as the prio selector,
  deadline@sp, tmo). **TrySend**: no timeout arg; mode check BEFORE
  enter-critical; **cfc0 read after resolve, never errors - only gates the
  final 0xfe4 dispatch** (woken!=0 && cause==0); mode0 pre-scan adds ALL
  queued receivers' wants to free before the fits test; returns
  **0x800201B3** iff would-block ((mode0 && rem>0) || (mode1 && nothing
  sent)); log msgno **102**; receive logs **103/104**. 3 new .dis
  annotation glitches in 0x9D7C-0xA798: 0xA04C "addiu" is really ADDU
  (word 01104821), 0xA14C j really targets 0x9ED4 (raw word 080027B5),
  0xA698 "lw s8" is really lw **t6**,16(s1) - plus beqzl @0x9F4C->0x9F6C
  and @0xA72C->0xA37C skip their delay-slot reloads (label placement, V
  gotcha class). Remaining internals: TryReceive @0xA798 (~288w expected),
  CancelMsgPipe @0xAC20 (108w).

- **Batch Z 5/5 MATCH, 0 relocs (priority/control miscellany)**: tm_z.c,
  full decode + run-queue mechanics in results/Z.md. **The runq deliverable**:
  heads `slot(p) = ctx+152+8p` are 8-byte RING ANCHORS {+0 first, +4 last}
  that are themselves members of the circular TCB list (empty ⟺
  slot->next==slot); bitmap word is really at **ctx+136+4*(p>>5)** (K's
  "+128" is the computed pointer, every access is +8 from it), bit
  31-(p&31) set via `rotrv(0x80000000,p)`, cleared only when a ring empties
  (0x16bf4: `and ~rot` when sole occupant). **SPECIAL funct 0x16 = Allegrex
  clz** (8 raw words module-wide, 2 cascades): clz-chain over ctx+136..+148
  = priority of most-urgent non-empty queue (clz(0)=32 adds 32 per skipped
  word; 128 = none) - used by RotateThreadReadyQueue (interrupt && prio==0
  → rotate that queue) and 0x14598's preempt test (current yields only if
  newprio >= scan). ChangeThreadPriority itself only stores s16 rec+186 and
  (iff newprio <= ceiling rec+188) tail-calls **0x14598(rec,prio,st)** which
  does the deque/requeue: READY target unlinked (bit maybe cleared), target
  more urgent than current → CURRENT re-queued at front of its own ring +
  bit set + state=2, target state=1, ctx+4=target, fe4(0,st); waiting target
  with slot attr 0x100 → wait-queue unlink 0x890 + 0xC30. Rotate's
  non-self path = pure head-to-tail ring dance, bitmap untouched; self path
  = yield (state=2 + 127d0 + fe4). New: **0x187c4(uid,&rec)** table-free uid
  resolver, **0x187fc(rec,table)** class-membership test; UID map additions
  **0x4D8 mutexes (type 12), 0x4F0 queue-links (type 14, 15th table)**;
  errors 0x80020193/0x800201A0(TEH)/0x800201A2/0x800201A7/0x800200D2;
  msgnos 26/27/33/46/166. IdList @0x163E0 (233w) decoded only: per-type ring
  walk via jump table @0x19E34, types 64/65 = ctx+0x498/0x4A0 wait queues,
  bad type → 0x800201BB. GOTCHA reconfirmed: t5/t6/t7 = $13/$14/$15.
- **Batch Y 5/5 MATCH, 0 relocs (thread termination & deletion - the exit
  path)**: tm_y.c, full decode in results/Y.md. ExitThread/ExitDelete are
  thin gates around the NEVER-RETURN core 0x178C0(deleteFlag, cookie, status):
  exit status is stored at TCB+0x54 (= rec+84) in the log-branch delay slot
  BEFORE anything else (ExitDelete reloads it from memory for its 3rd arg),
  negative statuses are clamped to 0x800200D2 (slti+movn). 0x178C0: asserts
  ctx+0x0C==0, TEH dispatch via sub_1580 (class 4 exit, class 8 delete;
  class 2 = 0x13E80 trampoline side), teardown chain 0x11E3C / **0xB48(rec,
  status) = type-9 waiter completion: per-waiter TCB+0x80 = exitStatus +
  sub_924 walk of the target's slot-view waiter list** (NOT a 0x1879C tag),
  0x60D4/0x66F0/0x26CC/0xE0D4, then either dead-list insert (ctx+0x4A8,
  state 16 DORMANT - plain Exit) or uid free 0x126AC(id) + state 0 (delete),
  ctx+4=0 + FE4(1,1), then panic+break - caller never resumes. Terminate/
  TerminateDelete are veneers: gates (tid!=0, attr bit 0x2, 0x187ac <=
  0x307FFFFF when dispatch busy; TerminateThread passes entry validation
  from INTERRUPT ctx and proceeds!) then sub_17A14(rec, 0|1, cookie) -
  dead target: 0x800201A2 (terminate) / full delete cleanup (terminate-
  delete); live-kill path @0x17B68 undecoded. DeleteThread: state must be
  0x10/0x20, attr bit 0x10, sentinel-uid guard (ctx+0x50C/+0x510), TEH
  class 8 + teardown + unlink + sub_155B8 + uid free - no waiter walk
  (already completed at exit). Log msgnos 17/19/20/21/22 (a1 = rec /
  status / status / COOKIE / cookie). GOTCHAs: `lui/j epi/ori` error tails -
  the ori is the j's DELAY slot, and `j 0x1345C` lands on the j; retail
  quirk tid==0 -> 0x000001A4 (v0=0 from the gate load). SPECIAL2 filler
  0x70050024 (rd=$0, result discarded) only in the Exit twins, spliced raw.
- **Batch X 5/5 MATCH, 0 relocs, ALL FIRST-COMPILE (sema/evf Create+Delete +
  CreateVpl)**: tm_x.c, full decode in results/X.md. NOTE: relaunch batch -
  the previous agent died on network failure and its claimed 4 matches were
  LOST (no tm_x.c/results/X.md in the tree); all 5 redone from scratch here.
  **Create* skeleton (4th/5th confirmations after N/O)**: name + (opt|opt+4)
  k1 gates -> D3; cfc0 -> 64; attr-mask (sema `ins t1,zero,0,9` raw .word
  0x7C094004 = mask 0x1FF; evf `li -768` = 0x2FF; vpl `li -17408` =
  0x43FF) -> 191; 0x186AC; **0x1875C(table, name, (attr|k1>>31)&0xFF, &rec)
  - the "user" byte = attr|usermode, NOT just the user flag**; dual-view
  stores; log via ctx+8 handler (msgno, a1, 1, uid; a1 = opt for
  sema/evf/mbx but the OBJECT VIEW PTR for vpl); release; return rec+12.
  Sema obj: +0 opt, +4 cur=init, +8 max, +12 init again; evf obj: +0 opt,
  +4/+8 = init x2, +12/+16 = 0; vpl obj +8 = 0x1874C(pool) FREE size at
  create. Delete twins (msgnos 58/66, errs 0x80020199/0x8002019A, tables
  0x4D0/0x4D4): attr16 rec+22 bit 0x10, 0x1877C(uid), **hardcoded return 0**
  (result discarded; exits route through v1). CreateVpl extras: size==0 ->
  0x800201B7 pre-acquire; 0x187BC(partition, sp /*16*/) query, user needs
  *(sp+12)&3==3 else D1; 0x1878C(partition, size, (attr>>13)&2, name), fail
  -> 0x1877C rollback + 0x80020190; attr bit 0 (user pool) -> new import
  **0x187C4(pool,&rec)** + OR attr16 bit 1 into the sysmem pool record on
  NULL; msgno 108 with a1 = obj view. GOTCHA: bnez back-edge @0xB634
  targets the `addiu` of a lui/addiu pair - the lui runs in the branch's
  delay slot; place the label between them.

- **Batch V 1/1 MATCH, 0 relocs (MsgPipe SEND CORE 0x97E0, internal)**:
  tm_v.c, full decode + semantics in results/V.md. 359/359 words exact
  via build/vdiff.py (internal-function word-diff harness, validated on
  tm_p's four matches first). **Send semantics**: waitMode (4th arg) only
  0/1 legal (else 0x80020195); mode 1 = wait-any - returns success after
  ANY progress with *pSentSize = size−rem; mode 0 = wait-all - writes to
  the ring only when the WHOLE message fits, else blocks. Loop choice:
  pipe+4==2 (receivers queued) → direct handoff copy into waiting
  receivers' TCB buffers via 0x1880c (recv view: +0x60 dst, +0x64 want,
  +0x68 size, +0x6C pSent, +0x70 mode; wake 0x924 iff mode==1 or want==0;
  slot+4=1 while partially served); pipe+4==1 (senders queued) → block
  behind them UNLESS slot attr 0x100 && slot+4==0 && my TCB+0x10 prio <
  head's (priority bypass → ring write); else ring write
  0xAFC0(pipe, src, min(free,rem)). Block: pipe+4=1, TCB wait fields,
  0x908(rec, **wait type 8**, attr&0x100, deadline@sp, pTimeout); arg6
  (t1) = pTimeoutUsec → **0x10D34 = absolute deadline builder** (0xECE4
  now + usec); new callees **0x16FA4** stack snapshot (result ignored),
  **0xAFC0** ring write. CB retry: notifyPending → 0x2170 pump +
  re-resolve (fail 0x800201B5); 0x908 result 0x800201AB && CB → loop.
  ctx+0x00 = current TCB (refines batch C's +0x08). GOTCHAs: `.dis`
  annotations wrong at beqz @0x9A1C (really →0x9B88) and beqzl @0x9D10
  (really →0x99AC) - raw words authoritative; intra-function j must use
  absolute retail targets (labels emit R_MIPS_26).

- **Batch T 5/5 MATCH, 0 relocs, ALL FIRST-COMPILE (thread wait/wake-adjacent
  family)**: tm_t.c, full decode in results/T.md. CancelWakeup: tid==0 means
  CURRENT thread (unique in the wake family), returns OLD TCB+0x50
  wakeupCount after zeroing it; attr bit 0x8; msgno 51. DonateWakeup (144w -
  verify sizes against next export, mid-listing estimates mislead): moves the
  donor's pending wakeupCount onto the target (delay-slot store, ANY target
  state), donor sleeps via sub_858(sleep queue, type 1) + FE4(1,1); target
  woken NOW only if state 4/12 AND waitType (TCB+0x58)==1 → sub_924; gates
  197/64/1A7/198/D1(attr 2)/1A2-dead; msgno 52. ReleaseWaitThread:
  wait-TYPE-blind - gates only on STATE 4/12 (else 0x800201A6); object waits
  additionally need the TCB+0x5C wait-block's slot attr bit 0x8 and get
  purged via sub_C30 = 0x1879C(rec, **0x85FE2B4C**) (third cancel-all tag);
  released thread gets waitResult 0x800201AA and sub_924 handles BOTH
  delayed (timer teardown via TCB+0x78) and sleeping (queue unlink) threads;
  r!=0 && thread ctx → ctx+4=0 + FE4(0,st); msgno 28 with a1 = tid.
  WaitThreadEnd/CB are 2w t3-veneers into the 170w core @0x3AD0 (decoded
  only, over budget): **wait type 9 = thread-end** (waiters queue on the
  TARGET's slot-view waiter list via sub_908(target,9,0,clock,timeoutPtr));
  dead target (state 0x10/0x20) → return its exit status rec+84 without
  blocking; CB variant = SleepThreadCB pump shape + RE-RESOLVE after every
  callback batch (0x800201B5 if deleted) + 0x800201AB retry; attr bit 0x4;
  msgnos 55 (plain) / 56 (CB). Wait-type catalog now 1 sleep, 2 delay,
  3 sema, 4 evf, 5 mbx, 9 thread-end. Thread attr bits: 0x1 refer, 0x2
  suspend/resume/start/release/donate, 0x4 wait-end, 0x8 cancel-wakeup.
- **Batch S 5/5 MATCH, 0 relocs (Cancel/Free leftovers)**: tm_s.c, full
  decode in results/S.md. All transcription first-compile except one gas
  GOTCHA: `break 0x7` encodes the code into the HIGH field (0x0007000D);
  retail wants 0x000001CD - splice raw `.word`. CancelMsgPipe: gates both
  out-ptrs, NO cfc0, msgno 106, `0x1879c(rec,0x86D94883)` count routed by
  pipe+4 direction (movn), **pipe RESET on cancel** (usedBytes=0, write/
  tail cursors = read cursor, direction=0). FreeVpl: per-waiter
  `0x18774(pool, TCB+0x64 wanted)` - grant stored in `jal 0x924`'s delay
  slot; alloc-fail: slot attr &0x200 skips waiter, else aborts walk;
  msgno 113 passes STALE s8 (uninitialized at log time). FreeFpl: inline
  block math (base=fpl+4, stride=fpl+28, n=fpl+24, div/beqzl/break-7,
  slots[idx]==0 double-free check); numWait>0 → single direct grant
  (TCB+0x60=block + `0xb08(rec,0,0,st)`), else `0xd2e4(fplView,idx)`
  free-ring push; msgno 121. CancelVpl/CancelFpl = exact twins (tables
  0x4E8/0x4EC, errs 0x19C/0x19D, msgnos 114/122), no cfc0, optional
  count store via bnezl-to-next-instruction. Import 0x187a4 = SysMem
  block-validate(pool, ptr).

- **Batch R 6/6 MATCH, 0 relocs (sema/evf OPERATION side)**: tm_r.c, full
  decode in results/R.md. Three compiles total (run 1: gas rejects 2-operand
  `beql rs,label` - must be `beqzl`; run 2: 4/6 + 3 hand-copy typos; run 3:
  6/6). SignalSema is 157w (7 over budget) - attempted anyway as the
  waiter-release centerpiece. **Wait-order semantics (the deliverable)**:
  wait queues live in the slot view (0x4C8)+12 as TCB lists (links
  TCB+0/+4, self-loop empty); insert via sub_908→sub_680(rec, waitType,
  selector, timeout, 0): **sema wait core passes the slot attr → attr bit
  0x100 = priority-ordered insert (before first numerically-larger TCB+0x10,
  FIFO within equals), else FIFO tail append; the evf wait core passes
  selector 0 → event-flag waits are ALWAYS FIFO**. SignalSema wakes in
  queue order with head-of-line blocking (stops at first waiter whose
  TCB+0x60 wanted > remaining count; no bypass), pre-checks overflow as
  maxCount >= cur+signal−Σ(all waiters' wanted) else 0x800201AE (count
  unwritten), and while ctx+0x30 (pending-dispatch list) is non-empty
  SKIPS user-thread waiters (attr<0 or attr&0x80000000). SetEventFlag scans
  the WHOLE queue (no stop; OR = any-bits, AND = all-bits via xor/sltiu),
  applies the waiter's own TCB+0x64 bits (0x10 → pattern=0, 0x20 →
  &= ~waitPattern) after each wake, no user gate. Both share the dispatch
  tail: woken==1 → 16bf4(t,prio)+16c48(t,st); woken>1 → ctx+4=0 +
  FE4(0,st); intr ctx & woken>0 → ctx+4=0. New: wait types 3=sema, 4=evf
  (TCB+0x58); TCB+0x60 wait arg, +0x64 evf mode, +0x68 evf result ptr;
  sub_924 returns 1 on ready/suspend transition; **0x1879C(rec, tag) =
  cancel-all-waiters** (tags 0x86D94883 CancelEventFlag, 0x5BD49380
  sub_924 cleanup); evfobj+12 = single-waiter slot for Poll's
  0x800201B0 check (0 or current thread OK unless slot attr 0x200);
  per-op user permission bits: attr16 &2 signal/set/clear, &4 wait/poll,
  &8 cancel. ClearEventFlag: cur &= arg (KEEP mask - contradicts
  PSPSDK "bits to clear" docs; retail does a bare `and`). Errors
  199/1AE sema, 19A/195/1AF/1B0/1B1 evf; msgnos 59/61/67/68/71/72.

- **Batch Q 6/6 MATCH, 0 relocs (LwMutex family - the embedded-struct
  objects)**: tm_q.c, full decode in results/Q.md. Four first-compile (all
  diffs were transcription typos: rd/base/rt operand fields). UID class map
  addition: **LwMutexes ctx+0x4DC**. The family differs from UID objects:
  callers pass a 32B SceLwMutexWorkArea pointer, not a SceUID - the k1<<11
  gate runs on the work pointer itself, Create also requires 4-alignment and
  ANDs the mask against a constant 0x80020004 (kernel-only entry; D3 from
  user k1), and identity is validated by resolving work+16 (uid) through
  0x18784 then checking the back-link `recView4DC+12 == pWork` else
  0x800201CA (stale/cloned area). WorkArea: +0 count, +4 owner
  (ctx->current ptr at acquire; wake-handoff stores *(waiterTCB+8)),
  +8 attr, +16 uid (-1 after Delete). lwm view: +8 uid/+12 pWork/+16 name/
  +20 initCount; wait queue at slot view (0x4C8)+12 (waiter TCBs,
  self-loop empty); wake: work->count = waiter TCB+0x60 (wanted count),
  sub_924 + 0x16bf4/0x16c48 pair. ReferLwMutexStatusByID has NO cfc0 check
  (unique in family); status 64B at scratch: +0x24 attr, +0x28 rawrec+12,
  +0x2C pWork, +0x30 initCount, +0x34 count, +0x38 owner|-1, +0x3C
  waitCount; min(size,64) copy-out. attr: 10 bits legal (0x80020191),
  0x200 = recursive/multi-count (count must be <2 without it → 0x800201BD);
  errors 1CA/1CB/1CC/1CD/1CE/1CF; log msgnos 82/84/87/89. Lock/CB are 2w
  veneers `j 0x7CE4; li t3,0/1` - the shared core 0x7CE4 (actually 236w) and
  Delete 0x7908 (85w) were closed by batch U (see below); family COMPLETE.

- **Batch U 2/2 MATCH, 0 relocs (LwMutex internals - family COMPLETE 9/9)**:
  tm_u.c, full decode in results/U.md. The shared lock core **0x7CE4 (236w,
  INTERNAL - not in the export map)** compared via a new documented method:
  name it `sub_07CE4` with .size so it lands in the .o symtab, compile with
  the normal harness, then diff with /tmp/cmp_internal.py which IMPORTS
  match.py's parse_obj/retail_words/mask_for (same ok/reloc/DIFF rules; no
  tools/ changes) - reusable for any internal function. DeleteLwMutex 85w
  first-compile; core took 2 (5 diffs, all one typo class: t6/t7 are $14/$15,
  not $22/$23). **Core semantics**: wait type 13 via sub_680(rec,13,slot->attr,
  sp,timerPtr) - **queue order = slot attr 0x100 ? priority : FIFO (inside
  0x680, same as sema waits); NO priority inheritance anywhere** (only queue
  order); recursive only with attr 0x200 (count += unlockCount, overflow →
  0x800201CD, else 0x800201CF); owner==0 fast acquire; timeout armed via new
  callee **0x10D34(sp,*timeout)** (clock-based wait-timer block, calls
  0xECD4); CB retry loop on result 0x800201AB through 0x2170 with uid
  re-resolve (fail → 0x800201B5 deleted-while-waiting); log msgnos **85**
  (Lock) / **86** (LockCB). **Delete**: attr bit 0x10, log msgno **83**
  (a2=1), 0x1877C frees the record, work+16 uid = -1 and work+4 owner = -1
  (release delay slot), NO waiter check - deletes strand waiters. Owner-field
  quirk in Q.md RESOLVED: owner = thread ID (value of current TCB+8, P =
  *(module+0x40) is the current TCB) uniformly - never a TCB pointer; S
  (=module+0x40) holds P at +0, logHandler at +8, dispatch-state gate at
  +0x0C. New TCB/ctx usage: P+0x60 wanted count, P+0x98 CB flag, P+0x9C
  notifyPending (consistent with H/K/L).

- **Batch P 5/5 MATCH, 0 relocs (MsgPipe family)**: tm_p.c, full decode in
  results/P.md. Four first-compile; Refer took 2 iters (GOTCHA: in the
  pointer gate `or a1,a2,a1` @0xADE4 the rt operand is the live arg
  register, not the callee-saved copy - transcribe operands verbatim).
  UID class map: **msgpipes ctx+0x4E4**. Pipe object (rec+4*hdr21(0x4E4)):
  +0 5th syscall arg (pointer-gated (p|p+4)&k1<<11), +4 wait direction
  (0/1 senders/2 receivers), +8 read / +12 write / +16 tail cursors (init =
  0x187e4(block) data head), +20 bufSize, +24 usedBytes (free = +20−+24),
  +28 kernel-allocated block; slot view (0x4C8): +0 attr (Create stores
  arg3; gates: bit 0x1 Refer, 0x10 Delete), +8 waitCount (routed to
  numSend/numRecv by pipe+4). New patched veneers 0x18794 (alloc block
  (arg2, name, bit28(attr) via `ext a2,s4,28,1` = 0x7E860380, bufSize)),
  0x187b4 (free), 0x187bc (16B validate arg2, user needs *(sp+12)&3==3
  else D1), 0x187e4 (block→data head). Create errors: 0x80020064 cause,
  0x80020191 attr mask ~0x51FF, 0x80020190 alloc, 0x8002019E unknown uid.
  ReferMsgPipeStatus: 56B SceKernelMsgPipeInfo at ctx+0x6D4 (+0 size 56,
  name[32] @+4, +36 attr, +40 bufSize, +44 freeSize, +48/+52 wait counts),
  log(107, &ctx, 2, uid, info); msgnos 98 Create / 99 Delete. Send/Receive
  exports are 2w veneers (j 0x97E0/0xA1B4, CB flag in t3); cores are 361w/
  379w, TrySend 266w, TryReceive 290w (skip-size); **CancelMsgPipe @0xAC20
  is only 108w - unassigned and untouched, prime next pick**.

- **Batch N 7/7 MATCH, 0 relocs, all FIRST-COMPILE (Mbox family)**: tm_n.c,
  full decode in results/N.md. UID class map: **mboxes ctx+0x4E0**
  (module+0x520). Mbox object (rec+4*hdr21(0x4E0)): +0 opt (Create a2 raw),
  +4 numMessages, +8 tail (newest); slot view (0x4C8): +0 attr (gates: Send
  0x2, Poll/Receive 0x4, Refer 0x1, Delete 0x10), +8 numWaitThreads, +12
  first waiter. Message ring via msg->next with self-loop; append = new callee
  sub_9338(mbx,slot,msg) (dup -> 0x800201C9, slot attr bit 0x400 alternate
  mode); Poll dequeues tail->next (oldest) after k1 re-validation of both the
  message and its next (D3). Send fast path: waiter = *(slot+12), msg stored
  at **(waiter+0x60) (TCB+0x60 = receiver's out-slot addr - reuses the delay
  expiry field), then sub_b08(rec,0,cause,st) wakes. Receive core 0x8A78:
  wait type 5 via sub_908, TCB+0x98=1 when CB, 0x800201A7/0x800201B5.
  Errors: 0x80020191 create attr mask ~0x1FF, 0x800201B2 poll empty; **Poll and
  Refer never read cfc0 cause** (only Create/Delete/Receive do). Log msgnos
  90/91/92/93/94/95/97 (a1 = opt/uid/slot/&ctx/&ctx/&ctx/s8-residue; a3=uid;
  t0 = msg/out/info) + a0=0 dispatch flavor with a3=0x19628/0x19638 data
  descriptors. ReferMbxStatus: 52B SceKernelMbxInfo at ctx+0x6D4, +48
  firstMessage left STALE when empty (zero loop covers +4..+44 only) - no
  0x187ac size gate unlike ReferThreadStatus.

- **Batch J 6/6 MATCH (VTimer cluster, UID class ctx+0x508)**: tm_j.c, full
  decode in results/J.md. Five first-compile; ReferVTimerStatus took 3 iters
  (GOTCHA: when a branch target lands at a shared delay slot, verify the
  target address against neighbour lines in the .dis - `beqz t0` @0x108AC
  targets 0x10A20 = the jal, while the lw at 0x10A1C is the preceding j's
  delay slot; also retail's log block REUSES a t9 loaded in a live j delay
  slot instead of reloading). VTimer object = rec + 4*hdr21(ctx+0x508):
  +0 active, +4 64-bit time (BASE while running / ELAPSED while stopped -
  Start and Stop both rewrite it as now-time64 via 0xECE4), +12 64-bit
  schedule, +18 handler (gates arming; zeroed at create), +1C common.
  Queue link block = rec + 4*hdr21(ctx+0x4FC) with alarm layout
  (+0/+4 links, +8/+12 abs expiry = sched+base), inserted by new callee
  0xEAE0, unlinked by Stop (CancelAlarm self-loop shape) + 0xEB7C.
  Status block 72B = PSPSDK SceKernelVTimerInfo (base/current/sched/
  handler/common at +40/+48/+56/+64/+68). New callee 0x1875C = UID entry
  allocator (table, name, (u8)user, &rec); rec+12 = the new SceUID.
  vtimer errors: 0x800201BE unknown, 0x800201BF sentinel (Start/Stop only),
  attr bits 0x1 refer / 0x2 start-stop / 0x10 delete; log msgnos 142/143/
  144/147/148/155. UID class map now complete low end: 0x4CC threads,
  0x4F4 TEH, 0x4F8 callbacks, 0x4FC links, 0x504 alarms, 0x508 vtimers.
- **Batch GG 6/6 MATCH, 0 relocs (vtimer setters + alarm twin)**: tm_gg.c,
  full decode in results/GG.md. SetVTimerTime[Wide]/SetVTimerHandler[Wide]/
  CancelVTimerHandler + SetSysClockAlarm (a 60w thin wrapper: gates only,
  then jal 0x116F4(clock.lo, clock.hi, handler, common) - the SAME alarm
  core SetAlarm calls with (usec, 0, ...); no UID table, no acquire).
  **Set-on-ACTIVE timers re-arms the queue**: all three mutating setters
  unlink the ctx+0x64 entry and re-insert via 0xEAE0 with expiry =
  sched(+0xC/+0x10) + rewritten base (now - newTime), then 0xEB7C.
  SetVTimerTime's clock arg is IN/OUT (returns previous face); Wide
  errors return -1 (v0/v1), not SCE codes. Handler-space rule: user
  threads only user handlers, kernel only kseg (D3). New fields:
  vt+0x14 = user flag, vt+0x20 = sub_1873c(handler) marker or gp
  (Wide stores gp directly, no 1873c call). +4/+8 = timer FACE (base
  while running / elapsed while stopped). Wide 4th/5th args arrive in
  t0/t1. Recipe GOTCHAs: symbolic `j label` emits R_MIPS_26 AND a
  wrong target still false-passes as "match (reloc)" (mask checks only
  the opcode) - always literal j; numeric labels leak ACROSS __asm__
  blocks into one .s (Nb without a local preceding N binds to a
  previous function's label); t9=$25 vs t1=$9 slips in the or-lane
  noise blocks.
- **Batch K 4/4 MATCH, 0 relocs (thread lifecycle)**: tm_k.c, full decode in
  results/K.md. The 211w ReferThreadStatus fell first-compile from batch I's
  struct blueprint; 299w StartThread also first-compile despite five
  non-MIPS-II words (`ins` x2 @0x1361C/0x138C0, `rotrv` @0x137EC, `cache` x2,
  `sync`) spliced as raw `.word` - **the guide's old "ins/ext = blocked" rule
  is superseded: under noreorder transcription only data layout blocks.**
  Thread state machine pinned: 1 RUNNING, 2 READY, 4 WAITING, 8 SUSPENDED,
  12 WAIT+SUSP, 16 DORMANT; Suspend/Resume switch via 33-entry jump tables
  @0x19B2C/0x19BB0 (`jr t5`, table arithmetic literal). Suspend list =
  ctx+0x4B0 (= module+0x4F0) with links AT record +0/+4 - StartThread also
  inserts there (started threads enter state 8, dispatcher wakes them);
  preemption: new rec+16 prio < current TCB+0x10 prio -> current re-queued
  (runq heads ctx+152+prio*8, bitmap ctx+128+(prio>>5)*4 via rotrv), current
  state=2, new state=1, sub_FE4(0,st); else state=2 + sub_127d0(s8).
  StartThread gates: argp k1-gate (D3), Cause!=0 OR current TCB+0x88 gate
  -> 0x80020064, tid==0 -> 0x80020197, state!=16 -> 0x800201A4, after
  sub_156bc(s8) reg-init the TCB+0x88 gate must be NULL. New ctx fields:
  +0x04 tail for the 0x4B0 list, +0x0C dispatch state (0/1/2/3), +0x30
  list head, +0x7D4 user-stack param (stack = (param<<6)&~0x3F).
  User-thread start: 256B frame at rec+220 (-1 at top), kernel anchor
  *( *(rec+48) ) = id; kernel thread: *(rec+44) = id; args copied via
  0x1880C with len (argLen+15)&~0xF. Log msgnos 18/34/53/54; new callees
  0x156bc (reg init), 0x134a8 (ctx setup), 0x16bf4 (dequeue), 0x16c48
  (make-ready). ReferThreadStatus decode refinements in results/K.md
  (struct really at ctx+0x6D4/module+0x714, live CPU-time fixup when
  rec == ctx->current via 0xECE4 - {ctx+0x70,+0x74}, 0x187AC > 0x2060 &&
  user size >= 109 -> 0x800201BC).
- **Batch L 6/6 MATCH, 0 relocs (delay/sleep family)**: tm_l.c, full decode in
  results/L.md. The 4 Delay exports are 2-word veneers tail-jumping shared
  cores 0x3D88 (usec) / 0x3FAC (SysClock*) with the CB flag in **t3**. Sleep
  state machine: entry gates Cause!=0 -> 0x80020064, acquire-cookie==0 or
  ctx+0x0C!=0 -> 0x800201A7 (CAN_NOT_WAIT); pending TCB+0x50 wakeupCount is
  consumed without blocking (waitResult TCB+0x80 pre-cleared in a plain branch
  delay); else sub_858(queue,waitType) links the TCB (links AT TCB+0x00/+0x04!)
  and sets state=4, **TCB+0x58 = wait type (1=sleep queue ctx+0x498, 2=delay
  queue ctx+0x4E0)** - which is why WakeupThread's gate==1 only breaks sleep
  waits - then ctx+4=0 + sub_FE4(1,1) blocks. CB variants (Sleep/delay) set
  **TCB+0x98=1 (flag, NOT a queue pointer - corrects H)** which arms
  NotifyCallback's abort; waitResult==0x800201AB loops through sub_2170
  (callback pump) and re-sleeps. Delay cores: timer via 0x10FAC (handle
  TCB+0x78, expiry TCB+0x60/64, cancel 0x11104), timeout 0x800201A8; log
  msgnos 48/49 sleep, 134-137 delay; TCB+0x7C zeroed on delay entry.
- **Batch M 4/4 MATCH (sema/evf refer + callback create/delete)**, all
  zero-reloc (tm_m.c, results/M.md). UID table map extended: semaphores
  ctx+0x4D0, event flags ctx+0x4D4, shared per-object slot table ctx+0x4C8
  (attr @slot+0, waitCount @slot+8; same role 0x4FC plays for alarms).
  SemaInfo 56B / EventFlagInfo 52B built in shared scratch ctx+0x6D4
  (template module+0x714) with dual rec views (obj = own table hdr21,
  slot = 0x4C8 hdr21) then min-size copy-out 0x1880C; unknown-uid errors
  0x80020199 (sema) / 0x8002019A (evf); log msgnos 64/73 (a1 = scratch).
  CreateCallback: UID-create via new callee 0x1875C(tbl@0x4F8, name,
  userFlag, &rec); record view = rec+4*hdr21: +8 uid(rec+12), +20 owner
  TCB, +24/+28 notify count/arg (0), +32 userFlag, +36 func, +40 common,
  +44 sub_1873C(func) result or gp; linked into owner TCB callback queue
  head TCB+0x90/+0x94 (append at tail); msgno 156. DeleteCallback: cfc0 +
  TCB+0xA4 guard + acquire-cookie test + ctx+0x0C gate (all → 0x80020064/
  0x800201A7), attr bit 0x10, delete via 0x1877C(cbid); msgno 157 with
  a1 = original k1 keyword. Refer-skeleton now proven for 5 families -
  Mbox/Vpl/Fpl/MsgPipe/VTimer Refer* are mechanical next.
- **Batch G 4/4 MATCH (alarm cluster)**: SysClock2USecWide/SetAlarm/
  CancelAlarm/ReferAlarmStatus all first-compile matches (tm_g.c,
  results/G.md) - literal-target transcription is fully mechanical now.
  Alarm family decode: alarm UID table = ctx+0x504; alarm object = rec +
  4*hdr21(ctx+0x4FC table) = {+0 next, +4 prev (active list, head ctx+0x64,
  self-loop on cancel), +8 time->status+16, +16 state (0x8002019F if busy)},
  attr u16 rec+22 bit 0x10 cancel / 0x1 refer (movz kernel bypass);
  ctx+0x60 = sentinel uid (Cancel rejects); ctx+0x6D4 = 20B alarm status
  scratch; module+0x714 = 20B SceKernelAlarmStatus template (Refer tail-calls
  copy veneer 0x1880C with sltu/movn-capped size). SetAlarm: handler non-NULL
  + k1 gate, k1 stays <<11 into core sub_116F4(a0,0,handler,common) which
  re-gates internally; log msgnos 138 (4 extras)/140/141. Cancel ctx-split:
  cause!=0 -> 0x126AC + state=1, else 0x1877C; 0xEB7C reprocess.
- **Batch H 2/2 (family's biggest members)**: WakeupThread 0x3050 (114w,
  107 exact + 7 veneer-jal reloc) + NotifyCallback 0x1CC0 (109w, 104
  exact + 5 reloc) matched in 2 iters via F-recipe (tm_h.c, results/H.md
  has the full semantic decode). Recipe additions: `cfc0 $N,$13` is fine
  under noreorder/-mips2; branch-likely live delay slots (`bnezl`/`beqzl`,
  Wakeup 0x310C/0x3128) transcribe for free; **absolute `jal 0xNNN` to
  internal functions (0x924/0xA08/0xC30/0xFE4) is word-exact** - no reloc,
  unlike extern veneer jal. Only compile slip: t7 = $15, not $23.
  Wakeup: TCB+0x0C state (0x10/0x20 dead -> 0x800201A2; 4/0xC waiting ->
  gate TCB+0x58==1 ? sub_A08(TCB,cause,st) wake-now : TCB+0x50
  wakeupCount++); tid==0 or target==ctx->current (thread ctx only) ->
  0x80020197. Notify: owner TCB = cbRec+20; TCB+0x9C notifyPending=1,
  notifyArg/Count cbRec+28/+24; owner waiting -> TCB+0x80 waitResult=
  0x800201AB, sub_924(owner), optional sub_C30 (TCB+0x5C flag), Cause==0
  -> ctx+4=0 + sub_FE4(0,st) dispatch request. Log: (50|158, record ptr,
  n, uid[, arg]) - a1 = object ptr, extras a3 then t0.
- **Batch E 4/4 MATCH (system-time cluster)**: USec2SysClock retry closed
  by transcribing A's decode (pure-C hybrid probe with pinned
  `register u32 x asm("$6")` regs made it WORSE - 7 diffs; `asm("r6")` is
  rejected, wants `$N`). 0x10A74 identified = `sceKernelSysClock2USec`
  (NID BA6B92E2): 3 k1 gates + `jal 0x113F0` (64/32 divmod, break-7,
  divisor 1e6 -> SysClock ticks are sub-usec scaled); odd quirk: NULL
  lo-out-ptr skips the division and copies clock->lo into *hi. New callees:
  0xECE4 = shared 64-bit clock reader (ctx+0x7C/+0x78 + MMIO 0xBC600000);
  sub_186ac's return is a cookie captured in the NEXT jal's delay slot and
  fed to sub_186dc. Log msgnos 131/132; handler a1 = syscall arg 1 when it
  exists (GetSystemTime passes the out ptr), else saved k1.
- **Batch I struct-map** (full detail in results/I.md): UID tables
  threads ctx+0x4CC / TEH +0x4F4 / callbacks +0x4F8; SceKernelCallbackInfo
  56B, TEHInfo 52B, SceKernelThreadInfo 108B (decoded, ReferThreadStatus
  211w queued); thread record: exitStatus rec+84+4idx, priority rec+192,
  entry rec+196, stack rec+16, runStatus s16 rec+184, CPU-time acc
  rec+52/+56, clocks rec+68..+156; new callees 0x18814 (name copy),
  0x1880c (bounded copy-out), 0x187ac (size validation); log msgnos
  31/34/47/163; ReferThreadStatus errors 0x80020197/0x800201BC.
- **Batch D 4/4 first-compile matches**: emitting intra-module `j`/`jal`
  targets as literal retail `.word` values upgrades LINK-MATCH to full
  MATCH (retroactively applicable to GetThreadCurrentPriority, back-edge
  word 0x08005B98). New TCB offsets: +0x1C pointer (to +0xB4 diagnostic
  arg), +0x2C kernel-stack check base, +0x30 user-path anchor, overflow
  threshold 64; log msgno catalog: 29 GetThreadId, 37 GetUserLevel,
  38 IsUserModeThread, 43 CheckThreadKernelStack; new internal callee
  0x186E4.
- **Batch F: k1 wrapper family PROVEN GRINDABLE (2/2 matched)**:
  CancelCallback/GetCallbackCount transcribed in 3 iters (tm_f.c,
  results/F.md). B's "backend patch" blockers vanish under `.set noreorder`
  transcription. Recipe additions: gas -mips2 rejects `movz` -> wrap in
  `.set push/.set mips4/.../.set pop`; j back-edges as absolute retail
  targets (`j 0x1F08` -> exact word 0x080007C2); veneer jal words stay
  extern (R_MIPS_26, reloc-covered - 5 sites/function = family floor).
  UID-record decode: attr u16 @rec+22 (Cancel needs bit 0x8, Count bit
  0x1), notifyCount u32 @rec+24+4*idx, notifyArg @rec+28+4*idx, idx =
  byte @UID-table-header+21 (ctx+0x4F8 = callbacks table); log call in
  this family passes a1=&ctx (NOT the k1 keyword), extras flow a3 then t0.
- **k1 wrapper family (batch B, decoded)**: 97 exported functions share the
  pattern `save k1; k1<<=11; sub_186ac() [enter-critical]; sub_18784(uid,
  ctx->uidTable[type], &rec) [UID resolver]; user-mode gate via k1>>31
  (error 0x800200D1); sub_186dc() [release]; restore k1`. Context struct at
  module+0x40 (round-1 "logCtx" is its front); UID tables at ctx+0x4CC
  (threads) .. ctx+0x508 (vtimers), 14 types. Module-wide: 157 sites jal
  0x186AC, 108 jal 0x18784, 473 jal 0x186DC, 74 `sll k1,k1,0xB` sites.
- **Blocked on Sony backend behavior (superseded for the wrapper family -
  see Batch F note)**: retail parks callee-saves lazily (e.g. `sw s0,16(sp)`
  in a jal delay slot, ra/s8/s2 saves after the k1 pair) and follows a
  k1-prologue register convention - unreachable from any C source shape,
  but trivially transcribed (tm_b.c banked the $27 regvar technique).
- **Layout/toolchain ceilings (batch A)**: GCC 3.3.6 8-aligns every static
  >=8 bytes, so retail globals at 4-mod-8 offsets (e.g. +0x17844) cap at
  LINK-MATCH; two functions blocked purely on old-RA temp ordering (this
  GCC's temp register order differs from Sony's) - likely toolchain
  ceiling without backend patch. Register steering: asm-output bindings
  pin value+position; plain register asm bindings are ignored.
  **(RESOLVED batch OO - the diagnosis was wrong: allocation was already
  retail-exact; the `-O3` regrename pass renamed it away. NOT a REG_ALLOC_ORDER
  issue.)**
- **TOOLCHAIN VARIANT prefix336b (batch OO)**: `../toolchain-build/prefix336b`
  = same gcc 3.3.6 + one patch to `gcc/regrename.c` (vanilla always renames
  every chain off its current reg; retail keeps the allocator's registers in
  functions WITH calls = GCC 3.4.6 prefer-current behavior, but renames in
  LEAF functions = vanilla behavior). Leaf functions compile identically on
  both; for functions with jal use `python3 tools/match_oo.py file.c`
  (match.py clone; objects in build/oo/). Corpus proof: all 42 tm*.c files,
  0 regressions, 165->167 ok. Patch + evidence: results/OO.md,
  ../toolchain-build/oo-regrename.patch (source tree carries the patch;
  vanilla backup /tmp/regrename.c.orig-vanilla; incremental rebuild dir
  src/b-gcc336oo, ~1 min via ../toolchain-build/oo-rebuild.sh).
- **KTLS decoded (A)**: GetKTLS(id) = GetThreadKTLS(id, NULL, 1), id 0-15,
  NULL thread = current; ctx+0x40 is a POINTER to the context (current
  thread at ctx+0x08, inner block at +0x24, callback-arg slot +0x80,
  KTLS id table +0xE0, KTLS descriptors +0x554 24B/entry).
- **k1/TCB decoded (batch C, docs/TCB.md)**: k1 is a packed per-thread
  keyword - bit 20 = user-mode flag, bits 0-19 = thread index; `sll k1,k1,0xB`
  turns bit 20 into a kernel-address mask for pointer gates (0x800200D3).
  The `li a0,29/30` dispatches are the USER-REGISTERED LOG HANDLER at
  ctx+0x48 (128 sites) - not a lookup helper. TCB offsets: id +0x08,
  currentPriority +0x10, attr +0x14 (bit31=user), exitInfo +0x24,
  gate +0x88; ctx+0x4CC = UID type table. 146 exports grindable via the
  tm_c.c asm-transcription recipe (gas note: only $sp/$ra/$fp aliases,
  others numeric).
- `sceKernelGetSystemTimeLow` reads the hardware clock at 0xBC600000.
