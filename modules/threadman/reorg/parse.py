#!/usr/bin/env python3
"""Parse tm*.c into top-level chunks with a real scanner (strings+comments aware)."""
import re, os, sys

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'match', 'threadman', 'batches')

def top_chunks(text):
    """Return list of (start, end) char ranges of top-level declarations."""
    n = len(text)
    i = 0
    depth_p = 0   # parens
    depth_b = 0   # braces
    starts = []
    chunk_start = 0
    while i < n:
        c = text[i]
        if c == '/' and i + 1 < n and text[i+1] == '/':
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == '/' and i + 1 < n and text[i+1] == '*':
            j = text.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        if c == '(':
            depth_p += 1
        elif c == ')':
            depth_p -= 1
        elif c == '{':
            depth_b += 1
        elif c == '}':
            depth_b -= 1
            if depth_b == 0 and depth_p == 0:
                # end of function/struct body
                starts.append((chunk_start, i + 1))
                chunk_start = i + 1
        elif c == ';' and depth_b == 0 and depth_p == 0:
            starts.append((chunk_start, i + 1))
            chunk_start = i + 1
        i += 1
    if chunk_start < n and text[chunk_start:].strip():
        starts.append((chunk_start, n))
    # normalize: strip leading whitespace/newlines into chunk
    return starts

KEYW = re.compile(r'^\s*(?:/\*.*?\*/\s*)*(typedef|extern|static|struct\s+\w+\s*;|enum|union|#)', re.S)

def chunk_kind(txt):
    t = txt.lstrip()
    while True:
        m = re.match(r'/\*.*?\*/\s*', t, re.S)
        if not m:
            break
        t = t[m.end():]
    if t.startswith('__asm__(') or t.startswith('asm('):
        return 'asm'
    if t.startswith('#'):
        return 'pre'
    if re.match(r'^(typedef|extern)\b', t):
        return 'decl'
    if t.startswith('static') and '{' not in strip_strings_comments(t):
        return 'decl'
    if re.match(r'^static\b', t):
        return 'static-def'   # static with initializer
    if '{' in txt and not txt.rstrip().endswith(';'):
        return 'func'
    return 'decl'

def strip_strings_comments(txt):
    out = []
    i = 0
    n = len(txt)
    while i < n:
        c = txt[i]
        if c == '/' and i + 1 < n and txt[i+1] == '/':
            j = txt.find('\n', i)
            i = n if j < 0 else j
        elif c == '/' and i + 1 < n and txt[i+1] == '*':
            j = txt.find('*/', i + 2)
            i = n if j < 0 else j + 2
        elif c == '"':
            out.append('" "')
            i += 1
            while i < n:
                if txt[i] == '\\':
                    i += 2
                    continue
                if txt[i] == '"':
                    i += 1
                    break
                i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)

def func_names(txt, kind):
    if kind == 'asm':
        return re.findall(r'\.globl\s+([A-Za-z0-9_$]+)', txt)
    if kind in ('func',):
        body = strip_strings_comments(txt)
        # header = up to first top-level '{'
        m = re.search(r'\{', body)
        hdr = body[:m.start()] if m else body
        ids = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', hdr)
        ids = [x for x in ids if x not in ('if','for','while','switch','sizeof','return')]
        return ids[-1:] if ids else []
    return []

def parse_file(path):
    text = open(path).read()
    chunks = []
    for s, e in top_chunks(text):
        txt = text[s:e]
        if not txt.strip():
            continue
        chunks.append({'s': s, 'e': e, 'text': txt, 'kind': chunk_kind(txt)})
    for c in chunks:
        c['names'] = func_names(c['text'], c['kind'])
    return text, chunks

if __name__ == '__main__':
    tot_blocks = 0
    tot_names = 0
    for f in sorted(os.listdir(DIR)):
        if not (f.startswith('tm') and f.endswith('.c')):
            continue
        text, chunks = parse_file(os.path.join(DIR, f))
        fn = [c for c in chunks if c['names']]
        tot_blocks += len(fn)
        tot_names += sum(len(c['names']) for c in fn)
        multis = [(c['names'], c['kind']) for c in fn if len(set(c['names'])) > 1]
        kinds = {}
        for c in chunks:
            kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
        print('%-10s chunks=%-3d kinds=%s fnblocks=%d names=%d' % (f, len(chunks), kinds, len(fn), sum(len(c['names']) for c in fn)))
        for names, kind in multis:
            print('   MULTI %s: %s' % (kind, names))
    print('TOTAL fn blocks=%d names=%d' % (tot_blocks, tot_names))
