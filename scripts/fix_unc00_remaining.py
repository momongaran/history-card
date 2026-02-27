#!/usr/bin/env python3
"""
v3.5 F-UNC-00 残存27件の分類・ラベル個別化

F-UNC-00に残っている27件を適切なカテゴリに再分類し、
具体的なFラベルに書き換える。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# (eventId, new_category, new_subCategory, new_label)
FIXES = [
    # --- F-ACT-01: 人物の決断・行動 ---
    ("EV_p0593_02", "F-ACT", "F-ACT-01",
     "崇峻天皇暗殺後の皇位継承で推古天皇が即位し、厩戸王が摂政に任命された"),
    ("EV_p0759_01", "F-ACT", "F-ACT-01",
     "大伴家持が防人歌や東歌を含む約四千五百首を体系的に編纂した"),
    ("EV_p0784_01", "F-ACT", "F-ACT-01",
     "桓武天皇が奈良仏教勢力からの脱却を図り長岡の地への遷都を決断した"),
    ("EV_p0905_01", "F-ACT", "F-ACT-01",
     "醍醐天皇が紀貫之らに勅撰和歌集の編纂を命じた"),
    ("EV_p0988_01", "F-ACT", "F-ACT-01",
     "尾張国の郡司・百姓が国司藤原元命の悪政を三十一ヶ条にまとめ太政官へ直訴した"),
    ("EV_p1096_01", "F-ACT", "F-ACT-01",
     "白河上皇が荘園整理のため全国の国ごとに田地面積を記録する大田文の作成を命じた"),
    ("EV_p1167_01", "F-ACT", "F-ACT-01",
     "平清盛が日宋貿易の利益を独占し、娘徳子を高倉天皇に入内させ外戚化を果たした"),
    ("EV_p1392_01", "F-ACT", "F-ACT-01",
     "南朝の後亀山天皇が三種の神器を北朝に譲渡し、義満の仲介で和議が成立した"),
    ("EV_p1576_01", "F-ACT", "F-ACT-01",
     "織田信長が天下統一の拠点として琵琶湖東岸の安土に築城を決断した"),
    ("EV_p1586_01", "F-ACT", "F-ACT-01",
     "九州・四国の大名が相次いで秀吉に臣従し、関白から太政大臣への昇進が実現した"),
    ("EV_p1589_01", "F-ACT", "F-ACT-01",
     "北条氏直が秀吉の上洛要求を拒否し、秀吉が二十万の大軍で小田原を包囲した"),
    ("EV_p1605_01", "F-ACT", "F-ACT-01",
     "家康が嫡子秀忠に将軍職を譲り、徳川家による世襲の前例を作った"),
    ("EV_p1635_01", "F-ACT", "F-ACT-01",
     "三代将軍家光が武家諸法度を改訂し、参勤交代を全大名への義務として明文化した"),
    ("EV_p1641_01", "F-ACT", "F-ACT-01",
     "ポルトガル人退去で空いた出島にオランダ商館を平戸から強制移転させた"),
    ("EV_p1688_01", "F-ACT", "F-ACT-01",
     "出版技術の普及と貸本屋の拡大により、文芸作品が町人層に大量に流通し始めた"),
    ("EV_p1964_01", "F-ACT", "F-ACT-01",
     "IOCが東京をオリンピック開催都市に選定し、国家的インフラ整備が加速した"),

    # --- F-ACT-02: 死去・崩御 ---
    ("EV_p1192_01", "F-ACT", "F-ACT-02",
     "後白河法皇が崩御し、頼朝の征夷大将軍任命を阻む最大の障害が消えた"),

    # --- F-CNF-01: 勢力間対立 ---
    ("EV_p1336_03", "F-CNF", "F-CNF-01",
     "中先代の乱鎮圧を機に足利尊氏が後醍醐天皇の帰京命令を無視し独自行動に出た"),
    ("EV_p1351_01", "F-CNF", "F-CNF-01",
     "足利直義が高師直との対立に敗れ南朝に降り、幕府が二分された"),
    ("EV_p1866_01", "F-CNF", "F-CNF-01",
     "第二次長州征討で幕府軍が長州藩に敗北し、幕府の軍事的権威が決定的に崩壊した"),

    # --- F-EXT-01: 対外圧力 ---
    ("EV_p1281_01", "F-EXT", "F-EXT-01",
     "元・高麗・旧南宋の連合軍約十四万が二方面から博多湾に再襲来した"),
    ("EV_p1853_02", "F-EXT", "F-EXT-01",
     "ペリー来航で黒船の圧倒的軍事力を目撃し、海防の脆弱性が衝撃的に露呈した"),
    ("EV_p1862_01", "F-EXT", "F-EXT-01",
     "東海道を通行中のイギリス人が島津久光の行列に遭遇し、薩摩藩士が斬殺した"),

    # --- F-CTD-01: 制度機能不全 ---
    ("EV_p0794_01", "F-CTD", "F-CTD-01",
     "長岡京で藤原種継暗殺と早良親王の怨霊騒ぎが続き、遷都がやむなしとなった"),

    # --- F-UNC-02: 災害発生 ---
    ("EV_p1923_01", "F-UNC", "F-UNC-02",
     "1923年9月1日正午、相模湾北部を震源とするM7.9の大地震が発生した"),
    ("EV_p1995_01", "F-UNC", "F-UNC-02",
     "1995年1月17日未明、淡路島北部を震源とするM7.3の直下型地震が発生した"),
    ("EV_p2011_01", "F-UNC", "F-UNC-02",
     "2011年3月11日、三陸沖を震源とするM9.0の巨大地震と大津波が発生した"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    fix_lookup = {eid: (cat, sub, label) for eid, cat, sub, label in FIXES}

    updated = 0
    not_found = []

    for fv in data["frameworkViews"]:
        eid = fv["eventId"]
        if eid not in fix_lookup:
            continue

        cat, sub, label = fix_lookup[eid]
        found = False

        for elem in fv.get("elements", []):
            if elem.get("layer") == "F" and elem.get("subCategory") == "F-UNC-00":
                elem["category"] = cat
                elem["subCategory"] = sub
                elem["label"] = label
                updated += 1
                found = True
                break

        if not found:
            not_found.append(eid)

    # 保存
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== v3.5 F-UNC-00 残存27件 分類・個別化 ===")
    print(f"更新対象: {len(FIXES)}件")
    print(f"更新成功: {updated}件")
    print(f"未発見: {len(not_found)}件")
    if not_found:
        print(f"  未発見ID: {not_found}")

    # 統計
    from collections import Counter
    cat_counts = Counter()
    unc00_remaining = 0
    for fv in data["frameworkViews"]:
        for el in fv.get("elements", []):
            if el.get("layer") == "F":
                cat_counts[el.get("subCategory", "?")] += 1
                if el.get("subCategory") == "F-UNC-00":
                    unc00_remaining += 1

    print(f"\nF-UNC-00 残存: {unc00_remaining}件")
    print(f"\n--- Fカテゴリ分布 ---")
    for sub, count in sorted(cat_counts.items()):
        print(f"  {sub}: {count}")

    print(f"\n>>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
