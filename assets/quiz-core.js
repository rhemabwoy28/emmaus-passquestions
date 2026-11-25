/* Pure quiz logic shared by the browser and Node tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.QuizCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  function scoreAnswer(question, choice) {
    return choice === question.answerIndex;
  }

  function selectQuestions(bank, filters) {
    filters = filters || {};
    let out = bank;
    if (filters.year != null && filters.year !== '') {
      const year = Number(filters.year);
      out = out.filter(q => Number(q.year) === year);
    }
    if (filters.topic) {
      out = out.filter(q => q.topic === filters.topic);
    }
    if (filters.limit) {
      out = out.slice(0, Number(filters.limit));
    }
    return out;
  }

  function gradeAttempt(questions, answers) {
    answers = answers || {};
    const details = questions.map(q => {
      const chosen = Object.prototype.hasOwnProperty.call(answers, q.id) && answers[q.id] != null
        ? Number(answers[q.id]) : null;
      return { id: q.id, correct: chosen === q.answerIndex, chosen, answerIndex: q.answerIndex };
    });
    const correct = details.filter(d => d.correct).length;
    const total = questions.length;
    return { total, correct, percentage: total ? Math.round((correct / total) * 100) : 0, details };
  }

  function quizKey(year, paper) {
    return `emmaus:best:${year}:${paper}`;
  }

  return { scoreAnswer, selectQuestions, gradeAttempt, quizKey };
});
