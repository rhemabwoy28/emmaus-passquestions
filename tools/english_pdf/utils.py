"""Reconstruct two-column BECE English PDF text with poppler bbox output."""
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

PDF = Path(os.environ.get('EMMAUS_ENG_PDF', ''))
BBOX = Path(os.environ.get('EMMAUS_ENG_BBOX', '/root/.hermes/cache/scratch/eng-bbox.xml'))
NS = '{http://www.w3.org/1999/xhtml}'


def ensure_bbox():
    pdf = Path(os.environ.get('EMMAUS_ENG_PDF', ''))
    if not pdf.exists():
        raise SystemExit('Set EMMAUS_ENG_PDF to the compiled BECE English PDF path.')
    if not BBOX.exists() or BBOX.stat().st_mtime < pdf.stat().st_mtime:
        BBOX.parent.mkdir(parents=True, exist_ok=True)
        with BBOX.open('wb') as f:
            subprocess.run(['pdftotext', '-bbox-layout', str(pdf), '-'], stdout=f, check=True)
    return ET.parse(BBOX).getroot()


def page_lines(root, page_no):
    """Return text lines in reading order: left column top-to-bottom, then right."""
    pages = root.findall(f'.//{NS}page')
    page = pages[page_no - 1]
    cols = {0: [], 1: []}
    for line in page.iter(f'{NS}line'):
        words = [w.text or '' for w in line.findall(f'{NS}word')]
        if not words:
            continue
        text = ' '.join(words)
        if 'complete set 1990' in text or 'complete practice book' in text.lower():
            continue
        if re.fullmatch(r'Page \d+', text.strip()):
            continue
        if re.search(r'PART [1-4] OF 4', text):
            continue
        if 'Independent BECE-style practice material' in text:
            continue
        xmin = float(line.get('xMin'))
        cols[0 if xmin < 300 else 1].append((float(line.get('yMin')), text))
    out = []
    for col in (0, 1):
        out.extend(text for _, text in sorted(cols[col]))
    return out
