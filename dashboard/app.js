'use strict';

/* ── State ───────────────────────────────────────────────── */
let ALL  = [];
let LIST = [];
let SORT_KEY = 'rank';
let SORT_DIR = 1;
let PAGE     = 1;
const PER    = 25;

// Scatter zoom state
let SCATTER_CHART = null;
let SCATTER_DATA  = [];
let SCATTER_MIN   = 0;
let SCATTER_MAX   = 100;

/* ── Bootstrap ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res  = await fetch('deals.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    init(data);
  } catch (e) {
    document.getElementById('loading').innerHTML = `
      <div style="text-align:center;color:#444;padding:40px;">
        <div style="font-size:13px;font-weight:600;color:#888;margin-bottom:8px;">Could not load deals.json</div>
        <div style="font-size:12px;color:#444;">${e.message}</div>
        <div style="margin-top:12px;font-size:12px;color:#333;">Run <code style="background:#161616;padding:2px 6px;border-radius:3px;color:#00c8f0;">python run.py</code> first</div>
      </div>`;
  }
});

function init(data) {
  ALL  = data.listings;
  LIST = [...ALL];
  SCATTER_DATA = data.scatter || [];

  setKPIs(data.meta);
  setFilters(data.meta);
  buildScatterChart(SCATTER_DATA);
  
  const scatterSelect = document.getElementById('scatter-range');
  if (scatterSelect) {
    const [min, max] = scatterSelect.value.split(',').map(Number);
    updateScatterChart(min, max);
  }

  buildCityChart(data.city_chart);
  buildDistChart(data.distribution);
  buildBubbleChart(ALL);
  renderTable();

  document.getElementById('loading').style.display = 'none';
  document.getElementById('app').style.display     = 'block';
}

/* ── KPIs ────────────────────────────────────────────────── */
function setKPIs(meta) {
  count('kpi-total', meta.total_listings);
  count('kpi-hot',   meta.hot_deals);
  count('kpi-good',  meta.good_deals);
  count('kpi-fair',  meta.fair_price);
  count('kpi-over',  meta.overpriced);
  document.getElementById('kpi-r2').textContent = meta.model_r2.toFixed(3);
  document.getElementById('model-accuracy-badge').textContent =
    `R\u00B2 ${(meta.model_r2 * 100).toFixed(1)}%`;
}

function count(id, target) {
  const el = document.getElementById(id);
  const t0 = performance.now();
  const dur = 800;
  const step = now => {
    const p = Math.min((now - t0) / dur, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(e * target).toLocaleString('en-IN');
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ── Filters ─────────────────────────────────────────────── */
function setFilters(meta) {
  const city = document.getElementById('filter-city');
  meta.cities.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; city.appendChild(o); });

  const type = document.getElementById('filter-type');
  meta.property_types.forEach(t => { const o = document.createElement('option'); o.value = t; o.textContent = t; type.appendChild(o); });

  const src = document.getElementById('filter-source');
  if (src && meta.sources) {
    meta.sources.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; src.appendChild(o); });
  }

  ['filter-city','filter-type','filter-bhk','filter-deal','filter-source'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', applyFilters);
  });
  document.getElementById('search-input').addEventListener('input', applyFilters);
}

function applyFilters() {
  const city   = document.getElementById('filter-city').value;
  const type   = document.getElementById('filter-type').value;
  const bhk    = document.getElementById('filter-bhk').value;
  const deal   = document.getElementById('filter-deal').value;
  const source = document.getElementById('filter-source')?.value || '';
  const q      = document.getElementById('search-input').value.toLowerCase().trim();

  LIST = ALL.filter(r => {
    if (city   && r.city          !== city)   return false;
    if (type   && r.property_type !== type)   return false;
    if (source && r.source        !== source) return false;
    if (bhk) {
      const b = parseInt(bhk);
      if (b === 5 ? r.bhk < 5 : r.bhk !== b) return false;
    }
    if (deal && r.deal_tag !== deal) return false;
    if (q && !`${r.name} ${r.location} ${r.city} ${r.title} ${r.source}`.toLowerCase().includes(q)) return false;
    return true;
  });

  PAGE = 1;
  renderTable();
}

