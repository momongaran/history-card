// ============================================================
// shared.js — 全ビュー・図鑑共通の定数・パターンID計算
// <script src="shared.js"></script> で読み込む（グローバル変数）
// ============================================================

const APP_VERSION = { hash: '', date: '2026-03-30', label: 'v0.9.1' };

// ── データソース一覧 ──
const ALL_SOURCES = [
  '../data/energyabs_v2.json',
  '../data/energyabs_europe_v1.json',
  '../data/energyabs_middleeast_v1.json',
  '../data/energyabs_india_v1.json',
  '../data/energyabs_china_v1.json',
  '../data/energyabs_americas_v1.json',
  '../data/energyabs_capitalism_standalone.json',
  '../data/energyabs_braudel_v1.json',
];

// ── fwType スタイル定義 ──
const FW_TYPE_STYLES = {
  'battle':      { color: '#c45a3c', shape: '⚔', label: '武力衝突', labelFull: '武力衝突・戦い' },
  'conflict':    { color: '#c8960a', shape: '▲', label: '対立蓄積', labelFull: '対立・緊張蓄積' },
  'collapse':    { color: '#8a3a3a', shape: '⊘', label: '崩壊', labelFull: '崩壊・滅亡' },
  'institution': { color: '#3a6a9a', shape: '■', label: '制度化', labelFull: '制度化・ルール化' },
  'power':       { color: '#6a3a8a', shape: '◆', label: '権力確立', labelFull: '権力確立・体制形成' },
  'shock':       { color: '#c47a3a', shape: '⚡', label: '外生衝撃', labelFull: '外生衝撃・外来要因' },
  'drift':       { color: '#5a8a5a', shape: '〜', label: '漸進変化', labelFull: '漸進的浸透・構造変化' },
  'reform':      { color: '#3a7a8a', shape: '✦', label: '改革', labelFull: '改革・変革' },
};

// ── bgType スタイル定義（図鑑 BG 定義に準拠） ──
const BG_TYPE_STYLES = {
  '構造変化':   { icon: '⇄', color: '#5a8a5a' },
  '武力衝突':   { icon: '⚔', color: '#c45a3c' },
  '勢力対立':   { icon: '⚡', color: '#c8960a' },
  '制度':       { icon: '■', color: '#3a6a9a' },
  '制度構築':   { icon: '■', color: '#3a6a9a' },
  '外生':       { icon: '☄', color: '#c47a3a' },
  '権力集中':   { icon: '◆', color: '#6a3a8a' },
  '改革':       { icon: '✦', color: '#3a7a8a' },
  '崩壊':       { icon: '⊘', color: '#8a3a3a' },
  '外圧':       { icon: '⟐', color: '#8a6a3a' },
  '経済拡大':   { icon: '▲', color: '#5a8a3a' },
  '硬直化':     { icon: '▰', color: '#6a6058' },
  '複合背景':   { icon: '◎', color: '#6a6058' },
  '思想潮流':   { icon: '〜', color: '#5a7a8a' },
  '経済圧':     { icon: '▲', color: '#5a8a3a' },
  '制度疲弊':   { icon: '▰', color: '#6a6058' },
  '制度的矛盾': { icon: '⊘', color: '#8a5a3a' },
  '外圧環境':   { icon: '⟐', color: '#8a6a3a' },
  '権力分散':   { icon: '◇', color: '#7a6a8a' },
  '自生':       { icon: '●', color: '#5a8a5a' },
  // releaseType 同義語（patNorm準拠）
  '制度化':     { icon: '■', color: '#3a6a9a' },
  '外生衝撃':   { icon: '⟐', color: '#8a6a3a' },
  '対立蓄積':   { icon: '⚡', color: '#c8960a' },
  '戦闘':       { icon: '⚔', color: '#c45a3c' },
  '権力確立':   { icon: '◆', color: '#6a3a8a' },
  '権力移行':   { icon: '◆', color: '#6a3a8a' },
  '衝撃':       { icon: '⟐', color: '#8a6a3a' },
};

