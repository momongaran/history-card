#!/usr/bin/env python3
"""A系課題 残作業: correspondences dangling / lanes orphan / accumulation null を修正"""

import json
import sys
from collections import defaultdict

DATA = "/Users/h/claude/1_history/data"

# ── Step 1: correspondences dangling eventId 12件 ──

def fix_correspondences():
    path = f"{DATA}/default_correspondences_v3_8.json"
    with open(path) as f:
        corr = json.load(f)

    # FWスコープ指定の置換マップ: {fw_key: {old_eventId: new_eventId}}
    replacements = {
        "FW_EV_p0752_01": {"EV_p0743_02": "EV_p0743_01"},  # 3件
        "FW_EV_p0759_01": {"EV_p0743_02": "EV_p0743_01"},  # 1件
        "FW_EV_p0769_01": {"EV_p0743_02": "EV_p0743_01"},  # 1件
        "FW_EV_p1016_02": {"EV_p1016_01": "EV_p1016_02"},  # 1件
        "FW_EV_p1185_03": {"EV_p1185_02": "EV_p1185_01"},  # 3件
        "FW_EV_p1281_01": {"EV_p1274_02": "EV_p1274_01"},  # 1件
        "FW_EV_p1641_01": {"EV_p1639_02": "EV_p1639_01"},  # 1件
        "FW_EV_p1688_01": {"EV_p1639_02": "EV_p1639_01"},  # 1件
    }

    count = 0
    for fw_key, rmap in replacements.items():
        if fw_key not in corr:
            print(f"  WARNING: FW {fw_key} not found in correspondences")
            continue
        for el_key, el_val in corr[fw_key].items():
            old_id = el_val.get("eventId")
            if old_id in rmap:
                el_val["eventId"] = rmap[old_id]
                count += 1
                print(f"  {fw_key}/{el_key}: {old_id} → {rmap[old_id]}")

    with open(path, "w") as f:
        json.dump(corr, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Step 1 完了: {count}件置換")
    return count


# ── Step 2: lanes orphan要素ID クリーンアップ ──

def fix_lanes_orphans():
    path = f"{DATA}/framework_output_v3_8.json"
    with open(path) as f:
        fw = json.load(f)

    count = 0
    for item in fw["frameworkViews"]:
        if "_legacy" in item and item.get("_legacy"):
            # _legacyブロック自体はスキップ対象外 — lanesのフィルタはelementsベース
            pass

        element_ids = {e["elementId"] for e in item.get("elements", [])}
        for lane in item.get("lanes", []):
            original = lane.get("elements", [])
            filtered = [eid for eid in original if eid in element_ids]
            removed = len(original) - len(filtered)
            if removed > 0:
                fw_id = item.get("frameworkViewId", "?")
                print(f"  {fw_id}: lanes orphan {removed}件除去 (残{len(filtered)}件)")
                count += removed
                lane["elements"] = filtered

    with open(path, "w") as f:
        json.dump(fw, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Step 2 完了: {count}件除去")
    return count


# ── Step 3: accumulation null 2件生成 ──

def fix_accumulation_null():
    fw_path = f"{DATA}/framework_output_v3_8.json"
    acc_path = f"{DATA}/accumulation_v3_8.json"

    with open(fw_path) as f:
        fw = json.load(f)
    with open(acc_path) as f:
        acc = json.load(f)

    # 生成対象の定義
    targets = {
        "FW_EV_p0647_01": {
            "b_elements": [
                ("EL_EV_p0647_01_7", "B-INS", "B-INS-02", "租庸調・班田収授の制度化"),
                ("EL_EV_p0647_01_8", "B-GEO", "B-GEO-04", "運脚の地理的負担"),
                ("EL_EV_p0647_01_9", "B-MIL", "B-MIL-03", "防人制度による労働力流出"),
            ],
            "relations": [
                {
                    "from": "EL_EV_p0647_01_7",
                    "to": "EL_EV_p0647_01_8",
                    "mechanism": "enabling",
                    "description": "租庸調の制度化が運脚の地理的負担を現実の圧力として作動させていた"
                },
                {
                    "from": "EL_EV_p0647_01_7",
                    "to": "EL_EV_p0647_01_9",
                    "mechanism": "enabling",
                    "description": "律令制度の確立が防人動員の法的根拠を提供していた"
                },
                {
                    "from": "EL_EV_p0647_01_8",
                    "to": "EL_EV_p0647_01_9",
                    "mechanism": "convergence",
                    "description": "地理的負担と軍事動員が農民の同一の生活基盤を圧迫し収斂していた"
                }
            ],
            "summary": "制度化された徴税・運脚と防人動員が農民生活を多重に圧迫し事象に至った"
        },
        "FW_EV_p1069_01": {
            "b_elements": [
                ("EL_EV_p1069_01_7", "B-INS", "B-INS-02", "荘園による租税基盤侵食"),
                ("EL_EV_p1069_01_8", "B-PWR", "B-PWR-04", "外戚なき天皇の独立性"),
                ("EL_EV_p1069_01_9", "B-INS", "B-INS-04", "従来整理の実効性欠如"),
            ],
            "relations": [
                {
                    "from": "EL_EV_p1069_01_7",
                    "to": "EL_EV_p1069_01_9",
                    "mechanism": "tension",
                    "description": "租税基盤の侵食と従来整理の無効が矛盾を拡大させていた"
                },
                {
                    "from": "EL_EV_p1069_01_7",
                    "to": "EL_EV_p1069_01_8",
                    "mechanism": "enabling",
                    "description": "荘園問題の深刻化が摂関家に依存しない天皇の行動余地を広げていた"
                },
                {
                    "from": "EL_EV_p1069_01_8",
                    "to": "EL_EV_p1069_01_9",
                    "mechanism": "enabling",
                    "description": "天皇の独立性が従来の国司主体整理を超える直接介入を可能にしていた"
                }
            ],
            "summary": "荘園拡大による財政悪化と天皇の独立性が従来整理の無効を突破する契機となり事象に至った"
        }
    }

    count = 0
    for item in fw["frameworkViews"]:
        fw_id = item.get("frameworkViewId")
        if fw_id in targets and item.get("accumulation") is None:
            t = targets[fw_id]
            acc_data = {
                "relations": t["relations"],
                "summary": t["summary"]
            }
            item["accumulation"] = acc_data
            count += 1
            print(f"  {fw_id}: accumulation生成 ({len(t['relations'])}ペア)")

    # accumulation_v3_8.json も更新
    acc_count = 0
    for fw_id, t in targets.items():
        if fw_id in acc["items"] and acc["items"][fw_id]["accumulation"] is None:
            acc["items"][fw_id]["accumulation"] = {
                "relations": t["relations"],
                "summary": t["summary"]
            }
            acc_count += 1
            print(f"  {fw_id}: accumulation_v3_8.json更新")

    with open(fw_path, "w") as f:
        json.dump(fw, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(acc_path, "w") as f:
        json.dump(acc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Step 3 完了: framework_output {count}件, accumulation_v3_8 {acc_count}件")
    return count + acc_count


# ── Step 4: 検証 ──

def validate():
    fw_path = f"{DATA}/framework_output_v3_8.json"
    corr_path = f"{DATA}/default_correspondences_v3_8.json"
    acc_path = f"{DATA}/accumulation_v3_8.json"

    with open(fw_path) as f:
        fw = json.load(f)
    with open(corr_path) as f:
        corr = json.load(f)
    with open(acc_path) as f:
        acc = json.load(f)

    # 全eventIdセット構築
    all_event_ids = {ev["eventId"] for ev in fw["events"]}
    errors = []

    # (a) correspondences内の全eventIdがeventsに存在
    dangling = []
    for fw_key, elements in corr.items():
        for el_key, el_val in elements.items():
            eid = el_val.get("eventId")
            if eid and eid not in all_event_ids:
                dangling.append(f"{fw_key}/{el_key}: {eid}")
    if dangling:
        errors.append(f"correspondences dangling eventId: {len(dangling)}件")
        for d in dangling:
            print(f"  DANGLING: {d}")
    else:
        print("  ✓ correspondences: dangling eventId なし")

    # (b) lanes内の全要素IDが同FWのelementsに存在
    orphans = []
    for item in fw["frameworkViews"]:
        element_ids = {e["elementId"] for e in item.get("elements", [])}
        for lane in item.get("lanes", []):
            for eid in lane.get("elements", []):
                if eid not in element_ids:
                    fw_id = item.get("frameworkViewId", "?")
                    orphans.append(f"{fw_id}/{lane['laneId']}: {eid}")
    if orphans:
        errors.append(f"lanes orphan要素: {len(orphans)}件")
        for o in orphans[:10]:
            print(f"  ORPHAN: {o}")
    else:
        print("  ✓ lanes: orphan要素 なし")

    # (c) accumulation nullの残存チェック (B要素1件のみのケースを除く)
    null_acc = []
    for item in fw["frameworkViews"]:
        fw_id = item.get("frameworkViewId", "?")
        b_count = sum(1 for e in item.get("elements", []) if e.get("layer") == "B")
        if item.get("accumulation") is None and b_count > 1:
            null_acc.append(f"{fw_id} (B要素{b_count}件)")
    if null_acc:
        errors.append(f"accumulation null (B>1): {len(null_acc)}件")
        for n in null_acc:
            print(f"  NULL_ACC: {n}")
    else:
        print("  ✓ accumulation: null残存なし (B>1)")

    # accumulation_v3_8.json側も確認
    null_acc_file = []
    for fw_key, item in acc["items"].items():
        if item.get("accumulation") is None:
            # framework_outputでB要素数を確認
            for fwi in fw["frameworkViews"]:
                if fwi.get("frameworkViewId") == fw_key:
                    b_count = sum(1 for e in fwi.get("elements", []) if e.get("layer") == "B")
                    if b_count > 1:
                        null_acc_file.append(f"{fw_key} (B要素{b_count}件)")
                    break
    if null_acc_file:
        errors.append(f"accumulation_v3_8.json null (B>1): {len(null_acc_file)}件")
        for n in null_acc_file:
            print(f"  NULL_ACC_FILE: {n}")
    else:
        print("  ✓ accumulation_v3_8.json: null残存なし (B>1)")

    # (d) JSONパース正常 — ここまで来れば正常
    print("  ✓ 全ファイルJSONパース正常")

    if errors:
        print(f"\n検証NG: {len(errors)}件の問題")
        for e in errors:
            print(f"  ✗ {e}")
        return False
    else:
        print("\n検証OK: 全チェック通過")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Step 1: correspondences dangling eventId 修正")
    print("=" * 60)
    fix_correspondences()

    print()
    print("=" * 60)
    print("Step 2: lanes orphan要素ID クリーンアップ")
    print("=" * 60)
    fix_lanes_orphans()

    print()
    print("=" * 60)
    print("Step 3: accumulation null 生成")
    print("=" * 60)
    fix_accumulation_null()

    print()
    print("=" * 60)
    print("Step 4: 検証")
    print("=" * 60)
    ok = validate()
    sys.exit(0 if ok else 1)
