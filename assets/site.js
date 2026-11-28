/* Emmaus static replica — vanilla interactions, no network calls. */
(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = s => String(s).replace(/[&<>\"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* Theme: pre-paint script in <head> applies the stored class; this keeps UI in sync. */
  const syncThemeButton = () => {
    const btn = $('[data-theme-toggle]');
    if (!btn) return;
    const dark = document.documentElement.classList.contains('dark');
    btn.setAttribute('aria-pressed', String(dark));
    btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    const label = $('[data-theme-label]', btn);
    if (label) label.textContent = dark ? 'Light' : 'Dark';
  };
  document.addEventListener('DOMContentLoaded', () => {
    syncThemeButton();
    $('[data-theme-toggle]')?.addEventListener('click', () => {
      const dark = document.documentElement.classList.toggle('dark');
      try { localStorage.setItem('emmaus:theme', dark ? 'dark' : 'light'); } catch (_) {}
      syncThemeButton();
    });
  });

  /* Mobile menu */
  document.addEventListener('DOMContentLoaded', () => {
    const toggle = $('[data-menu-toggle]');
    const menu = $('[data-mobile-nav]');
    toggle?.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    $$('[data-mobile-nav] a').forEach(a => a.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle?.setAttribute('aria-expanded', 'false');
    }));
  });

  /* Question of the day: client-side grading, explanation first, then gate. */
  document.addEventListener('DOMContentLoaded', () => {
    const quiz = $('[data-quiz]');
    if (!quiz) return;
    /* Question of the day rotates from the bank, keyed to the UTC date. */
    if (quiz.hasAttribute('data-qotd') && window.QUESTION_BANK && QuizCore.dailyQuestion) {
      const q = QuizCore.dailyQuestion(QUESTION_BANK);
      if (q) {
        const text = $('.q-text', quiz);
        if (text) text.textContent = q.prompt;
        const optionsBox = $('.options', quiz);
        if (optionsBox) optionsBox.innerHTML = q.options.map((option, i) =>
          `<button class="option" type="button" data-correct="${i === q.answerIndex}">`
          + `<span class="letter">${'ABCD'[i]}</span><span>${esc(option)}</span></button>`).join('');
        const explanation = $('[data-explanation]', quiz);
        if (explanation) explanation.innerHTML = `<strong>Explanation:</strong> ${esc(q.explanation)}`;
        const meta = $('.q-head .muted', quiz);
        if (meta) meta.textContent = `${q.subject.replace(/-/g, ' ')} · ${q.year} · new question daily`;
        delete quiz.dataset.done;
      }
    }
    const options = $$('[data-correct]', quiz);
    const verdict = $('[data-verdict]', quiz);
    const explanation = $('[data-explanation]', quiz);
    const gate = $('[data-gate]', quiz);
    options.forEach(btn => btn.addEventListener('click', () => {
      if (quiz.dataset.done === '1') return;
      quiz.dataset.done = '1';
      const right = btn.dataset.correct === 'true';
      options.forEach(o => {
        o.disabled = true;
        o.setAttribute('aria-disabled', 'true');
        const correct = o.dataset.correct === 'true';
        o.classList.toggle('correct', correct);
        o.classList.toggle('wrong', !correct && o === btn);
        o.classList.toggle('dim', !correct && o !== btn);
      });
      if (verdict) {
        verdict.textContent = right ? 'Correct — well done.' : "Not quite. Check the explanation.";
        verdict.classList.remove('hidden');
        quiz.setAttribute('aria-live', 'polite');
      }
      explanation?.classList.remove('hidden');
      gate?.classList.remove('hidden');
    }));
  });

  /* Level tabs (visual only in the static build). */
  document.addEventListener('DOMContentLoaded', () => {
    const tabs = $$('[data-tab]');
    if (!tabs.length) return;
    const select = name => {
      tabs.forEach(t => t.setAttribute('aria-selected', String(t.dataset.tab === name)));
      $$('[data-panel]').forEach(p => p.classList.toggle('hidden', p.dataset.panel !== name));
    };
    tabs.forEach(t => t.addEventListener('click', () => select(t.dataset.tab)));
  });

  /* Marquee pause/play */
  document.addEventListener('DOMContentLoaded', () => {
    const band = $('[data-marquee]');
    const btn = $('[data-marquee-toggle]');
    btn?.addEventListener('click', () => {
      const paused = band.classList.toggle('paused');
      btn.textContent = paused ? 'Play' : 'Pause';
      btn.setAttribute('aria-pressed', String(paused));
    });
  });

  /* Local search across generated paper/topic links. */
  document.addEventListener('DOMContentLoaded', () => {
    const form = $('[data-search-form]');
    if (!form) return;
    const input = $('[data-search-input]', form);
    const results = $('[data-search-results]');
    const render = () => {
      const q = (input?.value || '').trim().toLowerCase();
      if (!results) return;
      if (!q) { results.innerHTML = '<p class="muted">Type a year, topic or paper to search.</p>'; return; }
      const links = $$('[data-searchable]');
      const hits = links.filter(a => (a.dataset.searchable || a.textContent || '').toLowerCase().includes(q));
      results.innerHTML = hits.length
        ? `<ul class="list">${hits.slice(0, 30).map(a => `<li><a href="${a.getAttribute('href')}">${a.textContent.trim()}</a><span class="muted small">${a.dataset.kind || ''}</span></li>`).join('')}</ul>`
        : '<p class="muted">No matches in this offline demo.</p>';
    };
    const qParam = new URLSearchParams(location.search).get('q');
    if (qParam && input) input.value = qParam;
    form.addEventListener('submit', e => { e.preventDefault(); render(); });
    input?.addEventListener('input', render);
    render();
  });

  /* Sign-in form is deliberately inert in the static build. */
  document.addEventListener('DOMContentLoaded', () => {
    const form = $('[data-demo-form]');
    form?.addEventListener('submit', e => {
      e.preventDefault();
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.textContent = 'Accounts are not enabled in this static demo.';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2600);
    });
  });
  /* Leaderboard: surface scores this device actually saved, alongside the demo rows. */
  document.addEventListener('DOMContentLoaded', () => {
    const box = $('[data-local-bests]');
    if (!box) return;
    const entries = [];
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (!key || !key.startsWith('emmaus:best:')) continue;
        const score = Number(localStorage.getItem(key));
        if (!Number.isFinite(score)) continue;
        const parts = key.slice('emmaus:best:'.length).split(':');
        const [year, paper] = parts;
        const rest = parts.slice(2);
        const subject = rest.length > 1 ? rest[0] : '';
        const topic = rest.length ? rest[rest.length - 1] : '';
        const label = `${year === 'all' ? 'All years' : year} · ${paper === 'all' ? 'All papers' : `Paper ${paper}`}`
          + `${subject ? ` · ${subject.replace(/-/g, ' ')}` : ''}${topic ? ` · ${topic.replace(/-/g, ' ')}` : ''}`;
        entries.push({ label, score });
      }
    } catch (_) {}
    entries.sort((a, b) => b.score - a.score);
    box.innerHTML = entries.length
      ? `<div class="table-wrap"><table><thead><tr><th>Set</th><th>Best</th></tr></thead><tbody>${entries.map(e =>
          `<tr><td>${esc(e.label)}</td><td><strong>${e.score}%</strong></td></tr>`).join('')}</tbody></table></div>`
        : '<p class="muted">No scores saved yet. <a href="practice.html">Answer a practice set</a> and your best will appear here.</p>';
  });

  /* Practice runner: filter, answer, explain, score, retry. */
  document.addEventListener('DOMContentLoaded', () => {
    const runner = $('[data-quiz-runner]');
    if (!runner || !window.QuizCore || !window.QUESTION_BANK) return;
    const form = $('[data-practice-controls]');
    const subjectSel = $('[data-practice-subject]');
    const yearSel = $('[data-practice-year]');
    const paperSel = $('[data-practice-paper]');
    const topicSel = $('[data-practice-topic]');
    const countSel = $('[data-practice-count]');
    const params = new URLSearchParams(location.search);
    if (params.get('subject') && subjectSel) subjectSel.value = params.get('subject');
    function syncTopics() {
      if (!topicSel) return;
      const subject = subjectSel?.value || '';
      Array.from(topicSel.options).forEach(opt => {
        if (!opt.value) return;
        const show = !subject || opt.dataset.subject === subject;
        opt.hidden = !show;
        opt.disabled = !show;
      });
      const chosen = topicSel.value;
      const chosenOpt = topicSel.querySelector(`option[value="${chosen}"]`);
      if (chosen && (!chosenOpt || chosenOpt.disabled)) topicSel.value = '';
    }
    syncTopics();
    if (params.get('year')) yearSel.value = params.get('year');
    if (params.get('paper') && paperSel) paperSel.value = params.get('paper');
    if (params.get('topic') && topicSel) topicSel.value = params.get('topic');
    subjectSel?.addEventListener('change', syncTopics);
    let state = null;

    const filters = () => ({
      subject: subjectSel?.value || '',
      year: yearSel.value,
      paper: paperSel?.value || '',
      topic: topicSel?.value || '',
      limit: Number(countSel.value) || 0,
    });

    function start() {
      const questions = QuizCore.selectQuestions(QUESTION_BANK, filters());
      if (!questions.length) {
        runner.innerHTML = '<p class="muted">No questions match those filters. Try another year or topic.</p>';
        state = null;
        return;
      }
      state = { questions, index: 0, answers: {}, locked: false };
      render();
    }

    function render() {
      if (state.index >= state.questions.length) return finish();
      const q = state.questions[state.index];
      const pct = Math.round((state.index / state.questions.length) * 100);
      const opts = q.options.map((text, i) =>
        `<button class="option" type="button" data-practice-option="${i}"><span class="letter">${'ABCD'[i]}</span><span>${esc(text)}</span></button>`
      ).join('');
      runner.innerHTML = `
<div class="quiz-shell" data-quiz-shell>
  <div class="quiz-topline"><span>Question ${state.index + 1} of ${state.questions.length}</span><span>${esc((q.subject || '').replace(/-/g, ' '))} · ${esc(q.year)} · ${esc(q.topic.replace(/-/g, ' '))}</span></div>
  <div class="progress"><span style="width:${pct}%"></span></div>
  <div class="quiz-question">${esc(q.prompt)}</div>
  <div class="options">${opts}</div>
  <div class="verdict hidden" data-practice-verdict></div>
  <div class="explanation hidden" data-practice-explanation></div>
  <button class="btn btn-primary btn-sm quiz-next hidden" type="button" data-practice-next>Next question →</button>
</div>`;
    }

    function choose(i) {
      if (!state || state.locked) return;
      state.locked = true;
      const q = state.questions[state.index];
      const right = QuizCore.scoreAnswer(q, i);
      state.answers[q.id] = i;
      runner.querySelectorAll('[data-practice-option]').forEach(btn => {
        const n = Number(btn.dataset.practiceOption);
        btn.disabled = true;
        btn.classList.toggle('correct', n === q.answerIndex);
        btn.classList.toggle('wrong', !right && n === i);
        btn.classList.toggle('dim', n !== q.answerIndex && n !== i);
      });
      const verdict = $('[data-practice-verdict]', runner);
      verdict.textContent = right ? 'Correct — well done.' : 'Not quite — check the explanation below.';
      verdict.classList.remove('hidden');
      const box = $('[data-practice-explanation]', runner);
      box.innerHTML = `<strong>Explanation:</strong> ${esc(q.explanation)}`;
      box.classList.remove('hidden');
      $('[data-practice-next]', runner).classList.remove('hidden');
    }

    function finish() {
      const result = QuizCore.gradeAttempt(state.questions, state.answers);
      const subject = subjectSel?.value || '';
      const topic = topicSel?.value || '';
      const label = subject ? `${subject}${topic ? `:${topic}` : ''}` : topic;
      const key = QuizCore.quizKey(yearSel.value || 'all', paperSel?.value || 'all', label);
      let best = result.percentage;
      try {
        const stored = Number(localStorage.getItem(key));
        if (stored > best) best = stored;
        else localStorage.setItem(key, String(best));
      } catch (_) {}
      const review = state.questions.map((q, i) => {
        const d = result.details[i];
        const correctText = esc(q.options[q.answerIndex]);
        return `<div class="review-item"><h4><span class="badge ${d.correct ? 'ok' : 'no'}">${d.correct ? 'Correct' : 'Wrong'}</span>${esc(q.prompt)}</h4>
          <p class="small">Answer: <strong>${correctText}</strong></p><p>${esc(q.explanation)}</p></div>`;
      }).join('');
      runner.innerHTML = `<div class="quiz-shell">
        <div class="result-box"><b>${result.percentage}%</b><span>${result.correct} of ${result.total} correct</span><p class="small muted" style="margin-top:8px">Best on this device: ${best}%</p></div>
        <div class="card-actions"><button class="btn btn-primary btn-sm" type="button" data-practice-retry>Try again</button><a class="btn btn-quiet btn-sm" href="bece/index.html">Browse papers</a></div>
        <h3 style="margin:20px 0 8px">Review</h3>${review}
      </div>`;
    }

    form?.addEventListener('submit', e => { e.preventDefault(); start(); });
    runner.addEventListener('click', e => {
      const opt = e.target.closest('[data-practice-option]');
      if (opt) return choose(Number(opt.dataset.practiceOption));
      if (e.target.closest('[data-practice-next]')) { state.index++; state.locked = false; render(); }
      if (e.target.closest('[data-practice-retry]')) start();
    });
    if (params.get('subject') || params.get('year') || params.get('paper') || params.get('topic')) start();
  });
})();
