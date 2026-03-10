#!/usr/bin/env python3
"""
fix_egenerates.py — A-2: eGenerates品質修正

検出された問題:
1. terminate年が早すぎる（BG_001, BG_006, BG_015, BG_079）
2. terminate後の誤った作用（BG_024の後北条≠鎌倉北条）
3. 二重generate（最初のgenerate以降はreinforceに変更）
4. effectLogとの不整合（effectLog側の10件をeGeneratesに追加）
"""

import json
from collections import defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def fix_terminate_timing(data):
    """terminate年が早すぎるケースを修正"""
    fixes = []
    events = {ev["eventId"]: ev for ev in data["events"]}

    # BG_001 (織田政権): 1573 terminate→reinforce, 1576 generate→reinforce
    # 実際のterminateは1582(本能寺の変)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            # 1573: terminate → reinforce (室町幕府滅亡は織田政権強化)
            if ev["eventId"] == "EV_p1573_01" and eg["targetBG"] == "BG_001" and eg["effect"] == "terminate":
                eg["effect"] = "reinforce"
                fixes.append(f"BG_001: EV_p1573_01 terminate→reinforce (室町幕府滅亡は織田政権終了ではない)")

            # 1576: generate → reinforce (安土城は再生成ではなく強化)
            if ev["eventId"] == "EV_p1576_01" and eg["targetBG"] == "BG_001" and eg["effect"] == "generate":
                eg["effect"] = "reinforce"
                fixes.append(f"BG_001: EV_p1576_01 generate→reinforce (安土城は再生成ではなく強化)")

            # 1582 (本能寺の変の影響): redirect → terminate
            if ev["eventId"] == "EV_p1582_02" and eg["targetBG"] == "BG_001" and eg["effect"] == "redirect":
                eg["effect"] = "terminate"
                fixes.append(f"BG_001: EV_p1582_02 redirect→terminate (本能寺の変で織田政権終了)")

    # BG_001: 1583, 1584の作用を削除（織田政権は1582で終了）
    for ev in data["events"]:
        if ev["eventId"] in ("EV_p1583_01", "EV_p1584_01"):
            before = len(ev["eGenerates"])
            ev["eGenerates"] = [eg for eg in ev["eGenerates"] if eg["targetBG"] != "BG_001"]
            if len(ev["eGenerates"]) < before:
                fixes.append(f"BG_001: {ev['eventId']} の BG_001 への作用を削除 (織田政権終了後)")

    # BG_006 (徳川家): 1615 terminate → redirect (大坂夏の陣は徳川家終了ではない)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            if ev["eventId"] == "EV_p1615_02" and eg["targetBG"] == "BG_006" and eg["effect"] == "terminate":
                eg["effect"] = "redirect"
                fixes.append(f"BG_006: EV_p1615_02 terminate→redirect (徳川家は大坂の陣後も継続)")

    # BG_006: 1716 generate → reinforce (享保の改革は再生成ではなく強化)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            if ev["eventId"] == "EV_p1716_02" and eg["targetBG"] == "BG_006" and eg["effect"] == "generate":
                eg["effect"] = "reinforce"
                fixes.append(f"BG_006: EV_p1716_02 generate→reinforce (享保の改革は徳川家強化)")

    # BG_015 (大名勢力): 1573 terminate → erode (大名勢力は近世も継続)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            if ev["eventId"] == "EV_p1573_01" and eg["targetBG"] == "BG_015" and eg["effect"] == "terminate":
                eg["effect"] = "erode"
                fixes.append(f"BG_015: EV_p1573_01 terminate→erode (大名勢力は近世も継続)")

    # BG_024 (北条執権体制): 1589, 1590の作用を削除（後北条氏≠鎌倉北条）
    for ev in data["events"]:
        if ev["eventId"] in ("EV_p1589_01", "EV_p1590_01"):
            before = len(ev["eGenerates"])
            ev["eGenerates"] = [eg for eg in ev["eGenerates"] if eg["targetBG"] != "BG_024"]
            if len(ev["eGenerates"]) < before:
                fixes.append(f"BG_024: {ev['eventId']} の BG_024 への作用を削除 (後北条氏≠鎌倉北条執権)")

    # BG_079 (対米関係): 1952 terminate → redirect (講和条約は関係変質であり終了ではない)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            if ev["eventId"] == "EV_p1952_02" and eg["targetBG"] == "BG_079" and eg["effect"] == "terminate":
                eg["effect"] = "redirect"
                fixes.append(f"BG_079: EV_p1952_02 terminate→redirect (講和条約は対米関係の変質)")

    return fixes


def fix_double_generate(data):
    """二重generateを修正: 最初のgenerate以外はreinforceに変更"""
    fixes = []
    first_gen = {}  # bgId → first generate eventId

    # まず全eGeneratesを時系列で走査
    all_events = sorted(data["events"], key=lambda ev: ev["year"])

    for ev in all_events:
        for eg in ev.get("eGenerates", []):
            if eg["effect"] == "generate":
                bgid = eg["targetBG"]
                if bgid in first_gen:
                    # 二重generate → reinforceに変更
                    eg["effect"] = "reinforce"
                    fixes.append(f"{bgid}: {ev['eventId']} generate→reinforce (二重generate修正、初回は{first_gen[bgid]})")
                else:
                    first_gen[bgid] = ev["eventId"]

    return fixes


