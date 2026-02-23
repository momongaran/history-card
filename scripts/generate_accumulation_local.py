#!/usr/bin/env python3
"""
generate_accumulation_local.py — API不要のローカル版 accumulation 生成

B要素のカテゴリ・ラベルを分析し、ルールベースで accumulation を生成する。
ラベルの条件記述化も行う。
"""

import json
import os
import re
import sys
import time
from itertools import combinations

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ============================================================
# Mechanism決定ルール
# ============================================================

# カテゴリペアからmechanismを推定するルール表
# (cat_a, cat_b) → mechanism  ※順序不問、最初にマッチしたものを使用
CATEGORY_MECHANISM_RULES = [
    # tension: 対立的な組み合わせ
    ({"B-PWR"}, {"B-RIV"}, "tension"),
    ({"B-PWR"}, {"B-SOC"}, "tension"),
    ({"B-PWR"}, {"B-EXT"}, "tension"),
    ({"B-INS"}, {"B-SOC"}, "tension"),
    ({"B-INS"}, {"B-RIV"}, "tension"),
    ({"B-MIL"}, {"B-SOC"}, "tension"),
    ({"B-MIL"}, {"B-EXT"}, "tension"),
    ({"B-NRM"}, {"B-RIV"}, "tension"),
    ({"B-LEG"}, {"B-RIV"}, "tension"),
    ({"B-RES"}, {"B-EXT"}, "tension"),

    # constraint: 制約的な組み合わせ
    ({"B-GEO"}, {"B-MIL"}, "constraint"),
    ({"B-GEO"}, {"B-RES"}, "constraint"),
    ({"B-GEO"}, {"B-EXT"}, "constraint"),
    ({"B-RES"}, {"B-MIL"}, "constraint"),
    ({"B-RES"}, {"B-INS"}, "constraint"),
    ({"B-INS"}, {"B-PWR"}, "constraint"),
    ({"B-INS"}, {"B-MIL"}, "constraint"),

    # enabling: 促進的な組み合わせ
    ({"B-RES"}, {"B-PWR"}, "enabling"),
    ({"B-INF"}, {"B-INS"}, "enabling"),
    ({"B-INF"}, {"B-PWR"}, "enabling"),
    ({"B-NRM"}, {"B-LEG"}, "enabling"),
    ({"B-NRM"}, {"B-INS"}, "enabling"),
    ({"B-LEG"}, {"B-PWR"}, "enabling"),
    ({"B-SOC"}, {"B-RES"}, "enabling"),
    ({"B-EXT"}, {"B-NRM"}, "enabling"),

    # amplification: 増幅的な組み合わせ
    ({"B-MIL"}, {"B-PWR"}, "amplification"),
    ({"B-MIL"}, {"B-RIV"}, "amplification"),
    ({"B-EXT"}, {"B-RIV"}, "amplification"),
    ({"B-RES"}, {"B-RIV"}, "amplification"),
    ({"B-SOC"}, {"B-RIV"}, "amplification"),
    ({"B-PWR"}, {"B-PWR"}, "amplification"),
    ({"B-EXT"}, {"B-EXT"}, "amplification"),

    # convergence: 同カテゴリ同士（amplification以外）
    ({"B-SOC"}, {"B-SOC"}, "convergence"),
    ({"B-INS"}, {"B-INS"}, "convergence"),
    ({"B-RES"}, {"B-RES"}, "convergence"),
    ({"B-NRM"}, {"B-NRM"}, "convergence"),
    ({"B-MIL"}, {"B-MIL"}, "convergence"),
    ({"B-LEG"}, {"B-LEG"}, "convergence"),
    ({"B-GEO"}, {"B-GEO"}, "convergence"),
    ({"B-INF"}, {"B-INF"}, "convergence"),
]

# ラベルキーワードによるmechanism補正
KEYWORD_MECHANISM = [
    # tension keywords
    (["反発", "対立", "不満", "抵抗", "対抗", "衝突", "矛盾", "緊張", "敵対", "反乱"], "tension"),
    # constraint keywords
    (["制約", "限界", "不足", "困難", "圧迫", "狭", "行き詰", "疲弊", "弱体", "衰退"], "constraint"),
    # amplification keywords
    (["強化", "激化", "拡大", "増大", "高まり", "深刻", "悪化", "膨張", "過熱"], "amplification"),
    # enabling keywords
    (["基盤", "前提", "準備", "整備", "蓄積", "確立", "形成", "成立", "普及"], "enabling"),
    # convergence keywords
    (["集中", "重なり", "合流", "同時", "並行", "重複", "連動"], "convergence"),
]


