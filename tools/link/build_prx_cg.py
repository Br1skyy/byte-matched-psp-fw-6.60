#!/usr/bin/env python3
"""Full-module PRX link for the CLOCKGEN byte-match grind.

    python3 tools/link/build_prx_cg.py [--no-compile] [--no-retail]

Sibling of build_prx.py (threadman pipeline untouched; this file shares
nothing with it but the etch container pattern and tools/link/reltab.py's
A1 stream format knowledge).

Stages
  1. compile match/clockgen/{cg.c,cg_asm.c} with prefix336 (GCC 3.3.6)
  2. place every mapped function at its retail address inside the ph0
     image (vaddr 0..0x8E8), resolving:
       R_MIPS_26   -> map addresses (module internals) or import-veneer
                     addresses (the 10 stubs at 0x6D4..0x723)
       HI16/LO16   -> RW data model (g_Cy27040@+0, g_ClockGenSysEv@+0x10,
                     ph1-relative, matching the stored retail words) and
                     the .rodata anchor ("SceClockgen" @0x8D8)
  3. fill the rest of ph0: import veneers, export/import entries, NID
     tables, strings, SceModuleInfo -- GENERATED in both modes (they are
     plain words from the inventory below); --no-retail additionally
     generates the ph1 RW image from cg.o's .data initializers and the
     ph2 relocation stream via the calibrated A1 codec (RECORDS_CG +
     class tables = the parsed retail stream; every delta/lo16/class is
     re-derived from the generated image; round-trip against retail is
     asserted) and assembles the ELF from header fields.  Default mode
     copies the retail file and splices only the linked text.
  4. emit build/link-cg/clockgen-linked.prx and diff per region vs
     orig retail kd/clockgen.prx.

Provenance of the embedded inventories (same standing as the map JSON):
  * FUNC addresses: match/clockgen/clockgen-map.json (tools/prx.py output)
  * import-veneer layout, NID tables, entry flags/counts, modinfo
    constants, ELF header fields: structural parse of the retail module
    (documented in match/clockgen/results/results.md)
  * RECORDS_CG + FTBL/TTBL/FIMAP/TIMAP: reltab.decode() of the retail ph2
    stream; the ORDER and index assignment are Sony ld's, the content is
    re-derived from our own image and byte-verified against retail.
"""
import glob
import json
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import match  # noqa: E402  (read-only reuse)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import reltab  # noqa: E402  (A1 stream format)

LINK = os.path.join(ROOT, 'build', 'link-cg')


