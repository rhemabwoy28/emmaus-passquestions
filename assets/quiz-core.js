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
    if (filters.paper != null && filters.paper !== '') {
      const paper = Number(filters.paper);
      out = out.filter(q => Number(q.paper) === paper);
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

  function quizKey(year, paper, topic) {
    const base = `emmaus:best:${year}:${paper}`;
    return topic ? `${base}:${topic}` : base;
  }

  function dailyQuestion(bank, date) {
    if (!bank || !bank.length) return null;
    const day = Math.floor((date ? date.getTime() : Date.now()) / 86400000);
    return bank[((day % bank.length) + bank.length) % bank.length];
  }

  return { scoreAnswer, selectQuestions, gradeAttempt, quizKey, dailyQuestion };
});
