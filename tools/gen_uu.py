#!/usr/bin/env python3
"""Generate match/threadman/tm_uu.c (batch UU — named-internals sweep) from
retail raw words. Method: tools/gen_tm.py (batch II) decoder, extended with
the accumulated fixes:
  - sllv/srlv/srav only when sa==0 (Allegrex rotrv = srlv sa=1 -> raw .word)
  - mfhi/mflo, multu/div/divu, xor/nor, bltzal/bgezal
  - 2-operand beql/bnel -> beqzl/bnezl
  - cfc0 rd-field aware (not just $13)
Branch/jump targets computed from RAW offset fields, never .dis annotations.
Module-data %hi/%lo sites hand-listed in LO below (verified each base reg is
a `lui $X,0` module anchor). ins/ext/clz/rotrv/SPECIAL2/break words splice raw.
"""
import subprocess, sys

ROOT = '/home/karin/Downloads/psp-tm'
REGS = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
        's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def R(i): return '$%d' % i

def words(addr, n):
    out = subprocess.run(['python3','tools/match.py','--disas','%x'%addr,str(n)],
                         cwd=ROOT, capture_output=True, text=True).stdout
    ws = []
    for line in out.splitlines():
        a, w = line.split(': ')
        ws.append((int(a,16), int(w,16)))
    assert len(ws) == n, (hex(addr), len(ws), n)
    return ws

def sx(x): return x-0x10000 if x & 0x8000 else x

def decode(w, addr):
    op = w >> 26
    rs, rt, rd = (w>>21)&31, (w>>16)&31, (w>>11)&31
    sa, fn = (w>>6)&31, w&63
    imm = w & 0xFFFF; simm = sx(imm)
    if op == 0:
        if fn == 0:
            return 'nop' if w == 0 else 'sll %s,%s,%d' % (R(rd),R(rt),sa)
        if fn == 2: return 'srl %s,%s,%d' % (R(rd),R(rt),sa)
        if fn == 3: return 'sra %s,%s,%d' % (R(rd),R(rt),sa)
        if fn == 4 and sa == 0: return 'sllv %s,%s,%s' % (R(rd),R(rt),R(rs))
        if fn == 6 and sa == 0: return 'srlv %s,%s,%s' % (R(rd),R(rt),R(rs))
        if fn == 7 and sa == 0: return 'srav %s,%s,%s' % (R(rd),R(rt),R(rs))
        if fn == 8: return 'jr %s' % R(rs)
        if fn == 9:
            return 'jalr %s' % R(rs) if rd == 31 else 'jalr %s,%s' % (R(rd),R(rs))
        if fn == 0x0A: return 'MOVZ(%s,%s,%s)' % (R(rd),R(rs),R(rt))
        if fn == 0x0B: return 'MOVN(%s,%s,%s)' % (R(rd),R(rs),R(rt))
        if fn == 0x10: return 'mfhi %s' % R(rd)
        if fn == 0x12: return 'mflo %s' % R(rd)
        if fn == 0x18: return 'mult %s,%s' % (R(rs),R(rt))
        if fn == 0x19: return 'multu %s,%s' % (R(rs),R(rt))
        if fn == 0x1A: return 'div %s,%s' % (R(rs),R(rt))
        if fn == 0x1B: return 'divu %s,%s' % (R(rs),R(rt))
        if fn == 0x21: return 'addu %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x23: return 'subu %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x24: return 'and %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x25: return 'or %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x26: return 'xor %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x27: return 'nor %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x2A: return 'slt %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x2B: return 'sltu %s,%s,%s' % (R(rd),R(rs),R(rt))
        return '.word 0x%08X' % w
    if op == 1:
        nm = {0:'bltz',1:'bgez',2:'bltzl',3:'bgezl',16:'bltzal',17:'bgezal'}[rt]
        return 'BR(%s %s,0x%05X)' % (nm, R(rs), addr+4+simm*4)
    if op in (2,3):
        return ('j ' if op==2 else 'jal ') + '0x%05X' % ((w & 0x3FFFFFF) << 2)
    if op in (4,5,6,7,20,21):
        nm = {4:'beq',5:'bne',6:'blez',7:'bgtz',20:'beql',21:'bnel'}[op]
        t = addr+4+simm*4
        if op in (4,5,20,21) and rt != 0:
            return 'BR(%s %s,%s,0x%05X)' % (nm,R(rs),R(rt),t)
        if op in (20,21):
            return 'BR(%szl %s,0x%05X)' % ('beq' if op==20 else 'bne', R(rs), t)
        if op in (4,5):
            return 'BR(%sz %s,0x%05X)' % ('beq' if op==4 else 'bne', R(rs), t)
        return 'BR(%s %s,0x%05X)' % (nm,R(rs),t)
    if op == 8: return 'addi %s,%s,%d' % (R(rt),R(rs),simm)
    if op == 9: return 'addiu %s,%s,%d' % (R(rt),R(rs),simm)
    if op == 10: return 'slti %s,%s,%d' % (R(rt),R(rs),simm)
    if op == 11: return 'sltiu %s,%s,%d' % (R(rt),R(rs),simm)
    if op == 12: return 'andi %s,%s,0x%X' % (R(rt),R(rs),imm)
    if op == 13: return 'ori %s,%s,0x%X' % (R(rt),R(rs),imm)
    if op == 14: return 'xori %s,%s,0x%X' % (R(rt),R(rs),imm)
    if op == 15: return 'lui %s,0x%X' % (R(rt),imm)
    if op == 16:
        if rs == 0: return 'mfc0 %s,$%d' % (R(rt), rd)
        if rs == 2: return 'cfc0 %s,$%d' % (R(rt), rd)
        if rs == 6: return 'ctc0 %s,$%d' % (R(rt), rd)
        return '.word 0x%08X' % w
    mem = {0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2B:'sw'}
    if op in mem: return '%s %s,%d(%s)' % (mem[op],R(rt),simm,R(rs))
    return '.word 0x%08X' % w

