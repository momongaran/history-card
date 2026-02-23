#!/usr/bin/env python3
"""
merge_accumulation.py — accumulation_v3_1.json を framework_output に統合

処理:
1. framework_output_v3_0_bfe.json をベースに
2. accumulation_v3_1.json の accumulation を各FWに追加
3. revisions のラベル・カテゴリ修正を適用
4. 出力: data/framework_output_v3_1_accum.json
5. version を "3.1" に更新
"""

import json
import os
import sys
from copy import deepcopy

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

VALID_MECHANISMS = {"tension", "amplification", "constraint", "enabling", "convergence"}


def validate_all(fw_data, accum_data):
    """Run all validation checks. Returns (errors, warnings)."""
    errors = []
    warnings = []

    fws_by_id = {fv['frameworkViewId']: fv for fv in fw_data['frameworkViews']}
    items = accum_data.get('items', {})

    # Check all FWs with B>=2 have accumulation
    for fv in fw_data['frameworkViews']:
        fw_id = fv['frameworkViewId']
        b_count = sum(1 for e in fv['elements'] if e['layer'] == 'B')

        if fw_id not in items:
            if b_count >= 2:
                errors.append(f"{fw_id}: accumulation データが存在しない (B={b_count})")
            continue

        item = items[fw_id]

        if b_count <= 1:
            if item.get('accumulation') is not None:
                warnings.append(f"{fw_id}: B={b_count} だが accumulation が null でない")
            continue

        # B>=2: validate accumulation
        accum = item.get('accumulation')
        if accum is None:
            errors.append(f"{fw_id}: B={b_count} だが accumulation が null")
            continue

        b_element_ids = {e['elementId'] for e in fv['elements'] if e['layer'] == 'B'}

        for i, rel in enumerate(accum.get('relations', [])):
            if rel.get('from') not in b_element_ids:
                errors.append(f"{fw_id}: relation[{i}].from '{rel.get('from')}' はB要素ではない")
            if rel.get('to') not in b_element_ids:
                errors.append(f"{fw_id}: relation[{i}].to '{rel.get('to')}' はB要素ではない")
            if rel.get('from') == rel.get('to'):
                errors.append(f"{fw_id}: relation[{i}] self-reference")
            if rel.get('mechanism') not in VALID_MECHANISMS:
                errors.append(f"{fw_id}: relation[{i}].mechanism '{rel.get('mechanism')}' は無効")

            desc = rel.get('description', '')
            if len(desc) < 20:
                warnings.append(f"{fw_id}: relation[{i}].description が短い ({len(desc)}文字)")
            if len(desc) > 100:
                warnings.append(f"{fw_id}: relation[{i}].description が長い ({len(desc)}文字)")

        # Check revisions
        for rev in item.get('revisions', []):
            if rev.get('elementId') not in b_element_ids:
                errors.append(f"{fw_id}: revision elementId '{rev.get('elementId')}' はB要素ではない")

    # Mechanism distribution check
    mech_counts = {}
    total_rels = 0
    for fw_id, item in items.items():
        accum = item.get('accumulation')
        if accum and accum.get('relations'):
            for rel in accum['relations']:
                m = rel.get('mechanism', 'unknown')
                mech_counts[m] = mech_counts.get(m, 0) + 1
                total_rels += 1

    if total_rels > 0:
        for m, c in mech_counts.items():
            pct = c / total_rels * 100
            if pct > 60:
                warnings.append(f"mechanism分布偏り: {m} = {pct:.1f}% (>{60}%)")

    return errors, warnings


def merge(fw_data, accum_data):
    """Merge accumulation data into framework output."""
    output = deepcopy(fw_data)
    output['version'] = '3.1'
    output['meta']['note'] = 'v3.1 accumulation追加。B要素間蓄積関係・ラベル条件記述化。'
    output['meta']['baseVersion'] = '3.0'
    output['meta']['accumulationScript'] = 'generate_accumulation.py'

    items = accum_data.get('items', {})
    revision_count = 0
    accum_count = 0

    for fv in output['frameworkViews']:
        fw_id = fv['frameworkViewId']
        item = items.get(fw_id)

        if item is None:
            fv['accumulation'] = None
            continue

        # Add accumulation
        fv['accumulation'] = item.get('accumulation')
        if fv['accumulation'] is not None:
            accum_count += 1

        # Apply revisions
        revisions = item.get('revisions', [])
        rev_by_id = {r['elementId']: r for r in revisions}

        for el in fv['elements']:
            if el['elementId'] in rev_by_id:
                rev = rev_by_id[el['elementId']]
                if rev.get('labelRevised'):
                    el['label'] = rev['labelRevised']
                if rev.get('categoryRevised'):
                    el['category'] = rev['categoryRevised']
                if rev.get('subCategoryRevised'):
                    el['subCategory'] = rev['subCategoryRevised']
                revision_count += 1

    return output, accum_count, revision_count


def main():
    # Load data
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_0_bfe.json')
    accum_path = os.path.join(BASE_DIR, 'accumulation_v3_1.json')

    if not os.path.exists(accum_path):
        print(f"エラー: {accum_path} が存在しません")
        print("先に generate_accumulation.py を実行してください")
        sys.exit(1)

    with open(fw_path, encoding='utf-8') as f:
        fw_data = json.load(f)
    with open(accum_path, encoding='utf-8') as f:
        accum_data = json.load(f)

    print(f"FW数: {len(fw_data['frameworkViews'])}")
    print(f"accumulation items: {len(accum_data.get('items', {}))}")

    # Validate
    print("\n=== バリデーション ===")
    errors, warnings = validate_all(fw_data, accum_data)

    if warnings:
        print(f"警告 ({len(warnings)}件):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        print(f"エラー ({len(errors)}件):")
        for e in errors:
            print(f"  ✗ {e}")
        print("\nエラーがあるためマージを中止します。--force で強制実行可能。")
        if '--force' not in sys.argv:
            sys.exit(1)
        print("--force: エラーを無視してマージを続行")

    # Merge
    print("\n=== マージ実行 ===")
    output, accum_count, revision_count = merge(fw_data, accum_data)

    out_path = os.path.join(BASE_DIR, 'framework_output_v3_1_accum.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"accumulation追加: {accum_count}件")
    print(f"revision適用: {revision_count}件")
    print(f"出力: {out_path}")
    print(f"version: {output['version']}")


if __name__ == '__main__':
    main()