def determine_mechanism(el_a, el_b):
    """2つのB要素間のmechanismを決定する"""
    cat_a = el_a['cat']
    cat_b = el_b['cat']
    label_a = el_a['label']
    label_b = el_b['label']
    combined_labels = label_a + label_b

    # まずラベルキーワードでチェック（具体的な内容に基づく）
    for keywords, mech in KEYWORD_MECHANISM:
        for kw in keywords:
            if kw in combined_labels:
                return mech

    # カテゴリペアルールでチェック
    for set_a, set_b, mech in CATEGORY_MECHANISM_RULES:
        if (cat_a in set_a and cat_b in set_b) or (cat_b in set_a and cat_a in set_b):
            return mech

    # デフォルト: カテゴリが同じならconvergence、異なればenabling
    if cat_a == cat_b:
        return "convergence"
    return "enabling"


# ============================================================
# Description生成
# ============================================================

CAT_SHORT_NAMES = {
    'B-PWR': '権力構造', 'B-LEG': '正統性基盤', 'B-INS': '制度枠組み',
    'B-SOC': '社会構造', 'B-RES': '資源基盤', 'B-EXT': '対外圧力',
    'B-MIL': '軍事基盤', 'B-NRM': '価値規範', 'B-INF': '情報基盤',
    'B-GEO': '地理条件', 'B-RIV': '利害対立',
}

MECHANISM_DESC_TEMPLATES = {
    "tension": "{a_cat}と{b_cat}が逆方向に作用し構造的緊張が蓄積された",
    "amplification": "{a_cat}が{b_cat}を強化し危機のエネルギーが増幅された",
    "constraint": "{a_cat}が{b_cat}の選択肢を狭め行動を制約していた",
    "enabling": "{a_cat}が{b_cat}の作動前提を形成していた",
    "convergence": "{a_cat}と{b_cat}が同一の圧力点に収斂していた",
}


def extract_subject(label, max_len=15):
    """ラベルから主語（最初の「が」「の」まで）を抽出する"""
    # 「〜が」で区切られる主語を取得
    m = re.match(r'^(.+?[がのを])', label)
    if m:
        subj = m.group(1)
        if len(subj) <= max_len:
            return subj.rstrip('がのを')
    # フォールバック: 先頭N文字
    return label[:max_len]


def generate_description(el_a, el_b, mechanism):
    """relation descriptionを生成する"""
    a_cat = CAT_SHORT_NAMES.get(el_a['cat'], el_a['cat'])
    b_cat = CAT_SHORT_NAMES.get(el_b['cat'], el_b['cat'])
    a_subj = extract_subject(el_a['label'])
    b_subj = extract_subject(el_b['label'])

    # カテゴリが同じ場合は主語を使って区別
    if el_a['cat'] == el_b['cat']:
        a_cat = a_subj
        b_cat = b_subj

    template = MECHANISM_DESC_TEMPLATES[mechanism]
    desc = template.format(a_cat=a_cat, b_cat=b_cat)

    # 長すぎる場合はカテゴリ名で再生成
    if len(desc) > 100:
        a_cat = CAT_SHORT_NAMES.get(el_a['cat'], el_a['cat'])
        b_cat = CAT_SHORT_NAMES.get(el_b['cat'], el_b['cat'])
        desc = template.format(a_cat=a_cat, b_cat=b_cat)
    if len(desc) > 100:
        desc = desc[:97] + "..."
    return desc


def generate_summary(fw_title, relations, b_elements):
    """accumulation summaryを生成する"""
    cats = set(e['cat'] for e in b_elements)
    cat_names = {
        'B-PWR': '権力配置', 'B-LEG': '正統性', 'B-INS': '制度',
        'B-SOC': '社会構造', 'B-RES': '資源', 'B-EXT': '対外環境',
        'B-MIL': '軍事', 'B-NRM': '価値体系', 'B-INF': '情報',
        'B-GEO': '地理条件', 'B-RIV': '利害対立',
    }
    cat_labels = [cat_names.get(c, c) for c in sorted(cats)]

    mechs = set(r['mechanism'] for r in relations)
    mech_names = {
        'tension': '緊張', 'amplification': '増幅', 'constraint': '制約',
        'enabling': '促進', 'convergence': '収斂',
    }
    mech_label = '・'.join(mech_names.get(m, m) for m in sorted(mechs))

    summary = f"{'と'.join(cat_labels)}の{mech_label}が蓄積し事象に至った"
    if len(summary) > 100:
        summary = summary[:97] + "..."
    return summary


