#!/usr/bin/env python3
"""
generate_momentum_local.py — momentum（Eの解放の方向）をローカルで生成

API不要。ルールベース＋ヒューリスティックで全221件のmomentumを生成する。
- 設計メモ（notes_v3_3_design.html）の実証例はそのまま使用
- 残りはE-category + E-label + eventTitleからパターン導出

出力: data/momentum_v3_3.json
"""

import json
import os
import re
import sys
import time

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ============================================================
# 設計メモの実証例（そのまま使用）
# notes_v3_3_design.html セクション3.6, 4.2, 4.3
# ============================================================

KNOWN_MOMENTUM = {
    # 律令国家建設（セクション3.6）
    593: {"FW_EV_p0593_01": "王権を中心とした安定的統治が求められる方向へ"},
    603: {"FW_EV_p0603_01": "氏族的秩序から能力的秩序への転換が進む方向へ"},
    604: {"FW_EV_p0604_01": "統治が慣習から理念に基づくものへ移行する方向へ"},
    630: {"FW_EV_p0630_01": "律令的統治の具体的モデルが蓄積される方向へ"},
    645: {"FW_EV_p0645_01": "豪族支配を排し天皇中心の統治へ踏み出す方向へ"},
    672: {"FW_EV_p0672_01": "天皇の権威が圧倒的になり律令編纂を主導できる方向へ"},
    689: {"FW_EV_p0689_01": "律令に基づく官僚統治の実効性が高まる方向へ"},
    701: {"FW_EV_p0701_01": "律令国家としての運用が本格化する方向へ"},
    # 中央統治低下→地方自律（セクション4.2）
    939: {"FW_EV_p0939_01": "地方武力が中央統治を代替する方向へ"},
    988: {"FW_EV_p0988_01": "国司支配の矛盾が公然化し制度的正統性が揺らぐ方向へ"},
    1051: {"FW_EV_p1051_01": "武士が朝廷の軍事代行者として実績を積む方向へ"},
    1069: {"FW_EV_p1069_01": "王権が統制を試みるが荘園の根本構造は温存される方向へ"},
    1083: {"FW_EV_p1083_01": "武士間の主従関係が朝廷の制度外で強化される方向へ"},
    1156: {"FW_EV_p1156_01": "政治的決定に武力が不可欠となる方向へ"},
    1180: {"FW_EV_p1180_01": "武士が独自の統治機構を持つ方向へ"},
    1192: {"FW_EV_p1192_01": "武士政権が制度的に正統化される方向へ"},
    # 元禄文化（セクション4.3）
    1590: {"FW_EV_p1590_01": "統一権力による秩序形成の方向へ"},
    1588: {"FW_EV_p1588_01": "武力の集中管理と民間非武装化の方向へ"},
    1603: {"FW_EV_p1603_01": "安定的統治機構の恒常化の方向へ"},
    1615: {"FW_EV_p1615_01": "軍事的緊張の消滅と平和の恒常化の方向へ"},
    1635: {"FW_EV_p1635_01": "大名の経済力が街道・都市に流入する方向へ"},
    1639: {"FW_EV_p1639_01": "経済循環が国内に閉じ自己完結する方向へ"},
    1651: {"FW_EV_p1651_01": "武断から文治への統治原理転換の方向へ"},
    1688: {"FW_EV_p1688_01": "町人経済と文芸が自律的に展開する方向へ"},
}

# ============================================================
# E-categoryベースの変換テンプレート
# E-labelから方向性テキストを導出するパターン
# ============================================================

