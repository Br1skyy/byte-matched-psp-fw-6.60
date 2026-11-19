#!/usr/bin/env python3
"""Full-module PRX link pipeline for the threadman byte-match grind.

    python3 tools/link/build_prx.py [--no-compile] [--report PATH]

Stages
  1. compile every match/threadman/tm*.c in the etch container (per-file, so
     one in-flight batch never blocks the link) with every available GCC
     (prefix336 + patched prefix336b) into build/link/<src>.<tc>.o
  2. inventory every function symbol (export names via orig/threadman-map.json,
     internals via the sub_XXXXX naming convention), link each at its RETAIL
     address inside a copy of the retail ph0 image
  3. resolve relocations ourselves against ONE unified module-data image
     (every batch's g_pad statics overlaid at their retail offsets; known
     GCC-alignment-ceiling symbols re-placed at their documented retail
     offsets -- see DATA_OVERRIDES), so `match (reloc)` functions close
  4. fill the rest of ph0: default mode copies the import-veneer table,
     export tables, import stubs, SceModuleInfo, rodata and the ph2
     relocation table from retail bytes; with --no-retail ALL of those are
     GENERATED instead (tools/link/meta.py + rodata.py inventories,
     tools/link/reltab.py A1 relocation codec, headers from fields) and the
     output contains no retail bytes
  5. emit build/link/threadman-linked.prx
     and diff it region-by-region against orig/threadman.prx:
     matched-exact / matched-reloc-pending / unmatched-gap per region,
     byte-level gap ranges (= the wave-11 target list), and a data-image
     map cross-checked against the offsets documented in results/*.md.

tools/match.py and tools/prx.py are IMPORTED read-only, never modified.
"""
import argparse
import glob
import json
import os
import re
import struct
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import match  # noqa: E402  (read-only reuse of the grind harness)
import prx as prxmod  # noqa: E402  (read-only reuse of the PRX parser)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta      # noqa: E402  (module-metadata generator, tools/link)
import reltab    # noqa: E402  (ph2 relocation-table codec, tools/link)

LINK = os.path.join(ROOT, 'build', 'link')
RETAIL = os.path.join(ROOT, 'orig', 'threadman.prx')

# Container paths (see tools/match.py; etch386 + from-source toolchains)
TC_CANDIDATES = ['prefix336', 'prefix336b']      # under /tc (toolchain-build)
GCC_FLAGS = '-O3 -mips2 -G0 -mabi=eabi'

# Manual placements in the unified module-data model.
# Each batch's own .o static layout drifts from retail where GCC alignment
# rules bite; the unified image places the symbol at the retail offset the
# grind documented (see the cited result file).
#   - tm.c: LogCtx got 8-aligned so every later static sits +8/+4 off
#     (results round-1: statusFlag +0x810, deadThreadHandler +0x838).
#   - tm_a.c: GCC 8-aligns every static >= 8 bytes, so the documented pair
#     at +0x17844 landed +0x17848 (results/A.md).
DATA_OVERRIDES = {
    # rekeyed for the family-file reorg (match/threadman/*.c): util.c holds
    # the round-1 statics chain, thread.c the dead-thread handler.  The
    # family sources declare these with pad prefixes at their retail
    # offsets already (g_deadThreadHandler lands +0x838 naturally), so
    # these are belt-and-braces; only g_d366[2] still needs the +0x17844
    # fix (GCC 8-aligns every static >= 8 bytes).
    ('util', 'g_systemStatusFlag'): 0x810,
    ('thread', 'g_deadThreadHandler'): 0x838,
    ('util', 'g_d366'): 0x17844,
}

