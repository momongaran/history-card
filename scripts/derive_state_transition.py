#!/usr/bin/env python3
"""
derive_state_transition.py — G-3: 状態S₀/S₁の形式化

no11「イベント＝状態変換関数 e: S₀→S₁」に基づき、
既存データからイベント前後の状態を構造化して導出する。

S₀ (pre-state): イベント前の状態
  - activeBGs: そのイベント年時点で活性なBG（effectLogから推定）
  - tension: 背景が生む圧・歪み（background.label）
  - trigger: 発火条件（params[slotFunction=トリガー]）

S₁ (post-state): イベント後の状態
  - result: 帰結（causalFrame.result）
  - bgDelta: BGへの変化（eGenerates）
  - newActiveBGs: イベント後の活性BG
"""

import json
from collections import defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def build_bg_active_periods(data):
    """各BGの活性期間を構築（effectLogから）"""
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    active_periods = {}  # bgId → [(start, end)]

    for bg in data["backgroundElements"]:
        bid = bg["bgId"]
        log = bg.get("effectLog", [])
        if not log:
            # effectLogなし → generatedByから推定、またはphaseから
            phases = bg.get("phases", [])
            if phases:
                try:
                    start = int(phases[0]["period"].split("-")[0])
                    end_str = phases[-1]["period"].split("-")[-1]
                    end = int(end_str) if end_str else 9999
                    active_periods[bid] = [(start, end)]
                except (ValueError, IndexError):
                    active_periods[bid] = [(0, 9999)]
            else:
                active_periods[bid] = [(0, 9999)]
            continue

        # effectLogから活性期間を推定
        periods = []
        current_start = None
        for eff in sorted(log, key=lambda e: e["year"]):
            if eff["effect"] == "generate":
                current_start = eff["year"]
            elif eff["effect"] == "terminate":
                if current_start is not None:
                    periods.append((current_start, eff["year"]))
                    current_start = None
                else:
                    # generate無しでterminate → 最初から存在
                    periods.append((0, eff["year"]))
            elif current_start is None and eff["effect"] in ("reinforce", "erode", "redirect"):
                # generate無しで作用 → 最初から存在
                current_start = 0

        if current_start is not None:
            periods.append((current_start, 9999))

        if not periods:
            # ログはあるがperiod導出できず → 最初のログ年〜
            first_year = min(e["year"] for e in log)
            periods = [(first_year, 9999)]

        active_periods[bid] = periods

    return active_periods


def is_bg_active(bg_id, year, active_periods):
    """指定年にBGが活性か"""
    for start, end in active_periods.get(bg_id, []):
        if start <= year <= end:
            return True
    return False


def derive_states(data):
    """各イベントのS₀/S₁を導出"""
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    active_periods = build_bg_active_periods(data)
    all_bg_ids = set(bgs.keys())

    for ev in sorted(data["events"], key=lambda e: e["year"]):
        cf = ev["causalFrame"]
        year = ev["year"]

        # === S₀: イベント前の状態 ===
        # 活性BG
        active_before = sorted([
            bid for bid in all_bg_ids
            if is_bg_active(bid, year - 1, active_periods)
        ])

        # 直接関連するBG（backgroundのrefs）
        related_bgs = []
        for bg in cf.get("background", []):
            for ref in bg.get("refs", []):
                related_bgs.append({
                    "bgId": ref["bgId"],
                    "role": ref["role"],
                    "bname": bg["bname"],
                })

        # テンション（背景の圧）
        tension = cf["background"][0]["label"] if cf.get("background") else ""

        # トリガー
        triggers = [
            p["value"] for p in cf.get("params", [])
            if p.get("slotFunction") == "トリガー"
        ]

        s0 = {
            "activeBGs": active_before,
            "relatedBGs": related_bgs,
            "tension": tension,
            "triggers": triggers,
        }

        # === S₁: イベント後の状態 ===
        # BGへの変化
        bg_delta = []
        for eg in ev.get("eGenerates", []):
            bg_delta.append({
                "bgId": eg["targetBG"],
                "effect": eg["effect"],
            })

        # イベント後の活性BG
        active_after = set(active_before)
        for eg in ev.get("eGenerates", []):
            if eg["effect"] == "generate":
                active_after.add(eg["targetBG"])
            elif eg["effect"] == "terminate":
                active_after.discard(eg["targetBG"])

        s1 = {
            "result": cf["result"],
            "bgDelta": bg_delta,
            "activeBGs": sorted(active_after),
        }

        # イベントに付与
        ev["stateTransition"] = {"s0": s0, "s1": s1}

    return data


def main():
    data = load_data()
    data = derive_states(data)

    # 統計
    total_active = []
    total_delta = []
    total_triggers = []
    for ev in data["events"]:
        st = ev["stateTransition"]
        total_active.append(len(st["s0"]["activeBGs"]))
        total_delta.append(len(st["s1"]["bgDelta"]))
        total_triggers.append(len(st["s0"]["triggers"]))

    print("=== 状態遷移 S₀→S₁ 導出完了 ===")
    print(f"イベント数: {len(data['events'])}")
    print(f"\nS₀.activeBGs: avg={sum(total_active)/len(total_active):.1f}, "
          f"min={min(total_active)}, max={max(total_active)}")
    print(f"S₀.triggers: avg={sum(total_triggers)/len(total_triggers):.1f}")
    print(f"S₁.bgDelta: avg={sum(total_delta)/len(total_delta):.1f}, "
          f"min={min(total_delta)}, max={max(total_delta)}")

    # activeBGs数の変化（generate/terminate）
    gen_count = sum(
        1 for ev in data["events"]
        for eg in ev.get("eGenerates", [])
        if eg["effect"] == "generate"
    )
    term_count = sum(
        1 for ev in data["events"]
        for eg in ev.get("eGenerates", [])
        if eg["effect"] == "terminate"
    )
    print(f"\ngenerate総数: {gen_count}, terminate総数: {term_count}")

    # サンプル出力
    samples = ["EV_p0507_01", "EV_p0645_02", "EV_p1600_01", "EV_p1868_01"]
    for eid in samples:
        ev = next((e for e in data["events"] if e["eventId"] == eid), None)
        if not ev:
            continue
        st = ev["stateTransition"]
        print(f"\n--- {eid} ({ev['year']}) {ev['title'][:30]} ---")
        print(f"  S₀: activeBGs={len(st['s0']['activeBGs'])}, "
              f"related={len(st['s0']['relatedBGs'])}, "
              f"triggers={len(st['s0']['triggers'])}")
        print(f"  S₁: delta={len(st['s1']['bgDelta'])}, "
              f"activeBGs={len(st['s1']['activeBGs'])}")
        if st["s0"]["triggers"]:
            print(f"  trigger: {st['s0']['triggers'][0][:50]}")
        print(f"  result: {st['s1']['result']['label'][:50]}")

    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
