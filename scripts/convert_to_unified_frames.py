#!/usr/bin/env python3
"""
convert_to_unified_frames.py — 統一フレームモデルへの変換

全スケールで同じ構造: Frame(params...) → result
- 背景レーン廃止: BGは「前のFrameのresult」として吸収
- params[].from で前のFrameのresultを参照（背景・eGenerates・bgLineageの統一）
- children[] で入れ子（ドリフトFWが因果フレームを含む）
"""

import json
from collections import defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        events_data = json.load(f)
    with open("data/parent_fw_master.json", "r") as f:
        pfw_data = json.load(f)
    return events_data, pfw_data


def convert_event_to_frame(ev, bg_map, bg_generators):
    """イベントの因果フレームを統一フレームに変換"""
    cf = ev["causalFrame"]

    # params変換: background refsをparamsのfromに統合
    params = []
    for p in cf.get("params", []):
        param = {
            "value": p["value"],
            "type": p["type"],
        }
        if p.get("slotFunction"):
            param["slotFunction"] = p["slotFunction"]
        params.append(param)

    # 背景をparamsとして先頭に挿入（fromつき）
    bg_params = []
    for bg in cf.get("background", []):
        for ref in bg.get("refs", []):
            bg_info = bg_map.get(ref["bgId"], {})
            gen_event = bg_info.get("generatedBy", "")
            bg_params.append({
                "value": bg["label"][:100] if bg.get("label") else bg_info.get("label", ""),
                "type": bg.get("bname", "背景"),
                "role": ref.get("role", ""),
                "from": gen_event if gen_event else None,
                "fromLabel": bg_info.get("label", "")[:40],
            })

    # bg_paramsを先頭に、既存paramsを後に
    all_params = bg_params + params

    # result変換
    result = cf.get("result", {})

    # generates: このフレームのresultが生むもの
    generates = []
    for eg in ev.get("eGenerates", []):
        bg_info = bg_map.get(eg["targetBG"], {})
        generates.append({
            "target": eg["targetBG"],
            "effect": eg["effect"],
            "label": bg_info.get("label", "")[:40],
        })

    frame = {
        "id": ev["eventId"],
        "scale": "event",
        "year": ev["year"],
        "title": ev["title"],
        "fname": cf.get("fname", ""),
        "fnameCategory": cf.get("fnameCategory", ""),
        "fnamePattern": cf.get("fnamePattern", ""),
        "params": all_params,
        "body": cf.get("body", ""),
        "result": result,
        "generates": generates,
    }

    return frame


def build_drift_frames(pfw_data, event_frames, events_data):
    """親FWをドリフトフレームに変換"""
    drift_frames = []

    for pfw in pfw_data["parentFW"]:
        # このドリフトに属するイベントフレーム
        children = [f["id"] for f in event_frames
                    if any(e["eventId"] == f["id"] and e.get("parentFWRef") == pfw["id"]
                           for e in events_data["events"])]

        # 前のドリフトのresultをparamのfromにする
        params = []
        # ドリフト独自のparams（中核機能→不足機能→補完層の流れ）
        for cf in pfw.get("coreFunction", []):
            params.append({
                "value": cf,
                "type": "中核機能",
            })
        for lf in pfw.get("lackFunction", []):
            params.append({
                "value": lf,
                "type": "不足機能",
            })
        for cl in pfw.get("complementLayer", []):
            params.append({
                "value": cl,
                "type": "補完層",
            })

        # 次段背景化子 → generates
        generates = []
        for nsb in pfw.get("nextStageBackgroundizers", []):
            generates.append({
                "target": nsb["toPFW"],
                "effect": "backgroundize",
                "label": nsb["label"],
            })

        # result
        result = {
            "type": "秩序遷移",
            "label": pfw.get("summary", "")[:80],
        }
        if pfw.get("nextCoreCandidate"):
            result["nextCore"] = pfw["nextCoreCandidate"]

        drift = {
            "id": pfw["id"],
            "scale": "drift",
            "period": pfw["period"],
            "title": pfw["name"],
            "fname": "不足機能外部化→補完層中核化",
            "fwType": pfw.get("fwType", ""),
            "params": params,
            "body": pfw.get("summary", ""),
            "result": result,
            "generates": generates,
            "children": children,
        }

        drift_frames.append(drift)

    return drift_frames


def main():
    events_data, pfw_data = load_data()

    # BG map
    bg_map = {bg["bgId"]: bg for bg in events_data["backgroundElements"]}

    # BG generators (which event created which BG)
    bg_generators = {}
    for bg in events_data["backgroundElements"]:
        if bg.get("generatedBy"):
            bg_generators[bg["bgId"]] = bg["generatedBy"]

    # Convert events to unified frames
    event_frames = []
    for ev in events_data["events"]:
        frame = convert_event_to_frame(ev, bg_map, bg_generators)
        event_frames.append(frame)

    # Convert parent FWs to drift frames
    drift_frames = build_drift_frames(pfw_data, event_frames, events_data)

    # 統計
    print("=== 統一フレームモデル変換結果 ===\n")
    print(f"イベントフレーム: {len(event_frames)}件")
    print(f"ドリフトフレーム: {len(drift_frames)}件")

    # params統計
    total_params = sum(len(f["params"]) for f in event_frames)
    bg_params = sum(1 for f in event_frames for p in f["params"] if p.get("from"))
    print(f"\nイベントparams総数: {total_params}")
    print(f"  うちfrom付き(旧BG参照): {bg_params}")
    print(f"  うちfromなし(既存params): {total_params - bg_params}")

    generates_total = sum(len(f["generates"]) for f in event_frames)
    print(f"\nイベントgenerates総数: {generates_total}")

    # サンプル出力
    sample_ids = ["EV_p0794_01", "EV_p1185_01", "EV_p1600_01", "EV_p1868_01"]
    for sid in sample_ids:
        f = next((f for f in event_frames if f["id"] == sid), None)
        if not f:
            continue
        print(f"\n--- {f['id']} ({f['year']}) {f['title'][:30]} ---")
        print(f"  fname: {f['fname'][:40]}")
        print(f"  params: {len(f['params'])}件 (from付き: {sum(1 for p in f['params'] if p.get('from'))})")
        print(f"  result: {f['result']['label'][:40]}")
        print(f"  generates: {len(f['generates'])}件")

    # ドリフトサンプル
    print("\n=== ドリフトフレーム ===")
    for d in drift_frames:
        print(f"\n{d['id']} {d['title']}")
        print(f"  params: {len(d['params'])} (中核{sum(1 for p in d['params'] if p['type']=='中核機能')} "
              f"不足{sum(1 for p in d['params'] if p['type']=='不足機能')} "
              f"補完{sum(1 for p in d['params'] if p['type']=='補完層')})")
        print(f"  children: {len(d['children'])}件")
        print(f"  generates: {len(d['generates'])}件")

    # 出力
    unified = {
        "version": "5.0-unified",
        "model": "Frame(params...) → result at all scales",
        "principle": "背景=前のresultの蓄積。別管理不要。",
        "frames": drift_frames + event_frames,
    }

    with open("data/unified_frames.json", "w") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/unified_frames.json")


if __name__ == "__main__":
    main()
