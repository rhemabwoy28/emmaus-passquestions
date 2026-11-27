"""Extract Paper 1 MCQs + answers from the BECE English PDF into quiz-bank JSON."""
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from utils import ensure_bbox, page_lines

YEAR_RE = re.compile(r'(\d{4}[a-z]?)\s+BECE\s+—\s+English Language \(Paper 1\)')
Q_RE = re.compile(r'^(\d{1,3})[.)]\s+(.+)$')
OPT_RE = re.compile(r'^([A-E])[.)]\s+(.*)$')
ANS_RE = re.compile(r'^(\d{1,3})[.)]\s+([A-E])[.)]\s*(.*)$')


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def classify(stem):
    s = stem.lower()
    if re.search(r'\b(spell|spelling|spelled|misspelt)\b', s):
        return 'eng-spelling'
    if re.search(r'\b(pronounc|syllable|stress(ed)?|sounds? like)\b', s):
        return 'eng-oral'
    if re.search(r'\b(means?|meaning|meanings|synonym|opposite|nearest|best explains|'
                 r'vocabulary|expression|idiom|phrase|word\s+that|similar in meaning|'
                 r'closest in meaning|is the|refers to|definition)\b', s):
        return 'eng-vocabulary'
    return 'eng-grammar'


def short_instruction(text):
    s = re.sub(r'\s+', ' ', text).strip()
    if re.search(r'opposite in meaning', s, re.I):
        return 'Choose the word most nearly OPPOSITE in meaning to the underlined word:'
    if re.search(r'nearest in meaning', s, re.I):
        return 'Choose the word NEAREST in meaning to the underlined word:'
    if re.search(r'best explains', s, re.I):
        return 'Choose the option that BEST EXPLAINS the underlined words:'
    if re.search(r'completes each sentence', s, re.I):
        return 'Choose the option that best completes the sentence:'
    return s[:100].strip()


def infer_instruction(instruction, stem, options):
    s = stem.lower()
    if re.search(r'\.\.\.\s*\?\s*$', s) or re.search(r'\b(tag question)\b', s):
        return ''
    if 'this means' in s or re.search(r'\bmeans\b', s):
        return 'Choose the option that BEST EXPLAINS the phrase:'
    if re.search(r'\b(is|are|was|were)\s+the\s+[\.\_]+', s):
        return 'Choose the word that BEST matches the definition:'
    if re.search(r'[\.\_]{2,}', s) and all(len(o.split()) <= 4 for o in options):
        return ''  # gap-fill grammar question; no meaning instruction needed
    return short_instruction(instruction)


PASSAGE_DEPENDENT = re.compile(
    r'\b(passage|according to|the writer|the author|the text|the story|the poem|the play|the above|from the dialogue)\b', re.I)


def extract_questions(root):
    lines = []
    for p in range(3, 96):  # Part 1: paper 1 questions
        lines.extend(page_lines(root, p))
    questions = []
    tag = None
    expected = 1
    cur = None
    section = None
    instructions = {}

    def looks_like_question(i):
        m = Q_RE.match(lines[i])
        if not m:
            return False
        n = int(m.group(1))
        if n != expected:
            return False
        # must be followed by at least four option markers before next numbered line
        opts = 0
        for line in lines[i + 1:i + 18]:
            if Q_RE.match(line):
                break
            if OPT_RE.match(line):
                opts += 1
        return opts >= 4

    i = 0
    while i < len(lines):
        line = lines[i]
        m = YEAR_RE.search(line)
        if m:
            if cur:
                questions.append(cur)
            tag, expected, cur, section = m.group(1), 1, None, None
            i += 1
            continue
        sec = re.match(r'^SECTION\s+([A-D])\b', line.strip(), re.I)
        if sec:
            section = sec.group(1).upper()
            bits = []
            for follow in lines[i + 1:i + 6]:
                if Q_RE.match(follow) or OPT_RE.match(follow):
                    break
                bits.append(follow.strip())
            instructions[(tag, section)] = ' '.join(bits)
            i += 1
            continue
        if re.match(r'^CLOZE\b', line.strip(), re.I):
            section = 'CLOZE'
            i += 1
            continue
        if looks_like_question(i):
            if cur:
                questions.append(cur)
            m = Q_RE.match(line)
            cur = {'tag': tag, 'num': int(m.group(1)), 'stem': m.group(2).strip(),
                   'options': {}, 'section': section,
                   'instruction': instructions.get((tag, section), '')}
            expected = cur['num'] + 1
            i += 1
            continue
        if cur is not None:
            m = OPT_RE.match(line)
            if m and m.group(1) in 'ABCDE':
                cur['options'][m.group(1)] = m.group(2).strip()
            else:
                last = max(cur['options'], key=lambda k: 'ABCDE'.index(k)) if cur['options'] else None
                size = len(cur['options'][last]) if last else len(cur['stem'])
                boundary = bool(re.match(
                    r'^(PASSAGE|SECTION|PART|CLOZE|COMPREHENSION|LITERATURE|ORAL|GRAMMAR|'
                    r'Read the|Answer all|Answer one|Answer the|For each|In the following|'
                    r'In each of the following|From the alternatives|From the list of|'
                    r'From the options|Choose from|Choose the word|word or group of words)',
                    line.strip(), re.I))
                if boundary or size > 240:
                    # The next passage/section started; this question is complete.
                    cur = None
                elif cur['options']:
                    cur['options'][last] += ' ' + line.strip()
                else:
                    cur['stem'] += ' ' + line.strip()
        i += 1
    if cur:
        questions.append(cur)
    return questions


