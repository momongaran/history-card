#!/usr/bin/env python3
"""
build_unified_v2.py — 統一フレームモデル v2

改善点:
(1) PARAMS → 各項目のtypeで語る（セクション名なし）
(2) 不足機能 → 摩擦（当時観測可能な問題）
(3) 引数削減 — ドリフトは一文要約、イベントは背景を圧縮
(4) fname → result を一体表示
(5) 局所FWでイベントをグループ化、フレーム間連鎖を可視化
"""

import json
from collections import defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def load_pfw():
    with open("data/parent_fw_master.json", "r") as f:
        return json.load(f)


# 局所FWの自動検出: fnamePattern + 時間近接 + BG共有でクラスタリング
def detect_local_fws(events, bg_map):
    """イベント群を局所FWにグループ化"""
    if not events:
        return []

    # イベントをソート
    events = sorted(events, key=lambda e: e["year"])

    # 各イベントのBG参照セットを構築
    def get_bg_set(ev):
        bgs = set()
        for bg in ev["causalFrame"].get("background", []):
            for ref in bg.get("refs", []):
                bgs.add(ref["bgId"])
        for eg in ev.get("eGenerates", []):
            bgs.add(eg["targetBG"])
        return bgs

    # グループ化: fnamePattern + BG重複 + 時間近接
    groups = []
    used = set()

    for i, ev in enumerate(events):
        if ev["eventId"] in used:
            continue

        group = [ev]
        used.add(ev["eventId"])
        ev_bgs = get_bg_set(ev)
        ev_pattern = ev["causalFrame"].get("fnamePattern", "")

        for j in range(i + 1, len(events)):
            ev2 = events[j]
            if ev2["eventId"] in used:
                continue

            # 時間が離れすぎたら別グループ
            if ev2["year"] - group[-1]["year"] > 50:
                break

            ev2_bgs = get_bg_set(ev2)
            ev2_pattern = ev2["causalFrame"].get("fnamePattern", "")

            # BG共有 or 同パターン → 同グループ
            bg_overlap = len(ev_bgs & ev2_bgs)
            same_pattern = ev_pattern == ev2_pattern and ev_pattern

            if bg_overlap >= 1 or same_pattern:
                group.append(ev2)
                used.add(ev2["eventId"])
                ev_bgs |= ev2_bgs  # グループのBGを拡張

        groups.append(group)

    return groups


def summarize_group(group):
    """局所FWグループの要約を生成"""
    patterns = defaultdict(int)
    bnames = defaultdict(int)
    for ev in group:
        p = ev["causalFrame"].get("fnamePattern", "")
        if p:
            patterns[p] += 1
        for bg in ev["causalFrame"].get("background", []):
            bnames[bg.get("bname", "")] += 1

    top_pattern = max(patterns, key=patterns.get) if patterns else "混合"
    top_bname = max(bnames, key=bnames.get) if bnames else ""

    year_range = f"{group[0]['year']}–{group[-1]['year']}" if len(group) > 1 else str(group[0]["year"])

    return {
        "pattern": top_pattern,
        "bname": top_bname,
        "yearRange": year_range,
        "title": f"{top_pattern}（{top_bname}）" if top_bname else top_pattern,
    }


def build_event_frame(ev, bg_map):
    """イベントを統一フレームに変換（v2: 簡潔版）"""
    cf = ev["causalFrame"]

    # 背景を1つの条件文に圧縮
    bg_labels = []
    bg_from = []
    for bg in cf.get("background", []):
        for ref in bg.get("refs", []):
            bg_info = bg_map.get(ref["bgId"], {})
            gen = bg_info.get("generatedBy", "")
            bg_labels.append(bg.get("label", "")[:60])
            if gen:
                bg_from.append({"id": gen, "role": ref.get("role", "")})

    # 条件（旧背景 + params を統合して簡潔に）
    conditions = []
    if bg_labels:
        conditions.append({
            "value": "；".join(bg_labels)[:120],
            "type": cf["background"][0].get("bname", "状況") if cf.get("background") else "状況",
            "from": bg_from,
        })
    for p in cf.get("params", []):
        conditions.append({
            "value": p["value"],
            "type": p.get("slotFunction", p["type"])[:20],
        })

    # generates
    generates = []
    for eg in ev.get("eGenerates", []):
        bg_info = bg_map.get(eg["targetBG"], {})
        generates.append({
            "effect": eg["effect"],
            "label": bg_info.get("label", eg["targetBG"])[:40],
        })

    return {
        "id": ev["eventId"],
        "scale": "event",
        "year": ev["year"],
        "title": ev["title"],
        "fname": cf.get("fname", ""),
        "fnameCategory": cf.get("fnameCategory", ""),
        "fnamePattern": cf.get("fnamePattern", ""),
        "conditions": conditions,
        "result": cf.get("result", {}),
        "generates": generates,
    }