function resetFilters() {
  ['filter-city','filter-type','filter-bhk','filter-deal','filter-source'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('search-input').value = '';
  LIST = [...ALL];
  PAGE = 1;
  renderTable();
}

/* ── Table ───────────────────────────────────────────────── */
function sortBy(key) {
  if (SORT_KEY === key) SORT_DIR *= -1;
  else { SORT_KEY = key; SORT_DIR = 1; }

  document.querySelectorAll('thead th').forEach(th => th.classList.remove('active'));
  const map = { rank:0, city:2, bhk:4, total_area:5, actual_price:6, predicted_fmv:7, deal_pct:8 };
  const idx = map[key];
  if (idx !== undefined) document.querySelectorAll('thead th')[idx]?.classList.add('active');

  LIST.sort((a, b) => {
    const av = a[key], bv = b[key];
    return typeof av === 'string' ? SORT_DIR * av.localeCompare(bv) : SORT_DIR * (av - bv);
  });
  PAGE = 1;
  renderTable();
}

function renderTable() {
  const start = (PAGE - 1) * PER;
  const slice = LIST.slice(start, start + PER);

  document.getElementById('count-shown').textContent =
    LIST.length === 0 ? '0'
    : `${start + 1}\u2013${Math.min(start + PER, LIST.length)}`;
  document.getElementById('count-total').textContent = LIST.length.toLocaleString('en-IN');

  document.getElementById('listings-tbody').innerHTML = slice.map((r, i) => {
    const pClass  = r.deal_pct >= 0 ? 'pos' : 'neg';
    const pSign   = r.deal_pct >= 0 ? '+' : '';
    const tagCls  = tagClass(r.deal_tag);
    const rankCls = r.rank <= 5 ? 'top' : '';
    const shortTitle = r.title.length > 42 ? r.title.slice(0, 42) + '\u2026' : r.title;
    const shortLoc   = r.location.length > 40 ? r.location.slice(0, 40) + '\u2026' : r.location;
    const srcKey = (r.source || '').split('/')[0].toLowerCase();

    return `<tr onclick="openModal(${start + i})">
      <td><span class="rank-num ${rankCls}">${r.rank}</span></td>
      <td class="wrap">
        <span class="prop-name">${esc(shortTitle)}</span>
        <span class="prop-loc">${esc(shortLoc)}</span>
      </td>
      <td class="dim">${esc(r.city)}</td>
      <td class="dim">${r.bhk}</td>
      <td class="mono dim">${r.total_area.toLocaleString('en-IN')}</td>
      <td class="price-val">${esc(r.actual_price_fmt)}</td>
      <td class="fmv-val">${esc(r.predicted_fmv_fmt)}</td>
      <td><span class="deal-pct ${pClass}">${pSign}${r.deal_pct.toFixed(1)}%</span></td>
      <td><span class="deal-tag ${tagCls}">${tagLabel(r.deal_tag)}</span></td>
    </tr>`;
  }).join('');

  renderPagination();
}

function tagClass(tag) {
  if (tag.includes('Hot'))  return 'hot';
  if (tag.includes('Good')) return 'good';
  if (tag.includes('Fair')) return 'fair';
  return 'over';
}

function tagLabel(tag) {
  if (tag.includes('Hot'))      return 'Hot';
  if (tag.includes('Good'))     return 'Good';
  if (tag.includes('Fair'))     return 'Fair';
  if (tag.includes('Slightly')) return 'High';
  return 'Over';
}

/* ── Pagination ──────────────────────────────────────────── */
function renderPagination() {
  const total = Math.ceil(LIST.length / PER) || 1;
  document.getElementById('page-info').textContent = `Page ${PAGE} / ${total}`;

  let pages = [];
  if (total <= 7) pages = Array.from({length:total},(_,i)=>i+1);
  else {
    pages = [1];
    if (PAGE > 3) pages.push('…');
    for (let p = Math.max(2,PAGE-1); p <= Math.min(total-1,PAGE+1); p++) pages.push(p);
    if (PAGE < total-2) pages.push('…');
    pages.push(total);
  }

  let html = `<button class="page-btn" onclick="goPage(${PAGE-1})" ${PAGE===1?'disabled':''}>←</button>`;
  pages.forEach(p => {
    if (p === '…') html += `<button class="page-btn" disabled>…</button>`;
    else html += `<button class="page-btn ${p===PAGE?'active':''}" onclick="goPage(${p})">${p}</button>`;
  });
  html += `<button class="page-btn" onclick="goPage(${PAGE+1})" ${PAGE>=total?'disabled':''}>→</button>`;
  document.getElementById('page-btns').innerHTML = html;
}

function goPage(p) {
  const total = Math.ceil(LIST.length / PER) || 1;
  if (p < 1 || p > total) return;
  PAGE = p;
  renderTable();
  document.querySelector('.table-section').scrollIntoView({behavior:'smooth',block:'start'});
}

/* ── Modal ───────────────────────────────────────────────── */
function openModal(idx) {
  const r = LIST[idx];
  if (!r) return;

  document.getElementById('modal-title').textContent    = r.title;
  document.getElementById('modal-subtitle').textContent = r.location;

  const pClass = r.deal_pct >= 0 ? 'pos' : 'neg';
  const pSign  = r.deal_pct >= 0 ? '+' : '';

  const pctEl = document.getElementById('modal-score-pct');
  pctEl.textContent = `${pSign}${r.deal_pct.toFixed(2)}%`;
  pctEl.className = `modal-score-big ${pClass}`;

  document.getElementById('modal-score-save').textContent =
    r.deal_score >= 0
      ? `Save ${r.deal_score_fmt}`
      : `${r.deal_score_fmt} above FMV`;

  document.getElementById('modal-score-tag').textContent = r.deal_tag;

  const rows = [
    ['Listing Price',   r.actual_price_fmt],
    ['Predicted FMV',   r.predicted_fmv_fmt],
    ['Dataset',         r.source || 'N/A'],
    ['Total Area',      `${r.total_area.toLocaleString('en-IN')} sqft`],
    ['Price / sqft',    `Rs ${r.price_per_sqft.toLocaleString('en-IN')}`],
    ['Configuration',   `${r.bhk} BHK / ${r.baths} Bath`],
    ['Balcony',         r.balcony],
    ['Property Type',   r.property_type],
    ['City',            r.city],
    ['Deal Rank',       `#${r.rank}`],
  ];

  document.getElementById('modal-body').innerHTML = rows.map(([label, val]) => `
    <div class="modal-row">
      <span class="modal-row-label">${label}</span>
      <span class="modal-row-value">${esc(String(val))}</span>
    </div>`).join('');

  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}
function closeModalOutside(e) {
  if (e.target.id === 'modal-overlay') closeModal();
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* ── Scatter Range Slider ────────────────────────────────── */
function onScatterRangeSelect() {
  const val = document.getElementById('scatter-range').value;
  const [min, max] = val.split(',').map(Number);
  updateScatterChart(min, max);
}

function updateScatterChart(min, max) {
  if (!SCATTER_CHART) return;
  const minInr = min * 1e7;
  const maxInr = max * 1e7;

  SCATTER_CHART.data.datasets.forEach((ds, i) => {
    if (ds.label === 'Fair Price') return;
    // Filter points in range
    ds.data = SCATTER_FULL[i]
      ? SCATTER_FULL[i].filter(pt => pt.x >= min && pt.x <= max)
      : ds.data;
  });

  // Update fair price line
  const lastDs = SCATTER_CHART.data.datasets[SCATTER_CHART.data.datasets.length - 1];
  lastDs.data = [{x: min, y: min}, {x: max, y: max}];

  const range = max - min;
  let step = 0.5;
  if (range <= 0.1) step = 0.02;
  else if (range <= 0.3) step = 0.05;
  else if (range <= 1.0) step = 0.1;
  else if (range <= 2.0) step = 0.2;

  if (!SCATTER_CHART.options.scales.x.ticks) SCATTER_CHART.options.scales.x.ticks = {};
  if (!SCATTER_CHART.options.scales.y.ticks) SCATTER_CHART.options.scales.y.ticks = {};
  
  SCATTER_CHART.options.scales.x.ticks.stepSize = step;
  SCATTER_CHART.options.scales.y.ticks.stepSize = step;

  SCATTER_CHART.options.scales.x.min = min;
  SCATTER_CHART.options.scales.x.max = max;
  SCATTER_CHART.options.scales.y.min = 0;
  SCATTER_CHART.options.scales.y.max = max * 1.2;
  SCATTER_CHART.update();
}

/* ── Charts ──────────────────────────────────────────────── */

// Muted color palette — less bright and more transparent to reduce clustering
const COLORS = {
  hot:  { fill: 'rgba(15, 115, 55,  0.80)', border: 'rgba(10, 90, 40,  1.0)' },
  good: { fill: 'rgba(34, 180, 90,  0.35)', border: 'rgba(34, 180, 90,  0.5)' },
  fair: { fill: 'rgba(200, 200, 200,0.35)', border: 'rgba(200,200,200, 0.6)' },
  over: { fill: 'rgba(210, 55,  55,  0.45)', border: 'rgba(210, 55,  55,  0.7)' },
  deep: { fill: 'rgba(160, 30,  30,  0.60)', border: 'rgba(160, 30,  30,  0.9)' },
  cyan: { fill: 'rgba(0,   185, 220, 0.45)', border: 'rgba(0,  185, 220, 0.7)' },
};

const TAG_COLOR_MAP = {
  'Hot Deal':            COLORS.hot.fill,
  'Good Deal':           COLORS.good.fill,
  'Fair Price':          COLORS.fair.fill,
  'Slightly Overpriced': COLORS.over.fill,
  'Overpriced':          COLORS.deep.fill,
};

const TIP = {
  backgroundColor: '#0e0e0e',
  borderColor: 'rgba(0,185,220,0.2)',
  borderWidth: 1,
  titleColor: '#e0e0e0',
  bodyColor: '#666',
  padding: 10,
};

const AXIS = (label) => ({
  title: { display: !!label, text: label, color: '#888888', font: { size: 11 } },
  ticks: { color: '#666666' },
  border: { display: true, color: 'rgba(255,255,255,0.35)', width: 1 },
  grid:  { color: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.35)', drawBorder: true },
});

// Full per-tag data for scatter zoom
let SCATTER_FULL = [];

function buildScatterChart(scatter) {
  // Group by tag
  const tagOrder = ['Hot Deal','Good Deal','Fair Price','Slightly Overpriced','Overpriced'];
  const groups = {};
  tagOrder.forEach(t => groups[t] = []);
  scatter.forEach(d => {
    const tag = d.tag;
    const normTag = tagOrder.find(t => tag.includes(t.split(' ')[0])) || 'Fair Price';
    const pt = { x: d.actual / 1e7, y: d.fmv / 1e7 };
    if (groups[normTag]) groups[normTag].push(pt);
  });

  const datasets = tagOrder.map(tag => ({
    label: tag,
    data: groups[tag],
    backgroundColor: TAG_COLOR_MAP[tag] || COLORS.fair.fill,
    pointRadius: 2.0,       // smaller points
    pointHoverRadius: 4.0,  // smaller hover
  }));

  SCATTER_FULL = datasets.map(d => [...d.data]);

  // Fair price line
  const maxVal = Math.max(...scatter.map(d => Math.max(d.actual, d.fmv))) / 1e7;
  datasets.push({
    label: 'Fair Price',
    data: [{x:0,y:0},{x:maxVal,y:maxVal}],
    type: 'line',
    borderColor: 'rgba(255,255,255,0.07)',
    borderDash: [4,4],
    borderWidth: 1,
    pointRadius: 0,
    fill: false,
  });

  const canvas = document.getElementById('scatterChart');
  if (SCATTER_CHART) SCATTER_CHART.destroy();

  SCATTER_CHART = new Chart(canvas, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 300 },
      plugins: {
        legend: {
          labels: { color: '#555', font: { size: 10 }, boxWidth: 10, padding: 10 }
        },
        tooltip: { ...TIP, callbacks: {
          label: ctx => ctx.dataset.label === 'Fair Price' ? null
            : [`List: Rs ${ctx.parsed.x.toFixed(2)} Cr`, `FMV:  Rs ${ctx.parsed.y.toFixed(2)} Cr`]
        }}
      },
      scales: {
        x: { ...AXIS('Listing Price (Rs Cr)'), min: 0, max: maxVal },
        y: { ...AXIS('Predicted FMV (Rs Cr)'), min: 0 },
      }
    }
  });
}