def _first_existing(*paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[-1]


MAP_JSON = _first_existing(os.path.join(ROOT, 'match', 'clockgen', 'clockgen-map.json'),
                           os.path.join(ROOT, 'map', 'clockgen-map.json'))

TC = '/tc/prefix336'
GCC_FLAGS = '-O3 -mips2 -G0 -mabi=eabi'


def retail_path():
    """module-local orig/ first (repo workspace pattern), else the dump"""
    p = os.path.join(ROOT, 'orig', 'clockgen.prx')
    return p if os.path.exists(p) else os.path.expanduser(
        '~/Downloads/psp-fw660/EBOOT/F0/kd/clockgen.prx')

# ---------------------------------------------------------------------------
# module layout (retail kd/clockgen.prx)
SEG_END = 0x8E8          # ph0 size
TEXT_END = 0x6D4         # end of code / start of import veneers
PH1_OFF, PH1_VADDR, PH1_SIZE = 0x990, 0x8F0, 0x50
REL_OFF, REL_SIZE = 0x9E0, 0x134
PH0_OFF, PHDRS_END, PH0_ALIGN = 0xA0, 0x94, 0x10
ELF = dict(e_type=65440, e_machine=8, e_entry=0x2B4, e_flags=0x10A23001,
           e_phoff=0x34, e_phnum=3)
MODINFO_V = 0x7A0
ENT_TOP, ENT_END = 0x734, 0x754
STUB_TOP, STUB_END = 0x75C, 0x79C
MODULE_ATTR_VER = 0x01091007        # attr 0x1007 | ver 0x0109
MODULE_GP = 0x8040
MODULE_NAME = b'sceClockgen_Driver\0'
SDK_WORD = 0x06060010

# import veneers: two words (jr ra; nop), load-patched; one per import
IMPORT_VENEERS = 10                 # 0x6D4..0x724

# import library inventory (structural parse of the retail stub tables):
#   (entry addr, name vaddr, counts word, NID-table vaddr, first stub, NIDs)
IMPORTS = [
    (0x75C, 0x7D8, 0x00050006, 0x8B0, 0x6D4,
     [0x0DDCD2C9, 0x6B30100F, 0xB011B11F, 0xB7D098C6, 0xF8170FBE]),   # ThreadManForKernel
    (0x774, 0x7F0, 0x00020005, 0x8D0, 0x714,
     [0xCD9E4BB5, 0xD7D3FDCD]),                                       # SceSysEventForKernel
    (0x788, 0x80C, 0x00030005, 0x8C4, 0x6FC,
     [0x47BDEAAA, 0x62C7E1E4, 0x8CBD8CCF]),                           # SceI2c_driver
]

# extern symbol -> veneer address (call sites resolve here)
STUBS = {
    'sceKernelTryLockMutex': 0x6D4, 'sceKernelUnlockMutex': 0x6DC,
    'sceKernelLockMutex': 0x6E4, 'sceKernelCreateMutex': 0x6EC,
    'sceKernelDeleteMutex': 0x6F4, 'sceI2cMasterTransmitReceive': 0x6FC,
    'sceI2cSetClock': 0x704, 'sceI2cMasterTransmit': 0x70C,
    'sceKernelRegisterSysEventHandler': 0x714,
    'sceKernelUnregisterSysEventHandler': 0x71C,
}

# rodata anchors: the only .rodata object is the mutex-name string
RODATA_ANCHOR = 0x8D8               # "SceClockgen"

STR_THREADMAN = b'ThreadManForKernel\0'
STR_SYSEVENT = b'sceSysEventForKernel\0'
STR_I2C = b'sceI2c_driver\0'
STR_DRIVER = b'sceClockgen_driver\0'
STR_MUTEXNAME = b'SceClockgen\0'

SYSLIB_FLAGS = 0x80000000
SYSLIB_COUNTS = 0x00020204          # 2 funcs + 2 vars
DRIVER_FLAGS = 0x00010011
DRIVER_ENTRY_V = 0x744
SYSLIB_NIDTABLE_V = 0x81C
DRIVER_NIDTABLE_V = 0x850
# syslib table: [module_start, module_reboot_before] + var NIDs/addr slots
SYSLIB_NIDS = [0xD632ACDB, 0x2F064FA6, 0xF01D73A7, 0x11B97506]
SYSLIB_VAR_ADDRS = [MODINFO_V, 0x8E4]     # module_info, module_sdk_version

# ---------------------------------------------------------------------------
# ph2 relocation stream: parsed retail inventory + calibrated codec tables
# (tools/link/cg_reloc_inventory.json; see the module docstring)


def load_reloc_inventory():
    import json as _json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cg_reloc_inventory.json')
    inv = _json.load(open(path))
    recs = [tuple(r) for r in inv['records']]
    fimap = {tuple(int(x) for x in k.split(',')): v for k, v in inv['fimap'].items()}
    timap = {int(k): v for k, v in inv['timap'].items()}
    return recs, bytes(inv['ftbl']), bytes(inv['ttbl']), fimap, timap


def encode_relocs(records, image, ftbl, ttbl, fimap, timap):
    """Emit the A1 stream for `records` against `image` (delta/lo16/class
    re-derived; order + index assignment from the inventory)."""
    def word(off):
        return struct.unpack('<I', image[off:off + 4])[0]
    next_lo = [len(records)] * (len(records) + 1)
    for i in range(len(records) - 1, -1, -1):
        next_lo[i] = i if records[i][0] == 5 else next_lo[i + 1]
    out = bytearray(bytes([0, 0, 3, 3]) + ftbl + ttbl)
    prev_off = prev_typ = prev_lo = None
    for idx, rec in enumerate(records):
        if rec[0] == 'S':
            _, seg, base = rec
            out += struct.pack('<H', ((base & 0xFFF) << 4) | (seg << 3) | 1)
            prev_off = base
            continue
        typ, aseg, off = rec
        delta = off if prev_off is None else off - prev_off
        j = next_lo[idx + 1]
        lo16 = (word(records[j][2]) & 0xFFFF) if typ == 4 else 0
        mid = not (-255 <= delta <= 255)
        if typ in (6, 7):
            cls = 0
        elif typ == 4:
            cls = 2 if (prev_typ == 4 and prev_lo == lo16) else 1
        else:
            cls = 2
        fi = fimap[(cls, mid)]
        ti = timap[typ]
        if not mid:
            out += struct.pack('<H', ((delta & 0x1FF) << 7) | (ti << 4) | (aseg << 3) | fi)
            if cls == 1:
                out += struct.pack('<H', lo16)
        else:
            out += struct.pack('<H', (((delta >> 16) & 0x1FF) << 7) | (ti << 4) | (aseg << 3) | fi)
            out += struct.pack('<H', delta & 0xFFFF)
            if cls == 1:
                out += struct.pack('<H', lo16)
        prev_off, prev_typ, prev_lo = off, typ, lo16
    return bytes(out)


# ---------------------------------------------------------------------------
# object parsing (needs reloc symbol names, which match.py discards)

class Obj:
    def __init__(self, path):
        self.path = path
        self.base = os.path.basename(path)
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
                                        'type': info & 0xf, 'shndx': shndx})
        self.text = None
        self.relocs = {}
        self.data_syms = {}
        for i, s in enumerate(shs):
            if s['sname'] == '.text':
                self.text = s
            elif s['sname'].startswith('.rel.text'):
                for i2 in range(s['size'] // 8):
                    o = s['off'] + i2 * 8
                    r_off, r_info = struct.unpack('<II', d[o:o + 8])
                    self.relocs[r_off] = (r_info & 0xff, r_info >> 8)
            elif s['sname'] in ('.data', '.bss'):
                for sym in self.symtab:
                    if sym['shndx'] == i and sym['name'] and not sym['name'].startswith('.'):
                        self.data_syms.setdefault(sym['name'], (sym['val'], sym['size']))
        assert self.text is not None

    def text_words(self, off, size):
        o = self.text['off'] + off
        return list(struct.unpack('<%dI' % (size // 4), self.d[o:o + size]))

    def data_bytes(self):
        for s in self.shs:
            if s['sname'] == '.data':
                return self.d[s['off']:s['off'] + s['size']]
        return b''

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


def sx16(x):
    return x - 0x10000 if x & 0x8000 else x


# ---------------------------------------------------------------------------

def compile_srcs(log):
    os.makedirs(LINK, exist_ok=True)
    srcs = ['match/clockgen/cg.c', 'match/clockgen/cg_asm.c']
    script = []
    for s in srcs:
        base = os.path.splitext(os.path.basename(s))[0]
        script.append('%s/bin/mipsel-elf-gcc -c %s %s -o build/link-cg/%s.o'
                      % (TC, GCC_FLAGS, s, base))
    cmd = ('mkdir -p /tc/prefix336/mipsel-elf/bin; '
           'for t in as ar ld nm ranlib; do '
           'ln -sf /tc/prefix/bin/mipsel-elf-$t /tc/prefix336/mipsel-elf/bin/$t; done; '
           'export PATH=/tc/prefix/bin:$PATH; cd /tm; ' + ' && '.join(script))
    r = subprocess.run(['podman', 'run', '--rm',
                        '-v', os.path.join(os.path.dirname(ROOT), 'toolchain-build') + ':/tc:Z',
                        '-v', ROOT + ':/tm:Z', 'etch386', 'sh', '-c', cmd],
                       capture_output=True, text=True)
    if r.returncode:
        log(r.stdout[-2000:] + r.stderr[-2000:])
        sys.exit(1)
    return [os.path.join(LINK, 'cg.o'), os.path.join(LINK, 'cg_asm.o')]


def link_functions(objs, nmap, log):
    """Resolve relocations and return {addr: words} + stats."""
    out = {}
    stats = {'exact': 0, 'pend': 0, 'diff': 0}
    retail_d, seg = match.load_retail()
    funcs = []
    for obj in objs:                     # objs: already-parsed Obj instances
        for sym in obj.functions():
            if sym['name'] in nmap:
                funcs.append((obj, sym, nmap[sym['name']]))
    placed = []
    for obj, sym, addr in funcs:
        off, size = sym['val'], sym['size']
        n = size // 4
        words = obj.text_words(off, size)
        relocs = {r: v for r, v in obj.relocs.items() if off <= r < off + size}
        pending_hi, ahi_stack, last_ahi = [], [], None
        pend = 0

        def sym_value(symidx):
            if symidx == 0:
                return 0
            s = obj.symtab[symidx]
            nm = s['name']
            if nm in nmap:
                return nmap[nm]
            if nm in STUBS:
                return STUBS[nm]
            if nm in obj.data_syms:
                return obj.data_syms[nm][0]        # ph1-relative (0 / 0x10)
            if nm == '.rodata':
                return RODATA_ANCHOR               # "SceClockgen"
            if nm in ('.text', '.data', '.bss'):
                return 0
            raise KeyError('unresolvable symbol %r' % nm)

        def flush_hi(V, idxs):
            hi = ((V - sx16(V & 0xFFFF)) >> 16) & 0xFFFF
            for wi in idxs:
                words[wi] = (words[wi] & 0xFFFF0000) | hi
        for r_off in sorted(relocs):
            rtype, symidx = relocs[r_off]
            wi = (r_off - off) // 4
            w = words[wi]
            S = sym_value(symidx)
            if rtype == 5:                          # R_MIPS_HI16
                pending_hi.append(wi)
                ahi_stack.append(w & 0xFFFF)
                last_ahi = w & 0xFFFF
            elif rtype == 6:                        # R_MIPS_LO16
                ahi = ahi_stack[-1] if ahi_stack else (last_ahi or 0)
                V = (S + ((ahi << 16) + sx16(w & 0xFFFF))) & 0xFFFFFFFF
                words[wi] = (w & 0xFFFF0000) | (V & 0xFFFF)
                if pending_hi:
                    flush_hi(V, pending_hi)
                    pending_hi, ahi_stack = [], []
            elif rtype == 4:                        # R_MIPS_26
                tgt = (S + ((w & 0x3FFFFFF) << 2)) & 0xFFFFFFFF
                words[wi] = (w & 0xFC000000) | ((tgt >> 2) & 0x3FFFFFF)
            elif rtype == 2:                        # R_MIPS_32
                words[wi] = (S + w) & 0xFFFFFFFF
            else:
                raise ValueError('reloc type %d unhandled' % rtype)
        assert not pending_hi, 'dangling HI16'
        ret = match.retail_words(retail_d, seg, addr, n)
        for i, w in enumerate(words):
            if w == ret[i]:
                stats['exact'] += 1
            elif relocs.get(off + 4 * i):
                stats['pend'] += 1     # unresolved-vs-retail divergence
            else:
                stats['diff'] += 1
        placed.append((addr, n, sym['name'], obj.base))
        out[addr] = words
    placed.sort()
    for i, (a, n, nm, ob) in enumerate(placed):
        nxt = placed[i + 1][0] if i + 1 < len(placed) else TEXT_END
        if a + 4 * n > nxt:
            log('  !! overlap: %s@0x%X+%dw runs into 0x%X' % (nm, a, n, nxt))
    return out, stats


def generate_tail(map_json):
    """Metadata region TEXT_END..SEG_END as plain generated words."""
    img = bytearray(SEG_END - TEXT_END)

    def put(vaddr, blob):
        img[vaddr - TEXT_END:vaddr - TEXT_END + len(blob)] = blob

    # import veneers
    for i in range(IMPORT_VENEERS):
        put(TEXT_END + 8 * i, struct.pack('<II', 0x03E00008, 0))
    # export entries
    put(ENT_TOP, struct.pack('<IIII', 0, SYSLIB_FLAGS, SYSLIB_COUNTS, SYSLIB_NIDTABLE_V))
    put(DRIVER_ENTRY_V, struct.pack('<IIII',
                                    0x83C, DRIVER_FLAGS, 0x000C0004, DRIVER_NIDTABLE_V))
    # syslib table: 4 NIDs then 4 addresses (2 funcs + 2 vars)
    driver_funcs = next(l['funcs'] for l in map_json['libs'] if l['name'] == 'sceClockgen_driver')
    syslib_funcs = next(l['funcs'] for l in map_json['libs'] if l['name'] == 'syslib')
    start_addr = next(f['addr'] for f in syslib_funcs if f['name'] == 'module_start')
    reboot_addr = next(f['addr'] for f in syslib_funcs if f['name'] == 'module_reboot_before')
    put(SYSLIB_NIDTABLE_V, struct.pack('<8I', *SYSLIB_NIDS,
                                       start_addr, reboot_addr, *SYSLIB_VAR_ADDRS))
    # driver table: NIDs (map order) then addresses
    put(DRIVER_NIDTABLE_V,
        struct.pack('<%dI' % len(driver_funcs), *(int(f['nid'], 16) for f in driver_funcs))
        + struct.pack('<%dI' % len(driver_funcs), *(f['addr'] for f in driver_funcs)))
    # import NID tables + entries + strings
    for (ev, namev, counts, nidv, stub, nids) in IMPORTS:
        put(nidv, struct.pack('<%dI' % len(nids), *nids))
        put(ev, struct.pack('<IIIII', namev, DRIVER_FLAGS, counts, nidv, stub))
    put(0x7D8, STR_THREADMAN + b'\0' * ((-len(STR_THREADMAN)) % 4))
    put(0x7F0, STR_SYSEVENT + b'\0' * ((-len(STR_SYSEVENT)) % 4))
    put(0x80C, STR_I2C + b'\0' * ((-len(STR_I2C)) % 4))
    put(0x83C, STR_DRIVER + b'\0' * ((-len(STR_DRIVER)) % 4))
    put(0x8D8, STR_MUTEXNAME + b'\0' * ((-len(STR_MUTEXNAME)) % 4))
    put(0x8E4, struct.pack('<I', SDK_WORD))
    # SceModuleInfo
    mi = struct.pack('<HH', MODULE_ATTR_VER & 0xFFFF, MODULE_ATTR_VER >> 16)
    mi += MODULE_NAME + b'\0' * (28 - len(MODULE_NAME))
    mi += struct.pack('<IIIII', MODULE_GP, ENT_TOP, ENT_END, STUB_TOP, STUB_END)
    put(MODINFO_V, mi)
    return img


def assemble(ph0, ph1, relseg, entry):
    ehdr = struct.pack('<16sHHIIIIIHHHHHH',
                       b'\x7fELF\x01\x01\x01\x00' + b'\0' * 9,
                       ELF['e_type'], ELF['e_machine'], 1, entry, ELF['e_phoff'],
                       0, ELF['e_flags'], 52, 32, ELF['e_phnum'], 0, 0, 0)
    ph0_hdr = struct.pack('<8I', 1, PH0_OFF, 0, 0x80000000 + PH0_OFF + MODINFO_V,
                          len(ph0), len(ph0), 5, PH0_ALIGN)
    ph1_hdr = struct.pack('<8I', 1, PH1_OFF, PH1_VADDR, 0, len(ph1), len(ph1), 6, PH0_ALIGN)
    ph2_hdr = struct.pack('<8I', 0x700000A1, REL_OFF, 0, 0, len(relseg), 0, 0, PH0_ALIGN)
    out = bytearray(ehdr + ph0_hdr + ph1_hdr + ph2_hdr)
    out += b'\0' * (PH0_OFF - len(out))
    out += ph0
    out += b'\0' * (PH1_OFF - len(out))
    out += ph1
    out += b'\0' * (REL_OFF - len(out))
    out += relseg
    return bytes(out)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-compile', action='store_true')
    ap.add_argument('--no-retail', action='store_true',
                    help='generate 100%% from source-derived material '
                         '(ph1 from cg.o .data initializers, ph2 via the '
                         'calibrated A1 codec, ELF from fields)')
    args = ap.parse_args()
    lines = []

    def log(s=''):
        print(s)
        lines.append(s)

    os.makedirs(LINK, exist_ok=True)
    objs = sorted(glob.glob(os.path.join(LINK, '*.o')))
    if args.no_compile or not objs:
        log('== stage 1: compile cg.c + cg_asm.c (etch container) ==')
        objs = compile_srcs(log)
    else:
        log('== stage 1: reused %d objects ==' % len(objs))

    map_json = json.load(open(MAP_JSON))
    nmap = {}
    for lib in map_json['libs']:
        for f in lib['funcs']:
            nmap[f['name']] = f['addr']
    match.set_module('clockgen')        # retail word source for the diff stats

    log('== stage 2: link at retail addresses ==')
    objs = [Obj(o) if isinstance(o, str) else o for o in objs]
    func_words, stats = link_functions(objs, nmap, log)
    log('functions linked: %d  (%d words exact, %d reloc-site, %d diff)'
        % (len(func_words), stats['exact'], stats['pend'], stats['diff']))

    if args.no_retail:
        image = bytearray(SEG_END)
    else:
        retail = open(retail_path(), 'rb').read()
        image = bytearray(retail[PH0_OFF:PH0_OFF + SEG_END])
    for addr, words in func_words.items():
        for i, w in enumerate(words):
            image[addr + 4 * i:addr + 4 * i + 4] = struct.pack('<I', w)

    log('== stage 3: generate metadata tail 0x%X..0x%X ==' % (TEXT_END, SEG_END))
    image[TEXT_END:] = generate_tail(map_json)

    ph1 = None
    if args.no_retail:
        cg_o = Obj(os.path.join(LINK, 'cg.o'))
        ph1 = bytearray(cg_o.data_bytes())
        ph1 += b'\0' * (PH1_SIZE - len(ph1))
        assert len(ph1) == PH1_SIZE, len(ph1)
        log('ph1 RW image from cg.o .data initializers: %d bytes' % len(ph1))

    recs, ftbl, ttbl, fimap, timap = load_reloc_inventory()
    relseg = encode_relocs(recs, bytes(image), ftbl, ttbl, fimap, timap)
    retail = open(retail_path(), 'rb').read()
    rel_ok = relseg == retail[REL_OFF:REL_OFF + REL_SIZE]
    log('ph2 relocation stream: %d bytes, %d records, byte-identical to retail: %s'
        % (len(relseg), len(recs), rel_ok))
    if not rel_ok:
        for i, (a, b) in enumerate(zip(relseg, retail[REL_OFF:])):
            if a != b:
                log('  first ph2 diff at +%d: mine %02x retail %02x' % (i, a, b))
                break

    if args.no_retail:
        out = assemble(bytes(image), bytes(ph1), relseg, ELF['e_entry'])
        src_note = '--no-retail: ELF/phdr scaffolding, functions, metadata tail, ph1 data and ph2 stream all GENERATED'
    else:
        out = bytearray(retail)
        out[PH0_OFF:PH0_OFF + SEG_END] = image
        src_note = 'retail-bytes base (functions + generated tail spliced)'
    path = os.path.join(LINK, 'clockgen-linked.prx')
    open(path, 'wb').write(out)
    same = out == retail
    log('wrote %s (%d bytes; identical to retail: %s -- %s)'
        % (path, len(out), same, src_note))
    if not same:
        diffs = [i for i, (a, b) in enumerate(zip(bytes(out), retail)) if a != b]
        log('  %d differing bytes; first at 0x%X' % (len(diffs), diffs[0]))
        regions = [('ehdr+phdrs', 0, PH0_OFF), ('ph0 text', PH0_OFF, PH0_OFF + TEXT_END),
                   ('ph0 metadata', PH0_OFF + TEXT_END, PH0_OFF + SEG_END),
                   ('pad', PH0_OFF + SEG_END, PH1_OFF), ('ph1 data', PH1_OFF, PH1_OFF + PH1_SIZE),
                   ('pad2', PH1_OFF + PH1_SIZE, REL_OFF), ('ph2 reloc', REL_OFF, REL_OFF + REL_SIZE)]
        for nm, lo, hi in regions:
            n = sum(1 for i in range(lo, min(hi, len(out))) if out[i] != retail[i])
            log('  %-14s 0x%03X..0x%03X  %d differing bytes' % (nm, lo, hi, n))

    open(os.path.join(LINK, 'report.txt'), 'w').write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
