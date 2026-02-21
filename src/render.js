// render.js — Horizontal badge layout (static mode, v2.1)

import { getState } from './state.js';
import { subCatName, linkCatName } from './taxonomy.js';

let tooltip = null;

/**
 * render(layout) — Full re-render of the UI
 */
export function render(layout) {
  renderEventLane(layout);
  renderCausalRows(layout);
  syncGridRows(layout);
  ensureTooltip();
}

// ── Event Lane ──
function renderEventLane(layout) {
  const wrapper = document.getElementById('eventScroll');
  const oldHeader = wrapper.querySelector('.event-lane-head');
  if (oldHeader) oldHeader.remove();

  const header = document.createElement('div');
  header.className = 'event-lane-head';
  header.textContent = 'イベント';
  wrapper.insertBefore(header, wrapper.firstChild);

  const container = document.getElementById('eventRows');
  container.innerHTML = '';

  for (let i = 0; i < layout.rows.length; i++) {
    const ev = layout.rows[i].event;
    const row = document.createElement('div');
    row.className = 'event-row';
    row.dataset.eventId = ev.eventId;
    row.dataset.rowIndex = String(i);

    const yearDiv = document.createElement('div');
    yearDiv.className = 'year';
    yearDiv.textContent = formatYear(ev.sortKey, ev.endKey);

    const titleDiv = document.createElement('div');
    titleDiv.className = 'title';
    titleDiv.textContent = ev.title;

    const expDiv = document.createElement('div');
    expDiv.className = 'expander';
    expDiv.setAttribute('aria-disabled', 'true');
    expDiv.textContent = '▾';

    row.appendChild(yearDiv);
    row.appendChild(titleDiv);
    row.appendChild(expDiv);
    container.appendChild(row);
  }
}

// ── Causal Rows (horizontal badges) ──
function renderCausalRows(layout) {
  const container = document.getElementById('lanes');
  container.innerHTML = '';

  // Header
  const header = document.createElement('div');
  header.className = 'causal-header';
  header.textContent = '因果要素';
  container.appendChild(header);

  const body = document.createElement('div');
  body.className = 'causal-body';
  body.id = 'causalBody';

  for (let i = 0; i < layout.rows.length; i++) {
    const rowData = layout.rows[i];
    const row = document.createElement('div');
    row.className = 'causal-row';
    row.dataset.rowIndex = String(i);

    let prevLayer = null;
    for (const entry of rowData.elements) {
      const el = entry.element;
      const sc = el.subCategory || el.layer;
      const layer = el.layer;
      const isNewBlock = prevLayer && prevLayer !== layer;

      const span = document.createElement('span');
      span.className = 'el-code';
      span.classList.add(`layer-${layer.toLowerCase()}`);

      // Layer boundary → margin-left for breathing room
      if (isNewBlock) {
        span.classList.add('block-start');
      }

      // F-UNC-00 = subdued
      if (sc === 'F-UNC-00') {
        span.classList.add('is-unc00');
      }

      span.dataset.fwViewId = entry.fwView.frameworkViewId;
      span.dataset.elementId = el.elementId;
      span.dataset.rowIndex = String(i);

      // C-PWR-02 → PWR02, F-UNC-01 → UNC01
      span.textContent = sc.replace(/^[CFPR]-/, '').replace(/-/g, '');

      if (entry.corr && entry.corr.eventId) {
        span.classList.add('has-link');
        span.dataset.linkedEventIdx = String(entry.linkedEventIdx ?? '');
        span.dataset.lcode = entry.corr.category || '';
      } else {
        span.classList.add('no-link');
      }

      // Data for tooltip
      span.dataset.seqNo = String(entry.seqNo);
      span.dataset.label = el.label || '';
      span.dataset.layer = layer;
      span.dataset.fullCode = sc;

      // Hover handlers
      span.addEventListener('mouseenter', handleBadgeEnter);
      span.addEventListener('mouseleave', handleBadgeLeave);

      row.appendChild(span);
      prevLayer = layer;
    }

    body.appendChild(row);
  }

  container.appendChild(body);
}

