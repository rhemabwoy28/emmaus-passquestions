const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../assets/quiz-core.js');

const bank = [
  { id: 'q1', year: 2024, paper: 1, topic: 'algebra', prompt: 'Solve x + 5 = 9', options: ['2', '4', '14', '45'], answerIndex: 1, explanation: 'Subtract 5 from both sides.' },
  { id: 'q2', year: 2024, paper: 1, topic: 'geometry', prompt: 'Angles in a triangle sum to?', options: ['90', '180', '270', '360'], answerIndex: 1, explanation: 'Interior angles of a triangle total 180 degrees.' },
  { id: 'q3', year: 2025, paper: 1, topic: 'algebra', prompt: 'If 3x = 21, x = ?', options: ['7', '18', '24', '63'], answerIndex: 0, explanation: 'Divide both sides by 3.' },
  { id: 'q4', year: 2025, paper: 2, topic: 'statistics', prompt: 'Mean of 2, 4, 6?', options: ['3', '4', '6', '12'], answerIndex: 1, explanation: '(2+4+6)/3 = 4.' },
];

test('scoreAnswer returns true for the configured answer index', () => {
  assert.equal(core.scoreAnswer(bank[0], 1), true);
});

test('scoreAnswer returns false for a wrong choice', () => {
  assert.equal(core.scoreAnswer(bank[0], 0), false);
});

test('selectQuestions filters by year', () => {
  assert.deepEqual(core.selectQuestions(bank, { year: 2025 }).map(q => q.id), ['q3', 'q4']);
});

test('selectQuestions filters by topic', () => {
  assert.deepEqual(core.selectQuestions(bank, { topic: 'algebra' }).map(q => q.id), ['q1', 'q3']);
});

test('selectQuestions respects the limit', () => {
  assert.deepEqual(core.selectQuestions(bank, { topic: 'algebra', limit: 1 }).map(q => q.id), ['q1']);
});

test('gradeAttempt counts correct answers and builds details', () => {
  const result = core.gradeAttempt(bank.slice(0, 2), { q1: 1, q2: 0 });
  assert.deepEqual(result, {
    total: 2,
    correct: 1,
    percentage: 50,
    details: [
      { id: 'q1', correct: true, chosen: 1, answerIndex: 1 },
      { id: 'q2', correct: false, chosen: 0, answerIndex: 1 },
    ],
  });
});

test('gradeAttempt treats unanswered questions as incorrect', () => {
  const result = core.gradeAttempt([bank[0]], {});
  assert.equal(result.correct, 0);
  assert.equal(result.details[0].correct, false);
  assert.equal(result.details[0].chosen, null);
});

test('gradeAttempt rounds percentage to the nearest integer', () => {
  const result = core.gradeAttempt(bank.slice(0, 3), { q1: 1, q2: 1, q3: 1 });
  assert.equal(result.percentage, 67);
});

test('quizKey builds a stable local-storage key', () => {
  assert.equal(core.quizKey(2025, 1), 'emmaus:best:2025:1');
});

test('quizKey includes an optional topic in the storage key', () => {
  assert.equal(core.quizKey(2025, 1, 'algebra'), 'emmaus:best:2025:1:algebra');
});

test('selectQuestions filters by paper', () => {
  assert.deepEqual(core.selectQuestions(bank, { paper: 2 }).map(q => q.id), ['q4']);
});

test('selectQuestions filters by subject', () => {
  const mixed = bank.map(q => ({ ...q, subject: q.year === 2025 ? 'english' : 'mathematics' }));
  assert.deepEqual(core.selectQuestions(mixed, { subject: 'english' }).map(q => q.id), ['q3', 'q4']);
});

test('dailyQuestion is stable within one UTC day', () => {
  const morning = core.dailyQuestion(bank, new Date('2026-11-26T01:00:00Z'));
  const evening = core.dailyQuestion(bank, new Date('2026-11-26T23:00:00Z'));
  assert.equal(evening.id, morning.id);
});

test('dailyQuestion moves to the next question the next day', () => {
  const today = core.dailyQuestion(bank, new Date('2026-11-26T01:00:00Z'));
  const tomorrow = core.dailyQuestion(bank, new Date('2026-11-27T01:00:00Z'));
  assert.notEqual(tomorrow.id, today.id);
});