// ── パターンID計算 ──
const PAT_SYNONYMS = {
  '制度':'制度','制度化':'制度','制度構築':'制度',
  '武力衝突':'武力衝突','戦闘':'武力衝突',
  '権力集中':'権力集中','権力確立':'権力集中','権力移行':'権力集中',
  '勢力対立':'勢力対立','対立蓄積':'勢力対立',
  '外圧':'外圧','外生':'外圧',
  '構造変化':'構造変化','改革':'改革','崩壊':'崩壊',
  '経済拡大':'経済圧','経済成長':'経済圧','経済圧':'経済圧',
  '硬直化':'制度疲弊','制度疲弊':'制度疲弊',
  '制度的矛盾':'制度的矛盾','思想潮流':'思想潮流',
  '複合背景':'複合背景','権力分散':'権力分散','自生':'自生',
  '外生衝撃':'外圧','衝撃':'外圧','蓄積':'勢力対立',
};

const PAT_PREFIX = {
  battle:'B', collapse:'L', conflict:'C', drift:'D',
  institution:'I', power:'P', reform:'R', shock:'S',
};

function patNorm(t) { return PAT_SYNONYMS[t] || t || '?'; }

function patKey(n) {
  const b = patNorm(n.bgType || '?');
  const r = n.releaseType ? patNorm(n.releaseType) : null;
  return r && r !== b ? b + '→' + r : b;
}
const patKeyOf = patKey; // alias for backward compatibility

// PAT_ID_MAP: "fwType|patKey" → stable pattern ID (e.g. "D01")
let PAT_ID_MAP = {};

function nodePatId(n) {
  return PAT_ID_MAP[n.fwType + '|' + patKey(n)] || null;
}

// ── ページナビゲーション（共通） ──
const PAGE_NAV = [
  { href: 'demo_catalog.html',            label: '日本史' },
  { href: 'demo_catalog_world.html',      label: '世界史' },
  { href: 'demo_catalog_europe.html',     label: '欧州史' },
  { href: 'demo_pattern_fwtype.html',     label: 'パターン図鑑' },
  { href: 'demo_slot_taxonomy.html',      label: 'スロット分類' },
  { href: 'demo_taxonomy_reference.html', label: '用語・分類リファレンス' },
];

// テストページ（パスワード保護）
const TEST_PAGES = [
  { href: 'demo_capitalism.html',       label: '資本主義の誕生' },
  { href: 'demo_braudel.html',          label: 'ブローデルの地中海' },
  { href: 'demo_pattern_catalog.html',  label: 'パターン図鑑詳細' },
  { href: 'demo_catalog_fallacy.html',  label: 'ファラシー' },
  { href: 'demo_pattern_language.html', label: 'パターンランゲージ' },
  { href: 'demo_foucault.html',        label: '監獄の誕生' },
];
const TEST_PASSWORD = 'history2026';

// ナビCSS注入（各HTMLから重複定義を排除するため）
(function injectNavCSS() {
  if (document.getElementById('page-nav-css')) return;
  const style = document.createElement('style');
  style.id = 'page-nav-css';
  style.textContent = `
    .page-nav {
      display:flex; gap:12px; font-size:12px; flex-wrap:wrap;
      max-width:1600px; margin:0 auto; padding:24px 20px 8px;
      align-items:center;
    }
    .page-nav a {
      color:var(--accent,#5c3d1e); text-decoration:none; padding:3px 10px;
      border:1.5px solid var(--line,#c9b89e); border-radius:14px; transition:all .2s;
    }
    .page-nav a:hover { background:var(--accent,#5c3d1e); color:#fff; border-color:var(--accent,#5c3d1e); }
    .page-nav-current {
      padding:3px 10px; border:1.5px solid var(--accent,#5c3d1e); border-radius:14px;
      background:var(--accent,#5c3d1e); color:#fff; font-weight:600;
    }
    .test-menu-wrap { position:relative; display:inline-block; }
    .test-menu-btn {
      color:var(--muted,#6a6058); padding:3px 10px; cursor:pointer;
      border:1.5px dashed var(--line,#c9b89e); border-radius:14px;
      font-size:12px; background:none; font-family:inherit; transition:all .2s;
    }
    .test-menu-btn:hover { border-color:var(--accent,#5c3d1e); color:var(--accent,#5c3d1e); }
    .test-menu-drop {
      display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:200;
      background:#fffdf8; border:1.5px solid var(--line,#c9b89e); border-radius:10px;
      padding:8px 0; min-width:180px; box-shadow:0 4px 16px rgba(40,28,14,.12);
    }
    .test-menu-drop.open { display:block; }
    .test-menu-drop a {
      display:block; padding:6px 16px; font-size:12px; border:none; border-radius:0;
      color:var(--ink,#28231e); text-decoration:none;
    }
    .test-menu-drop a:hover { background:#f0ebe0; color:var(--accent,#5c3d1e); }
  `;
  document.head.appendChild(style);
})();