# ---- per-function config ----
# %lo override table: addr -> full replacement asm line (module-data reloc sites).
# Every base register verified to be a `lui $X,0` module anchor at the site.
LO = {
 # sub_743C (static init: mutex name tables)
 0x7458:  'addiu $9,$2,%lo(g_padUU+1304)',
 # sub_EEB0 (TEH slot alloc)
 0xEEBC:  'addiu $6,$5,%lo(g_padUU+64)',
 # sub_12C04 (post-attr-change)
 0x12C30: 'addiu $4,$18,%lo(g_padUU+64)',
 0x12C3C: 'addiu $4,$18,%lo(g_padUU+64)',
 0x12C60: 'addiu $16,$18,%lo(g_padUU+64)',
 0x12C8C: 'addiu $7,$18,%lo(g_padUU+64)',
 0x12C94: 'addiu $16,$18,%lo(g_padUU+64)',
 # sub_16B40 / sub_16B84 (static init + early-exit teardown)
 0x16B5C: 'addiu $9,$2,%lo(g_padUU+1292)',
 0x16B9C: 'addiu $5,$2,%lo(g_padUU+824)',
 0x16BB0: 'lw $4,%lo(g_padUU+2060)($2)',
 # sub_E0D4 (Tlspl exit walker)
 0xE148:  'addiu $19,$3,%lo(g_padUU+64)',
 # sub_17EB4 (stack-switch runner)
 0x17EC4: 'addiu $23,$3,%lo(g_padUU+64)',
 0x17EFC: 'lw $17,%lo(g_padUU+64)($3)',
 # sub_1580 (TEH dispatch)
 0x158C:  'addiu $7,$23,%lo(g_padUU+64)',
 0x1614:  'lw $10,%lo(g_padUU+64)($11)',
 0x1658:  'addiu $13,$22,%lo(g_padUU+1280)',
 0x1758:  'addiu $13,$22,%lo(g_padUU+1280)',
 0x1768:  'addiu $13,$22,%lo(g_padUU+1280)',
 0x1664:  'addiu $16,$23,%lo(g_padUU+64)',
 # sub_4FBC (static init: sema name tables)
 0x4FD8:  'addiu $9,$2,%lo(g_padUU+1296)',
 # sub_5048 (sema waiter walk)
 0x5054:  'addiu $7,$10,%lo(g_padUU+64)',
 # sub_6120 / sub_6164 / sub_6230 (mutex side)
 0x613C:  'addiu $9,$2,%lo(g_padUU+1300)',
 0x6168:  'addiu $13,$14,%lo(g_padUU+64)',
 0x623C:  'lw $10,%lo(g_padUU+1300)($11)',
 # sub_75E4 (mutex waiter walk)
 0x75F0:  'addiu $7,$5,%lo(g_padUU+64)',
 # sub_84B4 / sub_8520 / sub_855C / sub_85A8 (LwMutex side)
 0x84D0:  'addiu $9,$2,%lo(g_padUU+1308)',
 0x852C:  'lw $11,%lo(g_padUU+1308)($12)',
 0x8560:  'addiu $24,$25,%lo(g_padUU+64)',
 0x85B4:  'addiu $9,$10,%lo(g_padUU+64)',
 # sub_C1FC / sub_C244 / sub_C32C (VPL side)
 0xC200:  'lw $6,%lo(g_padUU+1320)($3)',
 0xC260:  'addiu $9,$2,%lo(g_padUU+1320)',
 0xC338:  'addiu $9,$10,%lo(g_padUU+64)',
 # sub_118EC (vtimer delete)
 0x118F8: 'addiu $10,$8,%lo(g_padUU+64)',
 # sub_13E80 (thread start trampoline)
 0x13E98: 'lw $16,%lo(g_padUU+64)($17)',
 0x13F64: 'addiu $11,$17,%lo(g_padUU+64)',
 # sub_3D88 (delay core usec)
 0x3DE0:  'addiu $30,$16,%lo(g_padUU+64)',
 0x3E70:  'addiu $22,$9,%lo(g_padUU+1248)',
 0x3E98:  'addiu $5,$23,%lo(g_padUU+16884)',
 0x3EE0:  'addiu $13,$14,%lo(g_padUU+64)',
 # sub_3FAC (delay core SysClock)
 0x4018:  'addiu $30,$16,%lo(g_padUU+64)',
 0x40A8:  'addiu $22,$13,%lo(g_padUU+1248)',
 0x40D0:  'addiu $5,$23,%lo(g_padUU+16884)',
 0x4120:  'addiu $25,$30,%lo(g_padUU+64)',
 # sub_41F4 (delay-cancel walker)
 0x4228:  'sw $0,%lo(g_padUU+68)($3)',
 # sub_B7E4 (VPL allocate core)
 0xB8B0:  'addiu $30,$20,%lo(g_padUU+64)',
 0xBA78:  'addiu $12,$13,%lo(g_padUU+64)',
 # sub_2570 (TEH teardown-prep)
 0x258C:  'lw $7,%lo(g_padUU+1332)($4)',
 # sub_25FC (inline-vs-retarget gate)
 0x2600:  'addiu $7,$3,%lo(g_padUU+64)',
 # sub_27B4 (callback teardown-prep)
 0x27D0:  'lw $7,%lo(g_padUU+1336)($4)',
 # sub_283C (static init: TEH/callback name tables)
 0x285C:  'addiu $16,$5,%lo(g_padUU+1332)',
 # sub_28C0 (kernel-callback trampoline)
 0x28D8:  'lw $16,%lo(g_padUU+64)($3)',
 # sub_2DBC (return trampoline)
 0x2DD4:  'lw $4,%lo(g_padUU+64)($2)',
 # sub_4D68 (sema fairness gate)
 0x4D88:  'lw $9,%lo(g_padUU+64)($10)',
 0x4D8C:  'addiu $3,$10,%lo(g_padUU+64)',
 # sub_92F4 (static init: mbx name tables)
 0x9310:  'addiu $9,$2,%lo(g_padUU+1312)',
 # sub_C50 (static init: vtimer table)
 0xC68:   'addiu $8,$2,%lo(g_padUU+1288)',
 # sub_C8C (timeout core)
 0xD38:   'sw $0,%lo(g_padUU+68)($16)',
 # sub_E20 (cancel-all 0x800201B5)
 0xE2C:   'addiu $10,$30,%lo(g_padUU+64)',
 0xEC0:   'addiu $6,$30,%lo(g_padUU+64)',
 # sub_F10 (cancel-all 0x800201A9)
 0xF1C:   'addiu $3,$20,%lo(g_padUU+64)',
 0xF7C:   'addiu $8,$20,%lo(g_padUU+64)',
 # sub_D42C (FPL uid ring search)
 0xD430:  'lw $6,%lo(g_padUU+1324)($3)',
 # sub_D474 (static init: FPL/Tlspl name tables)
 0xD490:  'addiu $9,$2,%lo(g_padUU+1324)',
 # sub_14124 (resume-dispatch core)
 0x14138: 'lw $7,%lo(g_padUU+64)($3)',
 0x14140: 'addiu $8,$3,%lo(g_padUU+64)',
 # sub_14598 (requeue/preempt core)
 0x145BC: 'addiu $19,$17,%lo(g_padUU+64)',
 0x146C0: 'addiu $18,$17,%lo(g_padUU+64)',
 0x14778: 'addiu $16,$17,%lo(g_padUU+64)',
 # sub_156BC (reg init)
 0x1574C: 'addiu $18,$11,%lo(g_padUU+64)',
 # sub_177C4 / sub_17844 (dead-thread dispatchers)
 0x1780C: 'lw $7,%lo(g_padUU+1292)($8)',
 0x1788C: 'lw $4,%lo(g_padUU+1292)($10)',
 # sub_18504 (delete teardown)
 0x185B0: 'addiu $17,$11,%lo(g_padUU+64)',
 0x18620: 'lw $4,%lo(g_padUU+2080)($10)',
 0x18650: 'lw $4,%lo(g_padUU+2080)($8)',
 # sub_11E3C (KTLS exit walker)
 0x11E84: 'addiu $3,$23,%lo(g_padUU+1364)',
 0x11F10: 'addiu $7,$8,%lo(g_padUU+64)',
}