# Internal (non-exported) functions named by the grind notes -- used only to
# annotate gap ranges; addresses are retail vaddrs.
KNOWN_INTERNALS = {
    0x0680: 'wait-enqueue core (sub_680)',
    0x0858: 'sleep-queue tail append',
    0x0890: 'priority-insert leaf',
    0x0908: 'wait-enqueue veneer',
    0x0924: 'release-from-wait',
    0x0A08: 'wake-now',
    0x0B08: 'direct-wake handoff',
    0x0B48: 'exit-waiter walk',
    0x0BC4: 'wait-machinery cancel',
    0x0C30: 'wait-block cleanup',
    0x0FE4: 'resched request',
    0x113F0: '64/32 divmod',
    0x10D34: 'deadline builder',
    0x10FAC: 'delay timer arm',
    0x11104: 'delay timer cancel',
    0x116F4: 'alarm core',
    0x1580: 'TEH dispatch',
    0x2170: 'callback pump',
    0x28C0: 'callback thunk (OO)',
    0x2944: 'user-callback invoke thunk',
    0x3AD0: 'thread-end wait core',
    0x3D88: 'delay core (usec)',
    0x3FAC: 'delay core (SysClock)',
    0x4D68: 'sema fairness gate',
    0x6604: 'mutex acquire+boost',
    0x66F0: 'mutex exit mass-release',
    0x7480: 'mutex relinquish',
    0x97E0: 'MsgPipe send core',
    0xA1B4: 'MsgPipe receive core',
    0xAFC0: 'ring write',
    0xB094: 'ring read',
    0x9338: 'mbx insert',
    0xC950: 'FPL alloc core',
    0xD2E4: 'FPL ring push',
    0xD338: 'Tlspl ring push',
    0xD38C: 'FPL ring pop',
    0xD3DC: 'Tlspl ring pop',
    0xE0D4: 'Tlspl exit walker',
    0xE424: 'pool-block validate',
    0xE4A4: 'tlspl resolver',
    0xEAE0: 'alarm insert',
    0xEB7C: 'alarm reprocess',
    0xECE4: '64-bit clock read',
    0x11E3C: 'KTLS exit walker',
    0x126AC: 'uid free',
    0x12C04: 'post-attr-change',
    0x134A8: 'ctx setup',
    0x14124: 'dispatch-state helper',
    0x14598: 'requeue/preempt test',
    0x155B8: 'delete cleanup',
    0x156BC: 'reg init',
    0x16BF4: 'dequeue',
    0x16C48: 'make-ready',
    0x16FA4: 'kstack snapshot',
    0x1752C: 'post-exit teardown',
    0x177AC: 'deferred exit teardown',
    0x177C4: 'report tail',
    0x178C0: 'never-return exit core',
    0x17A14: 'terminate-pending',
    0x17B68: 'live-kill path',
    0x17EB4: 'stack-switch runner',
    0x180AC: 'ThreadDebugStatus builder',
    0x183EC: 'SystemStatus builder',
}

SUB_RE = re.compile(r'^[sS][uU][bB]_([0-9A-Fa-f]{3,6})$')


def sx16(x):
    return x - 0x10000 if x & 0x8000 else x


# --------------------------------------------------------------------------
# stage 1: compile
# --------------------------------------------------------------------------

def compile_all(log):
    os.makedirs(LINK, exist_ok=True)
    srcs = sorted(glob.glob(os.path.join(ROOT, 'match', 'threadman', '*.c')))
    script = ['cd /tm', 'mkdir -p build/link']
    expects = []
    for s in srcs:
        base = os.path.splitext(os.path.basename(s))[0]
        for tc in TC_CANDIDATES:
            out = 'build/link/%s.%s.o' % (base, tc)
            script.append('if %s/bin/mipsel-elf-gcc -c %s %s -o %s 2>>build/link/compile.log; '
                          'then :; else echo "COMPILE-FAIL %s %s" >> build/link/compile.log; fi'
                          % ('/tc/' + tc, GCC_FLAGS,
                             os.path.relpath(s, ROOT), out, base, tc))
            expects.append(out)
    cmd = ('mkdir -p /tc/prefix336/mipsel-elf/bin /tc/prefix336b/mipsel-elf/bin; '
           'for t in as ar ld nm ranlib; do '
           'ln -sf /tc/prefix/bin/mipsel-elf-$t /tc/prefix336/mipsel-elf/bin/$t; '
           'ln -sf /tc/prefix/bin/mipsel-elf-$t /tc/prefix336b/mipsel-elf/bin/$t; done; '
           'export PATH=/tc/prefix/bin:$PATH; ' + '; '.join(script))
    r = subprocess.run(['podman', 'run', '--rm',
                        '-v', os.path.join(os.path.dirname(ROOT), 'toolchain-build') + ':/tc:Z',
                        '-v', ROOT + ':/tm:Z', 'etch386', 'sh', '-c', cmd],
                       capture_output=True, text=True)
    if r.returncode:
        log('container run failed: %s%s' % (r.stdout[-2000:], r.stderr[-2000:]))
        sys.exit(1)
    objs = sorted(glob.glob(os.path.join(LINK, '*.o')))
    fails = []
    clog = os.path.join(LINK, 'compile.log')
    if os.path.exists(clog):
        fails = [l.split()[1] for l in open(clog) if l.startswith('COMPILE-FAIL')]
    if fails:
        for f in sorted(set(fails)):
            log('  COMPILE-FAIL %s (in-flight batch? object skipped)' % f)
    return srcs, objs


# --------------------------------------------------------------------------
# stage 2: object parsing (own ELF reader: need reloc symbol indices, which
# tools/match.py's parser discards)
# --------------------------------------------------------------------------

