#!/usr/bin/env python3
"""Emit family files (sema.c, evf.c, ... ) from the pristine batch blocks.

Source of truth: match/threadman/batches/tm*.c (verbatim copies of the
per-batch grind sources).  Output: match/threadman/<fam>.c + threadman.h.

Transformations (mission landmines 1-4):
  L1 asm labels deduped by prefixing the defining function's name; renames
     applied ONLY inside C string-literal content.
  L4 one `static u8 g_pad[0x40]` anchored at +0 per family (renaming every
     g_padXX reference in string content AND C bodies); the family files
     that need typed +0x40 statics declare them (LogCtx for util.c,
     Ctx *g_ctxPtr for callback.c); the three drift statics are declared
     with pad prefixes and stay covered by DATA_OVERRIDES (rekeyed).
Duplicate definitions are resolved to the baseline link winners:
  sceKernelUSec2SysClock -> tm_e.c copy (tm_a copy dropped)
  _sceKernelReturnFromCallback -> tm_a.c copy (tm_oo copy dropped)
"""
import os, re, sys, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BATCH = os.path.join(ROOT, 'match', 'threadman', 'batches')
OUT = os.path.join(ROOT, 'match', 'threadman')
PLAN = '/tmp/split_final.json'

# baseline link winners for the two cross-batch duplicate definitions
PREFER = {'sceKernelUSec2SysClock': 'tm_e.c',
          '_sceKernelReturnFromCallback': 'tm_a.c'}

# ------------------------------------------------------------------ scanner

def top_chunks(text):
    n = len(text); i = 0; dp = db = 0; cs = 0; out = []
    while i < n:
        c = text[i]
        if c == '/' and text.startswith('//', i):
            j = text.find('\n', i); i = n if j < 0 else j; continue
        if c == '/' and text.startswith('/*', i):
            j = text.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == '\\': i += 2; continue
                if text[i] == '"': i += 1; break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if text[i] == '\\': i += 2; continue
                if text[i] == "'": i += 1; break
                i += 1
            continue
        if c == '(': dp += 1
        elif c == ')': dp -= 1
        elif c == '{': db += 1
        elif c == '}':
            db -= 1
            if db == 0 and dp == 0:
                out.append((cs, i + 1)); cs = i + 1
        elif c == ';' and db == 0 and dp == 0:
            out.append((cs, i + 1)); cs = i + 1
        i += 1
    if cs < n and text[cs:].strip():
        out.append((cs, n))
    return out

def strip_cm(txt):
    out = []; i = 0; n = len(txt)
    while i < n:
        c = txt[i]
        if c == '/' and txt.startswith('//', i):
            j = txt.find('\n', i); i = n if j < 0 else j
        elif c == '/' and txt.startswith('/*', i):
            j = txt.find('*/', i + 2); i = n if j < 0 else j + 2
        elif c == '"':
            out.append('" "'); i += 1
            while i < n:
                if txt[i] == '\\': i += 2; continue
                if txt[i] == '"': i += 1; break
                i += 1
        else:
            out.append(c); i += 1
    return ''.join(out)

def chunk_kind(txt):
    t = txt.lstrip()
    while True:
        m = re.match(r'/\*.*?\*/\s*', t, re.S)
        if not m: break
        t = t[m.end():]
    if t.startswith(('__asm__(', 'asm(')): return 'asm'
    if t.startswith('#'): return 'pre'
    if t.startswith(('typedef', 'extern')): return 'decl'
    if t.startswith('static'):
        return 'static-def' if '{' in strip_cm(txt) and not txt.rstrip().endswith((';', '}')) else 'decl'
    if '{' in txt and not txt.rstrip().endswith(';'): return 'func'
    return 'decl'

def fn_names(txt, kind):
    if kind == 'asm':
        return re.findall(r'\.globl\s+([A-Za-z0-9_$]+)', txt)
    if kind in ('func', 'static-def'):
        body = strip_cm(txt)
        m = re.search(r'\{', body)
        hdr = body[:m.start()] if m else body
        ids = [x for x in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', hdr)
               if x not in ('if', 'for', 'while', 'switch', 'sizeof', 'return')]
        return ids[-1:] if ids else []
    return []

def parse_file(path):
    text = open(path).read()
    chunks = []
    for s, e in top_chunks(text):
        txt = text[s:e]
        if not txt.strip(): continue
        k = chunk_kind(txt)
        chunks.append({'text': txt, 'kind': k, 'names': fn_names(txt, k)})
    return chunks

# ------------------------------------------------------- string-literal work

