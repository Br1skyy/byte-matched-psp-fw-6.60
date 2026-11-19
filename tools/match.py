#!/usr/bin/env python3
"""Byte-match harness: compile C with the Sony-equivalent GCC 3.3.6 toolchain
and diff each exported function against retail firmware bytes, reloc-aware.

Usage:
  match.py file.c [more.c ...]        # compile + compare all mapped functions
  match.py --disas 0xADDR [WORDS]     # show retail disassembly at address
  match.py --list [pattern]           # list mapped functions
  match.py --module NAME ...          # select module (default: threadman)

Supported modules (see tools/README-MODULES.md):
  threadman  (default; unchanged legacy behavior)
  clockgen   (kd/clockgen.prx from the retail dump)

Word categories per function:
  ok      exact word match
  reloc   differing word but relocation covers the field (HI16/LO16 imm,
          jump target) -> will match once data layout / link matches
  DIFF    real mismatch
"""
import struct, sys, os, json, subprocess, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Multi-module support: each module names its retail PRX and its
# NID/name/address map. The threadman entry is EXACTLY the legacy pair
# (same paths, same behavior when --module is not given).
def _first_existing(*paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[-1]


MODULES = {
    'threadman': {
        'prx': os.path.join(ROOT, 'orig', 'threadman.prx'),
        'map': os.path.join(ROOT, 'orig', 'threadman-map.json'),
    },
    'clockgen': {
        # module-local orig/ first (repo workspace pattern), else the dump
        'prx': _first_existing(os.path.join(ROOT, 'orig', 'clockgen.prx'),
                               os.path.expanduser('~/Downloads/psp-fw660/EBOOT/F0/kd/clockgen.prx')),
        # live tree keeps it beside the sources; repo workspaces check it
        # in under map/ (with exports.exp)
        'map': _first_existing(os.path.join(ROOT, 'match', 'clockgen', 'clockgen-map.json'),
                               os.path.join(ROOT, 'map', 'clockgen-map.json')),
    },
}
PRX = MODULES['threadman']['prx']
MAP = MODULES['threadman']['map']
BUILD = os.path.join(ROOT, 'build')
TC = '/tc/prefix336'          # inside container
FLAGS = ['-O3', '-mips2', '-G0', '-mabi=eabi']

R = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']


def load_retail():
    d = open(PRX, 'rb').read()
    phoff, = struct.unpack('<I', d[28:32])
    phnum, = struct.unpack('<H', d[44:46])
    seg = None
    for i in range(phnum):
        o = phoff + i*32
        typ, off, vaddr, paddr, filesz, memsz, fl, al = struct.unpack('<8I', d[o:o+32])
        if typ == 1:
            seg = (off, vaddr, filesz)
            break
    return d, seg


def retail_words(d, seg, addr, n):
    off, vaddr, filesz = seg
    fo = off + addr - vaddr
    return list(struct.unpack('<%dI' % n, d[fo:fo+4*n]))


def name_map():
    m = json.load(open(MAP))
    out = {}
    for lib in m['libs']:
        for f in lib['funcs']:
            # NB: address 0 is a real placement (clockgen's sceClockgenSetup
            # sits at segment vaddr 0); threadman has no zero-addr entries.
            if f['addr'] is not None:
                out[f['name']] = f['addr']
    return out


def compile_srcs(srcs):
    os.makedirs(BUILD, exist_ok=True)
    objs = []
    for s in srcs:
        base = os.path.splitext(os.path.basename(s))[0]
        objs.append(os.path.join(BUILD, '%s.o' % base))
    script = ['set -e']
    for s, o in zip(srcs, objs):
        ro, rt = os.path.relpath(s, ROOT), os.path.relpath(o, ROOT)
        script.append('%s/bin/mipsel-elf-gcc -c %s -o /tm/%s /tm/%s' %
                      (TC, ' '.join(FLAGS), rt, ro))
    cmd = 'mkdir -p /tc/prefix336/mipsel-elf/bin; for t in as ar ld nm ranlib; do ln -sf /tc/prefix/bin/mipsel-elf-$t /tc/prefix336/mipsel-elf/bin/$t; done; export PATH=/tc/prefix/bin:$PATH; ' + ' && '.join(script)
    r = subprocess.run(['podman', 'run', '--rm',
                        '-v', TC_LC() + ':/tc:Z',
                        '-v', ROOT + ':/tm:Z', 'etch386',
                        'sh', '-c', cmd], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:]); print(r.stderr[-2000:])
        sys.exit(1)
    return objs


def TC_LC():
    return os.path.join(os.path.dirname(ROOT), 'toolchain-build')


