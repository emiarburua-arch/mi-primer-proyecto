import json, csv, io, sys, re

FILES = {
 'REAL_TPP_EA_n01': '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453611346.txt',
 'BACKTEST_CL':     '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453607816.txt',
 'REAL_E2T_2204':   '/root/.claude/projects/-home-user-mi-primer-proyecto/34cce73d-0c23-533e-95a7-ef3cccabda66/tool-results/mcp-Google_Drive-read_file_content-1786453586271.txt',
}

def rows_of(content):
    # section between 'Entrada de Datos ,' (2nd occurrence) and 'Detalle por bloques'
    idxs=[m.start() for m in re.finditer(r'Entrada de Datos ,', content)]
    start = idxs[-1] if idxs else 0
    end = content.find('Detalle por bloques', start)
    if end == -1: end = len(content)
    seg = content[start:end]
    return [r for r in seg.split(' ,')]

def parse(name, path):
    c = json.load(open(path))['fileContent']
    out=[]
    for r in rows_of(c):
        f = next(csv.reader(io.StringIO(r)))
        # a real trade row has a symbol at index 2 and a date at index 3
        if len(f) > 20 and f[2].strip() and re.match(r'\d{2}/\d{2}/\d{2}', f[3].strip() or ''):
            out.append(f)
    return out

for name, path in FILES.items():
    rows = parse(name, path)
    print('='*70)
    print(name, 'trades:', len(rows))
    if rows:
        print('sample:', rows[0])
        print('last  :', rows[-1])
