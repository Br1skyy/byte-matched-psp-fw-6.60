/* clockgen byte-match grind — cg.c (C-language functions)
 * Retail: PSP firmware 6.60 kd/clockgen.prx (owner's own console dump).
 * Toolchain: GCC 3.3.6 -O3 -mips2 -G0 -mabi=eabi (16-byte stack align patch).
 * Harness: python3 tools/match.py match/clockgen/cg.c --module clockgen
 *
 * Module layout (retail vaddrs, ph0 base 0):
 *   text 0x000..0x6D3 | import stubs 0x6D4..0x723 (veneers, patched at load)
 *   export entries 0x734/0x744 | import entries 0x75C..0x798
 *   SceModuleInfo 0x7A0 | rodata+strings+NID tables .. 0x8E8
 *   ph1 RW data @0x8F0: g_Cy27040 +0x00, g_ClockGenSysEv +0x10
 * The functions needing ins/daddu words GCC cannot emit live in cg_asm.c
 * (.set noreorder transcriptions): sceClockgenSetSpectrumSpreading,
 * module_reboot_before, _sceClockgenSysEventHandler, _sceClockgenSetControl1,
 * _cy27040_write_register.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

typedef struct {          /* RW data +0x00 (module 0x8F0), retail init -1 */
    s32 mutexId;          /* +0x00 */
    u32 protocol;         /* +0x04 */
    u8 curReg[3];         /* +0x08: reg0 revision, reg1 clock, reg2 spread */
    u8 oldReg[3];         /* +0x0B */
    u16 padding;          /* +0x0E */
} Cy27040;

typedef struct {          /* RW data +0x10 (module 0x900) */
    u32 size;             /* 0x40 */
    const char *name;     /* "SceClockgen" @ rodata 0x8D8 */
    u32 typeMask;         /* 0x00FFFF00 suspend|resume */
    s32 (*handler)(s32, char *, void *, s32 *);   /* sub_53C */
    u32 gp;
    s32 busy;
    void *next;
    u32 reserved[9];
} SceSysEventHandler;

static Cy27040 g_Cy27040 = { -1 };
static SceSysEventHandler g_ClockGenSysEv = {
    0x40, (const char *)0x8D8, 0x00FFFF00,
    (s32 (*)(s32, char *, void *, s32 *))0x53C, 0, 0, 0, { 0 },
};

/* imported via module stubs 0x6D4..0x720 (addresses are load-patched) */
extern s32 sceKernelCreateMutex(const char *name, s32 attr, s32 initCount, const void *opt);
extern s32 sceKernelDeleteMutex(s32 id);
extern s32 sceKernelLockMutex(s32 id, s32 count, const void *opt);
extern s32 sceKernelRegisterSysEventHandler(void *handler);
extern s32 sceKernelUnregisterSysEventHandler(void *handler);
extern s32 sceI2cSetClock(s32 a, s32 b);
extern s32 sceI2cMasterTransmit(u32 addr, const u8 *data, u32 len);
extern s32 sceI2cMasterTransmitReceive(u32 addr, const u8 *trsm, u32 trsmLen,
                                       u32 raddr, u8 *recv, u32 recvLen);

/* module-internal (cg_asm.c); veneer-style extern keeps GCC from inlining
 * these into the wrappers (retail wrappers are separate jal call sites) */
extern s32 _sceClockgenSetControl1(s32 bus, s32 mode);
extern s32 _cy27040_write_register(u8 idx, u8 val);

/* ------------------------------------------------------------------ */
/* proven batch (match/match2.c): pure C, byte-exact under the toolchain */

s32 sceClockgenSetProtocol(u32 prot) { g_Cy27040.protocol = prot; return 0; }

s32 sceClockgenGetRevision(void) { return g_Cy27040.curReg[0]; }

s32 sceClockgenGetRegValue(u32 idx) {
    if (idx < 3) return g_Cy27040.curReg[idx];
    return 0x80000102;
}

/* sceClockgenSetup / AudioClkSetFreq / AudioClk+LeptonClk Enable/Disable
 * wrappers, SetSpectrumSpreading, module_reboot_before and the internal
 * helpers are transcribed in cg_asm.c (see its header for why:
 * ins/daddu words GCC cannot emit, plus scheduling divergence). */

/* ------------------------------------------------------------------ */
/* sceClockgenInit @0x398 — 21 words.  module_start @0x2B4 carries its
 * own inlined copy; GCC -O3 inlines this static into both callers. */

static s32 clockgen_init(void)
{
    s32 mutexId;

    sceI2cSetClock(4, 4);
    mutexId = sceKernelCreateMutex("SceClockgen", 1, 0, 0);
    if (mutexId < 0)
        return mutexId;
    g_Cy27040.mutexId = mutexId;
    sceKernelRegisterSysEventHandler(&g_ClockGenSysEv);
    return 0;
}

s32 sceClockgenInit(void)
{
    return clockgen_init();
}

/* module_start @0x2B4 — syslib entry (ELF e_entry) */
int module_start(u32 argSize, const void *argBlock)
{
    (void)argSize; (void)argBlock;
    clockgen_init();
    g_Cy27040.protocol = 1;
    sceClockgenSetup();
    return 0;
}

/* ------------------------------------------------------------------ */
/* sceClockgenEnd @0x3EC — 19 words */

s32 sceClockgenEnd(void)
{
    if (g_Cy27040.mutexId >= 0) {
        sceKernelDeleteMutex(g_Cy27040.mutexId);
        g_Cy27040.mutexId = -1;
    }
    sceKernelUnregisterSysEventHandler(&g_ClockGenSysEv);
    return 0;
}
