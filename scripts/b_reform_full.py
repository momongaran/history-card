#!/usr/bin/env python3
"""
v3.6 B記述改革（全体展開）— 失敗学原則の適用

原則:
1. Bには「その時点で当事者が観察しえた事実」だけを書く
2. 後知恵的な診断を排除する
3. Fと重複するB要素は削除する（B要素数を可変に）
4. イベント内容そのものであるB要素は削除する

パイロット10件は済み。残り65件を処理。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# === 削除対象 ===
# パイロットで処理済みの8件を除く
# F完全一致の17件 + バッチ分析で追加された削除対象
DELETE_ELEMENTS = [
    # --- F完全一致（元のリストの17件） ---
    ("EV_p1016_02", "EL_EV_p1016_02_3"),
    ("EV_p1086_01", "EL_EV_p1086_01_3"),
    ("EV_p1086_02", "EL_EV_p1086_02_3"),
    ("EV_p1183_01", "EL_EV_p1183_01_3"),
    ("EV_p1184_01", "EL_EV_p1184_01_3"),
    ("EV_p1185_02", "EL_EV_p1185_02_3"),
    ("EV_p1338_01", "EL_EV_p1338_01_3"),
    ("EV_p1404_01", "EL_EV_p1404_01_3"),
    ("EV_p1571_01", "EL_EV_p1571_01_3"),
    ("EV_p1585_01", "EL_EV_p1585_01_3"),
    ("EV_p1590_01", "EL_EV_p1590_01_3"),
    ("EV_p1614_01", "EL_EV_p1614_01_3"),
    ("EV_p1772_01", "EL_EV_p1772_01_3"),
    ("EV_p1792_01", "EL_EV_p1792_01_3"),
    ("EV_p1839_01", "EL_EV_p1839_01_3"),
    ("EV_p1871_01", "EL_EV_p1871_01_3"),
    ("EV_p1972_01", "EL_EV_p1972_01_3"),

    # --- Batch 1 追加削除 ---
    ("EV_p0694_01", "EL_EV_p0694_01_3"),  # 藤原京: 造営されていた = イベント
    ("EV_p0752_01", "EL_EV_p0752_01_3"),  # 大仏: 動員されていた = イベント過程
    ("EV_p0858_01", "EL_EV_p0858_01_3"),  # 良房: 就任していた = イベント
    ("EV_p0901_01", "EL_EV_p0901_01_3"),  # 道真: 左遷され没した = イベント結果
    ("EV_p0905_01", "EL_EV_p0905_01_2"),  # 古今: 勅命により編纂 = イベント
    ("EV_p1016_01", "EL_EV_p1016_01_3"),  # 道長摂政: 就任していた = イベント
    ("EV_p1159_01", "EL_EV_p1159_01_2"),  # 平治: 院御所を襲撃 = イベント行動
    ("EV_p1177_01", "EL_EV_p1177_01_3"),  # 鹿ケ谷: 発覚し処罰 = イベント結果
    ("EV_p1185_03", "EL_EV_p1185_03_3"),  # 守護地頭: 任命権を獲得 = イベント
    ("EV_p1205_01", "EL_EV_p1205_01_3"),  # 時政失脚: 陰謀露見 = イベント結果
    ("EV_p1221_01", "EL_EV_p1221_01_2"),  # 承久: 院宣を発した = F
    ("EV_p1247_01", "EL_EV_p1247_01_3"),  # 宝治: 自害し断絶 = イベント結果
    ("EV_p1274_01", "EL_EV_p1274_01_3"),  # 文永: 上陸していた = イベント
    ("EV_p1281_01", "EL_EV_p1281_01_2"),  # 弘安: 侵攻していた = イベント

    # --- Batch 2 追加削除 ---
    ("EV_p1336_01", "EL_EV_p1336_01_3"),  # 南北朝: 北朝成立 = イベント
    ("EV_p1336_02", "EL_EV_p1336_02_3"),  # 室町幕府: 建武式目制定 = イベント
    ("EV_p1493_01", "EL_EV_p1493_01_3"),  # 明応: 義澄擁立 = F
    ("EV_p1549_01", "EL_EV_p1549_01_3"),  # ザビエル: 上陸・布教 = F
    ("EV_p1560_01", "EL_EV_p1560_01_3"),  # 桶狭間: 奇襲 = イベント
    ("EV_p1568_01", "EL_EV_p1568_01_3"),  # 信長上洛: 三好排除 = F
    ("EV_p1573_01", "EL_EV_p1573_01_3"),  # 室町滅亡: 追放 = イベント
    ("EV_p1587_02", "EL_EV_p1587_02_3"),  # 太政大臣: 島津降伏 = F
    ("EV_p1590_02", "EL_EV_p1590_02_3"),  # 小田原: 軍勢集結 = イベント
    ("EV_p1591_01", "EL_EV_p1591_01_2"),  # 身分統制: 必要であった = 後知恵
    ("EV_p1615_02", "EL_EV_p1615_02_3"),  # 夏の陣: 幸村戦死 = イベント
    ("EV_p1637_01", "EL_EV_p1637_01_3"),  # 島原: 蜂起していた = イベント
    ("EV_p1720_01", "EL_EV_p1720_01_3"),  # 洋書: 有用と判断 = F
    ("EV_p1858_01", "EL_EV_p1858_01_3"),  # 大獄: 弾圧決断 = F
    ("EV_p1873_01", "EL_EV_p1873_01_2"),  # 地租改正: 必要であった = 後知恵
    ("EV_p1914_01", "EL_EV_p1914_01_3"),  # 一次大戦: 占領していた = イベント
    ("EV_p1945_01", "EL_EV_p1945_01_3"),  # GHQ: 方針示された = イベント
]

# === 書き換え対象 ===
REWRITES = [
    # --- Batch 1 ---
    ("EV_p0593_02", "EL_EV_p0593_02_2",
     "推古天皇即位時、蘇我馬子は大臣として朝廷内で最大の軍事・経済基盤を有していた"),

    ("EV_p0607_01", "EL_EV_p0607_01_2",
     "倭国では冠位十二階・十七条憲法など国内制度の整備が進められており、隋は南北朝を統一した大陸最大の統一王朝として存在していた"),

    ("EV_p0701_01", "EL_EV_p0701_01_1",
     "飛鳥浄御原令（689年）は令のみで構成され、律（刑罰規定）に相当する法典は別途存在していなかった"),

    ("EV_p0743_01", "EL_EV_p0743_01_3",
     "三世一身法（723年）では開墾田は三世または一身の後に国へ返還されることが定められていた"),

    ("EV_p1051_01", "EL_EV_p1051_01_2",
     "源頼義は1051年に陸奥守として現地に赴任しており、安倍氏は奥六郡を支配して朝廷への貢納を滞らせていた"),

    ("EV_p1096_01", "EL_EV_p1096_01_1",
     "11世紀後半を通じて荘園の増加が続き、国衙が把握する公領の田地面積と実際の耕地との間に乖離が生じていた"),

    ("EV_p1185_02", "EL_EV_p1185_02_1",
     "1185年時点で源義経は頼朝の追討令を受けて逃亡中であり、頼朝は西国の武士を直接掌握する機構を持っていなかった"),

    ("EV_p1185_03", "EL_EV_p1185_03_2",
     "源義経は頼朝から追討を命じられたのち奥州へ向けて逃亡しており、鎌倉の人的ネットワークは東国に限定されていた"),

    ("EV_p1225_01", "EL_EV_p1225_01_2",
     "承久の乱（1221年）の後、幕府は没収した京方武士の所領を御家人に再分配し、西国にも新たに地頭を補任していた"),

    # --- Batch 2 ---
    ("EV_p1334_01", "EL_EV_p1334_01_3",
     "後醍醐天皇は即位後、天皇親政の回復を志向し、倒幕運動を二度試みていた"),

    ("EV_p1549_02", "EL_EV_p1549_02_3",
     "イエズス会はアジアにおいて布教と貿易を組み合わせた活動を展開しており、ポルトガル商船が東南アジア各地に寄港していた"),

    ("EV_p1555_01", "EL_EV_p1555_01_2",
     "毛利元就は陶晴賢への対抗上、石見銀山の確保や能島水軍など周辺勢力への工作を続けていた"),

    ("EV_p1576_01", "EL_EV_p1576_01_1",
     "織田信長は畿内平定後も各地に敵対勢力を抱えており、京と東国を結ぶ交通・兵站の要衝として近江が重要な位置にあった"),

    ("EV_p1639_01", "EL_EV_p1639_01_2",
     "ポルトガル船は貿易と布教を同一の船員・船舶で行っており、両者を分離した渡航の実例が存在していなかった"),

    ("EV_p1867_01", "EL_EV_p1867_01_3",
     "慶喜は将軍就任後も朝廷・諸藩との協調路線を模索しており、フランス支援による幕府強化策と並行して政治工作を続けていた"),

    ("EV_p1894_01", "EL_EV_p1894_01_2",
     "甲午農民戦争の鎮圧要請を受け、日清両国がほぼ同時期に朝鮮へ出兵し、双方の軍が朝鮮半島内に対峙していた"),

    ("EV_p1931_01", "EL_EV_p1931_01_3",
     "1920年代を通じて中国国民政府の権限拡大と鉄道回収運動が進み、満鉄沿線での日本の経済的・行政的優位が段階的に縮小していた"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build lookup
    elem_index = {}
    for fv in data["frameworkViews"]:
        for i, elem in enumerate(fv.get("elements", [])):
            elem_index[(fv["eventId"], elem.get("elementId"))] = (fv, elem, i)

    # === Delete ===
    deleted = 0
    delete_not_found = []
    for eid, elem_id in DELETE_ELEMENTS:
        key = (eid, elem_id)
        if key not in elem_index:
            delete_not_found.append(key)
            continue
        fv, elem, idx = elem_index[key]
        if elem in fv["elements"]:
            fv["elements"].remove(elem)
            deleted += 1

    # === Rewrite ===
    rewritten = 0
    rewrite_not_found = []
    for eid, elem_id, new_label in REWRITES:
        # Re-build index after deletions
        pass

    # Re-build index after deletions for rewrites
    elem_index2 = {}
    for fv in data["frameworkViews"]:
        for i, elem in enumerate(fv.get("elements", [])):
            elem_index2[(fv["eventId"], elem.get("elementId"))] = (fv, elem, i)

    for eid, elem_id, new_label in REWRITES:
        key = (eid, elem_id)
        if key not in elem_index2:
            rewrite_not_found.append(key)
            continue
        fv, elem, idx = elem_index2[key]
        elem["label"] = new_label
        rewritten += 1

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Stats
    b_count_dist = {}
    total_b = 0
    for fv in data["frameworkViews"]:
        n = sum(1 for el in fv.get("elements", []) if el["layer"] == "B")
        total_b += n
        b_count_dist[n] = b_count_dist.get(n, 0) + 1

    print(f"=== v3.6 B記述改革（全体展開） ===")
    print(f"削除: {deleted}/{len(DELETE_ELEMENTS)}件")
    print(f"書き換え: {rewritten}/{len(REWRITES)}件")
    if delete_not_found:
        print(f"削除未発見: {len(delete_not_found)}件")
        for k in delete_not_found:
            print(f"  {k}")
    if rewrite_not_found:
        print(f"書換未発見: {len(rewrite_not_found)}件")
        for k in rewrite_not_found:
            print(f"  {k}")

    print(f"\nB要素総数: {total_b}")
    print(f"B要素数分布:")
    for n in sorted(b_count_dist):
        print(f"  B={n}: {b_count_dist[n]}イベント")

    # Check remaining B-F overlaps
    from difflib import SequenceMatcher
    remaining_overlap = 0
    for fv in data["frameworkViews"]:
        f_labels = set(el.get("label","") for el in fv.get("elements",[]) if el["layer"]=="F")
        for el in fv.get("elements",[]):
            if el["layer"] == "B" and el.get("label","") in f_labels:
                remaining_overlap += 1

    print(f"\nB-F完全一致残存: {remaining_overlap}件")
    print(f"\n>>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