function renderPageNav() {
  const el = document.getElementById('page-nav');
  if (!el) return;
  // ナビを .page の外に移動（各ページの .page の padding/max-width に依存しない）
  const page = el.closest('.page');
  if (page && page.parentNode) {
    page.parentNode.insertBefore(el, page);
  }
  const here = location.pathname.split('/').pop();
  const isTestPage = TEST_PAGES.some(p => p.href === here);

  // 通常ナビ
  let html = PAGE_NAV.map(p => {
    if (p.href === here) {
      return `<span class="page-nav-current">${p.label}</span>`;
    }
    return `<a href="${p.href}">${p.label}</a>`;
  }).join('\n    ');

  // テストメニュー
  const testItems = TEST_PAGES.map(p => {
    if (p.href === here) {
      return `<span style="display:block;padding:6px 16px;font-size:12px;font-weight:600;color:var(--accent,#5c3d1e)">${p.label}</span>`;
    }
    return `<a href="#" data-test-href="${p.href}">${p.label}</a>`;
  }).join('');

  html += `
    <span class="test-menu-wrap">
      <button class="test-menu-btn" id="test-menu-toggle">${isTestPage ? '◉' : '○'} テスト</button>
      <div class="test-menu-drop" id="test-menu-drop">${testItems}</div>
    </span>
    <span style="margin-left:auto;font-size:10px;color:#b0a898;font-family:monospace;letter-spacing:.05em" title="${APP_VERSION.date} ${APP_VERSION.hash}">${APP_VERSION.label}</span>`;

  el.className = 'page-nav';
  el.innerHTML = html;

  // テストメニュー開閉
  const toggle = document.getElementById('test-menu-toggle');
  const drop = document.getElementById('test-menu-drop');
  toggle.addEventListener('click', (ev) => {
    ev.stopPropagation();
    drop.classList.toggle('open');
  });
  document.addEventListener('click', () => drop.classList.remove('open'));

  // パスワード認証してから遷移
  drop.querySelectorAll('a[data-test-href]').forEach(a => {
    a.addEventListener('click', (ev) => {
      ev.preventDefault();
      if (sessionStorage.getItem('test_auth') === '1') {
        location.href = a.dataset.testHref;
        return;
      }
      const pw = prompt('テストページのパスワードを入力してください');
      if (pw === TEST_PASSWORD) {
        sessionStorage.setItem('test_auth', '1');
        location.href = a.dataset.testHref;
      } else if (pw !== null) {
        alert('パスワードが違います');
      }
    });
  });
}

// 自動実行: DOM準備後にナビを描画
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderPageNav);
} else {
  renderPageNav();
}

// ============================================================
// 共通ブロック・エッジ描画モジュール
// ============================================================

// ── エッジ要素セレクタ（全ページ共通） ──
const EDGE_SEL = '.edge-line, .edge-head, .edge-dot, .edge-halo';

// ── ロール定義 ──
const ROLE_COLORS = {
  amplifies: '#c8960a', triggers: '#c45a3c', transforms: '#3a6a9a',
  sustains: '#3a8a3a', suppresses: '#7a3a8a', inherits: '#3a7a8a'
};
const ROLE_JA = {
  amplifies: '増幅', triggers: '発火', transforms: '変換',
  sustains: '維持', suppresses: '抑制', inherits: '継承'
};

