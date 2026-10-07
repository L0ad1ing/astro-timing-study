"""Map (chapter, first verse number) -> book page from the OCR'd Saravali (vol. I book page = PDF page - 4; vol. II
book page = PDF page + 361), write rules/saravali/pages.py and check the pages cited by rules/saravali_*.jsonl.
Usage: python scripts/saravali_versemap.py"""
import re, json, glob
from pathlib import Path
D = Path(__file__).resolve().parents[1] / 'data' / 'sources' / 'saravali'
VOLS = [('saravali_v1_ocr.txt', -4), ('saravali_v2_ocr.txt', 361)]
CHAPTER = re.compile(r'^[\s‘\x27\x22|_]*Chapter\s*(\d+)(\s+(?:[A-Z][a-z]|\(\w)|\s*$)')      # title on the same line or the next
VERSE = re.compile(r"^[‘'_ =.~-]*(\d+)\s*(?:-\s*(\d+))?\s*[.,]+\s+\S")
LISTY = re.compile(r"^[A-Z][a-z]+(\s+[A-Za-z]+){0,2}\s*[:—~-]")


def scan(text, offset, vm):
    ch, pg, last = 0, None, 0
    for l in text.split('\n'):
        m = re.match(r'=== PAGE (\d+) ===', l)
        if m:
            pg = int(m.group(1)) + offset
            continue
        m = CHAPTER.match(l)
        if m:
            ch, last = int(m.group(1)), 0
            continue
        if not l.strip():
            continue
        m = VERSE.match(l)
        if m and ch:
            a = int(m.group(1)); b = int(m.group(2) or a)
            if b < a:                                   # OCR slip such as '74-16.' for '74-76.'
                b = a
            # verse numbers only increase within a chapter; numbered lists and tables in the notes are skipped
            rest = l[m.end() - 1:].strip()
            listy = bool(LISTY.match(rest)) or len(l.strip()) < 25
            if 0 < a <= 200 and b - a < 25 and a > last and a - last <= 12 and not listy:
                for v in range(a, b + 1):
                    vm.setdefault((ch, v), pg)
                last = b


vm = {}
for fname, offset in VOLS:
    if (D / fname).exists():
        scan((D / fname).read_text(encoding='utf-8'), offset, vm)
# verse headings the OCR mangled ('25:30.', '» 31-36.', a heading with no number, '41-12.' for '11-12.'):
# pages read off the scan's page markers at those headings (2026-10-04)
OVERRIDES = {(25, 25, 30): 310, (25, 31, 36): 311, (25, 37, 42): 313, (25, 43, 48): 314, (25, 49, 54): 315,
             (25, 55, 60): 317, (25, 61, 66): 318, (26, 1, 2): 319, (26, 11, 12): 327, (26, 31, 36): 338,
             (26, 55, 60): 342, (26, 61, 66): 343,
             # ch. 31: verse numbers lost after v. 41 (inferred from the four-verse pattern); pages at each pair's first line
             (31, 42, 45): 542, (31, 46, 46): 542, (31, 47, 50): 543, (31, 51, 54): 544, (31, 55, 58): 544, (31, 59, 62): 545,
             (31, 63, 66): 546, (31, 67, 70): 546, (31, 71, 74): 547, (31, 75, 78): 548, (31, 79, 82): 548, (31, 83, 86): 549,
             (31, 87, 87): 550, (33, 82, 82): 592,
             # ch. 48: no chapter heading in the OCR; pages at each sign's heading
             (48, 3, 6): 767, (48, 7, 9): 768, (48, 10, 13): 769, (48, 14, 17): 769, (48, 18, 21): 770, (48, 22, 25): 771,
             (48, 26, 29): 771, (48, 30, 33): 772, (48, 34, 37): 773, (48, 38, 41): 773, (48, 42, 45): 774, (48, 46, 49): 775}                 # ch. 33 v. 82 printed as '§2.'
for (c, a_, b_), p_ in OVERRIDES.items():
    for v in range(a_, b_ + 1):
        vm[(c, v)] = p_
# fill verses with no detected heading by the page of the nearest earlier verse of the chapter (verses run in order)
for c in sorted({k[0] for k in vm}):
    known = sorted(v for (cc, v) in vm if cc == c)
    for v in range(1, max(known) + 1):
        if (c, v) not in vm:
            prior = [u for u in known if u < v]
            if prior:
                vm[(c, v)] = vm[(c, max(prior))]


def write_pages(path):
    items = sorted(vm.items())
    body = ',\n'.join(f'    ({c}, {v}): {p}' for (c, v), p in items)
    Path(path).write_text(
        '"""Book page of each (chapter, verse) of Saravali (R. Santhanam tr., 1983; vol. I ch. 1-26, vol. II ch. 27-55), from\n'
        'the verse headings of the locally OCR\'d scans (scripts/saravali_versemap.py; vol. I page = PDF - 4, vol. II = PDF + 361;\n'
        'a verse whose heading the OCR missed takes the page of the nearest earlier verse; mangled headings set by hand from\n'
        'the scan). Numbers only - no text."""\nPAGES = {\n' + body + '\n}\n', encoding='utf-8')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    write_pages(root / 'rules' / 'saravali' / 'pages.py')
    bad = 0
    for f in sorted(glob.glob(str(root / 'rules' / 'saravali_*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            m = re.search(r'ch\. (\d+) v\. ([0-9]+)[^(]*\(.*p\. (\d+)\)', r['ref'])
            if not m:
                continue
            c, v, p = int(m.group(1)), int(m.group(2)), int(m.group(3))
            exp = vm.get((c, v))
            if exp is not None and abs(exp - p) > 1:
                bad += 1
                print(r['id'], 'cited', p, 'map', exp)
    print('chapters', sorted({c for c, v in vm}))
    print('mismatches (before rebuild)', bad, 'map size', len(vm))