def parse_obj(path):
    d = open(path, 'rb').read()
    e_shoff, = struct.unpack('<I', d[32:36])
    e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHH', d[46:52])
    shs = []
    for i in range(e_shnum):
        o = e_shoff + i*e_shentsize
        name, typ, flags, addr, off, size, link, info, align, ent = struct.unpack('<10I', d[o:o+40])
        shs.append({'name': name, 'type': typ, 'off': off, 'size': size,
                    'link': link, 'entsize': ent, 'info': info})
    def sname(n):
        st = shs[e_shstrndx]
        o = st['off'] + n
        return d[o:d.index(b'\0', o)].decode()
    for s in shs:
        s['sname'] = sname(s['name'])
    # symbols
    syms = []
    for s in shs:
        if s['sname'] == '.symtab':
            strtab = shs[s['link']]
            for i in range(s['size'] // 16):
                o = s['off'] + i*16
                nm, val, sz, info, other, shndx = struct.unpack('<IIIBBH', d[o:o+16])
                no = strtab['off'] + nm
                name = d[no:d.index(b'\0', no)].decode()
                typ = info & 0xf
                if typ == 2 and sz > 0 and shs[shndx]['sname'] == '.text':
                    syms.append({'name': name, 'off': val, 'size': sz})
    # relocations on .text
    relocs = {}   # word offset in .text -> True
    for s in shs:
        if s['sname'].startswith('.rel.text'):
            for i in range(s['size'] // 8):
                o = s['off'] + i*8
                r_off, r_info = struct.unpack('<II', d[o:o+8])
                rtype = r_info & 0xff
                # 1=HI16 (shift16), 2=LO16, 4=26, 6=GPREL16... all affect low bits
                relocs[r_off] = rtype
    text = None
    for s in shs:
        if s['sname'] == '.text':
            text = s
    return text, syms, relocs, d


def mask_for(rtype, word):
    if rtype == 4 or rtype == 11:      # R_MIPS_26 family
        return word & 0xFC000000
    if rtype in (1, 2, 5, 6):          # 16-bit immediate fields
        return word & 0xFFFF0000
    return 0


def compare(nm, nm_addr, objs):
    d, seg = load_retail()
    for o in objs:
        text, syms, relocs, od = parse_obj(o)
        for sym in syms:
            if sym['name'] != nm:
                continue
            n = sym['size'] // 4
            mine = list(struct.unpack('<%dI' % n,
                         od[text['off']+sym['off']:text['off']+sym['off']+4*n]))
            ret = retail_words(d, seg, nm_addr, n)
            ok = reloc = bad = 0
            detail = []
            for i in range(n):
                if mine[i] == ret[i]:
                    ok += 1
                elif relocs.get(sym['off'] + 4*i) is not None:
                    rt = relocs[sym['off'] + 4*i]
                    if mask_for(rt, mine[i]) == mask_for(rt, ret[i]):
                        reloc += 1
                    else:
                        bad += 1
                        detail.append((i, ret[i], mine[i], 'reloc-struct'))
                else:
                    bad += 1
                    detail.append((i, ret[i], mine[i], ''))
            tag = '*** MATCH ***' if bad == 0 and reloc == 0 else \
                  ('match (reloc)' if bad == 0 else 'DIFF')
            print('%-44s 0x%05X %3d words  %s' % (nm, nm_addr, n, tag))
            if reloc:
                print('    %d word(s) differ only in relocated fields (layout-dependent)' % reloc)
            for i, rv, mv, note in detail[:8]:
                print('    +%03d  retail %08X  mine %08X  %s' % (4*i, rv, mv, note))
            if len(detail) > 8:
                print('    ... %d more mismatches' % (len(detail)-8))
            return bad == 0
    print('%-44s not found in objects' % nm)
    return False


def set_module(name):
    """Point the harness at another module's PRX + map (mutates the module
    globals so load_retail()/name_map()/--disas all follow)."""
    global PRX, MAP
    if name not in MODULES:
        sys.exit('unknown module %r (have: %s)' % (name, ', '.join(sorted(MODULES))))
    PRX, MAP = MODULES[name]['prx'], MODULES[name]['map']


def main():
    args = sys.argv[1:]
    if '--module' in args:
        i = args.index('--module')
        if i + 1 >= len(args):
            sys.exit('--module needs a name')
        set_module(args[i + 1])
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        return
    nm = name_map()
    if args[0] == '--list':
        pat = args[1] if len(args) > 1 else ''
        for k in sorted(nm, key=nm.get):
            if pat in k:
                print('0x%05X %s' % (nm[k], k))
        return
    if args[0] == '--disas':
        addr = int(args[1], 16)
        n = int(args[2]) if len(args) > 2 else 8
        d, seg = load_retail()
        for i, w in enumerate(retail_words(d, seg, addr, n)):
            print('0x%05X: %08X' % (addr + 4*i, w))
        return
    objs = compile_srcs([os.path.abspath(a) for a in args])
    d, seg = load_retail()
    seen = set()
    allok = True
    for o in objs:
        _, syms, _, _ = parse_obj(o)
        for sym in syms:
            if sym['name'] in nm and sym['name'] not in seen:
                seen.add(sym['name'])
                allok &= compare(sym['name'], nm[sym['name']], objs)
    if not seen:
        print('(no mapped export functions found in objects)')
    sys.exit(0 if allok else 1)


if __name__ == '__main__':
    main()