def fix_effectlog_sync(data):
    """effectLogとeGeneratesの不整合を修正"""
    fixes = []
    events = {ev["eventId"]: ev for ev in data["events"]}

    # effectLogにあるがeGeneratesにないケースをeGeneratesに追加
    missing_in_eg = [
        ("EV_p0507_01", "BG_041", "terminate"),
        ("EV_p0794_01", "BG_036", "reinforce"),
        ("EV_p0905_01", "BG_066", "generate"),
        ("EV_p1378_01", "BG_015", "generate"),
        ("EV_p1858_02", "BG_048", "reinforce"),
        ("EV_p1904_01", "BG_035", "reinforce"),
        ("EV_p1941_01", "BG_035", "reinforce"),
    ]
    # Note: 以下はfix_double_generateで既にreinforceに変更されるためスキップ
    # ("EV_p0967_01", "BG_066", "generate") → reinforce
    # ("EV_p1716_02", "BG_017", "generate") → reinforce
    # ("EV_p1720_01", "BG_045", "generate") → reinforce
    # これらはgenerate→reinforce変換後に追加
    missing_post_dedup = [
        ("EV_p0967_01", "BG_066", "reinforce"),
        ("EV_p1716_02", "BG_017", "reinforce"),
        ("EV_p1720_01", "BG_045", "reinforce"),
    ]

    for evid, bgid, effect in missing_in_eg + missing_post_dedup:
        ev = events.get(evid)
        if ev:
            # 既に存在しないか確認
            existing = any(
                eg["targetBG"] == bgid and eg["effect"] == effect
                for eg in ev.get("eGenerates", [])
            )
            if not existing:
                ev.setdefault("eGenerates", []).append({
                    "targetBG": bgid,
                    "effect": effect,
                    "description": "(effectLogから復元)",
                    "_needs_review": True,
                })
                fixes.append(f"{evid}: {effect} → {bgid} を追加 (effectLogから復元)")

    return fixes


def rebuild_effectlog(data):
    """eGeneratesからeffectLogを再構築"""
    events = {ev["eventId"]: ev for ev in data["events"]}
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}

    # effectLogをクリアして再構築
    for bg in data["backgroundElements"]:
        bg["effectLog"] = []

    for ev in sorted(data["events"], key=lambda e: e["year"]):
        for eg in ev.get("eGenerates", []):
            bgid = eg["targetBG"]
            if bgid in bgs:
                bgs[bgid]["effectLog"].append({
                    "eventId": ev["eventId"],
                    "year": ev["year"],
                    "effect": eg["effect"],
                })

    return len([bg for bg in data["backgroundElements"] if bg["effectLog"]])


def main():
    data = load_data()

    print("=== eGenerates品質修正 ===\n")

    # Phase 1: terminate timing
    fixes1 = fix_terminate_timing(data)
    print(f"--- terminate修正: {len(fixes1)}件 ---")
    for f in fixes1:
        print(f"  {f}")

    # Phase 2: double generate
    fixes2 = fix_double_generate(data)
    print(f"\n--- 二重generate修正: {len(fixes2)}件 ---")
    for f in fixes2:
        print(f"  {f}")

    # Phase 3: effectLog sync
    fixes3 = fix_effectlog_sync(data)
    print(f"\n--- effectLog同期: {len(fixes3)}件 ---")
    for f in fixes3:
        print(f"  {f}")

    # Phase 4: rebuild effectLog
    linked = rebuild_effectlog(data)
    print(f"\n--- effectLog再構築: {linked}/83 BGにeffectLog ---")

    # 修正後の検証
    print(f"\n=== 修正後の検証 ===")
    all_eg = []
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            all_eg.append({"eventId": ev["eventId"], "year": ev["year"],
                          "targetBG": eg["targetBG"], "effect": eg["effect"]})

    # terminate後に作用チェック
    term_year = {}
    gen_year = {}
    for eg in sorted(all_eg, key=lambda x: x["year"]):
        if eg["effect"] == "terminate":
            term_year[eg["targetBG"]] = eg["year"]
        elif eg["effect"] == "generate":
            # generateがterminateより後なら、terminateをリセット
            if eg["targetBG"] in term_year and eg["year"] >= term_year[eg["targetBG"]]:
                del term_year[eg["targetBG"]]

    post_term = []
    for eg in all_eg:
        if eg["targetBG"] in term_year and eg["year"] > term_year[eg["targetBG"]] and eg["effect"] != "generate":
            post_term.append(eg)
    print(f"  terminate後に作用: {len(post_term)}件 (修正前: 29件)")
    for eg in post_term:
        print(f"    {eg['eventId']}({eg['year']}) {eg['effect']} → {eg['targetBG']}")

    # 二重generate
    from collections import Counter
    gen_count = Counter()
    for eg in sorted(all_eg, key=lambda x: x["year"]):
        if eg["effect"] == "generate":
            gen_count[eg["targetBG"]] += 1
    dupes = {bg: c for bg, c in gen_count.items() if c > 1}
    print(f"  二重generate: {len(dupes)}件 (修正前: 31件)")

    # effectLog整合性
    effectlog_set = set()
    for bg in data["backgroundElements"]:
        for eff in bg.get("effectLog", []):
            effectlog_set.add((eff["eventId"], bg["bgId"], eff["effect"]))
    eg_set = set((eg["eventId"], eg["targetBG"], eg["effect"]) for eg in all_eg)
    mismatch = effectlog_set - eg_set
    print(f"  effectLog不整合: {len(mismatch)}件 (修正前: 10件)")

    total = len(fixes1) + len(fixes2) + len(fixes3)
    print(f"\n総修正数: {total}件")

    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
