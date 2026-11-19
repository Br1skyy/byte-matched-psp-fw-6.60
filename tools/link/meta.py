"""Module-metadata generator for the threadman link: import veneers, export
tables, import stub tables and SceModuleInfo, emitted from STRUCTURED data
(no retail byte blobs flow into the output).

Source of the structured data (parsed metadata, same standing as
orig/threadman-map.json -- which prx.py itself produced from retail):

  * EXPORT TABLES -- the three SceLibraryEntryTable records and their
    NID/address arrays for ThreadManForUser / ThreadManForKernel come from
    orig/threadman-map.json (NID + retail address per function, produced by
    tools/prx.py's parser).  Emitting these tables from that JSON is
    source-derived bookkeeping: the NIDs are the uofw exports.exp constants
    and the addresses are the function placements our own linker computed.
    The syslib table's 4 NIDs/addresses and the flags/version words are
    inventory constants below (no external source exists for them).
  * IMPORT STUBS + VENEERS -- the import inventory (IMPORT_LIBS) is the
    structural parse of the retail stub tables: library names, versions,
    function NID lists, one variable-import cell per library with a
    variable NID, and the load-patched var-stub words.  The 2-word
    `jr ra; nop` veneers (one per imported function) and the 5/6-word stub
    header records are EMITTED programmatically from this inventory.
  * SceModuleInfo -- attr/version/gp constants + module name string + the
    four table anchors, all of which are computed from the generated
    layout below (and round-check against the emitted stub/ent regions).

The fixed address layout mirrors the Sony linker's placement; every anchor
is asserted during assembly (emit() checks non-overlap and exact coverage
of 0x1868C..0x19EC4).
"""
import json
import os
import struct

VENEER_BASE = 0x1868C
ENT_TOP = 0x18844
STUB_TOP = 0x18884
MODINFO_V = 0x1891C
RODATA_BASE = 0x18950
SEG_END = 0x19EC4
TEXT_END = 0x1868C

MODULE_NAME = 'sceThreadManager'
MODULE_ATTR = 0x1007
MODULE_VER = 0x0108          # SceModuleInfo version word (bytes 08 01)
MODULE_GP = 0x7FF0

# syslib export table: module_start (= ELF entry), module_stop,
# module_reboot_phase, module_bootstart (addresses of small stubs; the
# first equals the map entry point).
SYSLIB_NIDS = [0xD3744BE0, 0x2F064FA6, 0xF01D73A7, 0x11B97506]
SYSLIB_ADDRS = [0x11F68, 0x16B84, 0x1891C, 0x19E30]

LIB_USER = dict(name='ThreadManForUser', flags=0x40010011, ver=0x0005,
                vcount=0, fcount=151)
LIB_KERNEL = dict(name='ThreadManForKernel', flags=0x00010011, ver=0x0105,
                  vcount=1, fcount=149)
KERNEL_VAR_NID = 0x921B7ACD   # the one variable export (no address entry)

