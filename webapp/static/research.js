'use strict';
(() => {
  const byId = id => document.getElementById(id);
  const text = (id, value) => { byId(id).textContent = String(value); };
  const metric = value => typeof value === 'number' && Number.isFinite(value) ? value.toFixed(4) : 'Unavailable';
  const names = { raw: 'Raw ranking score', platt: 'Platt / sigmoid', isotonic: 'Isotonic', constant: 'Prior-rate baseline' };
  function reliability(bins) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 430 350');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Reliability diagram: observed fraud rate against mean predicted probability, both axes from zero to one');
    const add = (tag, attrs, label) => {
      const node = document.createElementNS(ns, tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
      if (label !== undefined) node.textContent = String(label);
      svg.append(node); return node;
    };
    for (let step = 0; step <= 5; step++) {
      const value = step / 5, x = 55 + 310 * value, y = 295 - 250 * value;
      add('line', { x1: 55, x2: 365, y1: y, y2: y, stroke: '#304964' });
      add('text', { x: 43, y: y + 4, fill: '#b9c5ce', 'font-size': 11, 'text-anchor': 'end' }, value.toFixed(1));
      add('text', { x, y: 315, fill: '#b9c5ce', 'font-size': 11, 'text-anchor': 'middle' }, value.toFixed(1));
    }
    add('line', { x1: 55, x2: 365, y1: 295, y2: 45, stroke: '#b9c5ce', 'stroke-dasharray': '5 5' });
    add('text', { x: 210, y: 340, fill: '#d8e8ff', 'font-size': 12, 'text-anchor': 'middle' }, 'Mean predicted probability');
    add('text', { x: 55, y: 22, fill: '#d8e8ff', 'font-size': 12 }, 'Observed fraud rate');
    for (const bin of bins) {
      const point = add('circle', { cx: 55 + 310 * bin.mean_score, cy: 295 - 250 * bin.observed_rate, r: 5, fill: '#8f9bff', stroke: '#dbe4ff' });
      const title = document.createElementNS(ns, 'title');
      title.textContent = `${bin.count.toLocaleString('en-US')} rows; mean score ${metric(bin.mean_score)}; observed rate ${metric(bin.observed_rate)}`;
      point.append(title);
    }
    byId('reliability').replaceChildren(svg);
  }
  async function load() {
    byId('results').hidden = true; byId('retry').hidden = true;
    text('status', 'Loading verified research evidence…');
    try {
      const response = await fetch('/api/research/calibration', { cache: 'no-store', signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw new Error('Evidence unavailable');
      const payload = await response.json(), report = payload.evidence;
      const selected = report.development.selected_method;
      text('rows', report.source.rows.toLocaleString('en-US'));
      text('folds', report.development.folds.length);
      text('method', names[selected]);
      text('model-version', report.model_version);
      text('acceptance', report.final.acceptance.accepted_for_retrospective_probability ? 'Accepted within the documented retrospective scope' : 'Evaluation completed; probability acceptance criteria not met');
      const tbody = byId('metrics'); tbody.replaceChildren();
      for (const method of ['raw', 'platt', 'isotonic', 'constant']) {
        const item = report.final.metrics[method], tr = document.createElement('tr');
        if (method === selected) tr.className = 'selected';
        const label = document.createElement('th'); label.scope = 'row';
        label.textContent = names[method] + (method === selected ? ' · selected in development' : ''); tr.append(label);
        for (const key of ['roc_auc', 'average_precision', 'brier_score', 'log_loss', 'expected_calibration_error']) {
          const td = document.createElement('td'); td.textContent = metric(item[key]); tr.append(td);
        }
        tbody.append(tr);
      }
      reliability(report.final.metrics[selected].reliability_bins);
      byId('limitations').replaceChildren(...report.limitations.map(value => { const li = document.createElement('li'); li.textContent = value; return li; }));
      text('source-hash', report.source.transaction_sha256); text('artifact-hash', payload.artifact_sha256);
      byId('results').hidden = false;
      text('status', `Verified aggregate evidence · ${report.model_version} · historical research`);
    } catch (_) {
      text('status', 'Verified research evidence could not be loaded. Retry or inspect the repository methods.');
      byId('retry').hidden = false;
    }
  }
  byId('retry').addEventListener('click', load);
  load();
})();