# E-labelの末尾パターン → 方向性テンプレート
LABEL_PATTERNS = {
    # E-POW: 権力再編型
    "E-POW": {
        "templates": [
            (r"新王擁立", "新たな王権のもとで統治秩序が再編される方向へ"),
            (r"実権掌握", "特定勢力による権力集中が進む方向へ"),
            (r"権力者排除|権力者の.*排除", "権力構造が暴力的に再編される方向へ"),
            (r"権力.*移行|権力.*交代|支配主体.*交代", "権力の担い手が変わり統治構造が再編される方向へ"),
            (r"協調型.*成立", "複数勢力の均衡による統治が形成される方向へ"),
            (r"補佐統治", "補佐体制による権力分担が進む方向へ"),
            (r"排除", "既存権力構造が解体される方向へ"),
        ],
        "default": "権力構造が再編される方向へ",
    },
    # E-WAR: 武力衝突型
    "E-WAR": {
        "templates": [
            (r"蜂起|反乱", "武力による既存秩序への挑戦が顕在化する方向へ"),
            (r"政変", "政治秩序が武力によって転換される方向へ"),
            (r"勢力争い|決着", "武力による勢力均衡が決定される方向へ"),
            (r"壊滅|滅亡|壊滅", "旧勢力が武力で排除され新秩序が形成される方向へ"),
            (r"軍事.*衝突|武力衝突", "軍事的対立が統治構造に影響を及ぼす方向へ"),
            (r"内戦|内乱", "内部対立が武力で決着される方向へ"),
            (r"外征|侵攻", "対外軍事行動が国内体制に影響する方向へ"),
        ],
        "default": "武力が政治的秩序を規定する方向へ",
    },
    # E-SYS: 制度成立型
    "E-SYS": {
        "templates": [
            (r"創設|新設|導入", "新たな制度的秩序が形成される方向へ"),
            (r"改革宣言|改革.*開始", "制度的改革が本格化する方向へ"),
            (r"成文化|法制化|法典化", "統治の制度的基盤が確立される方向へ"),
            (r"統治方針|制度化", "制度による統治が強化される方向へ"),
            (r"強化|整備", "既存制度の実効性が高まる方向へ"),
            (r"中央集権", "中央集権的統治が進展する方向へ"),
            (r"官位|官制", "官僚制度が体系化される方向へ"),
        ],
        "default": "制度的秩序が形成・強化される方向へ",
    },
    # E-REG: 体制転換型
    "E-REG": {
        "templates": [
            (r"転換|変革", "統治体制が根本的に転換される方向へ"),
            (r"確立|成立|開設", "新たな統治体制が定着する方向へ"),
            (r"退位.*統治", "制度外の統治形態が定着する方向へ"),
        ],
        "default": "統治体制が構造的に変容する方向へ",
    },
    # E-CUL: 文化秩序変容型
    "E-CUL": {
        "templates": [
            (r"到来|伝来|流入", "外来文化が社会秩序に影響を与える方向へ"),
            (r"開花|発展|繁栄", "文化的活動が自律的に展開する方向へ"),
            (r"衝突", "文化的・宗教的対立が政治に波及する方向へ"),
            (r"儀礼|象徴", "文化的権威が統治に組み込まれる方向へ"),
        ],
        "default": "文化的秩序が変容する方向へ",
    },
    # E-ADP: 外圧適応型
    "E-ADP": {
        "templates": [
            (r"対等|外交", "対外関係の再定義が進む方向へ"),
            (r"学習|吸収", "外部モデルの学習と内部適応が進む方向へ"),
            (r"断絶|中止|閉鎖", "対外関係の縮小と内向化が進む方向へ"),
            (r"適応|対応", "外圧への制度的対応が進む方向へ"),
        ],
        "default": "対外環境への適応が進む方向へ",
    },
    # E-ECO: 経済構造転換型
    "E-ECO": {
        "templates": [
            (r"負担.*増大|困窮", "経済的負担が社会構造を変容させる方向へ"),
            (r"導入|創設", "新たな経済制度が社会に浸透する方向へ"),
        ],
        "default": "経済構造が変容する方向へ",
    },
    # E-COL: 崩壊型
    "E-COL": {
        "templates": [
            (r"崩壊|瓦解|終焉", "既存秩序が解体され新たな秩序が模索される方向へ"),
            (r"動揺|不安定", "社会秩序の不安定化が進む方向へ"),
            (r"危機|災害", "危機が社会の再編を迫る方向へ"),
        ],
        "default": "既存秩序が動揺し再編が迫られる方向へ",
    },
}


