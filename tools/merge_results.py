#!/usr/bin/env python3
"""Merge results/*.md batch reports into PROGRESS.md scoreboard tables.

Reads each results/*.md for status lines of the form
    MATCHED|LINK-MATCH|BLOCKED|UNFINISHED ... addr ... function
(any order; sees the '|'-separated table rows too) and rewrites the
'Matched' table in PROGRESS.md, preserving its Notes section.
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file)))
PROG = os.path.join(ROOT, 'PROGRESS.md')
SYM = {'MATCHED': '✅', 'LINK-MATCH': '🔗', 'BLOCKED': '⛔', 'UNFINISHED': '⬜'}

addr_re = re.compile(r'0x([0-9A-Fa-f]{4,6})')
name_re = re.compile(r'`?((?:sceKernel|_sceKernel|ThreadManForKernel|module_)[A-Za-z0-9_]+)`?')


def parse_reports():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'results', '*.md'))):
        batch = os.path.basename(path)
        for line in open(path):
            status = None
            for k in SYM:
                if k in line:
                    status = k
                    break
            if not status:
                continue
            a = addr_re.search(line)
            n = name_re.search(line)
            if a and n:
                out.append((int(a.group(1), 16), n.group(1), status, batch))
    return out


def main():
    rows = parse_reports()
    if not rows:
        print('no status rows found in results/'); sys.exit(1)
    seen = {}
    for addr, name, status, batch in sorted(rows):
        seen[(addr, name)] = (status, batch)
    table = ['| Addr | Size | Function | Status |',
             '|---|---|---|---|']
    for (addr, name), (status, batch) in sorted(seen.items()):
        table.append('| 0x%05X |  | `%s` | %s (%s) |' %
                     (addr, name, SYM[status], batch.replace('.md', '')))
    text = open(PROG).read()
    head = text[:text.index('## Matched')]
    rest = text[text.index('## Notes'):] if '## Notes' in text else ''
    open(PROG, 'w').write(
        head + '## Matched (' + str(len(seen)) + ')\n\n' +
        '\n'.join(table) + '\n\n' + rest)
    print('PROGRESS.md updated with %d rows' % len(seen))


if __name__ == '__main__':
    main()
