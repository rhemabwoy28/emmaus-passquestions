const test = require('node:test');
const assert = require('node:assert/strict');
const bank = require('../assets/questions.js');
const papers = require('../assets/data/papers.json');

test('question bank has enough questions for a practice run', () => {
  assert.ok(bank.length >= 20, `expected at least 20 questions, got ${bank.length}`);
});

test('every question is well formed', () => {
  const ids = new Set();
  for (const q of bank) {
    assert.ok(q.id, 'question needs an id');
    assert.ok(!ids.has(q.id), `duplicate id ${q.id}`);
    ids.add(q.id);
    assert.ok(q.prompt && q.prompt.length > 10, `${q.id} needs a prompt`);
    assert.equal(q.options.length, 4, `${q.id} needs four options`);
    assert.ok(Number.isInteger(q.answerIndex) && q.answerIndex >= 0 && q.answerIndex <= 3,
      `${q.id} needs an answerIndex between 0 and 3`);
    assert.ok(q.explanation && q.explanation.length > 10, `${q.id} needs an explanation`);
  }
});

test('question topics exist in the topic index', () => {
  const slugs = new Set(papers.topics.map(t => t.slug));
  for (const q of bank) {
    assert.ok(slugs.has(q.topic), `${q.id} has unknown topic ${q.topic}`);
  }
});

test('every question belongs to a known subject and its own subject topic', () => {
  const bySubject = new Map(papers.subjects.map(s => [s.slug, s]));
  for (const q of bank) {
    assert.ok(q.subject, `${q.id} needs a subject`);
    const subject = bySubject.get(q.subject);
    assert.ok(subject, `${q.id} has unknown subject ${q.subject}`);
    assert.ok(subject.topics.some(t => t.slug === q.topic),
      `${q.id}: topic ${q.topic} is not in subject ${q.subject}`);
  }
});

test('every subject topic has at least one practice question', () => {
  for (const t of papers.topics) {
    assert.ok(bank.some(q => q.topic === t.slug), `no question for topic ${t.slug}`);
  }
});

test('question years are within the archive range', () => {
  for (const q of bank) {
    assert.ok(q.year >= 1990 && q.year <= 2026, `${q.id} has invalid year ${q.year}`);
  }
});
