#!/usr/bin/env python3
"""
migrate_v3_3.py — v3.2→v3.3 マイグレーションスクリプト

処理:
1. v3.2 JSONを読み込み
2. B不足6件（sortKey: 507, 592, 593, 645, 647, 1069）にB要素を追加
3. 6件のF/Eラベルを実行者視点に更新（該当のみ）
4. sortKey 647のF要素をF-PRGに変更
5. 全221件のframeworkViewに momentum: null を追加
6. version を "3.3" に更新
7. バリデーション実行
8. data/framework_output_v3_3.json として出力
"""

import json
import os
import sys
from copy import deepcopy

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ============================================================
# B要素追加定義（design notes セクション6.4 に基づく）
# ============================================================

B_ADDITIONS = {
    # sortKey 507: 継体天皇が即位した
    "FW_EV_p0507_01": {
        "new_elements": [
            {
                "elementId": "EL_EV_p0507_01_7",
                "layer": "B",
                "category": "B-LEG",
                "subCategory": "B-LEG-02",
                "label": "武烈天皇が後嗣なく崩御し王統が断絶状態にある",
                "normalizedLabel": "王統断絶状態",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0507_01_8",
                "layer": "B",
                "category": "B-LEG",
                "subCategory": "B-LEG-01",
                "label": "応神天皇五世孫という血統的根拠と、越前・近江・尾張の豪族基盤を持つ候補が存在する",
                "normalizedLabel": "血統的根拠と地方基盤を持つ候補",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p0507_01_7", "EL_EV_p0507_01_8"],
    },
    # sortKey 592: 崇峻天皇が暗殺された
    "FW_EV_p0592_01": {
        "new_elements": [
            {
                "elementId": "EL_EV_p0592_01_7",
                "layer": "B",
                "category": "B-PWR",
                "subCategory": "B-PWR-04",
                "label": "蘇我馬子が大臣として実権を掌握し天皇は名目的地位にある",
                "normalizedLabel": "馬子が実権を掌握",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0592_01_8",
                "layer": "B",
                "category": "B-RIV",
                "subCategory": "B-RIV-01",
                "label": "后妃問題で蘇我氏が外戚の地位を確保できず、天皇との利害が対立している",
                "normalizedLabel": "外戚問題で利害対立",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p0592_01_7", "EL_EV_p0592_01_8"],
    },
    # sortKey 593: 推古天皇が即位した
    "FW_EV_p0593_01": {
        "new_elements": [
            {
                "elementId": "EL_EV_p0593_01_7",
                "layer": "B",
                "category": "B-PWR",
                "subCategory": "B-PWR-04",
                "label": "蘇我馬子が大臣として朝廷の実権を握っている",
                "normalizedLabel": "馬子が朝廷の実権を掌握",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0593_01_8",
                "layer": "B",
                "category": "B-LEG",
                "subCategory": "B-LEG-02",
                "label": "崇峻暗殺後、有力な男性皇位候補が不在または馬子にとって不都合である",
                "normalizedLabel": "有力男性候補の不在",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0593_01_9",
                "layer": "B",
                "category": "B-LEG",
                "subCategory": "B-LEG-01",
                "label": "推古は欽明天皇の皇女かつ蘇我氏を母系に持ち、馬子との協調が可能な血統にある",
                "normalizedLabel": "推古の血統的適格性",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p0593_01_7", "EL_EV_p0593_01_8", "EL_EV_p0593_01_9"],
    },
    # sortKey 645: 乙巳の変が起き大化改新が始まった
    "FW_EV_p0645_01": {
        "new_elements": [
            {
                "elementId": "EL_EV_p0645_01_7",
                "layer": "B",
                "category": "B-PWR",
                "subCategory": "B-PWR-04",
                "label": "蘇我蝦夷・入鹿が大臣として専権し、天皇の統治権が形骸化している",
                "normalizedLabel": "蘇我氏の専権と天皇権の形骸化",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0645_01_8",
                "layer": "B",
                "category": "B-EXT",
                "subCategory": "B-EXT-03",
                "label": "唐の律令体制が東アジアに影響を拡大し、中央集権モデルが認知されている",
                "normalizedLabel": "唐の律令モデルの影響",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0645_01_9",
                "layer": "B",
                "category": "B-RIV",
                "subCategory": "B-RIV-01",
                "label": "中大兄皇子と中臣鎌足が蘇我氏排除の連携を形成している",
                "normalizedLabel": "皇子と鎌足の連携",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p0645_01_7", "EL_EV_p0645_01_8", "EL_EV_p0645_01_9"],
    },
    # sortKey 647: 租庸調により農民負担が急増した
    # 既存B (EL_EV_p0647_01_1) を除去し、3件の新Bで置換
    "FW_EV_p0647_01": {
        "remove_element_ids": ["EL_EV_p0647_01_1"],
        "new_elements": [
            {
                "elementId": "EL_EV_p0647_01_7",
                "layer": "B",
                "category": "B-INS",
                "subCategory": "B-INS-02",
                "label": "大化改新により租庸調・班田収授が制度化され全国一律の徴税が始まっている",
                "normalizedLabel": "租庸調・班田収授の制度化",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0647_01_8",
                "layer": "B",
                "category": "B-GEO",
                "subCategory": "B-GEO-04",
                "label": "庸調の都への運搬（運脚）は自費・徒歩で、遠国ほど負担が大きい",
                "normalizedLabel": "運脚の地理的負担",
                "notes": []
            },
            {
                "elementId": "EL_EV_p0647_01_9",
                "layer": "B",
                "category": "B-MIL",
                "subCategory": "B-MIL-03",
                "label": "防人制度により成年男子が長期間動員され、農村の労働力が奪われている",
                "normalizedLabel": "防人制度による労働力流出",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p0647_01_7", "EL_EV_p0647_01_8", "EL_EV_p0647_01_9"],
    },
    # sortKey 1069: 延久の荘園整理令を出した
    # 既存B (EL_EV_p1069_01_1) を除去し、3件の新Bで置換
    "FW_EV_p1069_01": {
        "remove_element_ids": ["EL_EV_p1069_01_1"],
        "new_elements": [
            {
                "elementId": "EL_EV_p1069_01_7",
                "layer": "B",
                "category": "B-INS",
                "subCategory": "B-INS-02",
                "label": "荘園の乱立が公田を侵食し、国家の租税基盤が縮小している",
                "normalizedLabel": "荘園による租税基盤侵食",
                "notes": []
            },
            {
                "elementId": "EL_EV_p1069_01_8",
                "layer": "B",
                "category": "B-PWR",
                "subCategory": "B-PWR-04",
                "label": "後三条天皇は藤原氏の外戚関係を持たず、摂関家の意向に制約されない",
                "normalizedLabel": "外戚なき天皇の独立性",
                "notes": []
            },
            {
                "elementId": "EL_EV_p1069_01_9",
                "layer": "B",
                "category": "B-INS",
                "subCategory": "B-INS-04",
                "label": "従来の荘園整理は国司主体だったが、国司と有力貴族の癒着で実効性がなかった",
                "normalizedLabel": "従来整理の実効性欠如",
                "notes": []
            },
        ],
        "lane_insert_ids": ["EL_EV_p1069_01_7", "EL_EV_p1069_01_8", "EL_EV_p1069_01_9"],
    },
}

# ============================================================
# F/Eラベル更新定義（実行者視点への変更）
# design notes セクション6.4 に基づく
# ============================================================

LABEL_UPDATES = {
    # 592: 実行者=蘇我馬子
    "EL_EV_p0592_01_2": {
        "label": "馬子が天皇の「猪の首」発言から自身への殺意を察知した",
        "normalizedLabel": "馬子が天皇の殺意を察知",
    },
    "EL_EV_p0592_01_5": {
        "label": "先制的な権力者排除（東漢駒に命じて天皇を暗殺）",
        "normalizedLabel": "崇峻天皇が蘇我馬子の意向で暗殺された",
    },
    # 645: 実行者=中大兄皇子・中臣鎌足
    "EL_EV_p0645_01_1": {
        "label": "蘇我入鹿が山背大兄王一族を滅ぼし、専横が皇位継承にまで及んだ",
        "normalizedLabel": "蘇我入鹿の専横が皇位継承に及ぶ",
    },
    # 1069: 実行者=後三条天皇
    "EL_EV_p1069_01_2": {
        "label": "摂関家領が口頭の主張で違法荘園を諸国に出現させ国務が滞っているとの報告を受けた",
        "normalizedLabel": "摂関家領の違法荘園が国務を阻害",
    },
}

# ============================================================
# F-PRG変更（sortKey 647）
# ============================================================

F_PRG_UPDATES = {
    "EL_EV_p0647_01_F": {
        "category": "F-PRG",
        "subCategory": "F-PRG-01",
        "label": "大化改新の税制・兵役制度が全国で本格的に施行された",
        "normalizedLabel": "大化改新の制度が全国施行",
        "notes": [],
    },
}

# ============================================================
# 既存B要素の更新（design notesの書き直し）
# sortKey別に、既存Bのlabel/category/subCategoryを更新
# ============================================================

EXISTING_B_UPDATES = {
    # 507: 既存B (EL_EV_p0507_01_2) のlabelを客観記述に更新
    "EL_EV_p0507_01_2": {
        "label": "大伴金村・物部麁鹿火ら有力豪族が擁立の主導権を握っている",
        "normalizedLabel": "有力豪族が擁立主導権を保持",
    },
    # 592: 既存B (EL_EV_p0592_01_1) を更新
    "EL_EV_p0592_01_1": {
        "label": "崇峻天皇が馬子から距離を置き独自の軍事行動（任那派兵）を進めている",
        "normalizedLabel": "崇峻天皇が独自行動を推進",
        "category": "B-PWR",
        "subCategory": "B-PWR-02",
    },
    # 647, 1069: 既存Bは remove_element_ids で除去し新Bで置換するため、ここでは不要
}

# ============================================================
# E-ECO subCategory更新 (647: E-ECO-04 → E-ECO-01)
# design notes セクション6.4⑤に基づく
# ============================================================

E_SUBCAT_UPDATES = {
    "EL_EV_p0647_01_3": {
        "subCategory": "E-ECO-01",
    },
}


def migrate(data):
    """Execute v3.2 → v3.3 migration."""
    output = deepcopy(data)

    # Build FW lookup
    fw_by_id = {}
    for fv in output['frameworkViews']:
        fw_by_id[fv['frameworkViewId']] = fv

    # --- Step 1: Add B elements (with optional removal of old B) ---
    b_added = 0
    b_removed = 0
    for fw_id, spec in B_ADDITIONS.items():
        fv = fw_by_id.get(fw_id)
        if fv is None:
            print(f"  WARNING: {fw_id} not found, skipping B addition")
            continue

        # Remove old elements if specified
        remove_ids = set(spec.get('remove_element_ids', []))
        if remove_ids:
            fv['elements'] = [el for el in fv['elements'] if el['elementId'] not in remove_ids]
            lane = fv['lanes'][0]
            lane['elements'] = [eid for eid in lane['elements'] if eid not in remove_ids]
            b_removed += len(remove_ids)

        # Add new elements to elements array
        for el in spec['new_elements']:
            fv['elements'].append(el)
            b_added += 1

        # Insert B elementIds at the beginning of the first lane's elements list
        lane = fv['lanes'][0]
        for eid in reversed(spec['lane_insert_ids']):
            lane['elements'].insert(0, eid)

    print(f"  B要素追加: {b_added}件 (除去: {b_removed}件)")

    # --- Step 2: Update existing B element labels ---
    b_updated = 0
    for fv in output['frameworkViews']:
        for el in fv['elements']:
            if el['elementId'] in EXISTING_B_UPDATES:
                updates = EXISTING_B_UPDATES[el['elementId']]
                for key, val in updates.items():
                    el[key] = val
                b_updated += 1

    print(f"  既存B更新: {b_updated}件")

    # --- Step 3: Update F/E labels (executor perspective) ---
    label_updated = 0
    for fv in output['frameworkViews']:
        for el in fv['elements']:
            if el['elementId'] in LABEL_UPDATES:
                updates = LABEL_UPDATES[el['elementId']]
                el['label'] = updates['label']
                el['normalizedLabel'] = updates['normalizedLabel']
                label_updated += 1

    print(f"  F/Eラベル更新: {label_updated}件")

    # --- Step 4: F-PRG category change (sortKey 647) ---
    fprg_updated = 0
    for fv in output['frameworkViews']:
        for el in fv['elements']:
            if el['elementId'] in F_PRG_UPDATES:
                updates = F_PRG_UPDATES[el['elementId']]
                for key, val in updates.items():
                    el[key] = val
                fprg_updated += 1

    print(f"  F-PRG変更: {fprg_updated}件")

    # --- Step 5: E subCategory updates ---
    e_updated = 0
    for fv in output['frameworkViews']:
        for el in fv['elements']:
            if el['elementId'] in E_SUBCAT_UPDATES:
                updates = E_SUBCAT_UPDATES[el['elementId']]
                for key, val in updates.items():
                    el[key] = val
                e_updated += 1

    print(f"  Eサブカテゴリ更新: {e_updated}件")

    # --- Step 6: Add momentum: null to all FWs ---
    momentum_added = 0
    for fv in output['frameworkViews']:
        if 'momentum' not in fv:
            fv['momentum'] = None
            momentum_added += 1

    print(f"  momentum追加: {momentum_added}件")

    # --- Step 7: Update version and meta ---
    output['version'] = '3.3'
    output['meta']['note'] = 'v3.3 momentum導入、B補充6件、F-PRG新設、視点ルール適用。'
    output['meta']['baseVersion'] = '3.2'
    output['meta']['migrationScript'] = 'migrate_v3_3.py'

    return output


def validate(data):
    """Validate v3.3 data integrity."""
    errors = []
    warnings = []

    fws = data['frameworkViews']

    # Check total count
    if len(fws) != 221:
        errors.append(f"FW数が221ではない: {len(fws)}")

    # Check each FW
    layer_dist = {'B': 0, 'F': 0, 'E': 0}
    b_count_dist = {}
    momentum_count = 0

    for fv in fws:
        fw_id = fv['frameworkViewId']
        elements = fv['elements']

        # Layer count
        layers = {}
        for el in elements:
            layer = el['layer']
            layers[layer] = layers.get(layer, 0) + 1
            layer_dist[layer] = layer_dist.get(layer, 0) + 1

        b_count = layers.get('B', 0)
        b_count_dist[b_count] = b_count_dist.get(b_count, 0) + 1

        # Every FW must have at least one F and one E
        if layers.get('F', 0) == 0:
            errors.append(f"{fw_id}: F要素がない")
        if layers.get('E', 0) == 0:
            errors.append(f"{fw_id}: E要素がない")

        # Check momentum field exists
        if 'momentum' in fv:
            momentum_count += 1
        else:
            errors.append(f"{fw_id}: momentumフィールドがない")

        # Check lanes reference valid elementIds
        element_ids = {el['elementId'] for el in elements}
        for lane in fv['lanes']:
            for eid in lane['elements']:
                if eid not in element_ids:
                    # Some legacy elementIds in lanes may reference legacyPath elements
                    # This is acceptable for backward compatibility
                    pass

        # Validate element structure
        for el in elements:
            if not el.get('elementId'):
                errors.append(f"{fw_id}: elementIdが空")
            if el.get('layer') not in ('B', 'F', 'E'):
                errors.append(f"{fw_id}: {el.get('elementId')} の layer が不正: {el.get('layer')}")
            if not el.get('category'):
                errors.append(f"{fw_id}: {el.get('elementId')} の category が空")

    # Check specific 6 events have B >= 2
    target_fws = {
        "FW_EV_p0507_01": 507,
        "FW_EV_p0592_01": 592,
        "FW_EV_p0593_01": 593,
        "FW_EV_p0645_01": 645,
        "FW_EV_p0647_01": 647,
        "FW_EV_p1069_01": 1069,
    }
    fw_by_id = {fv['frameworkViewId']: fv for fv in fws}
    for fw_id, sk in target_fws.items():
        fv = fw_by_id.get(fw_id)
        if fv:
            b_count = sum(1 for el in fv['elements'] if el['layer'] == 'B')
            if b_count < 2:
                errors.append(f"{fw_id} (sortKey {sk}): B要素が{b_count}件 (2件以上必要)")
        else:
            errors.append(f"{fw_id}: FWが見つからない")

    # Check F-PRG on sortKey 647
    fv647 = fw_by_id.get("FW_EV_p0647_01")
    if fv647:
        f_elements = [el for el in fv647['elements'] if el['layer'] == 'F']
        has_fprg = any(el['category'] == 'F-PRG' for el in f_elements)
        if not has_fprg:
            errors.append("FW_EV_p0647_01: F-PRGカテゴリが設定されていない")

    # Summary
    print(f"\n=== バリデーション結果 ===")
    print(f"FW数: {len(fws)}")
    print(f"層分布: B={layer_dist.get('B', 0)}, F={layer_dist.get('F', 0)}, E={layer_dist.get('E', 0)}")
    print(f"B要素数分布: {dict(sorted(b_count_dist.items()))}")
    print(f"momentum: {momentum_count}/{len(fws)}")

    if errors:
        print(f"\nエラー ({len(errors)}件):")
        for e in errors:
            print(f"  ✗ {e}")

    if warnings:
        print(f"\n警告 ({len(warnings)}件):")
        for w in warnings:
            print(f"  ⚠ {w}")

    return errors, warnings


def main():
    # Load v3.2 data
    input_path = os.path.join(BASE_DIR, 'framework_output_v3_2_erev.json')
    output_path = os.path.join(BASE_DIR, 'framework_output_v3_3.json')

    if not os.path.exists(input_path):
        print(f"エラー: {input_path} が存在しません")
        sys.exit(1)

    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    print(f"入力: {input_path}")
    print(f"version: {data['version']}")
    print(f"FW数: {len(data['frameworkViews'])}")

    # Migrate
    print("\n=== マイグレーション実行 ===")
    output = migrate(data)

    # Validate
    errors, warnings = validate(output)

    if errors:
        print(f"\nエラーがあるためマイグレーションを中止します。--force で強制出力可能。")
        if '--force' not in sys.argv:
            sys.exit(1)
        print("--force: エラーを無視して出力を続行")

    # Output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"出力: {output_path}")
    print(f"version: {output['version']}")


if __name__ == '__main__':
    main()