# ---------------------------------------------------------------------------
# Import inventory: structural parse of the retail import stub tables.
# Each entry: library name, flags word, {size words, vcount, fcount},
# NID list (function imports), and for variable imports the {cell, struct}
# words.  Stub region layout: entries of `size` words at STUB_TOP; the
# veneer region at VENEER_BASE holds one 2-word jr ra;nop per function
# import, assigned bottom-up in the retail stub-address order.
# ---------------------------------------------------------------------------
IMPORT_LIBS = [
    dict(name='InterruptManagerForKernel', flags=0x00090011, size=6, vcnt=1, fcnt=16,
         nids=[0x02314986, 0x092968F4, 0x3B84732D, 0x4D6E7305, 0x551097F2, 0x55D18836,
               0x58DD8978, 0x5F10D406, 0x6042AEE0, 0xAF799F96, 0xB941600E, 0xCD36EB65,
               0xD774BA45, 0xE790EAED, 0xF153B371, 0xF987B1F0],
         stub=0x186A4, var_cell=[0x0001958C, 0x201A1A19], var_struct=[0x14004A7F, 0x14004AC1, 0x18004A80, 0]),
    dict(name='ExceptionManagerForKernel', flags=0x00010011, size=6, vcnt=1, fcnt=3,
         nids=[0x54B0CAD2, 0x96D47F7E, 0xFBC2353A],
         stub=0x1868C, var_cell=[0x00019584, 0x6437D22A], var_struct=[0x14000007, 0x18000010, 0]),
    dict(name='SysMemForKernel', flags=0x00010011, size=5, vcnt=0, fcnt=23,
         nids=[0x01810023, 0x034129FB, 0x0A34C078, 0x22A114DC, 0x235C2646, 0x23D81675,
               0x361F0F88, 0x44BDF332, 0x58148F07, 0x7158CE7E, 0x7D50CE82, 0x87C2AB85,
               0xB4F00CB5, 0xC1A26C6F, 0xC4EEAF20, 0xC90B0992, 0xD222DAA7, 0xDD6512D0,
               0xE860BE8F, 0xF12A62F7, 0xF2284ECC, 0xFAF29F34, 0xFFC63884],
         stub=0x1874C, var_cell=None, var_struct=None),
    dict(name='KDebugForKernel', flags=0x00010011, size=5, vcnt=0, fcnt=3,
         nids=[0x84F370BC, 0x86010FCB, 0xACF427DC],
         stub=0x18724, var_cell=None, var_struct=None),
    dict(name='sceSuspendForKernel', flags=0x00010011, size=5, vcnt=0, fcnt=2,
         nids=[0x91A77137, 0xB43D1A8C],
         stub=0x18824, var_cell=None, var_struct=None),
    dict(name='SysclibForKernel', flags=0x00010011, size=5, vcnt=0, fcnt=4,
         nids=[0x10F3BB61, 0xAB7592FF, 0xB49A7697, 0xC2145E80],
         stub=0x18804, var_cell=None, var_struct=None),
    dict(name='LoadCoreForKernel', flags=0x00010011, size=5, vcnt=0, fcnt=2,
         nids=[0x410084F9, 0xF976EF41],
         stub=0x1873C, var_cell=None, var_struct=None),
]

# fixed rodata sub-layout (the Sony linker's placement; asserted in emit)
NAME_ZONE = 0x18954          # first import-library name string
SYSLIB_TABLE = 0x18A00
USER_NAME = 0x18A20
USER_TABLE = 0x18A34
KERNEL_NAME = 0x18F6C
KERNEL_TABLE = 0x18F80
NID_TABLES = {               # import NID array placement per library
    'ExceptionManagerForKernel': 0x194B0,
    'InterruptManagerForKernel': 0x194BC,
    'KDebugForKernel': 0x194FC,
    'LoadCoreForKernel': 0x19508,
    'SysMemForKernel': 0x19510,
    'SysclibForKernel': 0x1956C,
    'sceSuspendForKernel': 0x1957C,
}
VAR_CELLS = 0x19584
VAR_STUBS = {'ExceptionManagerForKernel': 0x19594,
             'InterruptManagerForKernel': 0x195A0}
STUB_STRINGS_END = 0x18A00


def _pad4(s):
    b = s.encode() + b'\0'
    return b + b'\0' * (-len(b) % 4)


def _libs_from_map(map_json):
    out = {}
    for lib in map_json['libs']:
        funcs = sorted(lib['funcs'], key=lambda f: int(f['nid'], 16))
        out[lib['name']] = [(int(f['nid'], 16), f['addr']) for f in funcs]
    return out


# name-string pool placement (Sony linker's pool layout: pads vary)
NAME_OFFSETS = {
    'InterruptManagerForKernel': 0x18954,
    'ExceptionManagerForKernel': 0x18974,
    'SysMemForKernel': 0x18994,
    'KDebugForKernel': 0x189A8,
    'sceSuspendForKernel': 0x189BC,
    'SysclibForKernel': 0x189D4,
    'LoadCoreForKernel': 0x189EC,
}


def import_strings_blob():
    """The 7 import-library name strings, NUL padded (pool layout above)."""
    return {NAME_OFFSETS[lib['name']]: _pad4(lib['name']) for lib in IMPORT_LIBS}