// ── 共通CSS注入 ──
(function injectBlockCSS() {
  if (document.getElementById('block-css')) return;
  const s = document.createElement('style');
  s.id = 'block-css';
  s.textContent = `
    /* Canvas */
    .canvas {
      position:relative; background:var(--bg,#f0ebe0);
      border:1px solid #d8cebb; border-radius:20px;
      box-shadow:0 8px 28px rgba(40,28,14,.10);
      padding:30px 24px; overflow-x:auto;
    }
    .canvas::before {
      content:''; position:absolute; inset:0; border-radius:20px;
      background-image:
        linear-gradient(rgba(200,188,168,.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(200,188,168,.08) 1px, transparent 1px);
      background-size:40px 40px; pointer-events:none;
    }
    /* SVG layer */
    #edge-svg {
      position:absolute; inset:0; width:100%; height:100%;
      pointer-events:none; z-index:2;
    }
    .edge-line { fill:none; stroke-width:1.4; opacity:0.45; stroke-dasharray:5 4; stroke:#b0a898; }
    .edge-dot  { stroke:none; fill:#b0a898; opacity:0.5; }
    .edge-halo { pointer-events:none; }
    .edge-head { stroke:none; fill:#b0a898; opacity:0.6; }
    .edge-line.hl { opacity:0.85; stroke-width:2.5; }
    .edge-head.hl, .edge-dot.hl { opacity:0.85; }
    .edge-line.dim, .edge-head.dim, .edge-dot.dim, .edge-halo.dim { opacity:0.08; }
    /* role colors */
    .edge-line.r-amplifies  { stroke:#c8960a; }
    .edge-line.r-triggers   { stroke:#c45a3c; }
    .edge-line.r-transforms { stroke:#3a6a9a; }
    .edge-line.r-sustains   { stroke:#3a8a3a; }
    .edge-line.r-suppresses { stroke:#7a3a8a; }
    .edge-line.r-inherits   { stroke:#3a7a8a; }
    .edge-dot.r-amplifies   { fill:#c8960a; }
    .edge-dot.r-triggers    { fill:#c45a3c; }
    .edge-dot.r-transforms  { fill:#3a6a9a; }
    .edge-dot.r-sustains    { fill:#3a8a3a; }
    .edge-dot.r-suppresses  { fill:#7a3a8a; }
    .edge-dot.r-inherits    { fill:#3a7a8a; }
    .edge-head.r-amplifies  { fill:#c8960a; }
    .edge-head.r-triggers   { fill:#c45a3c; }
    .edge-head.r-transforms { fill:#3a6a9a; }
    .edge-head.r-sustains   { fill:#3a8a3a; }
    .edge-head.r-suppresses { fill:#7a3a8a; }
    .edge-head.r-inherits   { fill:#3a7a8a; }
    .role-arrow { display:inline; font-size:9px; line-height:1; margin-left:2px; }
    .role-arrow.r-amplifies  { color:#c8960a; }
    .role-arrow.r-triggers   { color:#c45a3c; }
    .role-arrow.r-transforms { color:#3a6a9a; }
    .role-arrow.r-sustains   { color:#3a8a3a; }
    .role-arrow.r-suppresses { color:#7a3a8a; }
    .role-arrow.r-inherits   { color:#3a7a8a; }
    /* Block row */
    .block-row {
      position:relative; z-index:1;
      display:flex; gap:16px; margin-bottom:12px;
      flex-wrap:wrap; justify-content:center;
    }
    /* Block */
    .block {
      width:var(--block-w,380px); background:var(--paper,#fffdf8);
      border:2px solid #b8a898; border-radius:var(--block-radius,14px);
      box-shadow:var(--shadow,0 6px 20px rgba(40,28,14,.08));
      position:relative; transition:border-color .3s, box-shadow .3s, opacity .3s;
      cursor:pointer; flex:0 0 auto;
    }
    .block:hover { box-shadow:0 8px 28px rgba(40,28,14,.15); }
    .block.hl   { box-shadow:0 0 0 5px rgba(92,61,30,.25); }
    .block.dim  { opacity:0.2; }
    .block.source-hl { box-shadow:0 0 0 4px rgba(92,61,30,.18); }
    .block-body { padding:12px 14px 24px; display:flex; flex-direction:column; gap:6px; }
    /* Inner area: incoming edges */
    .block-inner {
      border:1.5px solid #ddd4c8; border-radius:10px;
      background:linear-gradient(180deg, #faf7f0, #f5f1e8);
      padding:6px 8px; display:flex; gap:6px; flex-wrap:wrap; min-height:32px;
    }
    .block-inner.empty {
      border-style:dashed; min-height:24px;
      align-items:center; justify-content:center;
      color:#d0c4b0; font-size:10px;
    }
    .ref-chip {
      font-size:10px; padding:2px 7px; border-radius:10px;
      border:1px solid #d0c8bc; background:transparent;
      color:#9a9080; cursor:pointer; transition:all .15s; white-space:nowrap;
    }
    .ref-chip b { font-family:monospace; font-size:10px; margin-right:2px; }
    .ref-chip:hover { opacity:0.8; }
    /* Block content */
    .block-era {
      font-size:12px; font-weight:700; color:#2a2520;
      letter-spacing:.03em; margin-bottom:1px;
      display:flex; align-items:center; gap:8px;
    }
    .block-label { font-size:14px; font-weight:600; line-height:1.6; color:var(--ink,#28231e); }
    .block-summary { font-size:11px; color:var(--muted,#6a6058); line-height:1.55; }
    .block-abstract { margin-top:4px; padding-top:5px; border-top:1px solid #e8e0d8; }
    .block-pattern { font-size:11px; color:#a09080; line-height:1.5; letter-spacing:.01em; }
    .block-actors { display:flex; flex-wrap:wrap; gap:3px; margin-top:2px; }
    .actor {
      font-size:9px; background:transparent; border:1px solid #d0c8bc;
      border-radius:10px; padding:1px 6px; color:#9a9080; letter-spacing:.02em;
    }
    /* Footer */
    .block-id {
      position:absolute; bottom:5px; right:10px;
      font-size:11px; font-weight:700; font-family:monospace;
      color:#b0a090; letter-spacing:.08em;
    }
    .block-fw-label {
      position:absolute; bottom:5px; left:10px;
      font-size:10px; font-weight:600;
      display:flex; align-items:center; gap:4px;
    }
    .block-fw-label .fw-icon {
      width:16px; height:16px; border-radius:4px;
      display:inline-flex; align-items:center; justify-content:center;
      font-size:9px; flex-shrink:0;
      border:1px solid; opacity:0.9;
      font-variant-emoji:text;
    }
    .block-fw-label .fw-text { color:#a09080; }
    /* Outgoing refs */
    .block-out { display:flex; gap:4px; flex-wrap:wrap; margin-top:3px; }
    .out-chip {
      font-size:9px; color:#b0a090; border:1px solid #e0d8cc;
      border-radius:8px; padding:1px 6px; cursor:pointer; transition:all .15s;
    }
    .out-chip:hover { border-color:var(--accent,#5c3d1e); color:var(--accent,#5c3d1e); }
    /* Absorbed */
    .absorbed-toggle {
      font-size:10px; color:var(--muted,#6a6058); cursor:pointer;
      padding:2px 0; transition:color .2s;
    }
    .absorbed-toggle:hover { color:var(--accent,#5c3d1e); }
    .absorbed-arrow { display:inline-block; transition:transform .2s; }
    .absorbed-count {
      font-size:9px; background:#e8e0d8; border-radius:8px;
      padding:0 5px; margin-left:3px;
    }
    .absorbed-list { display:none; padding:4px 0 0 12px; }
    .absorbed-list.open { display:block; }
    .absorbed-item {
      font-size:10px; color:var(--muted,#6a6058); padding:1px 0;
      display:flex; gap:6px;
    }
    .absorbed-item-era { color:#b0a898; min-width:60px; flex-shrink:0; }
    /* Controls */
    .controls {
      display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center;
    }
    .controls button {
      font-family:inherit; font-size:12px; padding:5px 12px;
      border:1.5px solid var(--line,#c9b89e); border-radius:18px;
      background:var(--paper,#fffdf8); color:var(--muted,#6a6058);
      cursor:pointer; transition:all .2s;
    }
    .controls button:hover, .controls button.active {
      background:var(--accent,#5c3d1e); color:#fff; border-color:var(--accent,#5c3d1e);
    }
    .ctrl-info { font-size:11px; color:var(--muted,#6a6058); margin-left:auto; }
    /* Legend */
    .legend {
      display:flex; gap:14px; flex-wrap:wrap; font-size:11px;
      color:var(--muted,#6a6058); margin-bottom:16px;
    }
    .legend-item { display:flex; align-items:center; gap:4px; }
    .legend-sw { width:28px; height:3px; border-radius:2px; }
  `;
  document.head.appendChild(s);
})();

