/* 리포트 화면 상호작용: 사이드바 스크롤 이동 · 문항 필터/정렬 · 다개년 추이 차트 · 챗봇 */
(function () {
  const COLORS = { '긍정': '#3E8E5A', '중립': '#B0B7C3', '부정': '#D9534F' };
  const R = window.REPORT || {};

  /* ---------- 사이드바 바로가기: 점프 대신 스크롤 애니메이션 ---------- */
  document.querySelectorAll('.sidebar nav a[href^="#"], .sidebar .cta[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      window.history.pushState(null, '', link.getAttribute('href'));
    });
  });

  /* ---------- 문항 필터 · 정렬 ---------- */
  const midFilter = document.getElementById('midFilter');
  const sortBy = document.getElementById('sortBy');
  const list = document.getElementById('questionList');

  function applyQuestionView() {
    if (!list) return;
    const items = Array.from(list.querySelectorAll('.question-item'));
    const key = sortBy.value === 'neg' ? 'neg' : 'pos';
    items.sort((a, b) => parseFloat(b.dataset[key]) - parseFloat(a.dataset[key]));
    items.forEach(el => {
      const show = midFilter.value === '전체' || el.dataset.mid === midFilter.value;
      el.style.display = show ? '' : 'none';
      list.appendChild(el);           // 정렬 순서대로 재배치
    });
  }
  if (midFilter && sortBy) {
    midFilter.addEventListener('change', applyQuestionView);
    sortBy.addEventListener('change', applyQuestionView);
    applyQuestionView();
  }

  /* ---------- 3개년 추이 차트 ---------- */
  const charts = {};

  function paddedRange(values) {
    const lo = Math.min(...values), hi = Math.max(...values);
    const pad = Math.max((hi - lo) * 0.25, 5);
    return { min: Math.max(0, lo - pad), max: Math.min(100, hi + pad) };
  }

  function drawTrend(canvasId, trend, bucket) {
    const el = document.getElementById(canvasId);
    if (!el || typeof Chart === 'undefined') return;
    const values = trend.map(t => t[bucket]);
    const range = paddedRange(values);
    if (charts[canvasId]) charts[canvasId].destroy();

    let canvas = el.querySelector('canvas');
    if (!canvas) { canvas = document.createElement('canvas'); el.appendChild(canvas); }

    charts[canvasId] = new Chart(canvas, {
      type: 'line',
      data: {
        labels: trend.map(t => t.year),
        datasets: [{
          label: bucket,
          data: values,
          borderColor: COLORS[bucket],
          backgroundColor: COLORS[bucket],
          borderWidth: 3,
          pointRadius: 5,
          tension: 0.15
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: bucket, color: COLORS[bucket],
                   font: { size: 15, weight: 'bold' } },
          tooltip: { callbacks: { label: c => `${bucket} ${c.parsed.y}%` } }
        },
        scales: {
          y: { min: range.min, max: range.max, title: { display: true, text: '비중(%)' } }
        }
      }
    });
  }

  if (R.overallTrend) {
    drawTrend('trendPos', R.overallTrend, '긍정');
    drawTrend('trendNeu', R.overallTrend, '중립');
    drawTrend('trendNeg', R.overallTrend, '부정');
  }

  const midPick = document.getElementById('midTrendPick');
  function drawMidTrend() {
    const t = (R.midTrends || {})[midPick.value];
    if (!t) return;
    drawTrend('midPos', t, '긍정');
    drawTrend('midNeu', t, '중립');
    drawTrend('midNeg', t, '부정');
  }
  if (midPick) {
    midPick.addEventListener('change', drawMidTrend);
    drawMidTrend();
  }

  /* ---------- 챗봇 ---------- */
  const box = document.getElementById('chatBox');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');
  const history = [];

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function render(text) {
    // 굵게(**), 링크([t](u)), 줄바꿈만 지원하는 최소 마크다운
    return escapeHtml(text)
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
               '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
      .split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
  }

  function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML =
      `<div class="who">${role === 'user' ? '나' : 'AI'}</div><div class="body">${render(text)}</div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    history.push({ role, text });
    fetch('/api/chat/history', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ history })
    }).catch(() => {});
  }

  async function send(message) {
    if (!message.trim()) return;
    addMessage('user', message);
    const pending = document.createElement('div');
    pending.className = 'msg assistant';
    pending.innerHTML = '<div class="who">AI</div><div class="body">답변 생성 중…</div>';
    box.appendChild(pending);
    box.scrollTop = box.scrollHeight;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      pending.remove();
      addMessage('assistant', data.text || '답변을 가져오지 못했습니다.');
    } catch (e) {
      pending.remove();
      addMessage('assistant', '답변을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.');
    }
  }

  if (box) {
    addMessage('assistant', R.welcome || '안녕하세요.');
    form.addEventListener('submit', e => {
      e.preventDefault();
      const v = input.value;
      input.value = '';
      send(v);
    });
    document.querySelectorAll('#quickBtns button').forEach(b =>
      b.addEventListener('click', () => send(b.dataset.q)));
  }
})();
