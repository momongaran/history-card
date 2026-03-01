#!/usr/bin/env python3
"""
v3.7 E層サブカテゴリ再設計

問題:
- E-WAR-01に60件が集中（宮廷政変～対外戦争まで混在）
- E-POW-01に暗殺と即位が混在（逆ベクトル）
- カテゴリコードだけでイベント特徴を識別できない

設計方針:
E-WAR: 6分類（内戦, 地方反乱, 決戦, 対外衝突, 弾圧, 宮廷政変）
E-POW: 5分類（皇位継承, 権力集中, 権力者排除, 実権掌握, 権力空白）
E-WAR以外のカテゴリへの移動: 約10件
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# === E-WAR-01 → 新サブカテゴリ ===
# (eventId, elementId, new_category, new_subCategory)

REASSIGN_WAR = [
    # --- E-WAR-01: 内戦・全国規模戦役 ---
    # 全国規模の長期にわたる内乱、国を二分する戦争
    ("EV_p0672_01", "EL_EV_p0672_01_4", "E-WAR", "E-WAR-01"),  # 壬申の乱
    ("EV_p1180_01", "EL_EV_p1180_01_5", "E-WAR", "E-WAR-01"),  # 以仁王挙兵→源平合戦開始
    ("EV_p1185_01", "EL_EV_p1185_01_5", "E-WAR", "E-WAR-01"),  # 壇ノ浦（源平合戦決着）
    ("EV_p1221_01", "EL_EV_p1221_01_4", "E-WAR", "E-WAR-01"),  # 承久の乱
    ("EV_p1221_02", "EL_EV_p1221_02_4", "E-WAR", "E-WAR-01"),  # 承久の乱（結果視点）
    ("EV_p1331_01", "EL_EV_p1331_01_4", "E-WAR", "E-WAR-01"),  # 元弘の変
    ("EV_p1336_03", "EL_EV_p1336_03_5", "E-WAR", "E-WAR-01"),  # 尊氏離反→南北朝
    ("EV_p1351_01", "EL_EV_p1351_01_5", "E-WAR", "E-WAR-01"),  # 観応の擾乱
    ("EV_p1477_01", "EL_EV_p1477_01_4", "E-WAR", "E-WAR-01"),  # 応仁の乱

    # --- E-WAR-02: 地方反乱・武力蜂起 ---
    # 地方豪族の反乱、一揆、蜂起
    ("EV_p0527_01", "EL_EV_p0527_01_5", "E-WAR", "E-WAR-02"),  # 磐井の乱
    ("EV_p0740_01", "EL_EV_p0740_01_4", "E-WAR", "E-WAR-02"),  # 藤原広嗣の乱
    ("EV_p0939_01", "EL_EV_p0939_01_5", "E-WAR", "E-WAR-02"),  # 平将門の乱
    ("EV_p0939_02", "EL_EV_p0939_02_4", "E-WAR", "E-WAR-02"),  # 藤原純友の乱
    ("EV_p1213_01", "EL_EV_p1213_01_5", "E-WAR", "E-WAR-02"),  # 和田合戦
    ("EV_p1247_01", "EL_EV_p1247_01_5", "E-WAR", "E-WAR-02"),  # 宝治合戦
    ("EV_p1285_01", "EL_EV_p1285_01_5", "E-WAR", "E-WAR-02"),  # 霜月騒動
    ("EV_p1438_01", "EL_EV_p1438_01_4", "E-WAR", "E-WAR-02"),  # 永享の乱
    ("EV_p1637_01", "EL_EV_p1637_01_5", "E-WAR", "E-WAR-02"),  # 島原の乱
    ("EV_p1837_01", "EL_EV_p1837_01_4", "E-WAR", "E-WAR-02"),  # 大塩平八郎の乱
    ("EV_p1862_01", "EL_EV_p1862_01_5", "E-WAR", "E-WAR-02"),  # 生麦事件
    ("EV_p1651_01", "EL_EV_p1651_01_4", "E-WAR", "E-WAR-02"),  # 慶安の変

    # --- E-WAR-03: 決戦・会戦 ---
    # 特定の戦場での戦闘、勝敗が明確な合戦
    ("EV_p0587_01", "EL_EV_p0587_01_4", "E-WAR", "E-WAR-03"),  # 丁未の乱（蘇我vs物部）
    ("EV_p1156_01", "EL_EV_p1156_01_4", "E-WAR", "E-WAR-03"),  # 保元の乱
    ("EV_p1159_01", "EL_EV_p1159_01_4", "E-WAR", "E-WAR-03"),  # 平治の乱
    ("EV_p1555_01", "EL_EV_p1555_01_5", "E-WAR", "E-WAR-03"),  # 厳島の戦い
    ("EV_p1560_01", "EL_EV_p1560_01_5", "E-WAR", "E-WAR-03"),  # 桶狭間の戦い
    ("EV_p1570_01", "EL_EV_p1570_01_5", "E-WAR", "E-WAR-03"),  # 姉川の戦い
    ("EV_p1575_01", "EL_EV_p1575_01_5", "E-WAR", "E-WAR-03"),  # 長篠の戦い
    ("EV_p1582_01", "EL_EV_p1582_01_5", "E-WAR", "E-WAR-03"),  # 山崎の戦い
    ("EV_p1583_01", "EL_EV_p1583_01_5", "E-WAR", "E-WAR-03"),  # 賤ヶ岳の戦い
    ("EV_p1584_01", "EL_EV_p1584_01_5", "E-WAR", "E-WAR-03"),  # 小牧・長久手の戦い
    ("EV_p1590_02", "EL_EV_p1590_02_5", "E-WAR", "E-WAR-03"),  # 小田原征伐
    ("EV_p1600_01", "EL_EV_p1600_01_5", "E-WAR", "E-WAR-03"),  # 関ヶ原の戦い
    ("EV_p1864_01", "EL_EV_p1864_01_4", "E-WAR", "E-WAR-03"),  # 禁門の変

    # --- E-WAR-04: 対外軍事衝突 ---
    ("EV_p1274_01", "EL_EV_p1274_01_5", "E-WAR", "E-WAR-04"),  # 文永の役
    ("EV_p1274_02", "EL_EV_p1274_02_5", "E-WAR", "E-WAR-04"),  # 文永の役(別視点)
    ("EV_p1281_01", "EL_EV_p1281_01_4", "E-WAR", "E-WAR-04"),  # 弘安の役
    ("EV_p1863_01", "EL_EV_p1863_01_4", "E-WAR", "E-WAR-04"),  # 薩英戦争
    ("EV_p1931_01", "EL_EV_p1931_01_5", "E-WAR", "E-WAR-04"),  # 満州事変

    # --- E-WAR-05: 宗教・思想弾圧 ---
    ("EV_p1571_01", "EL_EV_p1571_01_5", "E-WAR", "E-WAR-05"),  # 比叡山焼き討ち
    ("EV_p1839_01", "EL_EV_p1839_01_5", "E-WAR", "E-WAR-05"),  # 蛮社の獄

    # --- E-WAR-06: 宮廷政変・クーデター ---
    # 政権中枢でのクーデター、陰謀事件
    ("EV_p0645_01", "EL_EV_p0645_01_3", "E-WAR", "E-WAR-06"),  # 乙巳の変
    ("EV_p0729_01", "EL_EV_p0729_01_4", "E-WAR", "E-WAR-06"),  # 長屋王の変
    ("EV_p0757_01", "EL_EV_p0757_01_4", "E-WAR", "E-WAR-06"),  # 橘奈良麻呂の乱
    ("EV_p0764_01", "EL_EV_p0764_01_4", "E-WAR", "E-WAR-06"),  # 恵美押勝の乱
    ("EV_p0810_01", "EL_EV_p0810_01_4", "E-WAR", "E-WAR-06"),  # 平城太上天皇の変
    ("EV_p0842_01", "EL_EV_p0842_01_4", "E-WAR", "E-WAR-06"),  # 承和の変
    ("EV_p0866_01", "EL_EV_p0866_01_4", "E-WAR", "E-WAR-06"),  # 応天門の変
    ("EV_p0969_01", "EL_EV_p0969_01_4", "E-WAR", "E-WAR-06"),  # 安和の変
    ("EV_p1177_01", "EL_EV_p1177_01_5", "E-WAR", "E-WAR-06"),  # 鹿ケ谷の陰謀
    ("EV_p1493_01", "EL_EV_p1493_01_5", "E-WAR", "E-WAR-06"),  # 明応の政変
    ("EV_p1582_02", "EL_EV_p1582_02_4", "E-WAR", "E-WAR-06"),  # 本能寺の変
]

# === E-WAR-01 → 別カテゴリへ移動 ===
MOVE_OUT_OF_WAR = [
    # 大政奉還: 武力衝突ではなく政体転換
    ("EV_p1867_01", "EL_EV_p1867_01_5", "E-REG", "E-REG-02"),
    # 廃藩置県: 行政改革
    ("EV_p1871_01", "EL_EV_p1871_01_5", "E-SYS", "E-SYS-04"),
    # 韓国併合: 支配構造再定義
    ("EV_p1910_01", "EL_EV_p1910_01_5", "E-REG", "E-REG-04"),
    # 国連脱退: 外交断絶（外圧適応の逆）→ E-ADP内に
    ("EV_p1933_01", "EL_EV_p1933_01_5", "E-ADP", "E-ADP-03"),
    # ポツダム宣言受諾: 政体転換
    ("EV_p1945_02", "EL_EV_p1945_02_5", "E-REG", "E-REG-02"),
    # 沖縄返還: 支配構造再定義
    ("EV_p1972_01", "EL_EV_p1972_01_5", "E-REG", "E-REG-04"),
    # 洋書輸入緩和: 文化秩序変化
    ("EV_p1720_01", "EL_EV_p1720_01_5", "E-CUL", "E-CUL-01"),
    # 田沼意次: 経済政策 → 経済構造転換
    ("EV_p1772_01", "EL_EV_p1772_01_5", "E-ECO", "E-ECO-01"),
    # 桜田門外の変: E-POW-01にいるが→E-POW-03（権力者排除）へ移動
    # （これはPOW再分類で処理）
]

# === E-POW 再分類 ===
REASSIGN_POW = [
    # --- E-POW-01: 皇位継承・即位 ---
    ("EV_p0507_01", "EL_EV_p0507_01_4", "E-POW", "E-POW-01"),  # 継体天皇即位
    ("EV_p0593_01", "EL_EV_p0593_01_4", "E-POW", "E-POW-01"),  # 推古天皇即位
    ("EV_p1068_01", "EL_EV_p1068_01_5", "E-POW", "E-POW-01"),  # 後三条天皇即位
    ("EV_p1108_01", "EL_EV_p1108_01_5", "E-POW", "E-POW-01"),  # 鳥羽天皇即位
    ("EV_p1989_01", "EL_EV_p1989_01_5", "E-POW", "E-POW-01"),  # 昭和崩御→平成即位
    ("EV_p2019_01", "EL_EV_p2019_01_5", "E-POW", "E-POW-01"),  # 令和改元即位

    # --- E-POW-03: 権力者排除・失脚 (NEW) ---
    ("EV_p0592_01", "EL_EV_p0592_01_5", "E-POW", "E-POW-03"),  # 崇峻天皇暗殺
    ("EV_p0901_01", "EL_EV_p0901_01_5", "E-POW", "E-POW-03"),  # 菅原道真左遷
    ("EV_p1205_01", "EL_EV_p1205_01_5", "E-POW", "E-POW-03"),  # 北条時政失脚
    ("EV_p1441_01", "EL_EV_p1441_01_4", "E-POW", "E-POW-03"),  # 足利義教暗殺
    ("EV_p1860_01", "EL_EV_p1860_01_4", "E-POW", "E-POW-03"),  # 桜田門外の変（井伊暗殺）

    # --- E-POW-04: 実権掌握・就任 (keep all existing) ---
    # These stay as-is: EV_p0512_01, EV_p0593_02, EV_p1016_01, EV_p1016_02,
    # EV_p1167_01, EV_p1183_01, EV_p1184_01, EV_p1192_01, EV_p1203_01,
    # EV_p1338_01, EV_p1568_01, EV_p1585_01, EV_p1586_01, EV_p1587_02

    # --- E-POW-05: 権力空白・動揺 (NEW) ---
    ("EV_p1129_01", "EL_EV_p1129_01_5", "E-POW", "E-POW-05"),  # 白河上皇崩御→権力空白
    ("EV_p1199_01", "EL_EV_p1199_01_5", "E-POW", "E-POW-05"),  # 源頼朝死去→幕府動揺
    ("EV_p1598_01", "EL_EV_p1598_01_5", "E-POW", "E-POW-05"),  # 秀吉死去→豊臣政権動揺
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build lookup
    elem_index = {}
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            elem_index[(fv["eventId"], elem.get("elementId"))] = elem

    all_ops = (
        [(eid, elid, cat, sc) for eid, elid, cat, sc in REASSIGN_WAR] +
        [(eid, elid, cat, sc) for eid, elid, cat, sc in MOVE_OUT_OF_WAR] +
        [(eid, elid, cat, sc) for eid, elid, cat, sc in REASSIGN_POW]
    )

    reassigned = 0
    not_found = []
    changes = []

    for eid, elid, new_cat, new_sc in all_ops:
        key = (eid, elid)
        if key not in elem_index:
            not_found.append(key)
            continue
        elem = elem_index[key]
        old_cat = elem.get("category", "?")
        old_sc = elem.get("subCategory", "?")
        elem["category"] = new_cat
        elem["subCategory"] = new_sc
        reassigned += 1
        if old_sc != new_sc:
            changes.append(f"  {eid}: {old_sc} → {new_sc}")

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Stats
    from collections import Counter
    e_counts = Counter()
    for fv in data["frameworkViews"]:
        for el in fv.get("elements", []):
            if el["layer"] == "E":
                e_counts[el.get("subCategory", "NONE")] += 1

    print(f"=== v3.7 E層サブカテゴリ再設計 ===")
    print(f"再分類: {reassigned}/{len(all_ops)}件")
    if not_found:
        print(f"未発見: {len(not_found)}件")
        for k in not_found:
            print(f"  {k}")

    print(f"\n--- E分布（再分類後） ---")
    for sc in sorted(e_counts):
        print(f"  {sc}: {e_counts[sc]}件")

    # Verify no E-WAR-02/03/04 old-style remain
    old_style = [sc for sc in e_counts if sc in ("E-WAR-02", "E-WAR-03", "E-WAR-04")]
    # These should now exist with new meanings

    # Show changes
    print(f"\n--- 変更詳細 ({len(changes)}件) ---")
    for c in changes[:30]:
        print(c)
    if len(changes) > 30:
        print(f"  ... 他{len(changes)-30}件")

    print(f"\n>>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