FUNCS = [
 ('sub_134A8', 0x134A8,  29),  # ctx/exception-frame init (deadbeef + FPU poison)
 ('sub_155B8', 0x155B8,  65),  # delete cleanup (cache ops + stack-block walk)
 ('sub_156BC', 0x156BC,  67),  # reg init (parked-stack walker)
 ('sub_2570',  0x2570,   35),  # teardown-prep: TEH view release
 ('sub_25FC',  0x25FC,   52),  # inline-vs-retarget gate (TEH class scan)
 ('sub_26CC',  0x26CC,   24),  # callback ring purge (uid free walk)
 ('sub_27B4',  0x27B4,   34),  # teardown-prep: callback view release
 ('sub_283C',  0x283C,   33),  # static init: TEH/callback name tables
 ('sub_28C0',  0x28C0,   33),  # kernel-callback trampoline
 ('sub_2B3C',  0x2B3C,   10),  # uid resolve -> view+12
 ('sub_2B64',  0x2B64,   70),  # wait-type-10 enqueue (0x800201A0)
 ('sub_2C7C',  0x2C7C,   10),  # uid resolve twin
 ('sub_2CA4',  0x2CA4,   70),  # wait-type-11 twin (0x800201A1)
 ('sub_2DBC',  0x2DBC,   13),  # callback return trampoline
 ('sub_4D68',  0x4D68,   34),  # sema fairness gate
 ('sub_92F4',  0x92F4,   17),  # static init: mbx name tables
 ('sub_9338',  0x9338,   58),  # mbx insert (prio-ordered)
 ('sub_9420',  0x9420,   10),  # uid resolve twin
 ('sub_9448',  0x9448,    8),  # uid resolve twin (0)
 ('sub_C50',   0xC50,    15),  # static init: vtimer table
 ('sub_C8C',   0xC8C,    79),  # timeout core (4th wake path)
 ('sub_DC8',   0xDC8,    22),  # view refcount-reset walker
 ('sub_E20',   0xE20,    60),  # cancel-all waiters (0x800201B5)
 ('sub_F10',   0xF10,    43),  # cancel-all twin (0x800201A9)
 ('sub_FBC',   0xFBC,     2),  # return 0
 ('sub_FC4',   0xFC4,     8),  # view refcount--
 ('sub_14124', 0x14124,  71),  # resume-dispatch core
 ('sub_14598', 0x14598, 175),  # requeue/preempt test
 ('sub_D2E4',  0xD2E4,   21),  # FPL ring push
 ('sub_D338',  0xD338,   21),  # Tlspl ring push
 ('sub_D38C',  0xD38C,   20),  # FPL ring pop
 ('sub_D3DC',  0xD3DC,   20),  # Tlspl ring pop
 ('sub_D42C',  0xD42C,   18),  # FPL uid ring search (view+32)
 ('sub_D474',  0xD474,   17),  # static init: FPL/Tlspl name tables
 ('sub_D4B8',  0xD4B8,   10),  # uid resolve twin
 ('sub_D4E0',  0xD4E0,   37),  # delete + block frees
 ('sub_11E3C', 0x11E3C,  67),  # KTLS exit walker (gp-swap dtor)
 ('sub_177C4', 0x177C4,  32),  # dead-thread dispatcher 1
 ('sub_17844', 0x17844,  31),  # dead-thread dispatcher 2
 ('sub_18474', 0x18474,  36),  # view ring init
 ('sub_18504', 0x18504,  98),  # delete teardown (17A14/156BC/stack frees)
 ('sub_10D34', 0x10D34,  22),  # deadline builder (now64 + usec)
 ('sub_10D8C', 0x10D8C,  26),  # deadline builder wide (now64 + 64-bit arg)
 ('sub_743C',  0x743C,   17),  # static init: mutex name tables
 ('sub_172A8', 0x172A8,   8),  # exit-delete-self helper
 ('sub_172C8', 0x172C8,   5),  # dead spin (mfc0/cache/madd self-loop)
 ('sub_172DC', 0x172DC,   7),  # exit-with-status helper
 ('sub_16B40', 0x16B40,  17),  # static init: thread class table (320B)
 ('sub_16B84', 0x16B84,  21),  # early-exit teardown (ReleaseSemaphore pair)
 ('sub_EEB0',  0xEEB0,   29),  # TEH slot alloc (ctx+0x4FC list)
 ('sub_12C04', 0x12C04,  61),  # post-attr-change (IMASK reprogram 0xBC000044)
 ('sub_16FA4', 0x16FA4,  40),  # kstack snapshot (kernel-stack free calc)
 ('sub_E0D4',  0xE0D4,   90),  # Tlspl exit walker (16-slot block return)
 ('sub_17EB4', 0x17EB4, 126),  # stack-switch runner (64B parked frame)
 ('sub_1580',  0x1580,  160),  # TEH dispatch
 ('sub_4FBC',  0x4FBC,   17),  # static init: sema name tables
 ('sub_5000',  0x5000,   10),  # uid resolve twin
 ('sub_5028',  0x5028,    8),  # uid resolve twin (0)
 ('sub_5048',  0x5048,   60),  # sema waiter walk (count grant)
 ('sub_60D4',  0x60D4,   19),  # mutex wait-queue unlink walk
 ('sub_6120',  0x6120,   17),  # static init: mutex name tables
 ('sub_6164',  0x6164,   41),  # mutex acquire bookkeeping
 ('sub_6208',  0x6208,   10),  # uid resolve twin
 ('sub_6230',  0x6230,   21),  # mutex unlink + resolve
 ('sub_755C',  0x755C,   10),  # uid resolve twin
 ('sub_7584',  0x7584,   24),  # relinquish wrapper (7480+1876c)
 ('sub_75E4',  0x75E4,   61),  # mutex waiter walk + ceiling boost
 ('sub_84B4',  0x84B4,   17),  # static init: LwMutex name tables
 ('sub_84F8',  0x84F8,   10),  # uid resolve twin
 ('sub_8520',  0x8520,   15),  # LwMutex unlink + resolve
 ('sub_855C',  0x855C,   19),  # LwMutex refcount pair
 ('sub_85A8',  0x85A8,   42),  # LwMutex waiter walk
 ('sub_C1FC',  0xC1FC,   18),  # VPL uid ring search
 ('sub_C244',  0xC244,   17),  # static init: VPL name tables
 ('sub_C288',  0xC288,   10),  # uid resolve twin
 ('sub_C2B0',  0xC2B0,   31),  # VPL delete (sysmem block free)
 ('sub_C32C',  0xC32C,   55),  # VPL waiter walk (grant + 924)
 ('sub_11834', 0x11834,  10),  # uid resolve twin
 ('sub_1185C', 0x1185C,   8),  # uid resolve twin (0)
 ('sub_1187C', 0x1187C,  10),  # uid resolve twin
 ('sub_118A4', 0x118A4,   8),  # uid resolve twin (0)
 ('sub_118C4', 0x118C4,  10),  # uid resolve twin
 ('sub_118EC', 0x118EC,  51),  # vtimer delete (queue unlink + EB7C)
 ('sub_119B8', 0x119B8,  19),  # view init (self-links)
 ('sub_11A04', 0x11A04,   8),  # uid resolve twin (0)
 ('sub_13E80', 0x13E80, 109),  # THREAD START TRAMPOLINE (ctxblk fill)
 ('sub_3D88',  0x3D88,  133),  # delay core (usec) — behind 3D78/3D80 veneers
 ('sub_3FAC',  0x3FAC,  146),  # delay core (SysClock) — behind 3F9C/3FA4 veneers
 ('sub_41F4',  0x41F4,   21),  # delay-cancel walker (924 + module+0x44 clear)
 ('sub_B7E4',  0xB7E4,  204),  # VPL allocate core — behind B7D4/B7DC veneers
]

