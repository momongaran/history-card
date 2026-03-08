#!/usr/bin/env python3
"""
v3.8 → v3.9 構造変換ドラフト生成スクリプト

v3.8のB要素を分析し、v3.9のBG(背景要素) + B(エネルギー)構造のドラフトを生成する。
出力は人間レビュー必須のドラフトであり、自動的に正となるものではない。

Usage: python3 scripts/convert_v38_to_v39_draft.py
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
V38_FILE = ROOT / "data" / "framework_output_v3_8.json"
OUT_FILE = ROOT / "data" / "v3_9_draft_converted.json"
REPORT_FILE = ROOT / "data" / "v3_9_conversion_report.md"

# v3.8 B category → v3.9 BG type mapping
CAT_TO_BG_TYPE = {
    "B-INS": "institution",
    "B-MIL": "resource",       # 軍事基盤 → resource
    "B-EXT": "external",
    "B-RES": "resource",
    "B-PWR": "power_structure",
    "B-RIV": "conflict",
    "B-NRM": "culture",
    "B-GEO": "demographic",
    "B-LEG": "power_structure", # 正統性基盤 → power_structure
    "B-INF": "knowledge",
    "B-SOC": "demographic",    # 社会構造 → demographic (broad)
}

# Energy detection heuristic
ENERGY_RE = re.compile(
    r'(圧[がをに]|矛盾|対立[がをし]|不満|歪[みがを]|危機|焦点|緊張|衝突|反発|不安[がをに定]|'
    r'脅威|限界|課題|必要[がとに]|求め|要求|迫ら|高まっ|強まっ|揺[らぎれ]|不足|欠[如乏]|困窮|'
    r'窮[乏迫]|摩擦|抵抗|障害|停滞|混乱|断絶|空白|動揺)'
)


def load_v38():
    with open(V38_FILE) as f:
        return json.load(f)


def classify_b_element(b_elem):
    """B要素をenergy/structureに分類"""
    label = b_elem.get("label", "")
    if ENERGY_RE.search(label):
        return "energy"
    return "structure"


def normalize_bg_key(b_elem):
    """B要素からBGキー候補を生成（同一BG判定の粗いキー）"""
    norm = b_elem.get("normalizedLabel", "")
    sub = b_elem.get("subCategory", "")
    # subCategory + normalizedLabel の組み合わせ
    return f"{sub}:{norm}"


def generate_bg_id(label, counter):
    """BGのID生成"""
    # 簡易的にカウンタベース
    return f"BG_{counter:04d}"


def convert():
    v38 = load_v38()
    fws = v38["frameworkViews"]

    # Phase 1: 全B要素を収集・分類
    all_b_elements = []  # (fw_index, b_elem, classification)
    for fi, fw in enumerate(fws):
        bs = [e for e in fw["elements"] if e["layer"] == "B"]
        for b in bs:
            cls = classify_b_element(b)
            all_b_elements.append((fi, b, cls))

    # Phase 2: Structure型B要素をBGに変換（類似グルーピング）
    bg_key_groups = defaultdict(list)  # bg_key -> [(fw_index, b_elem)]
    for fi, b, cls in all_b_elements:
        if cls == "structure":
            key = normalize_bg_key(b)
            bg_key_groups[key].append((fi, b))

    # BGエントリ生成
    bg_elements = {}  # bgId -> bg_entry
    bg_key_to_id = {}  # bg_key -> bgId
    b_elem_to_bg_id = {}  # elementId -> bgId
    bg_counter = 1

    for bg_key, items in bg_key_groups.items():
        bgId = generate_bg_id(bg_key, bg_counter)
        bg_counter += 1

        # 代表ラベル（最初の要素から）
        rep = items[0][1]
        bg_type = CAT_TO_BG_TYPE.get(rep.get("category", ""), "institution")

        bg_elements[bgId] = {
            "bgId": bgId,
            "type": bg_type,
            "label": rep.get("normalizedLabel", rep.get("label", "")[:30]),
            "fullLabel": rep.get("label", ""),
            "v38_category": rep.get("category", ""),
            "v38_subCategory": rep.get("subCategory", ""),
            "eventCount": len(items),
            "events": [fws[fi]["eventId"] for fi, _ in items],
            "lifecycle": {"generatedBy": None, "states": []},
            "_review": "AUTO-GENERATED: needs human review for label/type/lifecycle"
        }

        bg_key_to_id[bg_key] = bgId
        for fi, b in items:
            b_elem_to_bg_id[b["elementId"]] = bgId

    # Phase 3: 各イベントのv3.9 FW構造を生成
    v39_views = []
    for fi, fw in enumerate(fws):
        event_id = fw["eventId"]
        title = fw.get("title", "")
        sort_key = fw.get("sortKey", 0)

        bs = [e for e in fw["elements"] if e["layer"] == "B"]
        fs = [e for e in fw["elements"] if e["layer"] == "F"]
        es = [e for e in fw["elements"] if e["layer"] == "E"]

        # Structure型B → contributingBG
        contributing_bg_ids = []
        for b in bs:
            cls = classify_b_element(b)
            if cls == "structure":
                bg_id = b_elem_to_bg_id.get(b["elementId"])
                if bg_id and bg_id not in contributing_bg_ids:
                    contributing_bg_ids.append(bg_id)

        # Energy型B → B(energy)のlabel候補
        energy_bs = [b for b in bs if classify_b_element(b) == "energy"]

        # B(energy)の生成
        b_entries = []
        if energy_bs:
            for eb in energy_bs:
                b_entries.append({
                    "label": eb["label"],
                    "contributingBG": contributing_bg_ids[:],
                    "note": f"v3.8 elementId: {eb['elementId']}",
                    "_v38_source": eb["elementId"]
                })
        else:
            # エネルギー型Bがない場合、構造型から合成
            structure_labels = [b["label"][:30] for b in bs if classify_b_element(b) == "structure"]
            b_entries.append({
                "label": f"[要合成] {' + '.join(structure_labels[:3])}...による圧",
                "contributingBG": contributing_bg_ids[:],
                "note": "AUTO: エネルギー型B要素がなかったため合成が必要",
                "_v38_source": None,
                "_review": "NEEDS_SYNTHESIS"
            })

        # E/F
        e_entries = [{"code": e.get("subCategory", ""), "label": e["label"]} for e in es]
        f_entries = [{"code": f.get("subCategory", ""), "label": f["label"]} for f in fs]

        # eGenerates (placeholder - requires human analysis)
        e_generates = [{
            "targetBG": "???",
            "effect": "???",
            "description": f"[要記入] {title} の結果、どのBGにどう影響したか",
            "_review": "NEEDS_HUMAN_INPUT"
        }]

        v39_views.append({
            "eventId": event_id,
            "title": title,
            "year": sort_key,
            "causalFramework": {
                "E": e_entries,
                "F": f_entries,
                "B": b_entries
            },
            "eGenerates": e_generates,
            "_v38_elements_count": {"B": len(bs), "F": len(fs), "E": len(es)},
            "_conversion_notes": {
                "energy_b_count": len(energy_bs),
                "structure_b_count": len(bs) - len(energy_bs),
                "bg_refs": len(contributing_bg_ids)
            }
        })

    # Output
    output = {
        "_meta": {
            "description": "v3.9 draft: v3.8から自動変換。人間レビュー必須",
            "date": "2026-03-07",
            "status": "draft",
            "stats": {
                "events": len(v39_views),
                "bg_elements": len(bg_elements),
                "needs_synthesis": sum(1 for v in v39_views
                    if any(b.get("_review") == "NEEDS_SYNTHESIS" for b in v["causalFramework"]["B"])),
                "needs_eGenerates": len(v39_views)
            }
        },
        "backgroundElements": list(bg_elements.values()),
        "frameworkViews": v39_views
    }

    with open(OUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Generate report
    report = generate_report(output, bg_elements, v39_views)
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    print(f"Output: {OUT_FILE}")
    print(f"Report: {REPORT_FILE}")
    print(f"BG elements: {len(bg_elements)}")
    print(f"Events: {len(v39_views)}")
    print(f"Needs B synthesis: {output['_meta']['stats']['needs_synthesis']}")


def generate_report(output, bg_elements, v39_views):
    stats = output["_meta"]["stats"]
    lines = [
        "# v3.9 変換レポート",
        "",
        f"生成日: 2026-03-07",
        "",
        "## サマリ",
        "",
        f"- イベント数: {stats['events']}",
        f"- BG要素数: {stats['bg_elements']}",
        f"- B合成が必要: {stats['needs_synthesis']}件",
        f"- eGenerates記入が必要: {stats['needs_eGenerates']}件",
        "",
        "## BG要素一覧（出現頻度順）",
        "",
        "| bgId | type | label | 出現イベント数 |",
        "|------|------|-------|---------------|",
    ]

    sorted_bg = sorted(bg_elements.values(), key=lambda x: -x["eventCount"])
    for bg in sorted_bg[:40]:
        lines.append(f"| {bg['bgId']} | {bg['type']} | {bg['label'][:40]} | {bg['eventCount']} |")

    if len(sorted_bg) > 40:
        lines.append(f"| ... | ... | ({len(sorted_bg)-40}件省略) | ... |")

    lines += [
        "",
        "## B合成が必要なイベント",
        "",
    ]
    for v in v39_views:
        for b in v["causalFramework"]["B"]:
            if b.get("_review") == "NEEDS_SYNTHESIS":
                lines.append(f"- {v['eventId']} ({v['title']}): {b['label'][:60]}")

    lines += [
        "",
        "## BGタイプ分布",
        "",
    ]
    type_dist = defaultdict(int)
    for bg in bg_elements.values():
        type_dist[bg["type"]] += 1
    for t, c in sorted(type_dist.items(), key=lambda x: -x[1]):
        lines.append(f"- {t}: {c}")

    return "\n".join(lines)


if __name__ == "__main__":
    convert()
