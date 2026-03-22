// ── CONFIG ────────────────────────────────────────────────────────────────────
// Cambia esta URL a la de Railway cuando hagas deploy
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://superstore-analytics-production.up.railway.app';  // ← reemplazar al hacer deploy

// ── STATE ─────────────────────────────────────────────────────────────────────
let filters = { year: '', category: '', region: '', segment: '', market: '' };
let currentPage = 1;
let charts = {};

// ── API HELPER ────────────────────────────────────────────────────────────────
async function apiFetch(path, params = {}) {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries({...filters, ...params}).filter(([,v]) => v))
  ).toString();
  const url = `${API_BASE}${path}${qs ? '?' + qs : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// ── FORMATO ───────────────────────────────────────────────────────────────────
const fmt = {
  money:  v => '$' + Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }),
  pct:    v => Number(v || 0).toFixed(1) + '%',
  num:    v => Number(v || 0).toLocaleString('en-US'),
  date:   v => v ? v.substring(0, 10) : '—',
};

// ── CHART DEFAULTS ────────────────────────────────────────────────────────────
Chart.defaults.color          = '#768390';
Chart.defaults.borderColor    = '#1e2d3d';
Chart.defaults.font.family    = "'IBM Plex Mono', monospace";
Chart.defaults.font.size      = 11;
Chart.defaults.plugins.legend.labels.boxWidth = 12;

const COLORS = {
  accent:  'rgba(0, 212, 255, 1)',
  accentT: 'rgba(0, 212, 255, 0.15)',
  green:   'rgba(57, 211, 83, 1)',
  greenT:  'rgba(57, 211, 83, 0.15)',
  yellow:  'rgba(240, 192, 64, 1)',
  yellowT: 'rgba(240, 192, 64, 0.15)',
  red:     'rgba(255, 107, 107, 1)',
  palette: [
    'rgba(0,212,255,0.8)',
    'rgba(57,211,83,0.8)',
    'rgba(240,192,64,0.8)',
    'rgba(255,107,107,0.8)',
    'rgba(180,100,255,0.8)',
    'rgba(255,180,50,0.8)',
    'rgba(100,200,255,0.8)',
  ]
};

function makeOrUpdate(id, type, data, options = {}) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (charts[id]) { charts[id].destroy(); }
  charts[id] = new Chart(ctx, { type, data, options: { responsive: true, ...options } });
}

// ── INIT FILTROS ──────────────────────────────────────────────────────────────
async function initFilters() {
  try {
    const data = await apiFetch('/api/filters');

    const setOptions = (id, values, label) => {
      const sel = document.getElementById(id);
      if (!sel) return;
      sel.innerHTML = `<option value="">${label}</option>` +
        values.map(v => `<option value="${v}">${v}</option>`).join('');
    };

    setOptions('f-year',     data.years,      'Todos los años');
    setOptions('f-category', data.categories, 'Todas las categorías');
    setOptions('f-region',   data.regions,    'Todas las regiones');
    setOptions('f-segment',  data.segments,   'Todos los segmentos');
    setOptions('f-market',   data.markets,    'Todos los mercados');

    // Eventos
    ['year','category','region','segment','market'].forEach(k => {
      const el = document.getElementById(`f-${k}`);
      if (el) el.addEventListener('change', () => {
        filters[k] = el.value;
        currentPage = 1;
        loadAll();
      });
    });
  } catch(e) {
    console.error('Error cargando filtros:', e);
  }
}

function resetFilters() {
  filters = { year: '', category: '', region: '', segment: '', market: '' };
  ['year','category','region','segment','market'].forEach(k => {
    const el = document.getElementById(`f-${k}`);
    if (el) el.value = '';
  });
  currentPage = 1;
  loadAll();
}

// ── KPIs ──────────────────────────────────────────────────────────────────────
async function loadKPIs() {
  try {
    const d = await apiFetch('/api/kpis');

    const set = (id, val, cls = '') => {
      const el = document.getElementById(id);
      if (el) { el.textContent = val; el.className = `kpi-value ${cls}`; }
    };

    set('kpi-sales',    fmt.money(d.total_sales),  'accent');
    set('kpi-profit',   fmt.money(d.total_profit), d.total_profit >= 0 ? 'positive' : 'negative');
    set('kpi-orders',   fmt.num(d.total_orders));
    set('kpi-margin',   fmt.pct(d.profit_margin),  d.profit_margin >= 0 ? 'positive' : 'negative');
    set('kpi-discount', fmt.pct(d.avg_discount * 100));
    set('kpi-rows',     fmt.num(d.total_rows));
  } catch(e) { console.error('KPI error:', e); }
}

// ── VENTAS POR MES ────────────────────────────────────────────────────────────
async function loadSalesByMonth() {
  try {
    const data = await apiFetch('/api/sales-by-month');
    const labels  = data.map(r => r.month);
    const sales   = data.map(r => r.sales);
    const profit  = data.map(r => r.profit);

    makeOrUpdate('chart-monthly', 'line', {
      labels,
      datasets: [
        {
          label: 'Ventas',
          data: sales,
          borderColor: COLORS.accent,
          backgroundColor: COLORS.accentT,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
        },
        {
          label: 'Ganancia',
          data: profit,
          borderColor: COLORS.green,
          backgroundColor: COLORS.greenT,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
        }
      ]
    }, {
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { ticks: { maxTicksLimit: 12, maxRotation: 45 } },
        y: { ticks: { callback: v => '$' + (v/1000).toFixed(0) + 'k' } }
      }
    });
  } catch(e) { console.error('Monthly error:', e); }
}

// ── VENTAS POR CATEGORÍA ──────────────────────────────────────────────────────
async function loadByCategory() {
  try {
    const data = await apiFetch('/api/sales-by-category');

    // Agrupar por categoría principal
    const byCategory = {};
    data.forEach(r => {
      if (!byCategory[r.category]) byCategory[r.category] = 0;
      byCategory[r.category] += r.sales;
    });

    const labels = Object.keys(byCategory);
    const values = Object.values(byCategory);

    makeOrUpdate('chart-category', 'doughnut', {
      labels,
      datasets: [{
        data: values,
        backgroundColor: COLORS.palette.slice(0, labels.length),
        borderWidth: 0,
        hoverOffset: 8,
      }]
    }, {
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { callbacks: { label: ctx => ` ${fmt.money(ctx.raw)}` } }
      },
      cutout: '65%',
    });

    // Sub-categorías en tabla
    const tbody = document.getElementById('cat-tbody');
    if (tbody) {
      tbody.innerHTML = data.slice(0, 12).map(r => `
        <tr>
          <td>${badgeCategory(r.category)}</td>
          <td>${r.sub_category}</td>
          <td class="td-mono">${fmt.money(r.sales)}</td>
          <td class="td-mono ${r.profit >= 0 ? 'positive' : 'negative'}">${fmt.money(r.profit)}</td>
          <td class="td-mono">${fmt.pct(r.margin)}</td>
        </tr>`).join('');
    }
  } catch(e) { console.error('Category error:', e); }
}

function badgeCategory(cat) {
  const map = { 'Technology': 'badge-tech', 'Furniture': 'badge-furniture', 'Office Supplies': 'badge-office' };
  return `<span class="badge ${map[cat] || ''}">${cat}</span>`;
}

// ── VENTAS POR REGIÓN ─────────────────────────────────────────────────────────
async function loadByRegion() {
  try {
    const data = await apiFetch('/api/sales-by-region');
    const labels = data.map(r => r.region);
    const sales  = data.map(r => r.sales);
    const profit = data.map(r => r.profit);

    makeOrUpdate('chart-region', 'bar', {
      labels,
      datasets: [
        {
          label: 'Ventas',
          data: sales,
          backgroundColor: COLORS.palette,
          borderRadius: 3,
        },
        {
          label: 'Ganancia',
          data: profit,
          backgroundColor: COLORS.palette.map(c => c.replace('0.8)', '0.4)')),
          borderRadius: 3,
        }
      ]
    }, {
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { stacked: false },
        y: { ticks: { callback: v => '$' + (v/1000).toFixed(0) + 'k' } }
      }
    });
  } catch(e) { console.error('Region error:', e); }
}

// ── TENDENCIA ANUAL ───────────────────────────────────────────────────────────
async function loadYearlyTrend() {
  try {
    const data = await apiFetch('/api/yearly-trend');
    const labels = data.map(r => String(r.year));
    const sales  = data.map(r => r.sales);
    const margin = data.map(r => r.margin);

    makeOrUpdate('chart-trend', 'bar', {
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Ventas',
          data: sales,
          backgroundColor: COLORS.accentT,
          borderColor: COLORS.accent,
          borderWidth: 1,
          borderRadius: 3,
          yAxisID: 'y',
        },
        {
          type: 'line',
          label: 'Margen %',
          data: margin,
          borderColor: COLORS.yellow,
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 4,
          tension: 0.3,
          yAxisID: 'y2',
        }
      ]
    }, {
      plugins: { legend: { position: 'top' } },
      scales: {
        y:  { ticks: { callback: v => '$' + (v/1000).toFixed(0) + 'k' } },
        y2: { position: 'right', ticks: { callback: v => v + '%' }, grid: { drawOnChartArea: false } }
      }
    });
  } catch(e) { console.error('Trend error:', e); }
}

// ── SEGMENTOS ─────────────────────────────────────────────────────────────────
async function loadSegments() {
  try {
    const data = await apiFetch('/api/sales-by-segment');
    const labels = data.map(r => r.segment);
    const sales  = data.map(r => r.sales);

    makeOrUpdate('chart-segment', 'polarArea', {
      labels,
      datasets: [{
        data: sales,
        backgroundColor: COLORS.palette.slice(0, labels.length).map(c => c.replace('0.8)', '0.6)')),
        borderWidth: 0,
      }]
    }, {
      plugins: { legend: { position: 'bottom' } },
      scales: { r: { ticks: { backdropColor: 'transparent' } } }
    });
  } catch(e) { console.error('Segments error:', e); }
}

// ── TABLA DE ÓRDENES ──────────────────────────────────────────────────────────
async function loadOrders(page = 1) {
  currentPage = page;
  const tbody    = document.getElementById('orders-tbody');
  const pageInfo = document.getElementById('page-info');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--muted);font-family:var(--mono);font-size:11px">cargando...</td></tr>`;

  try {
    const d = await apiFetch('/api/orders', { page, per_page: 20 });

    if (pageInfo) pageInfo.textContent = `${fmt.num(d.total)} órdenes · página ${d.page} de ${d.pages}`;

    tbody.innerHTML = d.data.map(r => `
      <tr>
        <td class="td-mono">${r.order_id}</td>
        <td class="td-mono">${fmt.date(r.order_date)}</td>
        <td>${r.customer_name}</td>
        <td>${r.country}</td>
        <td>${badgeCategory(r.category)}</td>
        <td class="td-mono">${fmt.money(r.sales)}</td>
        <td class="td-mono ${r.profit >= 0 ? 'positive' : 'negative'}">${fmt.money(r.profit)}</td>
        <td class="td-mono">${r.ship_mode}</td>
      </tr>`).join('');

    // Paginación
    renderPagination(d.page, d.pages);

  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--red);padding:20px;text-align:center">Error cargando datos</td></tr>`;
  }
}

