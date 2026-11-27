"""Extract BECE Social Studies Paper 1 MCQs + answer keys into quiz-bank JSON.

Usage:
  python3 tools/social_pdf/extract.py \
      --questions-pdf /path/to/BECE-Social-Studies-Paper1-2011-2026-Questions.pdf \
      --answers-pdf   /path/to/BECE-Social-Studies-Paper1-2011-2026-Answers.pdf \
      --out /tmp/social_questions.json

The compiled books use one divider page per year ("YYYY - BECE Social Studies Paper 1").
Image-only years (2021) are OCRed with tesseract when the PDF has no text layer.
Answer keys are matched by year AND question number AND answer text; only verified
matches are kept. 2022 uses a vetted answer list because the web quiz key is wrong
for several questions (see answers_2022_override.json).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pymupdf

YEAR_DIV = re.compile(r'^\s*(\d{4})\s*-\s*BECE Social Studies Paper 1', re.I)
QNUM_LINE = re.compile(r'^(\d{1,2})[.,]\s*$')
QNUM_INLINE = re.compile(r'^(\d{1,2})[.,]\s+(.+)$')
OPT_LINE = re.compile(r'^([A-D])[.,:]\s*$')
OPT_INLINE = re.compile(r'^([A-D])[.,:]\s+(.+)$')


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def classify(stem, options):
    s = (stem + ' ' + ' '.join(options)).lower()
    rules = [
        (r'\b(map|maps|latitude|longitude|meridian|equator|contour|topographic|legend|'
         r'grid|scale|relief| erosion|flood|drought|volcan|earthquake|tremor|rainfall|'
         r'climate|weather|vegetation|savanna|forest|mangrove|swamp|soil|river|mountain|'
         r'plateau|scarp|coast|beach|tide|eclipse|rotation|revolution|sun|seasons|'
         r'pollution|atmosphere|natural disaster|water bod|gully|desert)\b',
         'sst-physical-environment'),
        (r'\b(constitution|parliament|judiciary|executive|legislature|president|court|'
         r'chief justice|district assembly|local government|minister|republic|law|'
         r'separation of powers|rule of law|vote|voting|election|governance|government|'
         r'speaker|amnesty|plebiscite|judge|parliamentary)\b',
         'sst-government'),
        (r'\b(colonial|colonization|colonisation|colonisation|independence|nkrumah|'
         r'positive action|1948 riot|guggisberg|bond of 1844|fante confederation|'
         r'yaa asantewaa|ugcc|cpp|convention people|slave trade|coussey|watson|'
         r'arden clarke|creasy|first republic|second republic|third republic|'
         r'fourth republic|migration of the ak|akans.*migrat| historical)\b',
         'sst-history-of-ghana'),
        (r'\b(save|saving|bank|insurance|ssnit|pension|trade|export|import|tax|'
         r'market|profit|price|production|industry|industries|entrepreneur|business|'
         r'proprietor|co-operativ|cooperative|joint stock|share|loan|capital|'
         r'foreign exchange|currency|ecowas|employment|unemployment|labour|'
         r'primary product|agricultur|farming|tourism|economy|economic|money|'
         r'consumer|goods|service|price)\b',
         'sst-economics'),
        (r'\b(adolescent|reproductive health|sex education|family|marriage|child|'
         r'children|youth|discipline|drug|hiv|aids|gender|fgm|female genital|'
         r'peer pressure|culture|cultural|religion|religious|festival|chieftaincy|'
         r'socialisation|social environment|tradition|value|morality|chastity|'
         r'bribery|corruption|human rights|rights of|social problem)\b',
         'sst-social-issues'),
        (r'\b(population|settlement|rural|urban|migration|slum|sanitation|health|'
         r'housing|community|town|city|development|urbanisation|urbanization|'
         r'family planning|sanitary|water supply|amenit|infrastructure|'
         r'dependency ratio|birth rate|death rate)\b',
         'sst-human-environment'),
        (r'\b(citizen|citizenship|duty of a citizen|responsibility|national symbol|'
         r'flag|anthem|coat of arms|pledge|national unity|cooperation|co-operation|'
         r'patriotism|good citizen|rights and duties|president|constitution)\b',
         'sst-citizenship'),
    ]
    for pattern, topic in rules:
        if re.search(pattern, s):
            return topic
    return 'sst-citizenship'


JUNK = re.compile(
    r'^(Source:|Questions - Objective Test|Answers - Objective Test|'
    r'Compiled for personal BECE revision|BECE Social Studies|'
    r'PART [AB]|OBJECTIVE TEST|Choose the correct answer|Answer all the questions|'
    r'Now answer the following questions|END OF|Page \d+|SRONU|FROM)$', re.I)


def page_text(page):
    text = page.get_text().strip()
    if len(text) >= 80:
        return text
    pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3))
    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    try:
        pix.save(path)
        out = subprocess.run(['tesseract', path, 'stdout'], capture_output=True,
                             text=True, check=True)
        return out.stdout
    finally:
        os.unlink(path)


def read_sections(pdf_path):
    doc = pymupdf.open(pdf_path)
    sections, year, buf = [], None, []
    for page in doc:
        text = page_text(page)
        match = YEAR_DIV.search(text)
        if match:
            if year is not None:
                sections.append((year, '\n'.join(buf)))
            year, buf = int(match.group(1)), []
            continue
        if year is not None:
            buf.append(text)
    if year is not None:
        sections.append((year, '\n'.join(buf)))
    doc.close()
    return sections


def clean_lines(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or JUNK.match(line):
            continue
        if re.fullmatch(r'[A-Z]', line):  # vertical watermark letters
            continue
        if len(line) <= 2 and not QNUM_LINE.match(line) and not OPT_LINE.match(line):
            continue
        out.append(line)
    return out


def parse_questions(text):
    questions, cur, expect, pending = [], None, 1, None
    for line in clean_lines(text):
        m = QNUM_INLINE.match(line)
        if m and int(m.group(1)) == expect:
            if cur:
                questions.append(cur)
            stem = re.sub(r'^\d{1,2}[.,]\s*', '', m.group(2).strip())
            cur = {'num': expect, 'stem': stem, 'options': {}, 'raw': []}
            expect += 1
            pending = 'stem'
            continue
        m = QNUM_LINE.match(line)
        if m and int(m.group(1)) == expect:
            if cur:
                questions.append(cur)
            cur = {'num': expect, 'stem': '', 'options': {}, 'raw': []}
            expect += 1
            pending = 'stem'
            continue
        if cur is None:
            continue
        cur['raw'].append(line)
        m = OPT_INLINE.match(line)
        if m:
            cur['options'][m.group(1)] = m.group(2).strip()
            pending = m.group(1)
            continue
        m = OPT_LINE.match(line)
        if m:
            cur['options'][m.group(1)] = ''
            pending = m.group(1)
            continue
        if pending == 'stem':
            cur['stem'] += ' ' + line
        elif pending in cur['options']:
            cur['options'][pending] += ' ' + line
    if cur:
        questions.append(cur)
    return questions


def parse_answers(text):
    flat = re.sub(r'\s+', ' ', text)
    pattern = re.compile(
        r'(\d{1,2})\.\s+([A-D])\.?\s*(.*?)'
        r'(?=\s+\d{1,2}\.\s+[A-D]\.?\s|\s*Source:|$)')
    answers = {}
    for m in pattern.finditer(flat):
        num = int(m.group(1))
        if 1 <= num <= 40 and num not in answers:
            answers[num] = (m.group(2), m.group(3).strip())
    return answers


def repair_question(q, answer):
    """OCR sometimes drops option letters; rebuild from the four trailing lines."""
    if not answer or len(q.get('options', {})) >= 4:
        return
    letter, ans_text = answer
    stem_norm = norm(q['stem'])
    lines = []
    for line in q.get('raw', []):
        if not line or QNUM_LINE.match(line) or QNUM_INLINE.match(line):
            continue
        if norm(line) in stem_norm or line.rstrip().endswith('?'):
            continue
        m = OPT_INLINE.match(line)
        if m:
            lines.append(m.group(2).strip())
        elif not OPT_LINE.match(line):
            lines.append(line.strip())
    if len(lines) < 4:
        return
    target, idx = norm(ans_text), ord(letter) - 65
    best = None
    for start in range(len(lines) - 3):
        window = lines[start:start + 4]
        got = norm(window[idx])
        score = 2 if target and (target == got or (len(target) >= 5 and
                        (target in got or got in target))) else 0
        score += 1 if all(len(x) < 110 for x in window) else 0
        if best is None or score > best[0]:
            best = (score, window)
    if best and best[0] >= 1:
        q['options'] = {chr(65 + i): v for i, v in enumerate(best[1])}


def load_override(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text())
    # The override file lists the 2022 answer key by question number.
    return {2022: {int(x['num']): (x['letter'], x['text']) for x in data}}


def build_bank(qpdf, apdf, override_path=None):
    qsecs = dict(read_sections(qpdf))
    asecs = dict(read_sections(apdf))
    override = load_override(override_path)
    counts = Counter()
    out, seen = [], set()
    for year in sorted(qsecs):
        answers = override.get(year) or parse_answers(asecs.get(year, ''))
        if override.get(year):
            # match by answer text, not by the quiz's unreliable question number
            texts = [(letter, text) for letter, text in answers.values()]
        for q in parse_questions(qsecs[year]):
            counts['parsed'] += 1
            if not override.get(year):
                repair_question(q, answers.get(q['num']))
            opts = q['options']
            if len(opts) != 4:
                counts['bad_options'] += 1
                continue
            stem = re.sub(r'\s+', ' ', q['stem']).strip()
            if len(stem) < 15:
                counts['short_stem'] += 1
                continue
            if override.get(year):
                candidates = []
                for letter, ans_text in texts:
                    a = norm(ans_text)
                    if not a:
                        continue
                    for k, v in opts.items():
                        c = norm(v)
                        if a == c or (len(a) >= 6 and (c.startswith(a[:30]) or a.startswith(c[:30]))):
                            candidates.append((k, letter, ans_text))
                unique = {c[0]: c for c in candidates}
                if len(unique) != 1:
                    counts['override_ambiguous'] += 1
                    continue
                key, letter, ans_text = next(iter(unique.values()))
            else:
                entry = answers.get(q['num'])
                if not entry:
                    counts['no_answer'] += 1
                    continue
                letter, ans_text = entry
                key = letter
                if key not in opts:
                    counts['letter_missing'] += 1
                    continue
                a, c = norm(ans_text), norm(opts[key])
                if len(a) >= 8 and not (c.startswith(a[:30]) or a.startswith(c[:30])
                                        or a in c or c in a):
                    counts['answer_text_mismatch'] += 1
                    continue
            correct = opts[key]
            ordered = [(k, re.sub(r'\s+', ' ', v).strip()) for k, v in sorted(opts.items())]
            if len(set(v for _, v in ordered)) != 4:
                counts['duplicate_options'] += 1
                continue
            idx = [k for k, _ in ordered].index(key)
            if stem.lower() in seen:
                counts['duplicate_prompt'] += 1
                continue
            seen.add(stem.lower())
            out.append({
                'id': f'sstp-{year}-{q["num"]:02d}',
                'subject': 'social-studies',
                'year': year,
                'paper': 1,
                'topic': classify(stem, [v for _, v in ordered]),
                'prompt': stem,
                'options': [v for _, v in ordered],
                'answerIndex': idx,
                'explanation': (f'From the {year} BECE Social Studies Paper 1 answer '
                                f'key: option {letter} - {correct}.'),
            })
            counts['accepted'] += 1
    return out, counts


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Extract Social Studies MCQs from compiled books.')
    ap.add_argument('--questions-pdf', required=True)
    ap.add_argument('--answers-pdf', required=True)
    ap.add_argument('--override', default=str(Path(__file__).with_name('answers_2022_override.json')))
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    bank, counts = build_bank(args.questions_pdf, args.answers_pdf, args.override)
    print('stats:', dict(counts), file=sys.stderr)
    Path(args.out).write_text(json.dumps(bank, indent=2, ensure_ascii=False))
