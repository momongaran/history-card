// ============================================================
// shared.js — 全ビュー・図鑑共通の定数・パターンID計算
// <script src="shared.js"></script> で読み込む（グローバル変数）
// ============================================================

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
    </span>`;

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