// ── Tooltip (no SVG overlay in static mode) ──
function ensureTooltip() {
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'hoverTooltip';
    tooltip.className = 'hover-tooltip';
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
  }
}

function handleBadgeEnter(e) {
  const badge = e.currentTarget;
  const layout = getState().layout;
  if (!layout) return;

  // Build tooltip content
  const seqNo = badge.dataset.seqNo;
  const label = badge.dataset.label;
  const lcode = badge.dataset.lcode;
  const linkedIdx = badge.dataset.linkedEventIdx;
  const ownIdx = parseInt(badge.dataset.rowIndex);

  const fullCode = badge.dataset.fullCode || badge.textContent;
  const scName = subCatName(fullCode) || '';
  let html = `<div class="tt-line1"><strong>${String(seqNo).padStart(2,'0')}</strong> ${fullCode}${scName ? '  ' + scName : ''}</div>`;
  html += `<div class="tt-label">${label || '—'}</div>`;

  if (lcode) {
    html += `<div class="tt-lcode">${lcode} ${linkCatName(lcode)}</div>`;
  }

  if (linkedIdx !== '' && linkedIdx !== undefined) {
    const li = parseInt(linkedIdx);
    if (li !== ownIdx && layout.rows[li]) {
      const linkedEvent = layout.rows[li].event;
      const diff = ownIdx - li;
      html += `<div class="tt-linked">→ ${linkedEvent.title} (↑${diff}行)</div>`;
    }
  }

  // Show tooltip
  ensureTooltip();
  tooltip.innerHTML = html;
  tooltip.style.display = 'block';

  const rect = badge.getBoundingClientRect();
  tooltip.style.left = `${rect.left}px`;
  tooltip.style.top = `${rect.bottom + 6}px`;

  // Clamp to viewport
  requestAnimationFrame(() => {
    const tr = tooltip.getBoundingClientRect();
    if (tr.right > window.innerWidth - 8) {
      tooltip.style.left = `${window.innerWidth - tr.width - 8}px`;
    }
    if (tr.bottom > window.innerHeight - 8) {
      tooltip.style.top = `${rect.top - tr.height - 6}px`;
    }
  });

}

function handleBadgeLeave() {
  if (tooltip) tooltip.style.display = 'none';
}

// ── Sync grid row heights ──
function syncGridRows(layout) {
  const { totalRows } = layout;
  const rowHeight = 48; // slightly shorter since badges are compact

  requestAnimationFrame(() => {
    const eventRowsEl = document.getElementById('eventRows');
    const causalBody = document.getElementById('causalBody');
    if (!causalBody) return;

    const heights = new Array(totalRows).fill(rowHeight);

    // Measure causal row heights
    for (let i = 0; i < causalBody.children.length && i < totalRows; i++) {
      const h = causalBody.children[i].scrollHeight + 8;
      if (h > heights[i]) heights[i] = h;
    }

    // Measure event row heights
    for (let i = 0; i < eventRowsEl.children.length && i < totalRows; i++) {
      const h = eventRowsEl.children[i].scrollHeight;
      if (h > heights[i]) heights[i] = h;
    }

    // Apply grid-template-rows
    const template = heights.map(h => `${Math.max(h, rowHeight)}px`).join(' ');

    eventRowsEl.style.gridTemplateRows = template;
    eventRowsEl.style.gridAutoRows = 'unset';

    causalBody.style.gridTemplateRows = template;
    causalBody.style.gridAutoRows = 'unset';

    // Apply individual row heights
    for (let i = 0; i < totalRows; i++) {
      const h = heights[i];
      if (eventRowsEl.children[i]) eventRowsEl.children[i].style.height = `${h}px`;
      if (causalBody.children[i]) causalBody.children[i].style.height = `${h}px`;
    }
  });
}

// ── Helpers ──
function formatYear(sortKey, endKey) {
  if (sortKey == null) return '';
  const s = sortKey < 0 ? `BC${Math.abs(sortKey)}` : String(sortKey);
  if (endKey != null) {
    const e = endKey < 0 ? `BC${Math.abs(endKey)}` : String(endKey);
    return `${s} – ${e}`;
  }
  return s;
}
