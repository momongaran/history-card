#!/usr/bin/env python3
"""
v3.9 frameworkView を コンポーザブル因果フレーム形式に変換する。

入力: archive/data/v3_9_full_draft.json (既存B-F-E形式、ビルドパイプラインの中間出力)
出力: data/framework_output_v3_9.json (v3.9 プロダクション)

Fname: 既存causalPatternから直接マッピング
Bname: BG型の組み合わせとFnameから推論
"""

import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DRAFT_FILE = BASE / "archive" / "data" / "v3_9_full_draft.json"
FRAMES_TAX = BASE / "data" / "causal_frames_taxonomy.json"
OUTPUT_FILE = BASE / "data" / "framework_output_v3_9.json"

# Fname mapping: old pattern ID -> new Fname
FNAME_MAP = {
    "A_pressure_release": "圧力解放",
    "B_deliberate_action": "主体的行為",
    "C_exogenous_shock": "外生衝撃",
    "D_contradiction_exposure": "矛盾露呈",
    "E_power_transition": "権力移行",
    "F_contingency": "偶発連鎖",
}

# Fname param role names (first param = Bname slot, second param = text slot)
FNAME_PARAMS = {
    "圧力解放":   {"bg_role": "背景",     "text_role": "揺らぎ",     "result_role": "解放"},
    "主体的行為": {"bg_role": "状況",     "text_role": "判断",       "result_role": "帰結"},
    "外生衝撃":   {"bg_role": "受容状態", "text_role": "衝撃",       "result_role": "適応"},
    "矛盾露呈":   {"bg_role": "潜在矛盾", "text_role": "顕在化契機", "result_role": "構造変化"},
    "権力移行":   {"bg_role": "権力空白", "text_role": "後継手続",   "result_role": "新体制"},
    "偶発連鎖":   {"bg_role": "脆弱性",   "text_role": "偶発事象",   "result_role": "連鎖帰結"},
}


def _dedupe_refs(bg_refs, bg_types):
    """Remove duplicate BG refs, preserving order and syncing types."""
    seen = set()
    out_refs, out_types = [], []
    for r, t in zip(bg_refs, bg_types):
        if r not in seen:
            seen.add(r)
            out_refs.append(r)
            out_types.append(t)
    return out_refs, out_types


# BG labels that should NOT map to 経済圧 despite resource/demographic type
_NON_ECONOMIC_LABELS = {
    "防衛体制", "インフラ・復興", "自然災害", "浪人問題",
}


def infer_bname(bg_types, bg_refs, fname, b_label, bg_label_map=None):
    """
    BG型の組み合わせとFnameからBnameを推論する。

    Returns: (bname, params_dict)
    """
    if bg_label_map is None:
        bg_label_map = {}

    # Step 0: deduplicate
    bg_refs, bg_types = _dedupe_refs(bg_refs, bg_types)
    type_set = set(bg_types)
    n_bgs = len(bg_refs)

    # Helper: check if a BG is truly economic
    def is_economic(ref):
        label = bg_label_map.get(ref, "")
        return label not in _NON_ECONOMIC_LABELS

    # 単一BG
    if n_bgs == 1:
        t = bg_types[0] if bg_types else "unknown"
        ref = bg_refs[0]
        bl = bg_label_map.get(ref, "")
        if t == "power_structure":
            return "権力集中", {"権力体": ref}
        elif t == "institution":
            return "制度疲弊", {"制度": ref}
        elif t == "external":
            return "外圧環境", {"国際環境": ref}
        elif t == "culture":
            return "思想潮流", {"思想": ref}
        elif t in ("resource", "economic"):
            if is_economic(ref):
                return "経済圧", {"経済構造": ref}
            else:
                return "複合背景", {"要素": bg_refs}
        elif t == "conflict":
            # single conflict BG -> 権力集中 (not 勢力対立 with 1 element)
            return "権力集中", {"権力体": ref}
        elif t == "demographic":
            if is_economic(ref):
                return "経済圧", {"経済構造": ref}
            else:
                return "複合背景", {"要素": bg_refs}
        else:
            return "複合背景", {"要素": bg_refs}

    # 複数BG — 同型
    if len(type_set) == 1:
        t = list(type_set)[0]
        if t == "power_structure":
            if n_bgs >= 2:
                return "勢力対立", {"勢力": bg_refs}
            return "権力集中", {"権力体": bg_refs[0]}
        elif t == "institution":
            return "制度的矛盾", {"要素": bg_refs}
        elif t == "external":
            return "外圧環境", {"国際環境": bg_refs[0]}
        elif t == "culture":
            return "思想潮流", {"思想": bg_refs[0]}
        else:
            return "複合背景", {"要素": bg_refs}

    # 複数BG — 異型: cultureが含まれる場合を先に判定
    if "culture" in type_set:
        cult_refs = [r for r, t in zip(bg_refs, bg_types) if t == "culture"]
        other_refs = [r for r, t in zip(bg_refs, bg_types) if t != "culture"]
        params = {"思想": cult_refs[0]}
        if other_refs:
            params["社会状態"] = other_refs[0]
        return "思想潮流", params

    if "power_structure" in type_set and "conflict" in type_set:
        return "勢力対立", {"勢力": bg_refs}

    if "institution" in type_set and "power_structure" in type_set:
        if fname in ("矛盾露呈", "圧力解放"):
            return "制度的矛盾", {"要素": bg_refs}
        else:
            return "複合背景", {"要素": bg_refs}

    if "external" in type_set:
        ext_refs = [r for r, t in zip(bg_refs, bg_types) if t == "external"]
        other_refs = [r for r, t in zip(bg_refs, bg_types) if t != "external"]
        params = {"国際環境": ext_refs[0]}
        if other_refs:
            params["国内状態"] = other_refs[0]
        return "外圧環境", params

    if "resource" in type_set or "economic" in type_set:
        res_refs = [r for r, t in zip(bg_refs, bg_types) if t in ("resource", "economic")]
        other_refs = [r for r, t in zip(bg_refs, bg_types) if t not in ("resource", "economic")]
        # Check if resource BGs are truly economic
        econ_refs = [r for r in res_refs if is_economic(r)]
        if econ_refs:
            params = {"経済構造": econ_refs[0]}
            if other_refs:
                params["階層"] = other_refs[0]
            return "経済圧", params
        else:
            return "複合背景", {"要素": bg_refs}

    # Fallback
    return "複合背景", {"要素": bg_refs}