// ── ブロックHTML生成 ──
// opts: { formatId, chipMaxLen, emptyLabel, eraBadge(n), showAbsorbed, showOutgoing,
//         showPatternLink, onChipClick, onActorClick, crossHighlight(e) }
function renderBlockHTML(node, inEdges, outEdges, opts) {
  opts = opts || {};
  const fmtId = opts.formatId || (id => id);
  const chipMax = opts.chipMaxLen || 14;
  const emptyLabel = opts.emptyLabel || '（起点）';
  const fwS = FW_TYPE_STYLES[node.fwType] || {};
  const id = node.id;

  let html = '';

  // Incoming ref-chips
  if (inEdges.length > 0) {
    html += '<div class="block-inner">';
    inEdges.forEach(e => {
      const src = opts.nodeMap ? opts.nodeMap[e.from] : null;
      const srcFw = FW_TYPE_STYLES[src?.fwType] || {};
      const srcColor = srcFw.color || '#b0a898';
      const shortLabel = src ? (src.label.length > chipMax ? src.label.slice(0, chipMax - 2) + '…' : src.label) : e.from;
      const crossBg = (opts.crossHighlight && opts.crossHighlight(e)) ? ';background:rgba(232,160,96,.12)' : '';
      const chipClick = opts.onChipClick
        ? ` onclick="event.stopPropagation();${opts.onChipClick}('${e.from}')"`
        : '';
      const chipHover = opts.onChipHover
        ? ` onmouseenter="hlSource('${e.from}',true)" onmouseleave="hlSource('${e.from}',false)"`
        : '';
      html += `<span class="ref-chip" id="chip-${e.from}-${id}" data-from="${e.from}" style="border-color:${srcColor}${crossBg}" title="${(e.note || '').replace(/"/g,'&quot;')}"${chipClick}${chipHover}>`;
      html += `<b>${fmtId(e.from)}</b> ${shortLabel}`;
      html += `<span class="role-arrow r-${e.role}">\u25B6</span></span>`;
    });
    html += '</div>';
  } else {
    html += `<div class="block-inner empty">${emptyLabel}</div>`;
  }

  // Era (with optional badge)
  if (opts.eraBadge) {
    html += `<div class="block-era">${opts.eraBadge(node)}</div>`;
  } else {
    html += `<div class="block-era">${node.era || ''}</div>`;
  }

  // Label + Summary
  html += `<div class="block-label">${node.label}</div>`;
  html += `<div class="block-summary">${node.summary}</div>`;

  // Absorbed (optional)
  if (opts.showAbsorbed && node.absorbed && node.absorbed.length > 0) {
    const aid = id + '-abs';
    html += `<div class="absorbed-toggle" onclick="event.stopPropagation();toggleAbsorbed('${aid}')">`;
    html += `<span class="absorbed-arrow" id="arr-${aid}">\u25B8</span> 内包イベント <span class="absorbed-count">${node.absorbed.length}</span>`;
    html += `</div>`;
    html += `<div class="absorbed-list" id="abs-${aid}">`;
    node.absorbed.forEach(a => {
      html += `<div class="absorbed-item"><span class="absorbed-item-era">${a.era}</span><span class="absorbed-item-label">${a.label}</span></div>`;
    });
    html += '</div>';
  }

  // Abstract: pattern + actors
  if (node.pattern) {
    html += '<div class="block-abstract">';
    html += `<div class="block-pattern">${node.pattern}</div>`;
    html += '</div>';
  }
  if (node.actors && node.actors.length > 0) {
    const actClick = opts.onActorClick ? (a => ` onclick="event.stopPropagation();${opts.onActorClick}('${a}')"`) : (() => '');
    html += '<div class="block-actors">';
    html += node.actors.map(a => `<span class="actor"${actClick(a)}>${a}</span>`).join('');
    html += '</div>';
  }

  // Outgoing refs (optional)
  if (opts.showOutgoing && outEdges.length > 0) {
    html += '<div class="block-out">';
    outEdges.forEach(e => {
      const tgt = opts.nodeMap ? opts.nodeMap[e.to] : null;
      const shortLabel = tgt ? (tgt.label.length > 12 ? tgt.label.slice(0, 10) + '…' : tgt.label) : e.to;
      html += `<span class="out-chip" onclick="event.stopPropagation();flashAndScroll('${e.to}')" title="${(tgt?.label || e.to) + '\n' + e.role + ': ' + (e.note || '')}">→${fmtId(e.to)} ${shortLabel}</span>`;
    });
    html += '</div>';
  }

  return html;
}