class Obj:
    def __init__(self, path):
        self.path = path
        self.base = os.path.basename(path)
        m = re.match(r'^(.*)\.(prefix\d+\w*)\.o$', self.base)
        self.src = m.group(1) if m else os.path.splitext(self.base)[0]
        self.tc = m.group(2) if m else '?'
        d = self.d = open(path, 'rb').read()
        e_shoff, = struct.unpack('<I', d[32:36])
        shent, shnum, shstrndx = struct.unpack('<HHH', d[46:52])
        shs = []
        for i in range(shnum):
            o = e_shoff + i * shent
            v = struct.unpack('<10I', d[o:o + 40])
            shs.append(dict(zip(['name', 'type', 'flags', 'addr', 'off',
                                 'size', 'link', 'info', 'align', 'entsize'], v)))
        st = shs[shstrndx]

        def sname(n):
            p = st['off'] + n
            return d[p:d.index(b'\0', p)].decode()
        for s in shs:
            s['sname'] = sname(s['name'])
        self.shs = shs
        # symbols
        self.symtab = []
        for s in shs:
            if s['sname'] == '.symtab':
                strt = shs[s['link']]
                for i in range(s['size'] // 16):
                    o = s['off'] + i * 16
                    nm, val, sz, info, other, shndx = struct.unpack('<IIIBBH', d[o:o + 16])
                    p = strt['off'] + nm
                    name = d[p:d.index(b'\0', p)].decode()
                    self.symtab.append({'name': name, 'val': val, 'size': sz,
                                        'type': info & 0xf, 'bind': info >> 4,
                                        'shndx': shndx})
        # .text bytes + relocs (offset -> (type, symidx))
        self.text = None
        self.relocs = defaultdict(list)
        for s in shs:
            if s['sname'] == '.text':
                self.text = s
            elif s['sname'].startswith('.rel.text'):
                for i in range(s['size'] // 8):
                    o = s['off'] + i * 8
                    r_off, r_info = struct.unpack('<II', d[o:o + 8])
                    self.relocs[r_off].append((r_info & 0xff, r_info >> 8))
        # data-model symbols: statics defined in .bss/.data (name -> (val, size))
        self.data_syms = {}
        for i, s in enumerate(shs):
            if s['sname'] in ('.bss', '.data'):
                for sym in self.symtab:
                    if (sym['shndx'] == i and sym['name']
                            and not sym['name'].startswith('.')
                            and not sym['name'].startswith('$')):
                        self.data_syms.setdefault(sym['name'], (sym['val'], sym['size']))
        assert self.text is not None, path

    def text_words(self, off, size):
        o = self.text['off'] + off
        return list(struct.unpack('<%dI' % (size // 4), self.d[o:o + size]))

    def functions(self):
        out = []
        for i, s in enumerate(self.shs):
            if s['sname'] != '.text':
                continue
            for sym in self.symtab:
                if (sym['type'] == 2 and sym['size'] > 0 and sym['shndx'] == i
                        and sym['name'] and not sym['name'].startswith('$')):
                    out.append(sym)
        return out


# --------------------------------------------------------------------------
# stage 3: link
# --------------------------------------------------------------------------

class Linker:
    def __init__(self, objs, log):
        self.objs = objs
        self.log = log
        self.retail_d, self.retail_seg = match.load_retail()
        self.nmap = match.name_map()
        self.touched = set()          # module-data offsets referenced by code
        self.func_addr = {}          # name -> retail addr (defined by us)
        for o in objs:
            for sym in o.functions():
                a = self.addr_for_name(sym['name'])
                if a is not None:
                    self.func_addr.setdefault(sym['name'], a)

    def addr_for_name(self, name):
        if name in self.nmap:
            return self.nmap[name]
        m = SUB_RE.match(name)
        if m:
            return int(m.group(1), 16)
        return None

    def sym_value(self, obj, symidx, unresolved):
        """Image-space value of relocation symbol symidx of object obj."""
        if symidx == 0:
            return 0
        try:
            sym = obj.symtab[symidx]
        except IndexError:
            return None
        nm = sym['name']
        if nm in ('.bss', '.data', '.text'):
            return 0                      # section base in the model
        if sym['type'] == 2 and nm in self.func_addr:
            return self.func_addr[nm]
        if nm in obj.data_syms:
            return self.unified_off(obj, nm)
        a = self.addr_for_name(nm)
        if a is not None:
            return a
        unresolved.append(nm)
        return None

    def unified_off(self, obj, name):
        val, _size = obj.data_syms[name]
        return DATA_OVERRIDES.get((obj.src, name), val)

    def remap_data_value(self, obj, symidx, V):
        """Map a data-model value V (S + AHL, own-layout coordinates) through
        the unified module-data image: attribute V to the innermost static of
        obj that contains it, then rebase on that static's unified offset.
        Values that attribute to no static (bare pad offsets, non-data
        targets) are returned unchanged -- the batch models already sit at
        retail offsets for those."""
        sym = obj.symtab[symidx] if symidx < len(obj.symtab) else None
        nm = sym['name'] if sym else ''
        if nm in obj.data_syms:
            val, size = obj.data_syms[nm]
            return self.unified_off(obj, nm) + (V - val)
        if nm in ('.bss', '.data'):
            best = None
            for sname, (val, size) in obj.data_syms.items():
                if val <= V and (best is None or val > best[1]):
                    best = (sname, val)
            if best is not None:
                sname, val = best
                return self.unified_off(obj, sname) + (V - val)
        return V

    def resolve_function(self, obj, sym):
        """Return (words, word_status, unresolved) after reloc resolution.
        word_status: None = no reloc; True = resolved reloc; False = unresolved.

        MIPS ABI REL semantics: paired HI16/LO16 share the combined addend
        AHL = (AHI << 16) + (short)ALO; the resolved target is S + AHL, and
        HI16/LO16 output fields are the hi/lo decomposition of the target
        (hi = (V - sext(V & 0xFFFF)) >> 16)."""
        off, size = sym['val'], sym['size']
        n = size // 4
        words = obj.text_words(off, size)
        status = [None] * n
        unresolved = []
        relocs = {r: v for r, v in obj.relocs.items() if off <= r < off + size}
        pending_hi = []   # word indices of HI16 awaiting their LO16 partner
        ahi_stack = []    # their ORIGINAL imm fields (addends), parallel
        last_ahi = None   # HI16 addends persist for follower LO16s (ABI pairs
                           # one HI16 with several LO16s)

        def flush_hi(V, idxs):
            hi = ((V - sx16(V & 0xFFFF)) >> 16) & 0xFFFF
            for wi in idxs:
                words[wi] = (words[wi] & 0xFFFF0000) | hi

        for r_off in sorted(relocs):
            rtype, symidx = relocs[r_off][0]
            wi = (r_off - off) // 4
            w = words[wi]
            S = self.sym_value(obj, symidx, unresolved)
            if S is None:
                status[wi] = False
                continue
            if rtype == 5:                       # R_MIPS_HI16
                pending_hi.append(wi)
                ahi_stack.append(w & 0xFFFF)
                last_ahi = w & 0xFFFF
                status[wi] = True
            elif rtype == 6:                     # R_MIPS_LO16
                ahi = ahi_stack[-1] if ahi_stack else (last_ahi or 0)
                AHL = (ahi << 16) + sx16(w & 0xFFFF)
                V = self.remap_data_value(obj, symidx, (S + AHL) & 0xFFFFFFFF)
                if V < 0x20000:
                    self.touched.add(V)
                words[wi] = (w & 0xFFFF0000) | (V & 0xFFFF)
                status[wi] = True
                if pending_hi:
                    flush_hi(V, pending_hi)
                    pending_hi, ahi_stack = [], []
            elif rtype == 4:                     # R_MIPS_26
                tgt = (S + ((w & 0x3FFFFFF) << 2)) & 0xFFFFFFFF
                words[wi] = (w & 0xFC000000) | ((tgt >> 2) & 0x3FFFFFF)
                status[wi] = True
            elif rtype == 2:                     # R_MIPS_32
                V = self.remap_data_value(obj, symidx, (S + w) & 0xFFFFFFFF)
                words[wi] = V & 0xFFFFFFFF
                status[wi] = True
            else:
                self.log('  note: unhandled reloc type %d at %s+0x%x' %
                         (rtype, obj.base, r_off))
                status[wi] = False
        if pending_hi:
            # no LO16 partner in range: approximate with lo = 0
            for wi, ahi in zip(pending_hi, ahi_stack):
                V = ahi << 16
                words[wi] = (words[wi] & 0xFFFF0000) | \
                    (((V - sx16(V & 0xFFFF)) >> 16) & 0xFFFF)
        return words, status, unresolved

    def classify(self, obj, sym, addr):
        words, status, unresolved = self.resolve_function(obj, sym)
        ret = match.retail_words(self.retail_d, self.retail_seg, addr, len(words))
        exact = pend = diff = 0
        for i, w in enumerate(words):
            if w == ret[i]:
                exact += 1
            elif status[i]:
                pend += 1
            else:
                diff += 1
        return {'obj': obj, 'sym': sym, 'addr': addr, 'words': words,
                'status': status, 'retail': ret, 'exact': exact,
                'pend': pend, 'diff': diff, 'unresolved': unresolved}


def pick_best(cands, log):
    """When several objects define the same function, keep the best."""
    def key(c):
        return (c['diff'], c['pend'], c['exact'] * -1, c['obj'].base)
    cands = sorted(cands, key=key)
    best = cands[0]
    for loser in cands[1:]:
        if (loser['diff'], loser['pend']) != (best['diff'], best['pend']):
            log('  duplicate %s: keep %s (%d diff/%d pend), drop %s (%d diff/%d pend)'
                % (best['sym']['name'], best['obj'].base, best['diff'],
                   best['pend'], loser['obj'].base, loser['diff'], loser['pend']))
    return best


# --------------------------------------------------------------------------
# stage 4/5: image assembly + diff
# --------------------------------------------------------------------------

PROV_RETAIL, PROV_EXACT, PROV_PEND, PROV_DIFF, PROV_GEN = 0, 1, 2, 3, 4
PROVNAME = {PROV_RETAIL: 'retail-copied', PROV_EXACT: 'matched-exact',
            PROV_PEND: 'matched-reloc-pending', PROV_DIFF: 'reconstructed-diff',
            PROV_GEN: 'generated-metadata'}


def find_veneer_region(d, seg, lo, hi):
    w = lambda a: match.retail_words(d, seg, a, 1)[0]
    a = lo
    while a + 12 < hi:
        if w(a) == 0x03E00008 and w(a + 4) == 0 and w(a + 8) == 0x03E00008 and w(a + 12) == 0:
            break
        a += 4
    else:
        return None, None
    end = a
    while end + 8 <= hi and w(end) == 0x03E00008 and w(end + 4) == 0:
        end += 8
    return a, min(end, hi)


def grep_documented_offsets():
    """module+0xNNN / ctx+0xNNN offsets from the grind notes (results/*.md)."""
    found = defaultdict(set)
    pat = re.compile(r'(?:module|ctx|g_pad[A-Za-z]*|\+)\+?\s*0x([0-9A-Fa-f]{2,5})\b')
    for f in glob.glob(os.path.join(ROOT, 'results', '*.md')):
        batch = os.path.splitext(os.path.basename(f))[0]
        for line in open(f, errors='replace'):
            for m in re.finditer(r'(?:module|ctx)\+0x([0-9A-Fa-f]+)', line):
                off = int(m.group(1), 16)
                if off <= 0x20000:
                    found[off].add(batch)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-compile', action='store_true',
                    help='reuse existing build/link/*.o')
    ap.add_argument('--no-retail', action='store_true',
                    help='generate 100%% from source-derived material: no retail '
                         'bytes flow into the output (veneer/export/stub/modinfo/'
                         'rodata from tools/link/meta.py+rodata.py, ph2 relocation '
                         'table from tools/link/reltab.py, ELF/program headers from '
                         'fields). Default path unchanged.')
    ap.add_argument('--out', default=os.path.join(LINK, 'threadman-linked.prx'))
    args = ap.parse_args()

    lines = []

    def log(s=''):
        print(s)
        lines.append(s)

    os.makedirs(LINK, exist_ok=True)
    if not args.no_compile:
        log('== stage 1: compile all tm*.c in etch container ==')
        srcs, objs = compile_all(log)
        log('compiled %d sources -> %d objects' % (len(srcs), len(objs)))
    else:
        objs = sorted(glob.glob(os.path.join(LINK, '*.o')))
        log('== stage 1: skipped (--no-compile), %d objects == ' % len(objs))
        srcs = []
    for o in objs:
        Obj(o)  # parse check

    retail = open(RETAIL, 'rb').read()
    p = prxmod.parse(RETAIL)
    seg_off, seg_vaddr, seg_filesz = p['seg_off'], p['seg_vaddr'], p['seg_filesz']
    seg_end = seg_vaddr + seg_filesz
    if args.no_retail:
        image = bytearray(seg_filesz)          # zeros: zero-fill IS the generator
    else:
        image = bytearray(retail[seg_off:seg_off + seg_filesz])
    prov = bytearray(len(image))

    # ---- inventory + link ----
    log()
    log('== stage 2/3: inventory + link at retail addresses ==')
    linker = Linker([Obj(o) for o in objs], log)
    byname = defaultdict(list)
    for obj in linker.objs:
        for sym in obj.functions():
            addr = linker.addr_for_name(sym['name'])
            if addr is None:
                log('  symbol %s in %s: no known address, skipped' % (sym['name'], obj.base))
                continue
            byname[sym['name']].append((obj, sym))
    funcs = []
    for name, cands in byname.items():
        cls = [linker.classify(obj, sym, linker.addr_for_name(name)) for obj, sym in cands]
        funcs.append(pick_best(cls, log))
    funcs.sort(key=lambda f: f['addr'])

    placed = []
    for f in funcs:
        a, n = f['addr'], len(f['words'])
        if a + 4 * n > seg_end:
            log('  !! %s at 0x%05X overruns segment' % (f['sym']['name'], a))
        for (pa, pn, pname) in placed:
            if not (a + 4 * n <= pa or pa + 4 * pn <= a):
                log('  !! placement overlap: %s@0x%X+%dw vs %s@0x%X+%dw'
                    % (f['sym']['name'], a, n, pname, pa, pn))
        placed.append((a, n, f['sym']['name']))
        for i, w in enumerate(f['words']):
            o = a + 4 * i - seg_vaddr
            if f['retail'][i] == w:
                pr = PROV_EXACT
            elif f['status'][i]:
                pr = PROV_PEND
            else:
                pr = PROV_DIFF
            image[o:o + 4] = struct.pack('<I', w)
            prov[o:o + 4] = bytes([pr]) * 4

    if args.no_retail:
        # generated metadata tail: veneers, export tables, import stub tables,
        # SceModuleInfo, rodata (see tools/link/meta.py + rodata.py)
        map_json = meta.load_map(ROOT)
        tail = meta.build_tail(map_json)
        for f in funcs:
            assert f['addr'] + 4 * len(f['words']) <= meta.TEXT_END, \
                'function %s overlaps metadata region' % f['sym']['name']
        image[meta.TEXT_END:] = tail
        prov[meta.TEXT_END:] = bytes([PROV_GEN]) * len(tail)
        for lo, hi in ((0x2F8, 0x300), (0x654, 0x680)):   # generated zero-fill
            prov[lo:hi] = bytes([PROV_GEN]) * (hi - lo)
        log('metadata tail generated from inventory: 0x%X..0x%X (%d B, '
            'byte-diff vs retail: %d)' % (meta.TEXT_END, seg_end, len(tail),
            sum(1 for a, b in zip(tail, retail[seg_off + meta.TEXT_END:seg_off + seg_end]) if a != b)))

    n_exact = sum(f['exact'] for f in funcs)
    n_pend = sum(f['pend'] for f in funcs)
    n_diff = sum(f['diff'] for f in funcs)
    full = [f for f in funcs if f['diff'] == 0]
    part = [f for f in funcs if f['diff'] != 0]

    log('functions linked: %d  (%d words exact, %d reloc-pending, %d diff)'
        % (len(funcs), n_exact, n_pend, n_diff))
    log('  fully matched (all words exact or reloc-pending): %d' % len(full))
    log('  partial (has real diffs): %d' % len(part))
    for f in part:
        log('    PARTIAL %-44s 0x%05X %4dw  %d diff %d pend  [%s]'
            % (f['sym']['name'], f['addr'], len(f['words']), f['diff'], f['pend'],
               f['obj'].base))
    if any(f['unresolved'] for f in funcs):
        allun = sorted({u for f in funcs for u in f['unresolved']})
        log('  unresolved relocation symbols: %s' % ', '.join(allun))

    # ---- data image ----
    log()
    log('== stage 4: unified module-data image ==')
    data_map = {}     # offset -> [(src, tc, name, size)]
    max_off = 0
    for obj in linker.objs:
        for name, (val, size) in obj.data_syms.items():
            off = linker.unified_off(obj, name)
            data_map.setdefault(off, []).append((obj.src, obj.tc, name, size))
            max_off = max(max_off, off + size)
    data_image = bytearray(max_off)
    with open(os.path.join(LINK, 'data_image.map'), 'w') as mf:
        for off in sorted(data_map):
            for src, tc, name, size in data_map[off]:
                mf.write('+0x%05X  %-28s %-10s %5d  (%s)\n' % (off, name, src, size, tc))
    open(os.path.join(LINK, 'data_image.bin'), 'wb').write(data_image)
    doc = grep_documented_offsets()
    touched = {t for t in linker.touched if t < max_off}
    log('unified data model spans +0x0000..+0x%05X (%d symbol placements from %d objects)'
        % (max_off, sum(len(v) for v in data_map.values()), len(linker.objs)))
    log('module-data anchor offsets (LO16 relocations) referenced by linked code: %d'
        % len(touched))

    # ---- regions + diff ----
    log()
    log('== stage 5: region diff vs orig/threadman.prx ==')
    v_lo, v_hi = find_veneer_region(linker.retail_d, linker.retail_seg, 0x18000, p['ent_top'])
    regions = [
        ('text (code)', seg_vaddr, v_lo),
        ('import veneers (patched at load)', v_lo, 0x18830),
        ('pad', 0x18830, p['ent_top']),
        ('export tables (ent_top..ent_end)', p['ent_top'], p['ent_end']),
        ('pad', p['ent_end'], p['stub_top']),
        ('import stubs (stub_top..stub_end)', p['stub_top'], p['stub_end']),
        ('pad', p['stub_end'], p['modinfo_v']),
        ('SceModuleInfo', p['modinfo_v'], p['modinfo_v'] + 52),
        ('rodata/data/strings/jump tables', p['modinfo_v'] + 52, seg_end),
    ]
    counts = {k: 0 for k in range(5)}
    log('%-38s %9s %8s %8s %8s %8s %8s' %
        ('region', 'bytes', 'exact', 'reloc', 'diff', 'copied', 'gen'))
    for name, lo, hi in regions:
        c = [0, 0, 0, 0, 0]
        for i in range(lo - seg_vaddr, hi - seg_vaddr):
            c[prov[i]] += 1
        for k in range(5):
            counts[k] += c[k]
        log('%-38s %9d %8d %8d %8d %8d %8d'
            % (name, hi - lo, c[PROV_EXACT], c[PROV_PEND], c[PROV_DIFF],
               c[PROV_RETAIL], c[PROV_GEN]))
    total = len(image)
    matched_bytes = counts[PROV_EXACT] + counts[PROV_PEND]
    gen_bytes = counts[PROV_GEN]
    log('%-38s %9d %8d %8d %8d %8d %8d'
        % ('TOTAL ph0', total, counts[PROV_EXACT], counts[PROV_PEND],
           counts[PROV_DIFF], counts[PROV_RETAIL], counts[PROV_GEN]))
    log('byte coverage of whole ph0 (0xC0..0x19F84 file = 0..0x19EC4 vaddr): '
        '%.2f%%  (exact %.2f%% + reloc-pending %.2f%% + generated %.2f%%)'
        % (100.0 * (matched_bytes + gen_bytes) / total,
           100.0 * counts[PROV_EXACT] / total,
           100.0 * counts[PROV_PEND] / total,
           100.0 * gen_bytes / total))
    tb = v_lo - seg_vaddr
    tc_ = [sum(1 for i in range(tb) if prov[i] == k) for k in range(5)]
    log('byte coverage of text region only (0..0x%X): %.2f%%  (%d exact + %d pend + %d gen of %d)'
        % (v_lo, 100.0 * (tc_[PROV_EXACT] + tc_[PROV_PEND] + tc_[PROV_GEN]) / tb,
           tc_[PROV_EXACT], tc_[PROV_PEND], tc_[PROV_GEN], tb))

    # ---- gaps in text ----
    addr2names = defaultdict(list)
    for k, v in linker.nmap.items():
        addr2names[v].append(k)
    log()
    log('== unmatched gaps in text (wave-11 target list) ==')
    gaps = []
    i = 0
    while i < v_lo:
        if prov[i] in (PROV_RETAIL, PROV_DIFF):
            j = i
            while j < v_lo and prov[j] in (PROV_RETAIL, PROV_DIFF):
                j += 1
            gaps.append((i, j))
            i = j
        else:
            i += 1
    matched_names = {f['sym']['name'] for f in full}
    matched_addrs = {f['addr'] for f in full}

    def names_in(lo, hi):
        out = []
        cand = sorted(set([a for a in KNOWN_INTERNALS if lo <= a < hi]
                          + [x for x in addr2names if lo <= x < hi]))
        for aa in cand:
            if aa in addr2names:
                out.append('%s @0x%05X' % (','.join(sorted(addr2names[aa])), aa))
            else:
                out.append('%s @0x%05X' % (KNOWN_INTERNALS[aa], aa))
        return out

    with open(os.path.join(LINK, 'gaps.txt'), 'w') as gf:
        for a, b in gaps:
            gf.write('0x%05X-0x%05X  %5d bytes  %s\n'
                     % (a, b, b - a, '; '.join(names_in(a, b)) or '(anonymous internal code)'))
    for a, b in gaps:
        log('  gap 0x%05X-0x%05X  %5d bytes  %s'
            % (a, b, b - a, '; '.join(names_in(a, b)) or '(anonymous internal code)'))

    # wave-11 grind list: unmatched exports first (with size estimates from
    # the next known anchor), then unmatched named internals.  An export is
    # covered when a matched function sits at its address even under another
    # name (batches transcribe some exports as sub_XXXXX for vdiff).
    anchors = sorted(set(list(linker.nmap.values()) + list(KNOWN_INTERNALS)
                         + [b for _a, b in gaps]))
    log()
    log('== wave-11 grind list ==')
    unexp = []
    for k, v in sorted(linker.nmap.items(), key=lambda kv: kv[1]):
        if v not in matched_addrs and v < v_lo:
            nxt = next((x for x in anchors if x > v), seg_end)
            unexp.append((k, v, nxt - v))
    log('unmatched exports: %d (of %d NIDs with located addresses)' % (len(unexp), len(linker.nmap)))
    for k, v, sz in unexp:
        log('  0x%05X  ~%4d B  %s' % (v, sz, k))
    unint = [(KNOWN_INTERNALS[a], a) for a in sorted(KNOWN_INTERNALS)
             if a not in matched_addrs and a < v_lo]
    log('unmatched named internals: %d' % len(unint))
    for nm, a in unint:
        log('  0x%05X  %s' % (a, nm))

    # documented-offset honoring: every byte-exact word already carries the
    # retail immediates, so a documented offset is honored if it appears as a
    # 16-bit immediate field anywhere in linked code (disp off an anchored
    # register) or as a resolved LO16 anchor value.
    imms = set()
    for f in funcs:
        for w in f['words']:
            imms.add(w & 0xFFFF)
    doc = grep_documented_offsets()
    doc_hit = [o for o in sorted(doc) if o in touched or (o & 0xFFFF) in imms]
    doc_miss = [o for o in sorted(doc) if o not in doc_hit]
    log()
    log('module-data offsets documented in results/*.md: %d; appearing as '
        'immediates in linked code: %d' % (len(doc), len(doc_hit)))
    if doc_miss:
        log('  documented offsets with no immediate occurrence (unused by the '
            'currently-linked code): %s' % ', '.join('+0x%X' % o for o in doc_miss))

    # write function table
    with open(os.path.join(LINK, 'functions.tsv'), 'w') as tf:
        tf.write('addr\twords\texact\treloc\tdiff\tstatus\tobject\tname\n')
        for f in funcs:
            st = 'EXACT' if f['diff'] == 0 and f['pend'] == 0 else \
                 ('RELOC-PENDING' if f['diff'] == 0 else 'PARTIAL')
            tf.write('0x%05X\t%d\t%d\t%d\t%d\t%s\t%s\t%s\n'
                     % (f['addr'], len(f['words']), f['exact'], f['pend'],
                        f['diff'], st, f['obj'].base, f['sym']['name']))

    # ---- output ELF ----
    if args.no_retail:
        badrel, relcnts = reltab.verify(reltab.RECORDS, bytes(image), seg_end, None)
        log('ph2 relocation inventory vs generated image: %d anomalies, '
            'types %s' % (len(badrel), relcnts))
        if badrel:
            for b in badrel[:10]:
                log('  RELOC-ANOMALY: %s' % b)
        relseg = reltab.encode(reltab.RECORDS, bytes(image))
        map_json = meta.load_map(ROOT)
        out = meta.assemble_prx(bytes(image), relseg, map_json['entry'])
        src_note = ('--no-retail: ELF/phdr scaffolding, metadata tail and ph2 '
                    'relocation table all GENERATED; no retail bytes copied '
                    'into the output')
    else:
        out = bytearray(retail)
        out[seg_off:seg_off + seg_filesz] = image
        src_note = 'retail-bytes base (default mode)'
    with open(args.out, 'wb') as of:
        of.write(out)
    # provenance-auditable twin: everything not reconstructed is zeroed, so
    # the byte-diff against retail equals exactly the coverage numbers above
    recon = bytearray(len(image))
    for i, pv in enumerate(prov):
        if pv in (PROV_EXACT, PROV_PEND, PROV_DIFF, PROV_GEN):
            recon[i] = image[i]
    with open(os.path.join(LINK, 'threadman-recon-only.bin'), 'wb') as rf:
        rf.write(recon)
    diff_recon = sum(1 for a, b in zip(recon, retail[seg_off:seg_off + seg_filesz]) if a != b)
    zeroed_equal = counts[PROV_RETAIL] - diff_recon
    same_full = sum(1 for a, b in zip(out, retail) if a == b)
    log()
    log('wrote %s (%d bytes; identical to retail: %s -- %s)'
        % (args.out, len(out), 'yes' if same_full == len(retail) else 'no', src_note))
    log('wrote build/link/threadman-recon-only.bin (non-reconstructed bytes zeroed: '
        '%d differ from retail, %d copied bytes were already zero)'
        % (diff_recon, zeroed_equal))

    with open(os.path.join(LINK, 'report.txt'), 'w') as rf:
        rf.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