def build_local_fw_frame(local_id, group, event_frames, bg_map):
    """局所FWフレームを構築"""
    summary = summarize_group(group)
    child_ids = [ev["eventId"] for ev in group]

    # この局所FWの入力: グループ内イベントの背景の集約
    from_set = set()
    for ev in group:
        for bg in ev["causalFrame"].get("background", []):
            for ref in bg.get("refs", []):
                bg_info = bg_map.get(ref["bgId"], {})
                gen = bg_info.get("generatedBy", "")
                if gen and gen not in child_ids:
                    from_set.add((gen, bg_info.get("label", "")[:30]))

    conditions = []
    for from_id, label in list(from_set)[:3]:
        conditions.append({
            "value": label,
            "type": "先行結果",
            "from": [{"id": from_id}],
        })

    # この局所FWの出力: グループ内イベントのgeneratesの集約
    generates = []
    seen_effects = set()
    for ev in group:
        for eg in ev.get("eGenerates", []):
            bg_info = bg_map.get(eg["targetBG"], {})
            key = (eg["effect"], eg["targetBG"])
            if key not in seen_effects:
                seen_effects.add(key)
                generates.append({
                    "effect": eg["effect"],
                    "label": bg_info.get("label", "")[:30],
                })

    # 最後のイベントのresultを局所FWのresultとする
    last_ev = group[-1]
    result = last_ev["causalFrame"].get("result", {})

    return {
        "id": local_id,
        "scale": "local",
        "year": group[0]["year"],
        "yearEnd": group[-1]["year"],
        "title": summary["title"],
        "pattern": summary["pattern"],
        "conditions": conditions,
        "result": result,
        "generates": generates[:5],
        "children": child_ids,
    }


def build_drift_frame(pfw, local_fws, events_data):
    """ドリフトフレームを構築（v2: 一文要約、摩擦表現）"""

    # 摩擦（旧不足機能を問題として表現）
    friction_map = {
        "在地執行": "地方紛争が中央から処理しにくい",
        "武力処理": "武力行使を担う層が不在",
        "所領保全": "所領の維持・保全が不安定",
        "即応的紛争処理": "紛争への即応が遅い",
        "運用持続コストの吸収": "制度維持のコストが増大",
        "地方統制の実効性": "地方の実態把握が困難に",
        "制度と現実の乖離処理": "制度と現実の乖離が拡大",
        "広域安定統治": "広域を安定的に統治する仕組みが未整備",
        "財政管理": "安定した財政基盤がない",
        "法的整合": "判断基準が不統一",
        "中央集権的統制力": "中央からの統制が弱い",
        "安定財政": "財源が不安定",
        "広域統一": "分散状態が非効率を生む",
        "経済変動への適応": "経済変化に対応できない",
        "民主的統制": "政治的統制の仕組みが弱い",
        "民主的抑制": "軍事膨張を止められない",
    }

    frictions = []
    for lf in pfw.get("lackFunction", []):
        frictions.append(friction_map.get(lf, lf + "が問題化"))

    # 条件: 一文に圧縮
    conditions = [
        {"value": pfw.get("summary", "")[:100], "type": "概況"},
    ]
    if frictions:
        conditions.append({
            "value": "；".join(frictions[:3]),
            "type": "摩擦",
        })
    if pfw.get("complementLayer"):
        conditions.append({
            "value": "、".join(pfw["complementLayer"]),
            "type": "台頭する層",
        })

    # generates
    generates = []
    for nsb in pfw.get("nextStageBackgroundizers", []):
        generates.append({
            "effect": "backgroundize",
            "label": nsb["label"],
            "target": nsb["toPFW"],
        })

    result = {
        "type": "秩序遷移",
        "label": pfw.get("summary", "")[:60],
    }
    if pfw.get("nextCoreCandidate"):
        result["nextCore"] = pfw["nextCoreCandidate"]

    # children: 局所FWのID
    local_ids = [lf["id"] for lf in local_fws]

    return {
        "id": pfw["id"],
        "scale": "drift",
        "period": pfw["period"],
        "title": pfw["name"],
        "fwType": pfw.get("fwType", ""),
        "conditions": conditions,
        "result": result,
        "generates": generates,
        "children": local_ids,
    }


