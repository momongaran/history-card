#!/usr/bin/env python3
"""
enrich_bname_profile.py — G-5: Bname内部構造のプロファイル化

各Bnameの「典型的な使われ方」をデータから導出し、
causal_frames_taxonomy.json にプロファイルとして追加する。

プロファイル項目:
  - primaryRole: そのBnameが最も多く果たすrole
  - typicalBGTypes: よく参照されるBGのtype
  - typicalScale: よく参照されるBGのscale
  - affinityPatterns: よく組み合わさるfnamePattern
  - mechanismType: Bnameが生む「圧」の性質（駆動型/圧力型/前提型）
"""

import json
from collections import Counter, defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def load_taxonomy():
    with open("data/causal_frames_taxonomy.json", "r") as f:
        return json.load(f)


def build_profiles(data):
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}

    # Bname別の使用データ収集
    bname_data = defaultdict(list)
    for ev in data["events"]:
        cf = ev["causalFrame"]
        for bg in cf.get("background", []):
            bname = bg.get("bname", "")
            for ref in bg.get("refs", []):
                bginfo = bgs.get(ref["bgId"], {})
                bname_data[bname].append({
                    "bgType": bginfo.get("type", ""),
                    "bgScale": bginfo.get("scale", ""),
                    "role": ref["role"],
                    "fnamePattern": cf.get("fnamePattern", ""),
                    "fnameCategory": cf.get("fnameCategory", ""),
                })

    profiles = {}
    for bname, items in bname_data.items():
        roles = Counter(i["role"] for i in items)
        bg_types = Counter(i["bgType"] for i in items)
        bg_scales = Counter(i["bgScale"] for i in items)
        fname_patterns = Counter(i["fnamePattern"] for i in items)
        fname_cats = Counter(i["fnameCategory"] for i in items)

        # mechanismType判定
        primary_role = roles.most_common(1)[0][0]
        if primary_role == "drives":
            mechanism = "駆動型"  # 内発的エネルギーで因果を駆動
        elif primary_role == "pressures":
            mechanism = "圧力型"  # 外発的圧力で因果を圧迫
        elif primary_role == "enables":
            mechanism = "前提型"  # 構造的前提として因果を可能にする
        else:
            mechanism = "支持型"  # 因果の方向を支持・増幅

        profiles[bname] = {
            "count": len(items),
            "primaryRole": primary_role,
            "roleDistribution": dict(roles.most_common()),
            "typicalBGTypes": [t for t, _ in bg_types.most_common(3)],
            "typicalScale": bg_scales.most_common(1)[0][0],
            "affinityPatterns": [p for p, _ in fname_patterns.most_common(5)],
            "affinityCats": [c for c, _ in fname_cats.most_common(3)],
            "mechanismType": mechanism,
        }

    return profiles


def main():
    data = load_data()
    taxonomy = load_taxonomy()

    profiles = build_profiles(data)

    # taxonomyに追加
    for bname_def in taxonomy.get("bnameTypes", []):
        bname = bname_def.get("name", "")
        if bname in profiles:
            bname_def["profile"] = profiles[bname]

    # 表示
    print("=== Bname内部構造プロファイル ===\n")
    for bname in ["権力集中", "外圧環境", "勢力対立", "思想潮流",
                  "経済圧", "複合背景", "制度疲弊", "制度的矛盾"]:
        p = profiles.get(bname, {})
        print(f"--- {bname} ({p.get('count', 0)}件) ---")
        print(f"  mechanismType: {p.get('mechanismType', '?')}")
        print(f"  primaryRole: {p.get('primaryRole', '?')}")
        print(f"  roles: {p.get('roleDistribution', {})}")
        print(f"  BGtypes: {p.get('typicalBGTypes', [])}")
        print(f"  scale: {p.get('typicalScale', '?')}")
        print(f"  patterns: {p.get('affinityPatterns', [])}")
        print()

    # taxonomy書き込み
    with open("data/causal_frames_taxonomy.json", "w") as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)
    print("書き込み完了: data/causal_frames_taxonomy.json")

    # stateTransitionも含むメインデータも保存（変更なしだが念のため）
    # → derive_state_transitionで既に書き込み済みなのでスキップ


if __name__ == "__main__":
    main()
