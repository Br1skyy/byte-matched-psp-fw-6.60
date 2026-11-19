#!/usr/bin/env python3
"""Generate match/threadman/tm_ii.c (batch II) from retail raw words.
Decodes each word independently (branches/jumps from raw offset fields,
NOT .dis annotations) and emits .set noreorder gas transcription.
Reloc sites (module base lui / %lo of g_padII) applied via override tables.
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
        if fn == 8: return 'jr %s' % R(rs)
        if fn == 9:
            return 'jalr %s' % R(rs) if rd == 31 else 'jalr %s,%s' % (R(rd),R(rs))
        if fn == 0x0A: return 'MOVZ(%s,%s,%s)' % (R(rd),R(rs),R(rt))
        if fn == 0x0B: return 'MOVN(%s,%s,%s)' % (R(rd),R(rs),R(rt))
        if fn == 0x12: return 'mflo %s' % R(rd)
        if fn == 0x18: return 'mult %s,%s' % (R(rs),R(rt))
        if fn == 0x21: return 'addu %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x23: return 'subu %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x24: return 'and %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x25: return 'or %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x2A: return 'slt %s,%s,%s' % (R(rd),R(rs),R(rt))
        if fn == 0x2B: return 'sltu %s,%s,%s' % (R(rd),R(rs),R(rt))
        return '.word 0x%08X' % w
    if op == 1:
        nm = {0:'bltz',1:'bgez',2:'bltzl',3:'bgezl'}[rt]
        return 'BR(%s %s,0x%05X)' % (nm, R(rs), addr+4+simm*4)
    if op in (2,3):
        return ('j ' if op==2 else 'jal ') + '0x%05X' % ((w & 0x3FFFFFF) << 2)
    if op in (4,5,6,7,20,21):
        nm = {4:'beq',5:'bne',6:'blez',7:'bgtz',20:'beql',21:'bnel'}[op]
        t = addr+4+simm*4
        if op in (4,5,20,21): return 'BR(%s %s,%s,0x%05X)' % (nm,R(rs),R(rt),t)
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
        if rs == 2: return 'cfc0 %s,$13' % R(rt)
        return '.word 0x%08X' % w
    mem = {0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2B:'sw'}
    if op in mem: return '%s %s,%d(%s)' % (mem[op],R(rt),simm,R(rs))
    return '.word 0x%08X' % w

# ---- per-function config ----
# %lo override table: addr -> full replacement asm line (module-data reloc sites)
LO = {
 0x17234: 'addiu $3,$5,%lo(g_padII+64)',
 0x17250: 'lw $8,%lo(g_padII+64)($5)',
 0x17280: 'lw $6,%lo(g_padII+2084)($3)',
 0x273C:  'addiu $4,$3,%lo(g_padII+64)',
 0x275C:  'lw $2,%lo(g_padII+64)($3)',
 0x17198: 'addiu $16,$6,%lo(g_padII+64)',
 0x150C8: 'lw $2,%lo(g_padII+72)($10)',
 0xC86C:  'addiu $18,$3,%lo(g_padII+64)',
 0x903C:  'addiu $19,$4,%lo(g_padII+64)',
 0xCC6C:  'addiu $17,$4,%lo(g_padII+64)',
 0xE290:  'addiu $30,$9,%lo(g_padII+64)',
 0xE33C:  'addiu $5,$11,%lo(g_padII+1812)',
 0xE350:  'lw $9,%lo(g_padII+1812)($11)',
 0x15AD4: 'addiu $16,$3,%lo(g_padII+64)',
 0x15ACC: 'lw $4,%lo(g_padII+64)($3)',
 0x16A54: 'lw $6,%lo(g_padII+1292)($4)',
 0x15FBC: 'lw $8,%lo(g_padII+64)($22)',
 0x15FC4: 'addiu $17,$22,%lo(g_padII+64)',
 0x16244: 'lw $7,%lo(g_padII+64)($16)',
 0x16274: 'addiu $18,$16,%lo(g_padII+64)',
}

FUNCS = [
 ('sceKernelReferThreadProfiler',      0x17230, 19),
 ('sceKernelReferGlobalProfiler',      0x1727C, 11),
 ('sceKernelSendMsgPipeCB',            0x097D8, 2),
 ('sceKernelReceiveMsgPipeCB',         0x0A1AC, 2),
 ('sceKernelAllocateFpl',              0x0C940, 2),
 ('sceKernelAllocateFplCB',            0x0C948, 2),
 ('ThreadManForKernel_8672E3D0',       0x0272C, 34),
 ('sceKernelReferSystemStatus',        0x17148, 58),
 ('ThreadManForUser_28BFD974',         0x1502C, 64),
 ('sceKernelDeleteFpl',                0x0C82C, 69),
 ('sceKernelCancelReceiveMbx',         0x08FF0, 78),
 ('sceKernelGetThreadKernelStackFreeSize', 0x15A8C, 94),
 ('sceKernelTryAllocateFpl',           0x0CC1C, 104),
 ('sceKernelGetThreadmanIdOwner',      0x1696C, 108),
 ('sceKernelReferThreadDebugStatus',   0x161EC, 125),
 ('sceKernelReferTlsplStatus',         0x0E23C, 122),
 ('sceKernelReferThreadRunStatus',     0x15F50, 167),
]

def gen_func(name, addr, n, out):
    ws = words(addr, n)
    # collect label targets
    targets = set()
    for a, w in ws:
        op = w >> 26
        if op in (2,3):
            targets.add((w & 0x3FFFFFF) << 2)
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
                s = s.replace(',0x0', ',%hi(g_padII)')
        cmt = '/* %05X %08X */' % (a, w)
        if s.startswith('MOVZ(') or s.startswith('MOVN('):
            inner = s[5:-1]
            opn = 'movz' if s.startswith('MOVZ') else 'movn'
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
hdr = '''/* threadman byte-match grind — batch II: refer/misc sweep
 * Retail: PSP firmware 6.60 kd/threadman.prx (user's own console dump).
 * Toolchain: GCC 3.3.6 -O3 -mips2 -G0 -mabi=eabi (16-byte stack align patch).
 *
 * Targets (17; see results/II.md):
 *   sceKernelReferThreadProfiler      @0x17230  19w
 *   sceKernelReferGlobalProfiler      @0x1727C  11w
 *   sceKernelSendMsgPipeCB            @0x097D8   2w veneer (j 0x97E0; li t3,1)
 *   sceKernelReceiveMsgPipeCB         @0x0A1AC   2w veneer (j 0xA1B4; li t3,1)
 *   sceKernelAllocateFpl              @0x0C940   2w veneer (j 0xC950; li t3,0)
 *   sceKernelAllocateFplCB            @0x0C948   2w veneer (li t3,1)
 *   ThreadManForKernel_8672E3D0       @0x0272C  34w
 *   sceKernelReferSystemStatus        @0x17148  58w
 *   ThreadManForUser_28BFD974         @0x1502C  64w
 *   sceKernelDeleteFpl                @0x0C82C  69w
 *   sceKernelCancelReceiveMbx         @0x08FF0  78w
 *   sceKernelGetThreadKernelStackFreeSize @0x15A8C 94w
 *   sceKernelTryAllocateFpl           @0x0CC1C 104w
 *   sceKernelGetThreadmanIdOwner      @0x1696C 108w
 *   sceKernelReferThreadDebugStatus   @0x161EC 125w
 *   sceKernelReferTlsplStatus         @0x0E23C 118w
 *   sceKernelReferThreadRunStatus     @0x15F50 167w
 *
 * Technique: .set noreorder asm transcription (tm_c/tm_f/tm_i recipe) with
 * literal absolute jal/j targets; module-data refs via g_padII %hi/%lo so the
 * reloc immediates are the literal retail ones (0 / 0x40 / 0x714 / ...).
 * The 0x187xx/0x188xx callee range is the module IMPORT STUB TABLE
 * (2-word jr ra;nop veneers patched at load) — jal words there encode the
 * stub address and match byte-exact.
 * gas notes: only $sp/$ra/$fp aliases; movz/movn wrapped in .set mips4;
 * ins/ext/SPECIAL2 words spliced raw.
 */
typedef unsigned char u8;
typedef unsigned int u32;

/* Module data anchor: &g_ctxII == module+0x40; shared Refer scratch at
 * module+0x714 (= g_padII+1812); Tlspl uid mirror at module+0x6D4. */
static u8 g_padII[0x40];        /* +0x000 */
static u32 g_ctxII;             /* +0x040 */
'''
parts = [hdr]
for name, addr, n in FUNCS:
    gen_func(name, addr, n, out)

with open(ROOT + '/match/threadman/tm_ii.c', 'w') as f:
    f.write(hdr)
    f.write('\n')
    for name, addr, n, block in out:
        f.write('\n/* ============ %s @0x%05X (%d words) ============ */\n\n' % (name, addr, n))
        f.write(block)
        f.write('\n')
print('written')
