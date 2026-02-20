// stats.js — Pattern statistics overlay

import { getState } from './state.js';
import { subCatName } from './taxonomy.js';

let overlay = null;

export function showStats() {
  if (overlay) { closeStats(); return; }

  const state = getState();
  const { events, frameworkViews, correspondences } = state;

  // ── Compute patterns ──
  const patternMap = new Map();

  for (const fv of frameworkViews) {
    const laneElements = [];
    if (fv.lanes && fv.lanes[0]) {
      const elementMap = new Map();
      for (const el of fv.elements) elementMap.set(el.elementId, el);
      for (const elId of fv.lanes[0].elements) {
        const el = elementMap.get(elId);
        if (el) laneElements.push(el);
      }
    }

    const codes = laneElements.map(el => el.subCategory || el.layer);
    const pattern = codes.join(' → ');
    const ev = events.find(e => e.eventId === fv.eventId);

    if (!patternMap.has(pattern)) {
      patternMap.set(pattern, { codes, count: 0, examples: [] });
    }
    const entry = patternMap.get(pattern);
    entry.count++;
    if (entry.examples.length < 5) {
      entry.examples.push(ev ? ev.title : fv.eventId);
    }
  }

  // ── Compute link stats ──
  let totalElements = 0;
  let linkedElements = 0;
  const lcodeCount = {};

  for (const fv of frameworkViews) {
    for (const el of fv.elements) {
      totalElements++;
      const corr = correspondences?.[fv.frameworkViewId]?.[el.elementId];
      if (corr && corr.eventId) {
        linkedElements++;
        const lc = corr.category || '未設定';
        lcodeCount[lc] = (lcodeCount[lc] || 0) + 1;
      }
    }
  }

  // ── Layer distribution ──
  const layerCount = { C: 0, P: 0, R: 0 };
  for (const fv of frameworkViews) {
    for (const el of fv.elements) {
      if (layerCount[el.layer] !== undefined) layerCount[el.layer]++;
    }
  }

  // ── Build overlay ──
  overlay = document.createElement('div');
  overlay.className = 'stats-overlay';

  const panel = document.createElement('div');
  panel.className = 'stats-panel';

  // Header
  const header = document.createElement('div');
  header.className = 'stats-header';
  header.innerHTML = `
    <span class="stats-title">統計分析</span>
    <button class="stats-close" id="statsClose">✕</button>
  `;
  panel.appendChild(header);

  const body = document.createElement('div');
  body.className = 'stats-body';

  // ── Summary cards ──
  const summary = document.createElement('div');
  summary.className = 'stats-summary';
  summary.innerHTML = `
    <div class="stats-card">
      <div class="stats-card-value">${events.length}</div>
      <div class="stats-card-label">イベント</div>
    </div>
    <div class="stats-card">
      <div class="stats-card-value">${frameworkViews.length}</div>
      <div class="stats-card-label">フレームワーク</div>
    </div>
    <div class="stats-card">
      <div class="stats-card-value">${totalElements}</div>
      <div class="stats-card-label">要素</div>
    </div>
    <div class="stats-card">
      <div class="stats-card-value">${linkedElements}</div>
      <div class="stats-card-label">リンク済</div>
    </div>
  `;
  body.appendChild(summary);

  // ── Layer distribution ──
  const layerSec = document.createElement('div');
  layerSec.className = 'stats-section';
  layerSec.innerHTML = `<div class="stats-section-title">レイヤー構成</div>`;
  const layerBar = document.createElement('div');
  layerBar.className = 'stats-bar';
  const total = layerCount.C + layerCount.P + layerCount.R;
  for (const [layer, count] of Object.entries(layerCount)) {
    const seg = document.createElement('div');
    seg.className = `stats-bar-seg layer-${layer.toLowerCase()}`;
    seg.style.width = `${(count / total * 100).toFixed(1)}%`;
    seg.title = `${layer}: ${count}件 (${(count / total * 100).toFixed(1)}%)`;
    seg.innerHTML = `<span>${layer} ${count}</span>`;
    layerBar.appendChild(seg);
  }
  layerSec.appendChild(layerBar);
  body.appendChild(layerSec);

  // ── L-code distribution ──
  const lcodeSec = document.createElement('div');
  lcodeSec.className = 'stats-section';
  lcodeSec.innerHTML = `<div class="stats-section-title">リンクカテゴリ分布</div>`;
  const lcodeList = document.createElement('div');
  lcodeList.className = 'stats-lcode-list';
  const sortedLcodes = Object.entries(lcodeCount).sort((a, b) => b[1] - a[1]);
  const maxLcode = sortedLcodes[0]?.[1] || 1;
  for (const [code, count] of sortedLcodes) {
    const row = document.createElement('div');
    row.className = 'stats-lcode-row';
    row.innerHTML = `
      <span class="stats-lcode-code">${code}</span>
      <div class="stats-lcode-bar-bg">
        <div class="stats-lcode-bar-fill" style="width:${(count / maxLcode * 100).toFixed(1)}%"></div>
      </div>
      <span class="stats-lcode-count">${count}</span>
    `;
    lcodeList.appendChild(row);
  }
  lcodeSec.appendChild(lcodeList);
  body.appendChild(lcodeSec);

  // ── Pattern analysis ──
  const patternSec = document.createElement('div');
  patternSec.className = 'stats-section';

  const sorted = [...patternMap.entries()]
    .sort((a, b) => b[1].count - a[1].count);
  const repeating = sorted.filter(([, v]) => v.count >= 2);
  const repeatingFwCount = repeating.reduce((s, [, v]) => s + v.count, 0);

  patternSec.innerHTML = `
    <div class="stats-section-title">
      因果パターン分析
      <span class="stats-section-sub">${patternMap.size}種類中 ${repeating.length}種が複数回出現（${repeatingFwCount}/${frameworkViews.length} FW）</span>
    </div>
  `;

  const patternList = document.createElement('div');
  patternList.className = 'stats-pattern-list';

  for (const [pattern, { codes, count, examples }] of sorted) {
    if (count < 2) continue;

    const item = document.createElement('div');
    item.className = 'stats-pattern-item';

    // Badge row
    const badgeRow = document.createElement('div');
    badgeRow.className = 'stats-pattern-badges';

    const countBadge = document.createElement('span');
    countBadge.className = 'stats-pattern-count';
    countBadge.textContent = `×${count}`;
    badgeRow.appendChild(countBadge);

    for (const code of codes) {
      const badge = document.createElement('span');
      const layer = code.charAt(0).toLowerCase();
      badge.className = `el-badge layer-${layer} has-link stats-badge-tip`;
      badge.textContent = code.replace(/^[CPR]-/, '').replace(/-/g, '');
      badge.dataset.tip = `${code}  ${subCatName(code)}`;
      badgeRow.appendChild(badge);
    }
    item.appendChild(badgeRow);

    // Examples
    const exList = document.createElement('div');
    exList.className = 'stats-pattern-examples';
    for (const ex of examples) {
      const exItem = document.createElement('div');
      exItem.className = 'stats-pattern-example';
      exItem.textContent = ex;
      exList.appendChild(exItem);
    }
    if (count > examples.length) {
      const more = document.createElement('div');
      more.className = 'stats-pattern-more';
      more.textContent = `他 ${count - examples.length}件`;
      exList.appendChild(more);
    }
    item.appendChild(exList);

    patternList.appendChild(item);
  }

  patternSec.appendChild(patternList);
  body.appendChild(patternSec);

  panel.appendChild(body);
  overlay.appendChild(panel);
  document.body.appendChild(overlay);

  // Close handlers
  document.getElementById('statsClose').addEventListener('click', closeStats);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeStats();
  });
}

export function closeStats() {
  if (overlay) {
    overlay.remove();
    overlay = null;
  }
}
