#!/usr/bin/env python3
"""
backgroundフィールドを旧コミット(2555201)のcausalFrameから復元する。

旧形式 (commit 2555201):
  causalFrame.params = {
    "権力空白": {
      "bname": "権力集中",
      "params": {"権力体": "BG_005"},
      "label": "権力集中のもとでの権力空白の圧（豪族勢力の複合）"
    },
    "後継手続": "武烈天皇が後継なく崩御し大王位が空位となった"
  }

新形式 background:
  [{"bname": "権力集中", "refs": ["BG_005"], "label": "..."}]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_FILE = ROOT / "data" / "framework_output_v3_9.json"
OLD_COMMIT = "2555201"


def extract_background_from_old(old_params: dict) -> list:
    """Extract bname/refs/label from old nested params format."""
    background = []
    if not isinstance(old_params, dict):
        return background
    for key, val in old_params.items():
        if isinstance(val, dict) and "bname" in val:
            refs = []
            for v in val.get("params", {}).values():
                if isinstance(v, str) and v.startswith("BG_"):
                    refs.append(v)
            background.append({
                "bname": val["bname"],
                "refs": refs,
                "label": val.get("label", ""),
            })
    return background


def main():
    # Load old data from git
    result = subprocess.run(
        ["git", "show", f"{OLD_COMMIT}:data/framework_output_v3_9.json"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"ERROR: git show failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    old_data = json.loads(result.stdout)
    old_map = {ev["eventId"]: ev for ev in old_data["events"]}

    # Load current data
    with open(CURRENT_FILE, encoding="utf-8") as f:
        current_data = json.load(f)

    restored = 0
    already_has = 0
    not_found = 0

    for event in current_data["events"]:
        eid = event["eventId"]
        cf = event.get("causalFrame", {})
        bg = cf.get("background", [])

        # Skip if already has non-empty background
        if bg:
            already_has += 1
            continue

        old_ev = old_map.get(eid)
        if not old_ev:
            print(f"WARNING: {eid} not found in old data", file=sys.stderr)
            not_found += 1
            continue

        old_cf = old_ev.get("causalFrame", {})
        old_params = old_cf.get("params", {})
        background = extract_background_from_old(old_params)

        if background:
            cf["background"] = background
            restored += 1
        else:
            print(f"INFO: {eid} has no bname in old params either", file=sys.stderr)

    print(f"Restored: {restored}")
    print(f"Already had background: {already_has}")
    print(f"Not found in old: {not_found}")

    # Verify
    empty = sum(1 for ev in current_data["events"]
                if not ev.get("causalFrame", {}).get("background"))
    print(f"Empty background after restore: {empty} / {len(current_data['events'])}")

    if "--dry-run" not in sys.argv:
        with open(CURRENT_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print(f"Written to {CURRENT_FILE}")
    else:
        print("[DRY RUN] No file written")


if __name__ == "__main__":
    main()
