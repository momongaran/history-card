// taxonomy.js — Taxonomy lookup helpers

let taxonomyData = null;

export function initTaxonomy(data) {
  taxonomyData = data;
}

/**
 * subCatName(code) → subcategory display name
 * code example: "C-LEG-02" → layer "C", category "C-LEG", subCat "C-LEG-02"
 */
export function subCatName(code) {
  if (!code || !taxonomyData) return '—';
  const parts = code.split('-');
  if (parts.length < 3) return '—';
  const layerKey = parts[0];
  const catKey = parts[0] + '-' + parts[1];
  const layer = taxonomyData.layers?.[layerKey];
  if (!layer) return '—';
  const cat = layer.categories?.[catKey];
  if (!cat) return '—';
  return cat.subCategories?.[code] || '—';
}

/**
 * getCategoriesForLayer(layerKey) → [{ catCode, catName, subCategories: [{code, name}] }]
 */
export function getCategoriesForLayer(layerKey) {
  if (!taxonomyData) return [];
  const layer = taxonomyData.layers?.[layerKey];
  if (!layer) return [];
  const result = [];
  for (const [catCode, cat] of Object.entries(layer.categories)) {
    const subs = [];
    for (const [subCode, subName] of Object.entries(cat.subCategories || {})) {
      subs.push({ code: subCode, name: subName });
    }
    result.push({
      catCode,
      catName: cat.name,
      subCategories: subs,
    });
  }
  return result;
}

/**
 * getLinkCategories() → [{ code, name }]
 * Lコード（対応リンクカテゴリ）の一覧を返す
 */
export function getLinkCategories() {
  if (!taxonomyData) return [];
  const layer = taxonomyData.layers?.['L'];
  if (!layer) return [];
  const result = [];
  for (const [catCode, cat] of Object.entries(layer.categories)) {
    result.push({ code: catCode, name: cat.name });
  }
  return result;
}

/**
 * linkCatName(code) → Lコードの表示名称
 * 例: "L-CAU" → "直接因果"
 */
export function linkCatName(code) {
  if (!code || !taxonomyData) return '—';
  const layer = taxonomyData.layers?.['L'];
  if (!layer) return '—';
  const cat = layer.categories?.[code];
  return cat?.name || '—';
}