def iter_strings(text):
    """Yield (start, end) spans of C string literals (quotes inclusive)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '/' and text.startswith('//', i):
            j = text.find('\n', i); i = n if j < 0 else j; continue
        if c == '/' and text.startswith('/*', i):
            j = text.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == '\\': j += 2; continue
                if text[j] == '"': break
                j += 1
            yield (i, j + 1)
            i = j + 1
            continue
        i += 1

def sub_in_strings(text, pat, repl):
    out = []; last = 0
    for s, e in iter_strings(text):
        out.append(text[last:s])
        inner = text[s + 1:e - 1]
        inner = pat.sub(repl, inner)
        out.append('"' + inner + '"')
        last = e
    out.append(text[last:])
    return ''.join(out)

def sub_in_code(text, pat, repl):
    """Sub outside strings and comments (applies to C bodies)."""
    spans = list(iter_strings(text))
    # also blank comments
    def build():
        res = []; last = 0; i = 0; n = len(text)
        while i < n:
            c = text[i]
            if c == '/' and text.startswith('//', i):
                j = text.find('\n', i); j = n if j < 0 else j
                res.append(text[last:i]); last = j; i = j; continue
            if c == '/' and text.startswith('/*', i):
                j = text.find('*/', i + 2); j = n if j < 0 else j + 2
                res.append(text[last:i]); last = j; i = j; continue
            if c == '"':
                j = i + 1
                while j < n:
                    if text[j] == '\\': j += 2; continue
                    if text[j] == '"': break
                    j += 1
                i = j + 1; continue
            i += 1
        res.append(text[last:])
        return ''.join(res)
    return pat.sub(repl, build())

def asm_content(text):
    """Concatenated (unescaped) asm string content of a block."""
    parts = []
    for s, e in iter_strings(text):
        raw = text[s + 1:e - 1]
        raw = raw.replace('\\n', '\n').replace('\\t', ' ').replace('\\"', '"')
        raw = raw.replace('\\\\', '\\')
        parts.append(raw)
    return '\n'.join(parts)

# ------------------------------------------------------------------- gather

def load_addresses():
    """name -> retail addr from the baseline link's functions.tsv."""
    addr = {}
    tsv = os.path.join(ROOT, 'build', 'link', 'functions.tsv')
    for line in open(tsv).read().split('\n')[1:]:
        f = line.split('\t')
        if len(f) >= 8:
            addr[f[7]] = int(f[0], 16)
    return addr

