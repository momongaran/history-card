#!/usr/bin/env python3
"""
重複イベントをマージ（削除側を除去し、参照を残す側に書き換え）するスクリプト。

Usage:
  python scripts/merge_duplicate_events.py              # dry-run (default)
  python scripts/merge_duplicate_events.py --execute    # 実行
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"

FRAMEWORK_FILE = ROOT / "framework_output_v3_3.json"
CORRESPONDENCES_FILE = ROOT / "default_correspondences.json"
MOMENTUM_FILE = ROOT / "momentum_v3_3.json"
ACCUMULATION_FILE = ROOT / "accumulation_v3_1.json"

# (keep_id, delete_id)
MERGE_TABLE = [
    ("EV_p0743_01", "EV_p0743_02"),
    ("EV_p1016_02", "EV_p1016_01"),
    ("EV_p1086_01", "EV_p1086_02"),
    ("EV_p1274_01", "EV_p1274_02"),
    ("EV_p1549_02", "EV_p1549_01"),
    ("EV_p1635_02", "EV_p1635_01"),
    ("EV_p1639_01", "EV_p1639_02"),
    ("EV_p1716_02", "EV_p1716_01"),
    ("EV_p1787_02", "EV_p1787_01"),
    ("EV_p1841_02", "EV_p1841_01"),
    ("EV_p1853_02", "EV_p1853_01"),
    ("EV_p1951_01", "EV_p1951_02"),
    ("EV_p1185_03", "EV_p1185_02"),
    ("EV_p1221_02", "EV_p1221_01"),
    ("EV_p1590_01", "EV_p1590_02"),
    ("EV_p1866_02", "EV_p1866_01"),  # 集約メタイベント削除→参照は1866_02へ
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fw_key(event_id):
    return f"FW_{event_id}"


def run(execute: bool):
    delete_ids = {d for _, d in MERGE_TABLE}
    rewrite_map = {d: k for k, d in MERGE_TABLE if k is not None}

    # --- Load ---
    framework = load_json(FRAMEWORK_FILE)
    correspondences = load_json(CORRESPONDENCES_FILE)
    momentum = load_json(MOMENTUM_FILE)
    accumulation = load_json(ACCUMULATION_FILE)

    stats = {
        "events_removed": 0,
        "fw_views_removed": 0,
        "corr_keys_removed": 0,
        "corr_refs_rewritten": 0,
        "momentum_keys_removed": 0,
        "accumulation_keys_removed": 0,
    }

    # 1. events[] から delete_id を除去
    orig_count = len(framework["events"])
    framework["events"] = [
        ev for ev in framework["events"] if ev["eventId"] not in delete_ids
    ]
    stats["events_removed"] = orig_count - len(framework["events"])

    # 2. frameworkViews[] から delete_id の FW を除去
    orig_count = len(framework["frameworkViews"])
    framework["frameworkViews"] = [
        fv
        for fv in framework["frameworkViews"]
        if fv["frameworkViewId"] not in {fw_key(d) for d in delete_ids}
    ]
    stats["fw_views_removed"] = orig_count - len(framework["frameworkViews"])

    # 3. correspondences から FW_delete_id のキーを除去
    for did in delete_ids:
        key = fw_key(did)
        if key in correspondences:
            stats["corr_keys_removed"] += 1
            del correspondences[key]

    # 4. correspondences の全エントリで eventId が delete_id → keep_id に書き換え
    for fw_key_name, elements in correspondences.items():
        for el_key, el_val in elements.items():
            if el_val.get("eventId") in rewrite_map:
                old = el_val["eventId"]
                new = rewrite_map[old]
                el_val["eventId"] = new
                stats["corr_refs_rewritten"] += 1

    # 5. momentum から FW_delete_id のキーを除去
    items = momentum.get("items", momentum)
    for did in delete_ids:
        key = fw_key(did)
        if key in items:
            stats["momentum_keys_removed"] += 1
            del items[key]

    # 6. accumulation から FW_delete_id のキーを除去
    acc_items = accumulation.get("items", accumulation)
    for did in delete_ids:
        key = fw_key(did)
        if key in acc_items:
            stats["accumulation_keys_removed"] += 1
            del acc_items[key]

    # --- Summary ---
    print("=== Merge Duplicate Events ===")
    print(f"Mode: {'EXECUTE' if execute else 'DRY-RUN'}")
    print()
    for label, count in stats.items():
        print(f"  {label}: {count}")
    print()
    print(f"  events count after merge: {len(framework['events'])}")
    print(f"  frameworkViews count after merge: {len(framework['frameworkViews'])}")

    # Verify no stale references remain in correspondences
    stale = []
    for fw_key_name, elements in correspondences.items():
        for el_key, el_val in elements.items():
            if el_val.get("eventId") in delete_ids:
                stale.append((fw_key_name, el_key, el_val["eventId"]))
    if stale:
        print(f"\n  WARNING: {len(stale)} stale eventId references remain:")
        for s in stale:
            print(f"    {s}")
    else:
        print("\n  OK: No stale eventId references in correspondences.")

    if not execute:
        print("\nNo files modified. Use --execute to apply changes.")
        return

    # --- Save ---
    save_json(FRAMEWORK_FILE, framework)
    save_json(CORRESPONDENCES_FILE, correspondences)
    save_json(MOMENTUM_FILE, momentum)
    save_json(ACCUMULATION_FILE, accumulation)
    print("\nFiles updated successfully.")


def main():
    parser = argparse.ArgumentParser(description="Merge duplicate events")
    parser.add_argument(
        "--execute", action="store_true", help="Apply changes (default: dry-run)"
    )
    args = parser.parse_args()
    run(execute=args.execute)


if __name__ == "__main__":
    main()