// ── ブロックフッタHTML生成 ──
function renderBlockFooter(node, opts) {
  opts = opts || {};
  const fmtId = opts.formatId || (id => id);
  const fwS = FW_TYPE_STYLES[node.fwType] || {};
  const bgS = BG_TYPE_STYLES[node.bgType] || {};
  const relS = BG_TYPE_STYLES[node.releaseType] || {};

  const bgIc = bgS.icon
    ? `<span class="fw-icon" style="color:${bgS.color};border-color:${bgS.color};background:${bgS.color}18">${bgS.icon}</span><span style="color:#c0b8a0;margin:0 1px">→</span>`
    : '';
  const relIc = relS.icon
    ? `<span class="fw-icon" style="color:${relS.color};border-color:${relS.color};background:${relS.color}18">${relS.icon}</span>`
    : `<span class="fw-icon" style="color:${fwS.color};border-color:${fwS.color};background:${fwS.color}18">${fwS.shape}</span>`;

  let footer = `<div class="block-fw-label">${bgIc}${relIc}<span class="fw-text">${fwS.label}</span>`;
  if (opts.showPatternLink) {
    const pid = nodePatId(node);
    if (pid) {
      footer += `<a href="demo_pattern_fwtype.html#${pid}" style="margin-left:4px;font-family:monospace;font-size:9px;color:#b0a090;text-decoration:none;border-bottom:1px dotted #c0b8a0;" title="パターン図鑑で表示">${pid}</a>`;
    }
  }
  footer += '</div>';
  footer += `<div class="block-id">${fmtId(node.id)}</div>`;
  return footer;
}