def main():
    plan = json.load(open(PLAN))
    fam_of = {n: fam for fam, ns in plan.items() for n in ns}
    addr = load_addresses()

    blocks = {}          # primary name -> dict(text, names, file)
    for f in sorted(os.listdir(BATCH)):
        if not (f.startswith('tm') and f.endswith('.c')): continue
        for c in parse_file(os.path.join(BATCH, f)):
            if not c['names']: continue
            primary = c['names'][0]
            want = PREFER.get(primary)
            if primary in blocks:
                if want and f == want:
                    blocks[primary] = dict(c, file=f)
                continue
            if want and f != want:
                continue
            blocks[primary] = dict(c, file=f)
    missing = [n for n in fam_of if n not in blocks]
    if missing:
        print('FATAL: plan names with no block:', missing); sys.exit(1)

    # label census per family (labels defined in asm string content)
    fam_label_owners = defaultdict(lambda: defaultdict(list))
    for name, c in blocks.items():
        if c['kind'] != 'asm': continue
        content = asm_content(c['text'])
        labs = set(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*):', content))
        labs -= set(c['names']) - set()   # keep globals out via per-block check
        for L in labs:
            fam_label_owners[fam_of[name]][L].append(name)

    roster = defaultdict(list)
    src = {}
    for fam, members in plan.items():
        for m in members:
            if m in blocks:
                roster[fam].append(m)
                src[m] = blocks[m]['file']

    # ---------------------------------------------------- emit family files
    os.makedirs(OUT, exist_ok=True)
    blockmap = {}
    for fam in sorted(plan):
        members = roster[fam]
        L = []
        L.append('/* %s — threadman byte-match family file (regenerated from' % fam)
        L.append(' * the per-batch grind sources by reorg/emit.py; per-block')
        L.append(' * provenance in reorg/blockmap.json). */')
        L.append('#include "threadman.h"')
        L.append('')
        # -- statics
        st = []
        if any(re.search(r'\bg_pad[A-Za-z0-9_]*\b', blocks[m]['text']) for m in members):
            st.append('static u8 g_pad[0x40];            /* module +0x000 anchor */')
        if fam == 'util.c':
            st += ['static LogCtx g_logCtx;             /* module +0x040 */',
                   'static u8   g_padB[0x810 - 0x48];    /* nominal +0x048 */',
                   'static u32  g_systemStatusFlag;      /* retail +0x810 (DATA_OVERRIDES) */',
                   'static u8   g_pad2[0x17840 - 0x818]; /* to +0x17840 */',
                   'static u32  g_pad17840;              /* +0x17840 */',
                   'static u32  g_d366[2];               /* retail +0x17844 (DATA_OVERRIDES) */']
        elif fam == 'thread.c':
            st += ['static u8 g_padB[0x838 - 0x40];      /* to +0x838 */',
                   'static u32 g_deadThreadHandler;      /* retail +0x838 */']
        elif fam == 'callback.c':
            st.append('static Ctx *g_ctxPtr;             /* module +0x040 */')
        if st:
            L.append('/* ---- unified module-data anchors ---- */')
            L.extend(st)
            L.append('')
        # -- blocks in retail address order
        def block_key(m):
            return min(addr.get(n, 0xFFFFFF) for n in blocks[m]['names'])
        for m in sorted(members, key=block_key):
            c = blocks[m]
            text = c['text'].rstrip('\n')
            # L4: pad renames (string content AND C bodies)
            padpat = re.compile(r'\bg_pad[A-Za-z0-9_]+\b')
            text = sub_in_strings(text, padpat, 'g_pad')
            text = sub_in_code(text, padpat, 'g_pad')
            # L1: label dedup with the defining function's name as prefix
            if c['kind'] == 'asm':
                content = asm_content(text)
                labs = set(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*):', content))
                labs -= set(c['names'])          # never rename global symbols
                for lab in sorted(labs):
                    owners = [o for o in fam_label_owners[fam].get(lab, [])
                              if o in members]
                    if len(owners) > 1:          # collides inside this family
                        new = '%s_%s' % (m, lab)
                        text = sub_in_strings(text, re.compile(r'\b%s\b' % re.escape(lab)), new)
            L.append(text)
            L.append('')
            blockmap[m] = c['file']
        open(os.path.join(OUT, fam), 'w').write('\n'.join(L) + '\n')

    # ---------------------------------------------------------- threadman.h
    extern_src = defaultdict(list)
    for f in sorted(os.listdir(BATCH)):
        if not (f.startswith('tm') and f.endswith('.c')): continue
        raw = open(os.path.join(BATCH, f)).read()
        raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
        for mm in re.finditer(r'extern\s+[^;{}]+;', raw):
            d = ' '.join(mm.group(0).split())
            nm = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', d)
            if nm:
                extern_src[nm[0]].append(d)
    h = []
    h.append('/* threadman.h — shared types and module-internal externs for the')
    h.append(' * family files (sema.c, evf.c, ...) of the threadman byte-match')
    h.append(' * grind.  Regenerated by reorg/emit.py; see results/REORG.md. */')
    h.append('#ifndef THREADMAN_H')
    h.append('#define THREADMAN_H')
    h.append('')
    h.append('typedef unsigned char u8;')
    h.append('typedef unsigned short u16;')
    h.append('typedef unsigned int u32;')
    h.append('typedef unsigned long long u64;')
    h.append('typedef int s32;')
    h.append('')
    h.append('typedef void (*TmLogHandler)(u32 msgno, u32 k1_keyword, u32 nextra, ...);')
    h.append('')
    h.append('/* TCB view (merged union of the batch C/D/DD variants; fields to +0x30). */')
    h.append('typedef struct {')
    h.append('    u32 unk00, unk04;')
    h.append('    u32 id;               /* +0x08 */')
    h.append('    u32 unk0c;')
    h.append('    u32 currentPriority;  /* +0x10 */')
    h.append('    u32 attr;             /* +0x14 bit31=user */')
    h.append('    u32 unk18, unk1c;')
    h.append('    u32 stackSize1;       /* +0x20 */')
    h.append('    u32 unk24;            /* +0x24 */')
    h.append('    u32 unk28;            /* +0x28 */')
    h.append('    u32 stackCheck;       /* +0x2C */')
    h.append('    u32 stackTop;         /* +0x30 */')
    h.append('} SceThread;')
    h.append('')
    h.append('/* module+0x40 region views (log context / current-thread record). */')
    h.append('typedef struct { u32 pad0, pad4; void *handler; } LogCtx;')
    h.append('typedef struct { u8 pad[0x18]; u32 v; } CtxInner;')
    h.append('typedef struct {')
    h.append('    u8 pad[0x24];')
    h.append('    CtxInner *inner;      /* +0x24 */')
    h.append('    u8 pad2[0x58];')
    h.append('    u32 out;              /* +0x80 */')
    h.append('} Ctx;')
    h.append('')
    h.append('/* module-internal veneers (0x18680..0x187E8, load-patched) and')
    h.append(' * helpers: jal words stay relocation-covered (family floor). */')
    for nm in sorted(extern_src):
        h.append(extern_src[nm][-1])
    h.append('')
    h.append('#endif /* THREADMAN_H */')
    open(os.path.join(OUT, 'threadman.h'), 'w').write('\n'.join(h) + '\n')

    json.dump(blockmap, open(os.path.join(HERE, 'blockmap.json'), 'w'), indent=1, sort_keys=True)
    print('emitted %d family files + threadman.h; %d blocks' % (len(plan), len(blocks)))
    for fam in sorted(plan):
        print('  %-12s %3d funcs' % (fam, len(roster[fam])))

if __name__ == '__main__':
    main()
