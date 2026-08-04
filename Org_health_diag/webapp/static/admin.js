/* 관리자 화면 차트: 부서별 긍정 비중 막대 + 부서별 3개년 추이 */
(function () {
  const A = window.ADMIN || {};
  if (typeof Chart === 'undefined' || !A.departments) return;

  const POS = '#3E8E5A', NEG = '#D9534F', MID = '#B0B7C3';
  const LINE_COLORS = ['#0f4c81', '#1a6fb5', '#3E8E5A', '#E8912D', '#8e6bbf', '#D9534F'];

  function mount(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    const c = document.createElement('canvas');
    el.appendChild(c);
    return c;
  }

  /* 부서별 긍정 비중 */
  const barCanvas = mount('deptChart');
  if (barCanvas) {
    const avg = A.companyWide['긍정'];
    new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: A.departments.map(d => d.org),
        datasets: [{
          data: A.departments.map(d => d['긍정']),
          backgroundColor: A.departments.map(d =>
            d.tone === 'good' ? POS : (d.tone === 'watch' ? NEG : MID))
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `긍정 ${c.parsed.y}% (전사 평균 ${avg}%)` } },
          annotation: false
        },
        scales: { y: { min: 0, max: 100, title: { display: true, text: '긍정 비중(%)' } } }
      },
      plugins: [{
        // 전사 평균 기준선
        id: 'avgLine',
        afterDraw(chart) {
          const { ctx, chartArea, scales } = chart;
          const y = scales.y.getPixelForValue(avg);
          ctx.save();
          ctx.strokeStyle = '#16232e';
          ctx.setLineDash([6, 4]);
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(chartArea.left, y);
          ctx.lineTo(chartArea.right, y);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = '#16232e';
          ctx.font = '12px sans-serif';
          ctx.fillText(`전사 평균 ${avg}%`, chartArea.left + 6, y - 6);
          ctx.restore();
        }
      }]
    });
  }

  /* 부서별 3개년 추이 */
  const trendCanvas = mount('trendChart');
  if (trendCanvas) {
    const years = A.departments[0].trend.map(t => t.year);
    new Chart(trendCanvas, {
      type: 'line',
      data: {
        labels: years,
        datasets: A.departments.map((d, i) => ({
          label: `${d.company}·${d.org}`,
          data: d.trend.map(t => t['긍정']),
          borderColor: LINE_COLORS[i % LINE_COLORS.length],
          backgroundColor: LINE_COLORS[i % LINE_COLORS.length],
          borderWidth: 2.5, pointRadius: 4, tension: 0.15
        }))
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 14, font: { size: 12 } } },
          tooltip: { callbacks: { label: c => `${c.dataset.label} ${c.parsed.y}%` } }
        },
        scales: { y: { title: { display: true, text: '긍정 비중(%)' } } }
      }
    });
  }
})();