def gen_func(name, addr, n, out):
    ws = words(addr, n)
    targets = set()
    for a, w in ws:
        op = w >> 26
        if op in (2,3):
            t = (w & 0x3FFFFFF) << 2
            if addr <= t <= addr + 4*(n-1):
                targets.add(t)
            elif (w & 0x3FFFFFF) << 2 != 0:
                pass  # external literal target, no label needed
        elif op in (1,4,5,6,7,20,21):
            simm = sx(w & 0xFFFF)
            t = a + 4 + simm*4
            if addr <= t <= addr + 4*(n-1):
                targets.add(t)
            else:
                print('WARN %s: branch %08X at %05X leaves function -> %05X' % (name,w,a,t), file=sys.stderr)
    lines = []
    lines.append('__asm__(')
    lines.append('".text\\n"')
    lines.append('".set push\\n"')
    lines.append('".set noreorder\\n"')
    lines.append('".globl %s\\n"' % name)
    lines.append('".type %s,@function\\n"' % name)
    lines.append('"%s:\\n"' % name)
    for a, w in ws:
        if a in targets and a != addr:
            lines.append('"L%05x:\\n"' % a)
        if a in LO:
            s = LO[a]
        else:
            s = decode(w, a)
            if s.startswith('lui $') and s.endswith(',0x0'):
                s = s.replace(',0x0', ',%hi(g_padUU)')
        cmt = '/* %05X %08X */' % (a, w)
        if s.startswith('MOVZ(') or s.startswith('MOVN('):
            inner = s[5:-1]
            opn = 'movz' if s.startswith('MOVZ(') else 'movn'
            lines.append('".set push\\n.set mips4\\n"')
            lines.append('"%s %s\\n.set pop\\n" %s' % (opn, inner, cmt))
        elif s.startswith('BR('):
            body = s[3:-1]  # "beq $4,$5,0x12345"
            mn, rest = body.split(' ', 1)
            regs, tgt = rest.rsplit(',0x', 1)
            lines.append('"%s %s,L%05x\\n" %s' % (mn, regs, int(tgt,16), cmt))
        else:
            lines.append('"%s\\n" %s' % (s, cmt))
    lines.append('".set pop\\n"')
    lines.append('".size %s,.-%s\\n"' % (name, name))
    lines.append(');')
    out.append((name, addr, n, '\n'.join(lines)))