def convert_event(fv, bg_type_map, bg_label_map):
    """Convert one frameworkView to causal frame format."""
    old_pattern = fv["causalPattern"]
    fname = FNAME_MAP.get(old_pattern)
    if not fname:
        print(f"  WARNING: unknown pattern {old_pattern} for {fv['eventId']}", file=sys.stderr)
        fname = "圧力解放"  # fallback

    fp = FNAME_PARAMS[fname]
    cf = fv["causalFramework"]

    # Collect all BG refs and their types
    all_bg_refs = []
    all_bg_types = []
    b_labels = []
    for b in cf.get("B", []):
        bgs = b.get("contributingBG", [])
        for bg_id in bgs:
            all_bg_refs.append(bg_id)
            all_bg_types.append(bg_type_map.get(bg_id, "unknown"))
        b_labels.append(b.get("label", ""))

    # Synthesize B label
    b_label = "; ".join(b_labels) if b_labels else ""

    # Infer Bname
    bname, bname_params = infer_bname(all_bg_types, all_bg_refs, fname, b_label, bg_label_map)

    # Build background frame
    bg_frame = {
        "bname": bname,
        "params": bname_params,
        "label": b_label
    }

    # Extract F (text param)
    f_items = cf.get("F", [])
    f_text = "; ".join(f.get("label", "") for f in f_items) if f_items else ""

    # Extract E (result)
    e_items = cf.get("E", [])
    e_text = "; ".join(e.get("label", "") for e in e_items) if e_items else ""

    # Build frame
    frame = {
        "fname": fname,
        "params": {
            fp["bg_role"]: bg_frame,
        },
        "result": {
            "role": fp["result_role"],
            "label": e_text
        }
    }

    # Add text param (F) — skip if empty and optional (権力移行)
    if f_text or fname != "権力移行":
        frame["params"][fp["text_role"]] = f_text

    # Build output event
    out = {
        "eventId": fv["eventId"],
        "title": fv["title"],
        "year": fv["year"],
        "causalFrame": frame,
        "eGenerates": fv.get("eGenerates", []),
    }

    return out


def main():
    print("Loading data...")
    draft = json.load(open(DRAFT_FILE, encoding="utf-8"))
    tax = json.load(open(FRAMES_TAX, encoding="utf-8"))

    # Build BG maps
    bg_type_map = {}
    bg_label_map = {}
    for bg in draft["backgroundElements"]:
        bg_type_map[bg["bgId"]] = bg["type"]
        bg_label_map[bg["bgId"]] = bg["label"]

    print(f"Converting {len(draft['frameworkViews'])} events...")

    converted = []
    bname_stats = Counter()

    for fv in draft["frameworkViews"]:
        out = convert_event(fv, bg_type_map, bg_label_map)
        converted.append(out)
        bname_stats[out["causalFrame"]["params"][list(out["causalFrame"]["params"].keys())[0]]["bname"]] += 1

    # Stats
    fname_stats = Counter(e["causalFrame"]["fname"] for e in converted)

    print(f"\n=== Fname分布 ===")
    for fname, count in fname_stats.most_common():
        print(f"  {fname}: {count}")

    print(f"\n=== Bname分布 ===")
    for bname, count in bname_stats.most_common():
        print(f"  {bname}: {count}")

    # Build output
    output = {
        "_meta": {
            "description": "v3.9 コンポーザブル因果フレーム形式ドラフト",
            "date": "2026-03-08",
            "source": "archive/data/v3_9_full_draft.json → convert_to_causal_frames.py",
            "stats": {
                "total_events": len(converted),
                "fname_distribution": dict(fname_stats.most_common()),
                "bname_distribution": dict(bname_stats.most_common()),
            }
        },
        "backgroundElements": draft["backgroundElements"],
        "events": converted,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"Total: {len(converted)} events converted")


if __name__ == "__main__":
    main()