// ── エッジ描画（3-pass ハロー+ドット） ──
function drawEdgesStandard(edges, blockEls, canvasEl, svgEl) {
  const cr = canvasEl.getBoundingClientRect();
  const sL = canvasEl.scrollLeft, sT = canvasEl.scrollTop;
  svgEl.innerHTML = '';
  svgEl.style.width = canvasEl.scrollWidth + 'px';
  svgEl.style.height = canvasEl.scrollHeight + 'px';
  svgEl.setAttribute('viewBox', `0 0 ${canvasEl.scrollWidth} ${canvasEl.scrollHeight}`);

  // Pass 1: compute geometry (block edge → ref-chip)
  const geom = [];
  edges.forEach(e => {
    const fromEl = blockEls[e.from];
    const chipEl = document.getElementById('chip-' + e.from + '-' + e.to);
    if (!fromEl || !chipEl) return;

    // Source node fwType color (from block border)
    const fwColor = fromEl.style.borderColor || null;

    const fr = fromEl.getBoundingClientRect();
    const ch = chipEl.getBoundingClientRect();

    const chipCX = ch.left + ch.width / 2 - cr.left + sL;
    const chipCY = ch.top + ch.height / 2 - cr.top + sT;
    const fromCX = fr.left + fr.width / 2 - cr.left + sL;
    const fromCY = fr.top + fr.height / 2 - cr.top + sT;

    const fT = fr.top - cr.top + sT, fB = fr.bottom - cr.top + sT;
    const fL = fr.left - cr.left + sL, fR = fr.right - cr.left + sL;
    let x1, y1;
    if (chipCY > fB)      { x1 = fromCX; y1 = fB; }
    else if (chipCY < fT) { x1 = fromCX; y1 = fT; }
    else if (chipCX < fL) { x1 = fL; y1 = fromCY; }
    else                  { x1 = fR; y1 = fromCY; }

    const cT = ch.top - cr.top + sT, cB = ch.bottom - cr.top + sT;
    const cL = ch.left - cr.left + sL, cR = ch.right - cr.left + sL;
    let x2, y2;
    if (fromCY < cT)      { x2 = chipCX; y2 = cT; }
    else if (fromCY > cB) { x2 = chipCX; y2 = cB; }
    else if (fromCX < cL) { x2 = cL; y2 = chipCY; }
    else                  { x2 = cR; y2 = chipCY; }

    const midY = Math.abs(y2 - y1) < 20
      ? Math.min(y1, y2) - 50
      : (y1 + y2) / 2;
    const d = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
    geom.push({ e, d, x1, y1, x2, y2, fwColor });
  });

  // Pass 2: lines
  geom.forEach(({ e, d }) => {
    const eid = e.id || `${e.from}-${e.to}`;
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', d);
    p.classList.add('edge-line', 'r-' + e.role);
    if (e._cross) p.classList.add('cross');
    p.dataset.from = e.from; p.dataset.to = e.to; p.dataset.role = e.role;
    p.dataset.eid = eid;
    svgEl.appendChild(p);
  });

  // Pass 3: halos + dots
  geom.forEach(({ e, x1, y1, x2, y2, fwColor }) => {
    const eid = e.id || `${e.from}-${e.to}`;
    const ns = 'http://www.w3.org/2000/svg';
    // Start: halo + dot (dot color = source node fwType color)
    const h = document.createElementNS(ns, 'circle');
    h.setAttribute('cx', x1); h.setAttribute('cy', y1); h.setAttribute('r', 5);
    h.setAttribute('fill', 'var(--paper,#fffdf8)'); h.setAttribute('stroke', 'none');
    h.classList.add('edge-halo');
    h.dataset.from = e.from; h.dataset.to = e.to;
    h.dataset.eid = eid;
    svgEl.appendChild(h);

    const ds = document.createElementNS(ns, 'circle');
    ds.setAttribute('cx', x1); ds.setAttribute('cy', y1); ds.setAttribute('r', 3);
    ds.classList.add('edge-dot');
    if (fwColor) ds.setAttribute('fill', fwColor);
    else ds.classList.add('r-' + e.role);
    if (e._cross) ds.classList.add('cross');
    ds.dataset.from = e.from; ds.dataset.to = e.to;
    ds.dataset.eid = eid;
    svgEl.appendChild(ds);

    // End: dot
    const de = document.createElementNS(ns, 'circle');
    de.setAttribute('cx', x2); de.setAttribute('cy', y2); de.setAttribute('r', 3);
    de.classList.add('edge-head', 'r-' + e.role);
    if (e._cross) de.classList.add('cross');
    de.dataset.from = e.from; de.dataset.to = e.to;
    de.dataset.eid = eid;
    svgEl.appendChild(de);
  });
}