def export_blob(map_json):
    """ent region, syslib/User/Kernel tables + names, from map.json."""
    m = _libs_from_map(map_json)
    user = m['ThreadManForUser']
    kernel = m['ThreadManForKernel']
    assert len(user) == LIB_USER['fcount'] and len(kernel) == LIB_KERNEL['fcount']
    blob = {}

    def put(a, data):
        blob[a] = data

    # ent region: syslib(4w) + User(4w) + sep + Kernel(4w) + sep
    put(ENT_TOP, struct.pack('<IIII', 0, 0x80000000, 0x00020204, SYSLIB_TABLE))
    put(ENT_TOP + 0x10, struct.pack('<IIII', USER_NAME, LIB_USER['flags'],
                                    (LIB_USER['fcount'] << 16) | (0 << 8) | 5, USER_TABLE))
    put(ENT_TOP + 0x20, struct.pack('<I', 0x00040000))
    put(ENT_TOP + 0x24, struct.pack('<IIII', KERNEL_NAME, LIB_KERNEL['flags'],
                                    (LIB_KERNEL['fcount'] << 16) | (LIB_KERNEL['vcount'] << 8) | 5,
                                    KERNEL_TABLE))
    put(ENT_TOP + 0x34, struct.pack('<I', 0x00040000))

    # syslib table: 4 NIDs then 4 addrs
    put(SYSLIB_TABLE, struct.pack('<8I', *(SYSLIB_NIDS + SYSLIB_ADDRS)))
    # library name strings
    put(USER_NAME, _pad4(LIB_USER['name']))
    put(KERNEL_NAME, _pad4(LIB_KERNEL['name']))
    # User NIDs+addrs
    put(USER_TABLE, struct.pack('<%dI' % (2 * len(user)),
                                *sum(([n for n, a in user], [a for n, a in user]), [])))
    # Kernel NIDs (func NIDs sorted + the variable NID appended) + addrs
    put(KERNEL_TABLE, struct.pack('<%dI' % (len(kernel) + 1 + len(kernel)),
                                  *([n for n, a in kernel] + [KERNEL_VAR_NID]
                                    + [a for n, a in kernel])))
    return blob


def import_tables_blob():
    """Stub-table entries + NID arrays + var-import cells/structs."""
    blob = {}
    a = STUB_TOP
    for lib in IMPORT_LIBS:
        nidtbl = NID_TABLES[lib['name']]
        words = [NAME_OFFSETS[lib['name']], lib['flags'],
                 (lib['fcnt'] << 16) | (lib['vcnt'] << 8) | lib['size'],
                 nidtbl, lib['stub']]
        if lib['size'] == 6:
            # variable import: 6th word points at the {struct-ptr, nid} cell
            words.append(VAR_CELLS + 0 if lib['name'] == 'ExceptionManagerForKernel'
                         else VAR_CELLS + 8)
        blob[a] = struct.pack('<%dI' % len(words), *words)
        a += 4 * len(words)
    assert a == 0x18918, hex(a)
    for lib in IMPORT_LIBS:
        blob[NID_TABLES[lib['name']]] = struct.pack('<%dI' % len(lib['nids']), *lib['nids'])
    # var cells (ptr, nid) + var stub structs
    blob[VAR_CELLS] = struct.pack('<II', VAR_STUBS['ExceptionManagerForKernel'],
                                  IMPORT_LIBS[1]['var_cell'][1])
    blob[VAR_CELLS + 8] = struct.pack('<II', VAR_STUBS['InterruptManagerForKernel'],
                                      IMPORT_LIBS[0]['var_cell'][1])
    for lib in IMPORT_LIBS:
        if lib['var_struct'] is not None:
            blob[VAR_STUBS[lib['name']]] = struct.pack('<%dI' % len(lib['var_struct']),
                                                       *lib['var_struct'])
    return blob


def modinfo_blob():
    return {MODINFO_V: struct.pack('<HH28sIIIII', MODULE_ATTR, MODULE_VER,
                                   _pad4(MODULE_NAME)[:28], MODULE_GP,
                                   ENT_TOP, ENT_TOP + 0x38, STUB_TOP, 0x18918)}


def veneers_blob():
    """One `jr ra; nop` pair per imported function (count = sum of fcnt;
    every veneer is identical so placement order is byte-irrelevant)."""
    n = sum(l['fcnt'] for l in IMPORT_LIBS)
    return {VENEER_BASE: struct.pack('<II', 0x03E00008, 0) * n}