# ============================================================
# ラベル条件記述化
# ============================================================

def revise_label(label):
    """行為記述を条件記述に変換する"""
    original = label

    # 既に条件記述（〜していた、〜であった、〜されていた等）なら変更不要
    condition_endings = [
        'していた', 'であった', 'されていた', 'いた', 'ていた',
        'なっていた', 'れていた', 'あった', 'きていた',
    ]
    for ending in condition_endings:
        if label.endswith(ending):
            return label

    # 行為記述パターンの変換
    replacements = [
        # 〜した → 〜していた
        (r'した$', 'していた'),
        # 〜された → 〜されていた
        (r'された$', 'されていた'),
        # 〜なった → 〜なっていた
        (r'なった$', 'なっていた'),
        # 〜った → 〜っていた
        (r'([^な])った$', r'\1っていた'),
        # 〜んだ → 〜んでいた
        (r'んだ$', 'んでいた'),
        # 〜いだ → 〜いでいた
        (r'いだ$', 'いでいた'),
        # 〜を行った → 〜が行われていた
        (r'を行った$', 'が行われていた'),
    ]

    for pattern, replacement in replacements:
        new_label = re.sub(pattern, replacement, label)
        if new_label != label:
            return new_label

    return label


def check_category(el):
    """カテゴリの妥当性をチェックし、修正が必要なら修正後のカテゴリを返す"""
    label = el['label']
    cat = el['cat']
    sub = el['sub']

    # ラベルに基づくカテゴリ推定
    suggested_cat = None
    suggested_sub = None

    # 軍事関連のラベルがB-INSやB-RESに入っている場合
    military_keywords = ['軍事', '軍', '兵', '動員', '武力', '武装', '戦力', '防衛', '軍団']
    if any(kw in label for kw in military_keywords):
        if cat not in ('B-MIL', 'B-RES', 'B-INS'):
            suggested_cat = 'B-MIL'
            if '動員' in label:
                suggested_sub = 'B-MIL-03'
            elif '防衛' in label:
                suggested_sub = 'B-MIL-04'
            elif '組織' in label or '軍団' in label:
                suggested_sub = 'B-MIL-01'
            else:
                suggested_sub = 'B-MIL-01'

    # 対外・外交関連のラベルがB-NRMに入っている場合
    external_keywords = ['外交', '半島', '唐', '隋', '新羅', '百済', '渤海', '朝鮮', '明', '清', '元', '蒙古', '対外']
    if any(kw in label for kw in external_keywords):
        if cat == 'B-NRM':
            # 外交圧力や軍事脅威の可能性
            if any(kw in label for kw in ['脅威', '侵攻', '攻撃', '軍事']):
                suggested_cat = 'B-EXT'
                suggested_sub = 'B-EXT-02'
            elif any(kw in label for kw in ['同盟', '関係', '外交']):
                suggested_cat = 'B-EXT'
                suggested_sub = 'B-EXT-01'
            elif any(kw in label for kw in ['文化', '仏教', '思想', '学問', '制度']):
                # 文化流入としてB-EXTが適切
                if '伝来' in label or '流入' in label or '献上' in label:
                    suggested_cat = 'B-EXT'
                    suggested_sub = 'B-EXT-03'

    # 権力・政治関連のラベルがB-INSに入っている場合
    power_keywords = ['権力', '実権', '掌握', '覇権', '勢力均衡', '主導権']
    if any(kw in label for kw in power_keywords):
        if cat == 'B-INS':
            suggested_cat = 'B-PWR'
            if '均衡' in label or 'バランス' in label:
                suggested_sub = 'B-PWR-02'
            elif '集権' in label or '中央' in label:
                suggested_sub = 'B-PWR-01'
            elif '実権' in label or '名目' in label:
                suggested_sub = 'B-PWR-04'
            else:
                suggested_sub = 'B-PWR-01'

    # 利害対立がB-PWRやB-SOCに入っている場合
    rivalry_keywords = ['対立', '抗争', '敵対', '反目', '争い']
    if any(kw in label for kw in rivalry_keywords):
        if cat in ('B-PWR', 'B-SOC') and 'B-RIV' not in cat:
            # 政治的対立はB-RIVが適切な場合がある
            # ただしPWRの権力配置としても妥当なケースが多いのでsubCategoryで判断
            pass

    if suggested_cat and suggested_cat != cat:
        return suggested_cat, suggested_sub
    return cat, sub


