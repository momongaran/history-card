#!/usr/bin/env python3
"""
assign_events_to_pfw.py — 既存207イベントを親FWに割り当て

年代ベースの自動割り当て + 内容ベースの微調整。
結果は parent_fw_master.json の eventRefs と
framework_output_v3_9.json の各イベントに parentFWRef を追加。
"""

import json
from collections import Counter, defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        events_data = json.load(f)
    with open("data/parent_fw_master.json", "r") as f:
        pfw_data = json.load(f)
    return events_data, pfw_data


# 年代ベースの割り当てルール
# 各親FWのperiodに基づいて割り当て
# 重複する時期は内容で微調整
def assign_by_year_and_content(ev, pfws):
    """イベントを最適な親FWに割り当て"""
    year = ev["year"]
    cf = ev["causalFrame"]
    fname = cf.get("fname", "")
    pattern = cf.get("fnamePattern", "")
    category = cf.get("fnameCategory", "")
    title = ev.get("title", "")

    # 年代で候補を絞る
    candidates = []
    for pfw in pfws:
        p = pfw["period"]
        if p["start"] <= year <= p["end"]:
            candidates.append(pfw)
        # 境界付近は両方候補にする（±10年）
        elif abs(year - p["start"]) <= 10 or abs(year - p["end"]) <= 10:
            candidates.append(pfw)

    if not candidates:
        # 範囲外 → 最も近い親FWを選択
        candidates = sorted(pfws, key=lambda p: min(
            abs(year - p["period"]["start"]),
            abs(year - p["period"]["end"])
        ))[:1]

    if len(candidates) == 1:
        return candidates[0]["id"]

    # 複数候補がある場合 → 内容で判定
    # 年代が中央に近い方を優先
    best = None
    best_score = -1
    for pfw in candidates:
        p = pfw["period"]
        mid = (p["start"] + p["end"]) / 2
        span = max(p["end"] - p["start"], 1)
        # 中央に近いほどスコアが高い
        score = 1.0 - abs(year - mid) / span

        # 内容マッチボーナス
        summary = pfw.get("summary", "")
        parts_text = " ".join(
            part.get("summary", "")
            for part in pfw.get("parts", {}).values()
        )
        context = summary + " " + parts_text

        # キーワードマッチ
        keywords = title + " " + fname + " " + pattern
        for word in ["律令", "遷都", "貴族", "摂関", "武家", "幕府",
                     "戦国", "統一", "鎖国", "開国", "明治", "戦争",
                     "改革", "占領", "経済"]:
            if word in keywords and word in context:
                score += 0.3

        if score > best_score:
            best_score = score
            best = pfw["id"]

    return best


def assign_part(ev, pfw):
    """イベントを親FWの A/B/C/D パートに割り当て"""
    year = ev["year"]
    p = pfw["period"]
    span = max(p["end"] - p["start"], 1)
    position = (year - p["start"]) / span

    # 時間的位置で大まかに A/B/C/D を推定
    if position < 0.2:
        return "A"
    elif position < 0.4:
        return "B"
    elif position < 0.75:
        return "C"
    else:
        return "D"


def main():
    events_data, pfw_data = load_data()
    pfws = pfw_data["parentFW"]

    # 割り当て実行
    assignments = {}  # eventId → pfwId
    part_assignments = {}  # eventId → part
    pfw_events = defaultdict(list)  # pfwId → [eventId]

    for ev in events_data["events"]:
        pfw_id = assign_by_year_and_content(ev, pfws)
        pfw = next(p for p in pfws if p["id"] == pfw_id)
        part = assign_part(ev, pfw)

        assignments[ev["eventId"]] = pfw_id
        part_assignments[ev["eventId"]] = part
        pfw_events[pfw_id].append(ev["eventId"])

    # 統計
    print("=== 親FW割り当て結果 ===\n")
    for pfw in pfws:
        evs = pfw_events.get(pfw["id"], [])
        print(f"{pfw['id']} {pfw['name']}: {len(evs)}件")
        # パート別
        parts = Counter(part_assignments[eid] for eid in evs)
        for part_name in ["A", "B", "C", "D"]:
            print(f"  {part_name}: {parts.get(part_name, 0)}件")

    print(f"\n合計: {sum(len(v) for v in pfw_events.values())}件")

    # イベントデータに parentFWRef を追加
    for ev in events_data["events"]:
        ev["parentFWRef"] = assignments[ev["eventId"]]
        ev["parentFWPart"] = part_assignments[ev["eventId"]]

    # 親FWマスタに eventRefs を追加
    for pfw in pfws:
        pfw["eventRefs"] = pfw_events.get(pfw["id"], [])

    # 書き出し
    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)
    print("\n書き込み完了: data/framework_output_v3_9.json")

    with open("data/parent_fw_master.json", "w") as f:
        json.dump(pfw_data, f, ensure_ascii=False, indent=2)
    print("書き込み完了: data/parent_fw_master.json")


if __name__ == "__main__":
    main()