def main():
    events_data = load_data()
    pfw_data = load_pfw()

    bg_map = {bg["bgId"]: bg for bg in events_data["backgroundElements"]}
    pfws = pfw_data["parentFW"]

    # イベントフレーム変換
    event_frames = {}
    for ev in events_data["events"]:
        f = build_event_frame(ev, bg_map)
        event_frames[f["id"]] = f

    # ドリフトごとに局所FW検出
    all_local_fws = []
    all_drift_frames = []
    local_counter = 0

    for pfw in pfws:
        # このドリフトのイベント
        drift_events = [ev for ev in events_data["events"]
                        if ev.get("parentFWRef") == pfw["id"]]

        # 局所FW検出
        groups = detect_local_fws(drift_events, bg_map)

        local_fws = []
        for group in groups:
            local_counter += 1
            local_id = f"LFW_{local_counter:03d}"
            lfw = build_local_fw_frame(local_id, group, event_frames, bg_map)
            local_fws.append(lfw)
            all_local_fws.append(lfw)

        # ドリフトフレーム
        drift = build_drift_frame(pfw, local_fws, events_data)
        all_drift_frames.append(drift)

    # ── 局所FW間の因果接続を計算 ──
    # イベント→局所FWの逆引き
    ev_to_lfw = {}
    for lfw in all_local_fws:
        for eid in lfw["children"]:
            ev_to_lfw[eid] = lfw["id"]

    # BG→生成元イベントの逆引き
    bg_generated_by = {}
    for bg in events_data["backgroundElements"]:
        if bg.get("generatedBy"):
            bg_generated_by[bg["bgId"]] = bg["generatedBy"]

    # 各イベントが参照するBGの生成元イベントを辿り、局所FW間の接続を構築
    lfw_connections = []  # [{from, to, via: [bgLabel], weight}]
    connection_map = defaultdict(lambda: {"bgs": [], "weight": 0})

    for ev in events_data["events"]:
        ev_lfw = ev_to_lfw.get(ev["eventId"])
        if not ev_lfw:
            continue
        for bg_entry in ev["causalFrame"].get("background", []):
            for ref in bg_entry.get("refs", []):
                bg_id = ref["bgId"]
                gen_ev = bg_generated_by.get(bg_id)
                if not gen_ev:
                    continue
                src_lfw = ev_to_lfw.get(gen_ev)
                if not src_lfw or src_lfw == ev_lfw:
                    continue
                key = (src_lfw, ev_lfw)
                bg_info = bg_map.get(bg_id, {})
                label = bg_info.get("label", bg_id)[:30]
                if label not in connection_map[key]["bgs"]:
                    connection_map[key]["bgs"].append(label)
                connection_map[key]["weight"] += 1

    for (src, tgt), info in connection_map.items():
        lfw_connections.append({
            "from": src,
            "to": tgt,
            "via": info["bgs"][:3],
            "weight": info["weight"],
        })

    # 接続情報を各局所FWに付与
    for lfw in all_local_fws:
        lfw["feedsTo"] = [c for c in lfw_connections if c["from"] == lfw["id"]]
        lfw["feedsFrom"] = [c for c in lfw_connections if c["to"] == lfw["id"]]

    # 統計
    print("=== 統一フレームモデル v2 ===\n")
    print(f"ドリフト: {len(all_drift_frames)}件")
    print(f"局所FW:  {len(all_local_fws)}件")
    print(f"イベント: {len(event_frames)}件")
    print(f"局所FW間接続: {len(lfw_connections)}本")

    print(f"\n=== ドリフト別局所FW ===")
    for d in all_drift_frames:
        local_children = [lf for lf in all_local_fws if lf["id"] in d["children"]]
        print(f"\n{d['id']} {d['title']}")
        for lf in local_children:
            ev_count = len(lf["children"])
            feeds_to = len(lf.get("feedsTo", []))
            feeds_from = len(lf.get("feedsFrom", []))
            print(f"  {lf['id']} {lf['title']} ({ev_count}件, ←{feeds_from} →{feeds_to})")

    # クロスドリフト接続の表示
    drift_children = {d["id"]: set(d["children"]) for d in all_drift_frames}
    lfw_to_drift = {}
    for did, children in drift_children.items():
        for cid in children:
            lfw_to_drift[cid] = did

    cross_drift = [c for c in lfw_connections if lfw_to_drift.get(c["from"]) != lfw_to_drift.get(c["to"])]
    print(f"\n=== クロスドリフト接続: {len(cross_drift)}本 ===")
    for c in cross_drift:
        src_d = lfw_to_drift.get(c["from"], "?")
        tgt_d = lfw_to_drift.get(c["to"], "?")
        print(f"  {c['from']}({src_d}) → {c['to']}({tgt_d}): {', '.join(c['via'][:2])}")

    # 出力
    unified = {
        "version": "5.0-unified-v2",
        "model": "Frame(conditions...) → result — 3スケール入れ子",
        "scales": ["drift", "local", "event"],
        "drifts": all_drift_frames,
        "localFWs": all_local_fws,
        "events": list(event_frames.values()),
        "connections": lfw_connections,
    }

    with open("data/unified_frames_v2.json", "w") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/unified_frames_v2.json")


if __name__ == "__main__":
    main()