function renderPagination(page, total) {
  const wrap = document.getElementById('pagination');
  if (!wrap) return;
  const pages = [];

  pages.push(`<button class="page-btn" onclick="loadOrders(${page-1})" ${page<=1?'disabled':''}>← Prev</button>`);

  const start = Math.max(1, page - 2);
  const end   = Math.min(total, page + 2);
  for (let i = start; i <= end; i++) {
    pages.push(`<button class="page-btn ${i===page?'active':''}" onclick="loadOrders(${i})">${i}</button>`);
  }

  pages.push(`<button class="page-btn" onclick="loadOrders(${page+1})" ${page>=total?'disabled':''}>Next →</button>`);
  wrap.innerHTML = pages.join('');
}

// ── TOP PAÍSES ────────────────────────────────────────────────────────────────
async function loadTopCountries() {
  try {
    const data = await apiFetch('/api/top-countries', { limit: 10 });
    const tbody = document.getElementById('countries-tbody');
    if (!tbody) return;
    tbody.innerHTML = data.map((r, i) => `
      <tr>
        <td class="td-mono" style="color:var(--muted)">${i+1}</td>
        <td>${r.country}</td>
        <td class="td-mono" style="color:var(--text2)">${r.region}</td>
        <td class="td-mono">${fmt.money(r.sales)}</td>
        <td class="td-mono ${r.profit >= 0 ? 'positive' : 'negative'}">${fmt.money(r.profit)}</td>
      </tr>`).join('');
  } catch(e) { console.error('Countries error:', e); }
}

// ── LOAD ALL ──────────────────────────────────────────────────────────────────
async function loadAll() {
  await Promise.all([
    loadKPIs(),
    loadSalesByMonth(),
    loadByCategory(),
    loadByRegion(),
    loadYearlyTrend(),
    loadSegments(),
    loadOrders(currentPage),
    loadTopCountries(),
  ]);
}

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await initFilters();
  await loadAll();

  // Fecha actual en header
  const dateEl = document.getElementById('current-date');
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  }
});
