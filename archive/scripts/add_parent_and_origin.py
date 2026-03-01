#!/usr/bin/env python3
"""
v3.5 parentFramework + origin 追加スクリプト

実行ユニット候補にparentFrameworkを追加し、
明確なE→B帰属がある要素にoriginを追加する。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# 実行ユニット: eventId → 親eventId
EXECUTION_UNITS = {
    "EV_p0694_01": "EV_p0672_01",  # 藤原京遷都 → 壬申の乱/天武朝
    "EV_p0708_01": "EV_p0701_01",  # 和同開珎 → 大宝律令
    "EV_p0710_01": "EV_p0701_01",  # 平城京遷都 → 大宝律令
    "EV_p0712_01": "EV_p0701_01",  # 古事記 → 大宝律令
    "EV_p0720_01": "EV_p0701_01",  # 日本書紀 → 大宝律令
    "EV_p0752_01": "EV_p0741_01",  # 東大寺大仏 → 国分寺建立の詔
    "EV_p0647_01": "EV_p0645_01",  # 租庸調 → 大化改新
    "EV_p1720_01": "EV_p1716_01",  # 洋書輸入緩和 → 享保の改革
    "EV_p1889_01": "EV_p1881_01",  # 帝国憲法発布 → 憲法発布決定
}
# EV_p0967_01（延喜式）と EV_p1685_01（生類憐み）は親が221件に不在のため除外

# origin追加: (eventId, elementIdの部分文字列, sourceEventId)
# B要素が明確に前のイベントのEに由来する場合
ORIGINS = [
    # 租庸調: B「大化改新により租庸調が制度化され」← 大化改新のE
    ("EV_p0647_01", "EL_EV_p0647_01_1", "EV_p0645_01"),
    # 兵役・防人: B「国防のため成年男子に兵役義務が課され」← 大化改新のE
    ("EV_p0648_01", "EL_EV_p0648_01_1", "EV_p0645_01"),
    # 飛鳥浄御原令: B「天武天皇が着手した律令編纂を持統天皇が継承」← 壬申の乱/天武のE
    ("EV_p0689_01", "EL_EV_p0689_01_1", "EV_p0672_01"),
    # 大宝律令: B「飛鳥浄御原令では律が欠けており」← 飛鳥浄御原令のE
    ("EV_p0701_01", "EL_EV_p0701_01_1", "EV_p0689_01"),
    # 平城京: B「藤原京が手狭になり」← 藤原京遷都のE
    ("EV_p0710_01", "EL_EV_p0710_01_1", "EV_p0694_01"),
    # 大日本帝国憲法発布: B「伊藤博文がヨーロッパで憲法調査を行い」← 憲法発布決定のE
    ("EV_p1889_01", "EL_EV_p1889_01_1", "EV_p1881_01"),
    # 日本国憲法施行: B「前年に公布された新憲法の施行準備」← 公布のE
    ("EV_p1947_01", "EL_EV_p1947_01_1", "EV_p1946_01"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build element lookup for origins
    origin_lookup = {}
    for event_id, elem_id, source_id in ORIGINS:
        origin_lookup[(event_id, elem_id)] = source_id

    parent_count = 0
    origin_count = 0

    for fv in data["frameworkViews"]:
        eid = fv["eventId"]

        # Add parentFramework
        if eid in EXECUTION_UNITS:
            fv["parentFramework"] = {
                "eventId": EXECUTION_UNITS[eid],
                "relationship": "execution_unit"
            }
            parent_count += 1
        elif "parentFramework" not in fv:
            fv["parentFramework"] = None

        # Add origin to B elements
        for elem in fv.get("elements", []):
            if elem["layer"] != "B":
                continue
            key = (eid, elem["elementId"])
            if key in origin_lookup:
                elem["origin"] = {
                    "sourceEventId": origin_lookup[key],
                    "sourceLayer": "E"
                }
                origin_count += 1

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== v3.5 parentFramework + origin 追加 ===")
    print(f"parentFramework 追加: {parent_count}件")
    print(f"origin 追加: {origin_count}件")
    print(f">>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
