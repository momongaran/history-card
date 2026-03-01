#!/usr/bin/env python3
"""
v3.7c B要素の逆算表現修正

原則: 「ないことは原因として作用しない」
     結果を知っているから書ける「不在」「欠如」「持っていなかった」を排除し、
     当時観察可能な事実に書き換える。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

REWRITES = [
    # 仏教伝来 — 「普遍的イデオロギーが不在であり…脆弱」→ 当時の観察事実
    ("EV_p0538_01", "EL_EV_p0538_01_3",
     "ヤマト政権内の氏族間序列は血統と軍事力に基づいており、各氏族がそれぞれの氏神を祀って独自の権威を主張していた"),

    # 推古天皇即位 — 「男性皇位候補が不在または馬子にとって不都合」→ 事実に
    ("EV_p0593_01", "EL_EV_p0593_01_8",
     "崇峻暗殺後、皇位継承の有力候補は限られ、蘇我馬子と血縁のある皇族が選択肢となった"),

    # 厩戸王摂政 — 「統治経験が不足していた」→ 事実に
    ("EV_p0593_02", "EL_EV_p0593_02_1",
     "推古天皇は即位時三十九歳で、蘇我氏の血を引く皇女として馬子との協調が求められていた"),

    # 遣唐使 — 「知識基盤の根本的欠如が改革を空論にしかねなかった」→ 事実に
    ("EV_p0630_01", "EL_EV_p0630_01_3",
     "大化改新後の律令制度導入にあたり、唐の官制・法制を直接学んだ人材が朝廷内にごく少数であった"),

    # 日本書紀 — 「正史がなく…証明できない」→ 事実に
    ("EV_p0720_01", "EL_EV_p0720_01_3",
     "唐・新羅は自国の正史を編纂済みであり、倭国は外交の場で漢文による国家の歴史書を提示する慣行に直面していた"),

    # 藤原道長摂政(2) — 「対抗勢力が存在しなかっていた」→ typo修正+事実に
    ("EV_p1016_02", "EL_EV_p1016_02_2",
     "藤原氏以外の有力貴族が相次いで政界から退き、朝廷の要職を藤原氏一族が独占していた"),

    # 守護地頭設置 — 「西国の武士を直接掌握する機構を持っていなかった」→ 事実に
    ("EV_p1185_02", "EL_EV_p1185_02_1",
     "1185年時点で源義経は頼朝の追討令を受けて逃亡中であり、西国各地の武士は在地の荘園領主や国衙に帰属したままであった"),

    # 花の御所 — 「恒久的な政権中枢の不在が…妨げていた」→ 事実に
    ("EV_p1378_01", "EL_EV_p1378_01_3",
     "室町幕府は発足以来、将軍の御所が転々と移り、政庁としての拠点が京都内で数度変遷していた"),

    # 大津浜事件 — 「制度的枠組みが存在しなかった」→ 事実に
    ("EV_p1824_01", "EL_EV_p1824_01_2",
     "イギリス捕鯨船の乗組員が常陸大津浜に上陸して食料・水を要求し、沿岸住民と藩役人が対応に混乱した"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    elem_index = {}
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            elem_index[(fv["eventId"], elem.get("elementId"))] = elem

    rewritten = 0
    not_found = []
    for eid, elem_id, new_label in REWRITES:
        key = (eid, elem_id)
        if key not in elem_index:
            not_found.append(key)
            continue
        elem_index[key]["label"] = new_label
        rewritten += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== v3.7c B逆算表現修正 ===")
    print(f"書き換え: {rewritten}/{len(REWRITES)}件")
    if not_found:
        print(f"未発見: {not_found}")

    # Verify: check for remaining hindsight expressions in B
    import re
    hindsight = re.compile(r'(イデオロギーが不在|の不在|根本的欠如|存在しなかっ|持っていなかった)')
    remaining = 0
    for fv in data["frameworkViews"]:
        for el in fv.get("elements", []):
            if el["layer"] == "B" and hindsight.search(el["label"]):
                remaining += 1
                print(f"  残存: {fv['eventId']} | {el['label'][:50]}")

    print(f"強い逆算表現の残存: {remaining}件")
    print(f">>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
