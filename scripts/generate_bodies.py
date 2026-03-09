#!/usr/bin/env python3
"""
causalFrame の body (関数本体) を生成する。

body の構造:
  [引数(Bname)]を条件として、[因果メカニズム]。
  return [result_type]("[result_label]")

引数は [] で参照し、因果の流れを自然言語で記述する。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "framework_output_v3_9.json"


def generate_body(ev_data: dict) -> str:
    """
    Generate a function body for an event.

    Pattern per fname:
    - 圧力解放: [bg]の圧力が蓄積するなかで、{trigger mechanism}
    - 主体的行為: [bg]の状況下で、{agent's decision and action}
    - 矛盾露呈: [bg]の潜在的矛盾が、{triggering event}により顕在化した
    - 外生衝撃: [bg]の状態に対し、{external shock}が加わった
    - 偶発連鎖: [bg]の脆弱性のもとで、{contingent event}が連鎖を引き起こした
    - 権力移行: [bg]のもとで権力の空白/移動が生じ、{succession process}
    """
    fname = ev_data["fname"]
    bname = ev_data["bname"]
    bg_labels = ev_data["bg_labels"]
    bname_label = ev_data["bname_label"]
    trigger = ev_data["trigger"]
    result_type = ev_data["result_type"]
    result_label = ev_data["result_label"]

    # Build Bname reference string
    if len(bg_labels) == 1:
        bg_ref = bg_labels[0]
    else:
        bg_ref = "・".join(bg_labels)

    # Generate body based on fname pattern
    if fname == "圧力解放":
        body = (
            f"{bname}（{bg_ref}）による構造的圧力が限界に達し、"
            f"{trigger}。"
            f"この圧力解放として{result_label}が生じた"
        )
    elif fname == "主体的行為":
        body = (
            f"{bname}（{bg_ref}）という状況を踏まえ、"
            f"{trigger}。"
            f"その結果、{result_label}に至った"
        )
    elif fname == "矛盾露呈":
        body = (
            f"{bname}（{bg_ref}）に内在する矛盾が、"
            f"{trigger}ことで表面化し、"
            f"{result_label}として顕在化した"
        )
    elif fname == "外生衝撃":
        body = (
            f"{bname}（{bg_ref}）の状態に対し、"
            f"{trigger}という外生的衝撃が加わり、"
            f"{result_label}が生じた"
        )
    elif fname == "偶発連鎖":
        body = (
            f"{bname}（{bg_ref}）の脆弱性のもとで、"
            f"{trigger}が偶発的に連鎖し、"
            f"{result_label}に発展した"
        )
    elif fname == "権力移行":
        body = (
            f"{bname}（{bg_ref}）のもとで権力の空白が生じ、"
            f"{trigger}を経て、"
            f"{result_label}が実現した"
        )
    else:
        body = f"{trigger} → {result_label}"

    return body


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    bg_map = {bg["bgId"]: bg["label"]
              for bg in data.get("backgroundElements", [])}

    bodies = {}
    for ev in data["events"]:
        cf = ev["causalFrame"]
        bname_param = [v for v in cf["params"].values() if isinstance(v, dict)][0]
        text_key = [k for k, v in cf["params"].items() if isinstance(v, str)][0]
        text_val = cf["params"][text_key]

        refs = []
        for v in bname_param.get("params", {}).values():
            if isinstance(v, list):
                refs.extend(v)
            else:
                refs.append(v)

        ev_data = {
            "id": ev["eventId"],
            "title": ev["title"],
            "fname": cf["fname"],
            "bname": bname_param["bname"],
            "bg_labels": [bg_map.get(r, r) for r in refs],
            "bname_label": bname_param["label"],
            "trigger": text_val,
            "result_type": cf["result"]["role"],
            "result_label": cf["result"]["label"],
        }

        body = generate_body(ev_data)
        bodies[ev["eventId"]] = body

    # Output
    with open(ROOT / "data" / "causal_frame_bodies.json", "w",
              encoding="utf-8") as f:
        json.dump(bodies, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(bodies)} bodies")
    # Show samples per fname
    from collections import defaultdict
    by_fname = defaultdict(list)
    for ev in data["events"]:
        by_fname[ev["causalFrame"]["fname"]].append(ev["eventId"])

    for fname, ids in by_fname.items():
        eid = ids[0]
        ev = next(e for e in data["events"] if e["eventId"] == eid)
        print(f"\n=== {fname} === {eid} {ev['title']}")
        print(f"  body: {bodies[eid]}")


if __name__ == "__main__":
    main()