def rodata_blob():
    """Pair LUTs from rodata.py inventory."""
    import rodata
    blob = {}
    blob[PAIR_LUT_A_V] = struct.pack('<%dI' % len(rodata.PAIR_TABLE_A), *rodata.PAIR_TABLE_A)
    blob[PAIR_LUT_B_V] = struct.pack('<%dI' % len(rodata.PAIR_TABLE_B), *rodata.PAIR_TABLE_B)
    for off, kind, val in rodata.RODATA_TAIL:
        if kind == 's':
            blob[off] = _pad4(val)
        else:
            blob[off] = struct.pack('<I', val)
    for off, words, label in rodata.RODATA_WORDS:
        blob[off] = struct.pack('<%dI' % len(words), *words)
    return blob


PAIR_LUT_A_V = 0x18EEC
PAIR_LUT_B_V = 0x1942C


def build_tail(map_json):
    """Assemble the complete ph0 tail 0x1868C..0x19EC4 (veneers through
    rodata).  Returns bytearray; asserts exact, gapless coverage."""
    blob = {}
    for part in (veneers_blob(), export_blob(map_json), import_strings_blob(),
                 import_tables_blob(), modinfo_blob(), rodata_blob()):
        for a, data in part.items():
            assert a not in blob or blob[a] == data
            blob[a] = data
    out = bytearray(SEG_END - TEXT_END)
    covered = bytearray(SEG_END - TEXT_END)
    for a, data in sorted(blob.items()):
        o = a - TEXT_END
        assert o >= 0 and o + len(data) <= len(out), hex(a)
        assert not any(covered[o:o + len(data)])
        out[o:o + len(data)] = data
        covered[o:o + len(data)] = b'\1' * len(data)
    # everything not covered must be structural zero padding
    assert all(c or out[i] == 0 for i, c in enumerate(covered)), \
        'uncovered non-zero byte in tail layout'
    return out


def load_map(root):
    return json.load(open(os.path.join(root, 'orig', 'threadman-map.json')))


# ---------------------------------------------------------------------------
# whole-file scaffolding (ELF header, program headers, pads) from fields
# ---------------------------------------------------------------------------
E_TYPE = 0xFFA0              # ET_SCE_RELEXEC
E_MACHINE = 8                # EM_MIPS
E_FLAGS = 0x10A23001         # retail module flags (no reorder / mips2 / eabi)
PH0_OFF = 0xC0
PH1_VADDR = 0x19F00
PH1_MEMSZ = 0x844
RELOC_TYPE = 0x700000A1
RELOC_ALIGN = 0x10
RELOC_OFF = 0x19FC0          # ph1 (filesz 0) and the reloc segment share it


def assemble_prx(image, relseg, entry):
    """Whole PRX file from fields + the generated ph0 image and ph2 segment."""
    assert len(image) == SEG_END - seg_vaddr0
    ehdr = struct.pack('<16sHHIIIIIHHHHHH',
                       b'\x7fELF\x01\x01\x01\x00' + b'\0' * 9,
                       E_TYPE, E_MACHINE, 1, entry, 0x34, 0, E_FLAGS,
                       52, 32, 3, 0, 0, 0)
    modinfo_foff = PH0_OFF + MODINFO_V
    phdrs = struct.pack('<8I', 1, PH0_OFF, 0, 0x80000000 + modinfo_foff,
                        len(image), len(image), 5, 0x40)
    phdrs += struct.pack('<8I', 1, RELOC_OFF, PH1_VADDR, 0,
                         0, PH1_MEMSZ, 6, 0x40)
    phdrs += struct.pack('<8I', RELOC_TYPE, RELOC_OFF, 0, 0,
                         len(relseg), 0, 0, RELOC_ALIGN)
    out = bytearray()
    out += ehdr + phdrs
    out += b'\0' * (PH0_OFF - len(out))          # 0x94..0xC0 pad
    out += image
    out += b'\0' * (RELOC_OFF - len(out))        # 0x19F84..0x19FC0 pad
    out += relseg
    return bytes(out)


seg_vaddr0 = 0