# ============================================================
# メイン処理
# ============================================================

def process_fw(fw):
    """1つのFWを処理してaccumulation + revisionsを返す"""
    b_elements = fw['b_elements']
    b_count = len(b_elements)

    # relations生成
    relations = []
    pairs = list(combinations(range(b_count), 2))

    for i, j in pairs:
        el_a = b_elements[i]
        el_b = b_elements[j]
        mechanism = determine_mechanism(el_a, el_b)
        description = generate_description(el_a, el_b, mechanism)
        relations.append({
            "from": el_a['id'],
            "to": el_b['id'],
            "mechanism": mechanism,
            "description": description,
        })

    # B=2の場合: 1件のみ（既にそうなっている）
    # B=3の場合: 1-3件（全ペアを出力、ただし意味が薄いものは除外可能）
    # ここでは全ペアを出力（最大3件）

    summary = generate_summary(fw['title'], relations, b_elements)

    # revisions生成
    revisions = []
    for el in b_elements:
        new_label = revise_label(el['label'])
        new_cat, new_sub = check_category(el)
        revisions.append({
            "elementId": el['id'],
            "labelRevised": new_label,
            "categoryRevised": new_cat,
            "subCategoryRevised": new_sub,
        })

    return {
        "accumulation": {
            "relations": relations,
            "summary": summary,
        },
        "revisions": revisions,
    }


def main():
    # Load data
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_0_bfe.json')
    with open(fw_path, encoding='utf-8') as f:
        data = json.load(f)

    events = {ev['eventId']: ev for ev in data['events']}
    fws = data['frameworkViews']

    output_items = {}
    target_count = 0
    skip_count = 0

    for fw in fws:
        fw_id = fw['frameworkViewId']
        b_elements = [
            {
                'id': e['elementId'],
                'label': e['label'],
                'cat': e['category'],
                'sub': e['subCategory'],
            }
            for e in fw['elements'] if e['layer'] == 'B'
        ]
        b_count = len(b_elements)

        if b_count <= 1:
            output_items[fw_id] = {
                "accumulation": None,
                "revisions": [],
            }
            skip_count += 1
            continue

        target_count += 1
        fw_data = {
            'fw_id': fw_id,
            'title': fw['title'],
            'sortKey': fw.get('sortKey'),
            'b_elements': b_elements,
        }
        result = process_fw(fw_data)
        output_items[fw_id] = result

    # Assemble output
    output = {
        "version": "3.1",
        "generatedBy": "generate_accumulation_local.py",
        "model": "rule-based",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": output_items,
    }

    out_path = os.path.join(BASE_DIR, 'accumulation_v3_1.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Statistics
    mech_counts = {}
    total_rels = 0
    label_changed = 0
    cat_changed = 0

    for fw_id, item in output_items.items():
        accum = item.get('accumulation')
        if accum and accum.get('relations'):
            for rel in accum['relations']:
                m = rel['mechanism']
                mech_counts[m] = mech_counts.get(m, 0) + 1
                total_rels += 1

        for rev in item.get('revisions', []):
            # Check if label was changed
            # Find original element
            pass

    # Count actual changes
    for fw in fws:
        fw_id = fw['frameworkViewId']
        item = output_items.get(fw_id)
        if not item:
            continue
        for el in fw['elements']:
            if el['layer'] != 'B':
                continue
            rev = None
            for r in item.get('revisions', []):
                if r['elementId'] == el['elementId']:
                    rev = r
                    break
            if rev:
                if rev['labelRevised'] != el['label']:
                    label_changed += 1
                if rev['categoryRevised'] != el['category']:
                    cat_changed += 1

    print(f"=== 生成完了 ===")
    print(f"対象FW: {target_count}件 (B>=2)")
    print(f"スキップ: {skip_count}件 (B<=1)")
    print(f"relations総数: {total_rels}")
    print(f"ラベル変更: {label_changed}件")
    print(f"カテゴリ変更: {cat_changed}件")
    print(f"出力: {out_path}")

    print(f"\n=== mechanism分布 ===")
    for m, c in sorted(mech_counts.items(), key=lambda x: -x[1]):
        pct = c / total_rels * 100 if total_rels > 0 else 0
        flag = " ⚠️" if pct > 60 else ""
        print(f"  {m}: {c} ({pct:.1f}%){flag}")


if __name__ == '__main__':
    main()
