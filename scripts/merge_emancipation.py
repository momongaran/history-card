#!/usr/bin/env python3
"""
merge_emancipation.py — E要素ラベル書き換え + legacyResult保管マージ

処理:
1. framework_output_v3_1_accum.json をベースに
2. emancipation_revisions_v3_2.json のE-label書き換えを適用
3. 旧E-labelを notes.legacyResult に臨時保管
4. version を "3.2" に更新
5. 出力: data/framework_output_v3_2_erev.json
"""

import json
import os
import sys
from copy import deepcopy

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

VALID_E_CATEGORIES = {
    "E-POW", "E-WAR", "E-SYS", "E-REG", "E-CUL", "E-ADP", "E-ECO", "E-COL"
}


def validate(fw_data, rev_data):
    """Run validation checks. Returns (errors, warnings)."""
    errors = []
    warnings = []

    items = rev_data.get('items', {})
    fws_by_id = {fv['frameworkViewId']: fv for fv in fw_data['frameworkViews']}

    # Check all FWs have a revision entry
    for fv in fw_data['frameworkViews']:
        fw_id = fv['frameworkViewId']
        e_elements = [e for e in fv['elements'] if e.get('layer') == 'E']

        if not e_elements:
            warnings.append(f"{fw_id}: E要素が存在しない")
            continue

        if fw_id not in items:
            errors.append(f"{fw_id}: revisionデータが存在しない")
            continue

        item = items[fw_id]

        # Check elementId matches
        e_el = e_elements[0]
        if item.get('elementId') != e_el['elementId']:
            errors.append(f"{fw_id}: elementId不一致 revision={item.get('elementId')} actual={e_el['elementId']}")

        # Check revisedLabel
        label = item.get('revisedLabel', '')
        if not label or len(label) < 5:
            errors.append(f"{fw_id}: revisedLabel が短すぎる ({len(label)}文字)")
        if len(label) > 50:
            warnings.append(f"{fw_id}: revisedLabel が長い ({len(label)}文字): {label}")

        # Check category
        cat = item.get('categoryRevised', '')
        if cat and cat not in VALID_E_CATEGORIES:
            errors.append(f"{fw_id}: categoryRevised '{cat}' は無効")

    # Check for extra items in revisions
    for fw_id in items:
        if fw_id not in fws_by_id:
            warnings.append(f"{fw_id}: revisionに存在するがFWに存在しない")

    return errors, warnings


def merge(fw_data, rev_data):
    """Merge E-label revisions into framework output."""
    output = deepcopy(fw_data)
    output['version'] = '3.2'
    output['meta']['note'] = 'v3.2 E要素ラベル書き換え（抽象化）+ legacyResult臨時保管。'
    output['meta']['baseVersion'] = '3.1'
    output['meta']['emancipationScript'] = 'revise_emancipation.py'

    items = rev_data.get('items', {})
    revision_count = 0
    legacy_count = 0

    for fv in output['frameworkViews']:
        fw_id = fv['frameworkViewId']
        item = items.get(fw_id)
        if item is None:
            continue

        for el in fv['elements']:
            if el.get('layer') != 'E':
                continue
            if el['elementId'] != item.get('elementId'):
                continue

            original_label = el['label']

            # Apply revised label
            el['label'] = item['revisedLabel']

            # Apply category if changed
            if item.get('categoryRevised'):
                el['category'] = item['categoryRevised']
            if item.get('subCategoryRevised'):
                el['subCategory'] = item['subCategoryRevised']

            revision_count += 1

            # Save original label to notes.legacyResult
            notes = fv.get('notes')
            if notes is None or isinstance(notes, list):
                # Convert array notes to object if needed
                if isinstance(notes, list) and len(notes) > 0:
                    fv['notes'] = {'legacyNotes': notes}
                else:
                    fv['notes'] = {}
                notes = fv['notes']

            notes['legacyResult'] = original_label
            legacy_count += 1

    return output, revision_count, legacy_count


def main():
    # Load data
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_1_accum.json')
    rev_path = os.path.join(BASE_DIR, 'emancipation_revisions_v3_2.json')

    if not os.path.exists(rev_path):
        print(f"エラー: {rev_path} が存在しません")
        print("先に revise_emancipation.py を実行してください")
        sys.exit(1)

    with open(fw_path, encoding='utf-8') as f:
        fw_data = json.load(f)
    with open(rev_path, encoding='utf-8') as f:
        rev_data = json.load(f)

    print(f"FW数: {len(fw_data['frameworkViews'])}")
    print(f"revision items: {len(rev_data.get('items', {}))}")

    # Validate
    print("\n=== バリデーション ===")
    errors, warnings = validate(fw_data, rev_data)

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
    output, revision_count, legacy_count = merge(fw_data, rev_data)

    out_path = os.path.join(BASE_DIR, 'framework_output_v3_2_erev.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"E-label書き換え: {revision_count}件")
    print(f"legacyResult保管: {legacy_count}件")
    print(f"出力: {out_path}")
    print(f"version: {output['version']}")

    # Post-merge validation
    print("\n=== 事後バリデーション ===")
    e_count = 0
    legacy_result_count = 0
    category_ok = 0
    for fv in output['frameworkViews']:
        for el in fv['elements']:
            if el.get('layer') == 'E':
                e_count += 1
                if el.get('label'):
                    category_ok += 1
        notes = fv.get('notes', {})
        if isinstance(notes, dict) and notes.get('legacyResult'):
            legacy_result_count += 1

    print(f"E要素数: {e_count}")
    print(f"E-label存在: {category_ok}/{e_count}")
    print(f"legacyResult保管: {legacy_result_count}")

    if e_count != category_ok:
        print("⚠ E-labelが欠損しているE要素があります")
    if legacy_result_count < revision_count:
        print("⚠ legacyResultの保管数がrevision数より少ない")

    # Show samples
    print("\n=== サンプル (先頭5件) ===")
    count = 0
    for fv in output['frameworkViews']:
        if count >= 5:
            break
        for el in fv['elements']:
            if el.get('layer') == 'E':
                notes = fv.get('notes', {})
                legacy = notes.get('legacyResult', '(なし)') if isinstance(notes, dict) else '(なし)'
                print(f"  {fv['title']}")
                print(f"    新E-label: {el['label']}")
                print(f"    legacyResult: {legacy}")
                count += 1
                break


if __name__ == '__main__':
    main()
