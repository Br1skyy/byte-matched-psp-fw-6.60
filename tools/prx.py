#!/usr/bin/env python3
"""PSP PRX parser: segments, SceModuleInfo, export tables -> NID/address map.

Usage: prx.py <file.prx> [--dump-exports] [--map out.json]
"""
import struct, sys, json, re


def parse(prx):
    d = open(prx, 'rb').read()
    (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
     e_ehsize, e_phentsize, e_phnum) = struct.unpack('<HHIIIIIHHH', d[16:46])
    ph = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        ph.append(struct.unpack('<8I', d[o:o+32]))
    typ, off, vaddr, paddr, filesz, memsz, fl, al = ph[0]
    base = vaddr
    # file offset <-> vaddr within first load segment
    def v2f(v): return off + v - base

    # Locate SceModuleInfo structurally: p_paddr is a packer constant, not
    # the modinfo address. Kernel-PRX layout: attr(2) ver(2) name[28] gp(4)
    # ent_top(u32) ent_end(u32) stub_top(u32) stub_end(u32), all absolute
    # module vaddrs.
    mi = None
    for f in range(off, off + filesz - 52, 4):
        nm = d[f+4:f+32].split(b'\0')[0]
        if len(nm) < 4 or not all(32 <= c < 127 for c in nm):
            continue
        gp, et, ee, st, se = struct.unpack('<IIIII', d[f+32:f+52])
        if gp == 0:
            continue
        if not (base <= et < ee <= st < se <= base + filesz):
            continue
        mi = f
        break
    assert mi is not None, 'SceModuleInfo not found'
    attr = struct.unpack('<H', d[mi:mi+2])[0]
    name = d[mi+4:mi+32].split(b'\0')[0].decode('ascii', 'replace')
    gp, ent_top, ent_end, stub_top, stub_end = struct.unpack('<IIIII', d[mi+32:mi+52])
    seg_end_v = base + filesz
    return {
        'data': d, 'entry': e_entry, 'flags': e_flags,
        'seg_off': off, 'seg_vaddr': base, 'seg_filesz': filesz,
        'modinfo_v': base + mi - off, 'mi': mi, 'attr': attr, 'name': name, 'gp': gp,
        'ent_top': ent_top, 'ent_end': ent_end,
        'stub_top': stub_top, 'stub_end': stub_end,
        'v2f': v2f, 'seg_end_v': seg_end_v,
    }


def parse_exports(p):
    """Locate export entries by scanning for name-pointers, then parse each
    as: name u32, flags u32, ver u16, fcount u8, x u8, table u32.
    Table = [NID * fcount] then [ADDR * fcount]."""
    d = p['data']
    v2f = p['v2f']
    lo = v2f(p['ent_top'])
    hi = v2f(max(p['ent_end'], p['ent_top'] + 0x40))
    seg_end_v = p['seg_vaddr'] + p['seg_filesz']
    libs = []
    off = lo
    def try_entry(off):
        nameoff, flags = struct.unpack('<II', d[off:off+8])
        fcount = d[off+10]
        tableoff = struct.unpack('<I', d[off+12:off+16])[0]
        if not (0 < fcount < 256):
            return None
        if not (p['seg_vaddr'] < tableoff < seg_end_v):
            return None
        name = None
        if nameoff:
            if not (p['seg_vaddr'] < nameoff < seg_end_v):
                return None
            no = v2f(nameoff)
            z = d.find(b'\0', no, no+40)
            if z < 0 or not all(32 <= c < 127 for c in d[no:z]):
                return None
            name = d[no:z].decode('ascii')
        toff = v2f(tableoff)
        if toff + 8*fcount > lo and toff < hi and toff + 8*fcount > len(d):
            return None
        # NID block length: scan until a run of small values (addresses)
        nid_count = 0
        while nid_count < 512:
            w = struct.unpack('<I', d[toff+4*nid_count:toff+4*nid_count+4])[0]
            if w < 0x10000:
                break
            nid_count += 1
        nids = [struct.unpack('<I', d[toff+4*i:toff+4*i+4])[0] for i in range(nid_count)]
        if nid_count < fcount:
            return None      # fewer NIDs than claimed entries -> misparse
        addrs = [struct.unpack('<I', d[toff+4*nid_count+4*i:toff+4*nid_count+4*i+4])[0] for i in range(fcount)]
        # NB: address 0 is legal (a function CAN sit at segment vaddr 0 --
        # clockgen's sceClockgenSetup does); nid_count >= fcount above is the
        # real guard against misparsed zero tables.
        if not all(0 <= a < seg_end_v for a in addrs):
            return None
        return {'name': name or 'syslib', 'flags': flags, 'fcount': fcount,
                'nids': nids, 'addrs': addrs, 'table_v': tableoff}
    while off + 16 <= hi:
        e = try_entry(off)
        if e:
            libs.append(e)
            off += 16
        else:
            off += 4
    return libs


def load_nid_names(exp_path):
    """name -> NID from a uofw exports.exp file."""
    names = {}
    for m in re.finditer(r'PSP_EXPORT_FUNC_NID\((\w+),\s*0x([0-9A-Fa-f]+)\)', open(exp_path).read()):
        names[m.group(1)] = int(m.group(2), 16)
    return names


# Standard syslib NIDs (fixed by the PSP module format; not present in any
# exports.exp because syslib entries use PSP_EXPORT_FUNC_HASH without NIDs).
# Without these the syslib exports land in the map as sub_<addr>.
SYSLIB_NIDS = {
    'module_start': 0xD632ACDB,
    'module_stop': 0xCEE8593C,
    'module_reboot_before': 0x2F064FA6,
    'module_reboot_phase': 0xADF12745,
    'module_bootstart': 0xD3744BE0,
    'module_reboot_start': 0xDCF1F72A,
    'module_info': 0xF01D73A7,
    'module_sdk_version': 0x11B97506,
}


def build_map(prx_path, exp_path):
    p = parse(prx_path)
    libs = parse_exports(p)
    nid2name = {v: k for k, v in SYSLIB_NIDS.items()}
    if exp_path:
        for k, v in load_nid_names(exp_path).items():
            nid2name[v] = k
    out = {'module': p['name'], 'entry': p['entry'], 'libs': []}
    for lib in libs:
        addrs = lib['addrs']
        funcs = []
        for nid, a in zip(lib['nids'], addrs):
            nm = nid2name.get(nid, 'sub_%08X' % a if a else 'NOADDR')
            funcs.append({'nid': '%08X' % nid, 'name': nm, 'addr': a})
        out['libs'].append({'name': lib['name'], 'funcs': funcs})
    return out, p


if __name__ == '__main__':
    prx = sys.argv[1]
    exp = sys.argv[2] if len(sys.argv) > 2 else None
    m, p = build_map(prx, exp)
    if '--dump-exports' in sys.argv:
        print(json.dumps(m, indent=1))
    for lib in m['libs']:
        print(f"== {lib['name']} ({len(lib['funcs'])} funcs) ==")
        for f in sorted(lib['funcs'], key=lambda x: x['addr']):
            print(f"  0x{f['addr']:05X} {f['name']}")
    out = [a for a in sys.argv if a.endswith('.json')]
    if out:
        json.dump(m, open(out[-1], 'w'), indent=1)
        print(f"wrote {out[-1]}")
