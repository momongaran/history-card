#!/usr/bin/env python3
"""
v3.5 origin拡張スクリプト

明確なE→B帰属（前イベントのEが後イベントのBの条件となっている）を
originフィールドで記録する。

既存7件に加え、キーワードマッチで特定した候補から
帰属関係が明確なものを追加。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# (eventId, elementId, sourceEventId)
# 既存の7件は除外（すでにoriginあり）
NEW_ORIGINS = [
    # 八色の姓: B「壬申の乱の功臣と旧来の豪族の序列を再整理」← 壬申の乱のE
    ("EV_p0684_01", "EL_EV_p0684_01_2", "EV_p0672_01"),
    # 墾田永年私財法: B「三世一身法では開墾意欲の喚起に不十分」← 三世一身法のE
    ("EV_p0743_01", "EL_EV_p0743_01_1", "EV_p0723_01"),
    # 平治の乱: B「保元の乱後の恩賞配分をめぐり…」← 保元の乱のE
    ("EV_p1159_01", "EL_EV_p1159_01_1", "EV_p1156_01"),
    # 平清盛: B「保元・平治の乱で武功を立てた平清盛が急速に昇進」← 平治の乱のE
    ("EV_p1167_01", "EL_EV_p1167_01_1", "EV_p1159_01"),
    # 北条泰時・評定衆: B「承久の乱後に幕府の支配権が西国にも拡大」← 承久の乱のE
    ("EV_p1225_01", "EL_EV_p1225_01_2", "EV_p1221_01"),
    # 御成敗式目: B「承久の乱後に西国の所領争いが増加」← 承久の乱のE
    ("EV_p1232_01", "EL_EV_p1232_01_2", "EV_p1221_01"),
    # 永仁の徳政令: B「元寇後の恩賞不足と貨幣経済の浸透で御家人が困窮」← 元寇のE
    ("EV_p1297_01", "EL_EV_p1297_01_1", "EV_p1274_01"),
    # 室町幕府: B「建武の新政の恩賞配分が公家偏重」← 建武の新政のE
    ("EV_p1336_02", "EL_EV_p1336_02_1", "EV_p1336_01"),
    # 尊氏離反: B「建武の新政の恩賞配分が公家偏重で武士の不満」← 建武の新政のE
    ("EV_p1336_03", "EL_EV_p1336_03_1", "EV_p1336_01"),
    # 山崎の戦い: B「本能寺の変で織田信長が横死し権力の空白」← 本能寺の変のE
    ("EV_p1582_01", "EL_EV_p1582_01_1", "EV_p1582_02"),
    # 江戸幕府開設: B「関ヶ原の戦いで勝利し…」← 関ヶ原のE
    ("EV_p1603_01", "EL_EV_p1603_01_1", "EV_p1600_01"),
    # 武家諸法度: B「大坂の陣終結後に大名統制の法的枠組みが必要」← 大坂の陣のE
    ("EV_p1615_03", "EL_EV_p1615_03_1", "EV_p1615_01"),
    # 鎖国完成: B「島原の乱でキリスト教の脅威が再認識」← 島原の乱のE
    ("EV_p1639_01", "EL_EV_p1639_01_1", "EV_p1637_01"),
    # 鎖国強化: B「島原の乱を契機にキリスト教の根絶が最優先課題」← 島原の乱のE
    ("EV_p1639_02", "EL_EV_p1639_02_1", "EV_p1637_01"),
    # 寛政の改革: B「天明の飢饉と田沼政治の弊害で社会不安」← 田沼のE
    ("EV_p1787_01", "EL_EV_p1787_01_1", "EV_p1772_01"),
    # 松平定信: B「田沼意次の失脚後に改革派として老中に登用」← 田沼のE
    ("EV_p1787_02", "EL_EV_p1787_02_3", "EV_p1772_01"),
    # 日米和親条約: B「ペリーが翌年に7隻の艦隊を率いて再来航」← ペリー来航のE
    ("EV_p1854_01", "EL_EV_p1854_01_1", "EV_p1853_01"),
    # 桜田門外の変: B「安政の大獄による弾圧が尊攘派の憎悪を増大」← 安政の大獄のE
    ("EV_p1860_01", "EL_EV_p1860_01_1", "EV_p1858_01"),
    # 薩英戦争: B「生麦事件の賠償をめぐり薩摩藩とイギリスが対立」← 生麦事件のE
    ("EV_p1863_01", "EL_EV_p1863_01_1", "EV_p1862_01"),
    # 王政復古: B「大政奉還後も徳川家の政治的影響力が残存」← 大政奉還のE
    ("EV_p1867_02", "EL_EV_p1867_02_1", "EV_p1867_01"),
    # 韓国併合: B「日露戦争後に日本が韓国の外交権を奪い保護国化」← 日露戦争のE
    ("EV_p1910_01", "EL_EV_p1910_01_1", "EV_p1904_01"),
    # 治安維持法: B「普通選挙法の成立で社会主義勢力の議会進出が懸念」← 普通選挙法のE
    ("EV_p1925_02", "EL_EV_p1925_02_1", "EV_p1925_01"),
]

# 除外（帰属ではなく単なる言及/時系列参照のもの）:
# - EV_p1605_01 (関ヶ原に遅参) → 参照だが帰属とは言えない
# - EV_p1720_01 (鎖国下で洋書輸入) → 鎖国は制度的前提で帰属的進化ではない
# - EV_p1732_01 (享保の改革下で飢饉) → 改革のEが飢饉のBとは言えない
# - EV_p1782_01 (田沼期に飢饉) → 田沼のEが飢饉のBとは言えない
# - EV_p1792_01 (鎖国下でラクスマン来航) → 鎖国は制度的前提
# - EV_p1825_01 (鎖国体制の維持) → 制度的前提
# - EV_p1841_02 (寛政の改革に倣い) → 参考程度
# - EV_p1853_02 (黒船の圧倒的軍事力) → 同一イベントの別視点
# - EV_p1854_01 B3(鎖国維持は不可能) → 制度的前提
# - EV_p1945_02 (ポツダム宣言) → 異なるイベント構造


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build element lookup
    elem_lookup = {}
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            elem_lookup[(fv["eventId"], elem.get("elementId"))] = elem

    added = 0
    skipped = 0
    not_found = []

    for eid, elem_id, source_eid in NEW_ORIGINS:
        key = (eid, elem_id)
        if key not in elem_lookup:
            not_found.append((eid, elem_id))
            continue

        elem = elem_lookup[key]
        if elem.get("origin"):
            skipped += 1
            continue

        elem["origin"] = {
            "sourceEventId": source_eid,
            "sourceLayer": "E"
        }
        added += 1

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Count total origins
    total_origins = 0
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            if elem.get("origin"):
                total_origins += 1

    print(f"=== v3.5 origin拡張 ===")
    print(f"追加対象: {len(NEW_ORIGINS)}件")
    print(f"追加成功: {added}件")
    print(f"既存スキップ: {skipped}件")
    print(f"未発見: {len(not_found)}件")
    if not_found:
        for eid, elem_id in not_found:
            print(f"  {eid} / {elem_id}")
    print(f"\norigin総数: {total_origins}件 (既存7 + 新規{added})")
    print(f">>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