// ── インタラクション共通関数 ──
function hlSource(nid, on) {
  const el = document.getElementById('blk-' + nid);
  if (!el) return;
  if (on) {
    el.classList.add('source-hl');
    document.querySelectorAll('.edge-line').forEach(line => {
      if (line.dataset.from === nid || line.dataset.to === nid) {
        line.style.opacity = '0.8'; line.style.strokeWidth = '2.5';
      }
    });
  } else {
    el.classList.remove('source-hl');
    document.querySelectorAll('.edge-line').forEach(line => {
      if (line.dataset.from === nid || line.dataset.to === nid) {
        line.style.opacity = ''; line.style.strokeWidth = '';
      }
    });
  }
}

function flashAndScroll(nid) {
  const el = document.getElementById('blk-' + nid);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.classList.add('hl');
  setTimeout(() => el.classList.remove('hl'), 2000);
}

function toggleAbsorbed(aid) {
  const list = document.getElementById('abs-' + aid);
  const arrow = document.getElementById('arr-' + aid);
  if (!list) return;
  list.classList.toggle('open');
  if (arrow) arrow.textContent = list.classList.contains('open') ? '\u25BE' : '\u25B8';
}

async function buildPatternIds() {
  const rs = await Promise.allSettled(
    ALL_SOURCES.map(u => fetch(u).then(r => r.json()))
  );
  const fwPK = {};
  rs.forEach(r => {
    if (r.status !== 'fulfilled') return;
    r.value.nodes.forEach(n => {
      if (!n.fwType || !PAT_PREFIX[n.fwType]) return;
      const k = patKey(n);
      if (!fwPK[n.fwType]) fwPK[n.fwType] = new Set();
      fwPK[n.fwType].add(k);
    });
  });
  Object.keys(PAT_PREFIX).sort().forEach(fw => {
    if (!fwPK[fw]) return;
    [...fwPK[fw]].sort().forEach((k, i) => {
      PAT_ID_MAP[fw + '|' + k] = PAT_PREFIX[fw] + String(i + 1).padStart(2, '0');
    });
  });
}
