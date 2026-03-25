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
