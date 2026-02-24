#!/usr/bin/env python3
"""
merge_momentum.py — momentum_v3_3.json を framework_output_v3_3.json に統合

処理:
1. framework_output_v3_3.json をベースに
2. momentum_v3_3.json の momentum を各FWに追加
3. 出力: framework_output_v3_3.json（上書き）
"""

import json
import os
import sys
from copy import deepcopy

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def validate(fw_data, momentum_data):
    """Validate momentum data against framework output."""
    errors = []
    warnings = []

    fw_ids = {fv['frameworkViewId'] for fv in fw_data['frameworkViews']}
    items = momentum_data.get('items', {})

    # Check coverage
    missing = fw_ids - set(items.keys())
    if missing:
        for fw_id in sorted(missing):
            errors.append(f"{fw_id}: momentum データが存在しない")

    extra = set(items.keys()) - fw_ids
    if extra:
        for fw_id in sorted(extra):
            warnings.append(f"{fw_id}: FWに存在しないmomentumデータ")

    # Validate individual items
    for fw_id, item in items.items():
        momentum = item.get('momentum')
        if momentum is None:
            warnings.append(f"{fw_id}: momentum が null")
            continue
        if not isinstance(momentum, str):
            errors.append(f"{fw_id}: momentum が文字列でない: {type(momentum)}")
            continue
        if len(momentum) < 5:
            warnings.append(f"{fw_id}: momentum が短い ({len(momentum)}文字): {momentum}")
        if not momentum.endswith("方向へ"):
            warnings.append(f"{fw_id}: momentum が「方向へ」で終わらない: {momentum}")

    return errors, warnings


def merge(fw_data, momentum_data):
    """Merge momentum data into framework output."""
    output = deepcopy(fw_data)
    items = momentum_data.get('items', {})
    merged_count = 0

    for fv in output['frameworkViews']:
        fw_id = fv['frameworkViewId']
        item = items.get(fw_id)

        if item is not None and item.get('momentum') is not None:
            fv['momentum'] = item['momentum']
            merged_count += 1

    return output, merged_count


def main():
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_3.json')
    momentum_path = os.path.join(BASE_DIR, 'momentum_v3_3.json')

    if not os.path.exists(momentum_path):
        print(f"エラー: {momentum_path} が存在しません")
        print("先に generate_momentum.py を実行してください")
        sys.exit(1)

    with open(fw_path, encoding='utf-8') as f:
        fw_data = json.load(f)
    with open(momentum_path, encoding='utf-8') as f:
        momentum_data = json.load(f)

    print(f"FW数: {len(fw_data['frameworkViews'])}")
    print(f"momentum items: {len(momentum_data.get('items', {}))}")

    # Validate
    print("\n=== バリデーション ===")
    errors, warnings = validate(fw_data, momentum_data)

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
    output, merged_count = merge(fw_data, momentum_data)

    with open(fw_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Count filled momentum
    filled = sum(1 for fv in output['frameworkViews'] if fv.get('momentum') is not None)

    print(f"momentum統合: {merged_count}件")
    print(f"momentum充填率: {filled}/{len(output['frameworkViews'])}")
    print(f"出力: {fw_path}（上書き）")


if __name__ == '__main__':
    main()
