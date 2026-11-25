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

test('question years are within the archive range', () => {
  for (const q of bank) {
    assert.ok(q.year >= 1990 && q.year <= 2026, `${q.id} has invalid year ${q.year}`);
  }
});