def generate_momentum_for_fw(fw):
    """Generate momentum text for a single FW."""
    fw_id = fw['frameworkViewId']
    sort_key = fw['sortKey']
    title = fw['title']

    # 1. 設計メモの既知momentumを優先
    if sort_key in KNOWN_MOMENTUM:
        known = KNOWN_MOMENTUM[sort_key]
        if fw_id in known:
            return known[fw_id]

    # 2. E要素を取得
    e_elements = [el for el in fw['elements'] if el['layer'] == 'E']
    if not e_elements:
        return None

    e_el = e_elements[0]
    e_cat = e_el['category']
    e_label = e_el['label']

    # 3. カテゴリ別テンプレートでパターンマッチ
    patterns = LABEL_PATTERNS.get(e_cat)
    if patterns:
        for regex, template in patterns['templates']:
            if re.search(regex, e_label):
                return template
        return patterns['default']

    return "新たな秩序が形成される方向へ"


def main():
    # Load data
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_3.json')
    if not os.path.exists(fw_path):
        print(f"エラー: {fw_path} が存在しません")
        print("先に migrate_v3_3.py を実行してください")
        sys.exit(1)

    with open(fw_path, encoding='utf-8') as f:
        data = json.load(f)

    fws = data['frameworkViews']
    print(f"対象FW: {len(fws)}件")

    # Generate momentum for all FWs
    output = {
        "version": "3.3",
        "generatedBy": "generate_momentum_local.py",
        "model": "rule-based",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": {}
    }

    known_count = 0
    pattern_count = 0
    default_count = 0

    for fw in fws:
        fw_id = fw['frameworkViewId']
        sort_key = fw['sortKey']

        momentum = generate_momentum_for_fw(fw)

        # 分類統計
        if sort_key in KNOWN_MOMENTUM and fw_id in KNOWN_MOMENTUM.get(sort_key, {}):
            known_count += 1
            source = "known"
        else:
            # テンプレートかデフォルトか判定
            e_elements = [el for el in fw['elements'] if el['layer'] == 'E']
            if e_elements:
                e_cat = e_elements[0]['category']
                e_label = e_elements[0]['label']
                patterns = LABEL_PATTERNS.get(e_cat, {})
                matched = False
                for regex, _ in patterns.get('templates', []):
                    if re.search(regex, e_label):
                        matched = True
                        break
                if matched:
                    pattern_count += 1
                    source = "pattern"
                else:
                    default_count += 1
                    source = "default"
            else:
                default_count += 1
                source = "default"

        output["items"][fw_id] = {"momentum": momentum}

        # 表示
        label_short = momentum[:35] if momentum else "(null)"
        print(f"  [{sort_key:>4}] {fw_id}: {label_short}  [{source}]")

    # Validate
    print(f"\n=== 統計 ===")
    print(f"設計メモ既知: {known_count}件")
    print(f"パターンマッチ: {pattern_count}件")
    print(f"デフォルト: {default_count}件")
    print(f"合計: {known_count + pattern_count + default_count}件")

    # 方向へ で終わるか確認
    bad_ending = 0
    for fw_id, item in output["items"].items():
        m = item.get("momentum")
        if m and not m.endswith("方向へ"):
            bad_ending += 1
            print(f"  ⚠ {fw_id}: 「方向へ」で終わらない: {m}")
    print(f"フォーマット不正: {bad_ending}件")

    # Output
    out_path = os.path.join(BASE_DIR, 'momentum_v3_3.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n出力: {out_path}")


if __name__ == '__main__':
    main()