def extract_answers(root):
    answers = defaultdict(dict)
    tag = None
    for p in range(119, 133):  # Part 3: paper 1 answers
        for line in page_lines(root, p):
            m = YEAR_RE.search(line)
            if m:
                tag = m.group(1)
                continue
            m = ANS_RE.match(line)
            if m and tag:
                answers[tag][int(m.group(1))] = (m.group(2), m.group(3).strip())
    return answers


def build_bank(root):
    raw = extract_questions(root)
    answers = extract_answers(root)
    stats = Counter()
    out = []
    seen_prompts = set()
    for q in raw:
        stats['questions_parsed'] += 1
        key = answers.get(q['tag'], {}).get(q['num'])
        if not key:
            stats['no_answer_key'] += 1
            continue
        letter, ans_text = key
        opts = q['options']
        if letter not in opts or len(opts) < 4:
            stats['option_mismatch'] += 1
            continue
        correct = opts[letter]
        a, c = norm(ans_text), norm(correct)
        if len(a) >= 8 and not (c.startswith(a[:30]) or a.startswith(c[:30]) or a in c or c in a):
            stats['answer_text_mismatch'] += 1
            continue
        raw_stem = re.sub(r'\s+', ' ', q['stem']).strip()
        if q.get('section') == 'A':
            stats['comprehension_dependent'] += 1  # passage not included in the bank
            continue
        if len(raw_stem) < 15 or PASSAGE_DEPENDENT.search(raw_stem):
            stats['passage_dependent_or_short'] += 1
            continue
        instruction = infer_instruction(q.get('instruction', ''), raw_stem, list(opts.values()))
        stem = f'{instruction} {raw_stem}'.strip() if instruction else raw_stem
        if stem.lower() in seen_prompts:
            stats['duplicate_prompt'] += 1
            continue
        seen_prompts.add(stem.lower())
        # keep exactly four options, including the correct one; drop a trailing distractor
        wrong = [k for k in 'ABCDE' if k in opts and k != letter]
        if len(opts) > 4:
            drop = wrong[-1] if wrong else None
            opts = {k: v for k, v in opts.items() if k != drop}
        if len(opts) != 4 or len(set(opts.values())) != 4:
            stats['bad_options'] += 1
            continue
        ordered = [(k, re.sub(r'\s+', ' ', v).strip()) for k, v in sorted(opts.items())]
        idx = [k for k, _ in ordered].index(letter)
        year = int(re.match(r'\d{4}', q['tag']).group())
        out.append({
            'id': f'engp-{q["tag"]}-{q["num"]:02d}',
            'subject': 'english',
            'year': year,
            'paper': 1,
            'topic': classify(stem),
            'prompt': stem,
            'options': [v for _, v in ordered],
            'answerIndex': idx,
            'explanation': f'From the {q["tag"]} BECE English Paper 1 answer key: option {letter} — {correct}.',
            '_source_tag': q['tag'],
            '_source_num': q['num'],
        })
        stats['accepted'] += 1
    return out, stats


if __name__ == '__main__':
    import argparse
    import sys

    ap = argparse.ArgumentParser(description='Extract BECE English Paper 1 MCQs and answer keys.')
    ap.add_argument('--pdf', required=True, help='path to the compiled BECE English PDF')
    ap.add_argument('--out', required=True, help='output JSON path for the extracted questions')
    args = ap.parse_args()
    os.environ['EMMAUS_ENG_PDF'] = args.pdf
    root = ensure_bbox()
    bank, stats = build_bank(root)
    print('stats:', dict(stats), file=sys.stderr)
    print('accepted:', len(bank), file=sys.stderr)
    Path(args.out).write_text(json.dumps(bank, indent=2, ensure_ascii=False))
