// render.js — Horizontal badge layout with hover SVG lines

import { getState } from './state.js';
import { subCatName, linkCatName } from './taxonomy.js';

let svgOverlay = null;
let tooltip = null;

/**
 * render(layout) — Full re-render of the UI
 */
export function render(layout) {
  renderEventLane(layout);
  renderCausalRows(layout);
  syncGridRows(layout);
  ensureOverlay();
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

    for (const entry of rowData.elements) {
      const badge = document.createElement('span');
      badge.className = 'el-badge';
      badge.classList.add(`layer-${entry.element.layer.toLowerCase()}`);
      badge.dataset.fwViewId = entry.fwView.frameworkViewId;
      badge.dataset.elementId = entry.element.elementId;
      badge.dataset.rowIndex = String(i);

      const sc = entry.element.subCategory || entry.element.layer;
      // C-PWR-02 → PWR02
      badge.textContent = sc.replace(/^[CPR]-/, '').replace(/-/g, '');

      if (entry.corr && entry.corr.eventId) {
        badge.classList.add('has-link');
        badge.dataset.linkedEventIdx = String(entry.linkedEventIdx ?? '');
        badge.dataset.lcode = entry.corr.category || '';
      } else {
        badge.classList.add('no-link');
      }

      // Store data for tooltip
      badge.dataset.seqNo = String(entry.seqNo);
      badge.dataset.label = entry.element.label || '';
      badge.dataset.layer = entry.element.layer;
      badge.dataset.fullCode = sc;

      // Hover handlers
      badge.addEventListener('mouseenter', handleBadgeEnter);
      badge.addEventListener('mouseleave', handleBadgeLeave);

      row.appendChild(badge);
    }

    body.appendChild(row);
  }

  container.appendChild(body);
}

// ── SVG Overlay + Tooltip ──
function ensureOverlay() {
  if (!svgOverlay) {
    svgOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgOverlay.id = 'svgOverlay';
    svgOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1000;';
    document.body.appendChild(svgOverlay);
  }
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
  ensureOverlay();
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

  // Draw SVG line to linked event (if different row)
  if (linkedIdx !== '' && linkedIdx !== undefined) {
    const li = parseInt(linkedIdx);
    if (li !== ownIdx) {
      drawLinkLine(badge, li);
    }
  }
}

function handleBadgeLeave() {
  if (tooltip) tooltip.style.display = 'none';
  clearSvg();
  // Remove any highlight
  document.querySelectorAll('.event-row.is-link-target').forEach(el => {
    el.classList.remove('is-link-target');
  });
}

function drawLinkLine(badge, targetRowIdx) {
  if (!svgOverlay) return;
  clearSvg();

  const badgeRect = badge.getBoundingClientRect();

  // Find target event row
  const eventRows = document.getElementById('eventRows');
  const targetRow = eventRows.children[targetRowIdx];
  if (!targetRow) return;

  targetRow.classList.add('is-link-target');

  const targetRect = targetRow.getBoundingClientRect();

  // Badge center-left → target row center-right
  const x1 = badgeRect.left;
  const y1 = badgeRect.top + badgeRect.height / 2;
  const x2 = targetRect.right;
  const y2 = targetRect.top + targetRect.height / 2;

  // Smooth bezier curve
  const dx = Math.abs(x1 - x2) * 0.4;
  const dy = Math.abs(y1 - y2) * 0.15;

  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', `M${x1},${y1} C${x1 - dx},${y1 - dy} ${x2 + dx},${y2 + dy} ${x2},${y2}`);
  path.setAttribute('stroke', '#5b82c2');
  path.setAttribute('stroke-width', '1.5');
  path.setAttribute('fill', 'none');
  path.setAttribute('opacity', '0.5');

  // Glow effect
  const glow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  glow.setAttribute('d', path.getAttribute('d'));
  glow.setAttribute('stroke', '#5b82c2');
  glow.setAttribute('stroke-width', '6');
  glow.setAttribute('fill', 'none');
  glow.setAttribute('opacity', '0.08');

  // Target dot
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('cx', String(x2));
  circle.setAttribute('cy', String(y2));
  circle.setAttribute('r', '4');
  circle.setAttribute('fill', '#5b82c2');
  circle.setAttribute('opacity', '0.6');

  // Source dot
  const srcCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  srcCircle.setAttribute('cx', String(x1));
  srcCircle.setAttribute('cy', String(y1));
  srcCircle.setAttribute('r', '3');
  srcCircle.setAttribute('fill', '#5b82c2');
  srcCircle.setAttribute('opacity', '0.4');

  svgOverlay.appendChild(glow);
  svgOverlay.appendChild(path);
  svgOverlay.appendChild(circle);
  svgOverlay.appendChild(srcCircle);
}

function clearSvg() {
  if (svgOverlay) svgOverlay.innerHTML = '';
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
