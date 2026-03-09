#!/usr/bin/env python3
"""
causalFrame に関数型フレームオーバーレイを適用する。

functional_frames_all.json から fnameCategory, fname, params[{value,type}], body を読み込み、
既存の causalFrame にオーバーレイする。既存の bname/refs 情報は background フィールドに保存。

Before (current production):
  {
    "fname": "圧力解放",
    "params": [
      {"bname": "外圧環境", "refs": ["BG_022"], "label": "..."}
    ],
    "body": "[外圧環境]のもとで...",
    "result": {"type": "解放", "label": "..."}
  }

After:
  {
    "fnameCategory": "圧力解放",
    "fname": "具体的な因果関数名",
    "params": [
      {"value": "具体的事実", "type": "抽象的因果プリミティブ"}
    ],
    "body": "[%1]のもとで[%2]て => [%3]",
    "result": {"type": "解放", "label": "..."},
    "background": [
      {"bname": "外圧環境", "refs": ["BG_022"], "label": "..."}
    ]
  }
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "framework_output_v3_9.json"
OUTPUT_FILE = ROOT / "data" / "framework_output_v3_9.json"  # in-place
FRAMES_FILE = Path("/tmp/functional_frames_all.json")


def convert_causal_frame(event: dict, frames: dict) -> dict:
    """Apply functional frame overlay to a single event's causalFrame."""
    cf = event["causalFrame"]
    event_id = event["eventId"]
    frame = frames.get(event_id)

    if not frame:
        print(f"WARNING: No functional frame for {event_id}", file=sys.stderr)
        return cf

    # Preserve existing bname/refs as background
    old_params = cf.get("params", [])
    background = []
    if isinstance(old_params, list):
        background = [p for p in old_params if "bname" in p]

    return {
        "fnameCategory": frame["fnameCategory"],
        "fname": frame["fname"],
        "params": frame["params"],
        "body": frame["body"],
        "result": cf.get("result", {}),
        "background": background,
    }


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # Load functional frames
    with open(FRAMES_FILE, encoding="utf-8") as f:
        frames = json.load(f)
    print(f"Loaded {len(frames)} functional frames")

    # Convert all events
    converted = 0
    missing = 0
    for event in data["events"]:
        if "causalFrame" in event:
            event["causalFrame"] = convert_causal_frame(event, frames)
            if "fnameCategory" in event["causalFrame"]:
                converted += 1
            else:
                missing += 1

    # Update meta
    meta_key = "_meta" if "_meta" in data else "meta"
    if meta_key in data:
        data[meta_key]["causalFrameVersion"] = "functional_v2"

    # Stats
    print(f"Converted {converted} events to functional causalFrame format")
    if missing:
        print(f"WARNING: {missing} events missing functional frames")

    # Show samples (one per fnameCategory)
    seen = set()
    for ev in data["events"]:
        cat = ev["causalFrame"].get("fnameCategory", "")
        if cat and cat not in seen:
            seen.add(cat)
            print(f"\n=== {cat} === {ev['eventId']} {ev['title']}")
            print(json.dumps(ev["causalFrame"], ensure_ascii=False, indent=2))

    # Write
    if "--dry-run" not in sys.argv:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nWritten to {OUTPUT_FILE}")
    else:
        print("\n[DRY RUN] No file written")


if __name__ == "__main__":
    main()