out = []
hdr = '''/* threadman byte-match grind — batch UU: named-internals sweep (41 INTERNAL
 * functions; see results/UU.md). Retail: PSP firmware 6.60 kd/threadman.prx
 * (user's own console dump). Toolchain: GCC 3.3.6 -O3 -mips2 -G0 -mabi=eabi
 * (16-byte stack align patch).
 *
 * Technique: .set noreorder asm transcription (tools/gen_tm.py method, this
 * file generated by /tmp/gen_uu.py) with literal absolute jal/j targets;
 * module-data refs via g_padUU %%hi/%%lo so the reloc immediates are the
 * literal retail ones. gas notes: only $sp/$ra/$fp aliases; movz/movn
 * wrapped in .set mips4; ins/ext/clz/rotrv/break/SPECIAL2 words spliced raw.
 * The 0x1868C..0x18830 callee range is the import-veneer table (patched at
 * load) — jal words there encode the stub address and match byte-exact.
 */
typedef unsigned char u8;
typedef unsigned int u32;

/* Module data anchor: &g_padUU == module+0 (so %lo offsets == retail).
 * +0x40 = current-thread record pointer P; +0x44 conditional waiter-refcnt;
 * +0x408/+0x51C class tables; +0x820 pool table. */
static u8 g_padUU[0x40];        /* +0x000 */
static u32 g_ctxUU;             /* +0x040 */
'''
parts = [hdr]
for name, addr, n in FUNCS:
    gen_func(name, addr, n, out)

with open(ROOT + '/match/threadman/tm_uu.c', 'w') as f:
    f.write(hdr)
    f.write('\n')
    for name, addr, n, block in out:
        f.write('\n/* ============ %s @0x%05X (%d words) ============ */\n\n' % (name, addr, n))
        f.write(block)
        f.write('\n')
print('written')