function buildCityChart(cityData) {
  const top = cityData
    .filter(d => d.count >= 5)
    .sort((a,b) => b.avg_deal_pct - a.avg_deal_pct)
    .slice(0, 14);

  new Chart(document.getElementById('cityChart'), {
    type: 'bar',
    data: {
      labels: top.map(d => d.City),
      datasets: [{
        label: 'Avg Deal %',
        data: top.map(d => +d.avg_deal_pct.toFixed(2)),
        backgroundColor: top.map(d =>
          // positive = muted green, negative = muted red
          d.avg_deal_pct >= 0 ? 'rgba(34, 160, 80, 0.70)' : 'rgba(200, 55, 55, 0.65)'
        ),
        borderRadius: 3,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { ...TIP, callbacks: {
          label: ctx => `${ctx.parsed.y > 0 ? '+' : ''}${ctx.parsed.y}%`
        }}
      },
      scales: {
        x: { ticks: { color: '#444', font:{size:10} }, grid: { display: false } },
        y: { ...AXIS('Deal %') }
      },
    }
  });
}

function buildDistChart(dist) {
  const labels = Object.keys(dist);
  const vals   = Object.values(dist);

  // Check if we have data
  const total = vals.reduce((a,b) => a+b, 0);
  if (total === 0) return;

  const labelsWithPct = labels.map((label, i) => {
    const pct = ((vals[i] / total) * 100).toFixed(1);
    return `${label} (${pct}%)`;
  });

  // Distinct visible colors: deep red → red → white → light green → green
  const colors = [
    'rgba(155, 28,  28,  0.90)',   // Overpriced      — deep red
    'rgba(210, 65,  65,  0.80)',   // Slightly Over   — mid red
    'rgba(230, 230, 230, 0.90)',   // Fair Price       — near white
    'rgba(34,  160, 80,  0.75)',   // Good Deal        — muted green
    'rgba(15,  100, 45,  1.00)',   // Hot Deal         — very deep green
  ];

  new Chart(document.getElementById('distChart'), {
    type: 'doughnut',
    data: {
      labels: labelsWithPct,
      datasets: [{
        data: vals,
        backgroundColor: colors,
        borderColor: '#080808',
        borderWidth: 3,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#555', font:{size:10}, padding:12, boxWidth:10 }
        },
        tooltip: { ...TIP, callbacks:{
          label: ctx => ` ${ctx.label}: ${ctx.parsed.toLocaleString('en-IN')} (${((ctx.parsed/total)*100).toFixed(1)}%)`
        }}
      }
    }
  });
}

function buildBubbleChart(listings) {
  const types = [...new Set(listings.map(l => l.property_type))].slice(0, 6);

  // Muted distinct colors per type
  const typeColors = {
    'Flat':             'rgba(0,   175, 210, 0.55)',
    'Villa':            'rgba(30,  155, 75,  0.55)',
    'Independent House':'rgba(180, 120, 0,   0.50)',
    'Studio':           'rgba(150, 80,  180, 0.50)',
    'Penthouse':        'rgba(0,   200, 170, 0.50)',
    'Other':            'rgba(120, 120, 120, 0.40)',
    'Plot':             'rgba(90,  90,  90,  0.45)',
  };

  const datasets = types.map(type => ({
    label: type,
    data: listings
      .filter(l => l.property_type === type)
      .sort(() => Math.random() - 0.5)
      .slice(0, 80)
      .map(l => ({
        x: l.total_area,
        y: l.actual_price / 1e5,
        // Smaller bubbles: r from 2 to 7 based on BHK
        r: Math.max(2, Math.min(7, l.bhk * 1.5)),
      })),
    backgroundColor: typeColors[type] || 'rgba(120,120,120,0.4)',
  }));

  new Chart(document.getElementById('bubbleChart'), {
    type: 'bubble',
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { labels: { color: '#555', font:{size:10}, boxWidth:10 } },
        tooltip: { ...TIP, callbacks:{
          label: ctx => [
            `${ctx.dataset.label}`,
            `Area: ${ctx.parsed.x.toLocaleString('en-IN')} sqft`,
            `Price: Rs ${ctx.parsed.y.toFixed(1)} L`,
          ]
        }}
      },
      scales: { x: AXIS('Area (sqft)'), y: AXIS('Price (Rs L)') },
    }
  });
}

/* ── Utility ─────────────────────────────────────────────── */
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
