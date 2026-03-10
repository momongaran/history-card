#!/usr/bin/env python3
"""
build_bg_lineage.py — G-2: 背景間系譜リンクの構築

backgroundElements間の関係を推定し、bgLineage フィールドを生成する。

リンク種別（no12準拠）:
  inherits   — 同一性の継承（AからBが正統に続く）
  transforms — 変質（Aが変質してBになった）
  branches   — 分岐（Aから分かれてBが生じた）
  merges     — 統合（AとBが合流）
  reinforces — 併走強化（独立しつつ互いの圧を強め合う）
"""

import json
from collections import defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def build_bg_timeline(data):
    """各BGの生成年・終了年・effectLogからタイムラインを構築"""
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    timelines = {}

    for bgid, bg in bgs.items():
        log = bg.get("effectLog", [])
        if not log:
            timelines[bgid] = {"start": None, "end": None, "events": []}
            continue

        years = [e["year"] for e in log]
        gen_events = [e for e in log if e["effect"] == "generate"]
        term_events = [e for e in log if e["effect"] == "terminate"]

        timelines[bgid] = {
            "start": gen_events[0]["year"] if gen_events else min(years),
            "end": term_events[0]["year"] if term_events else None,
            "events": log,
            "generate_event": gen_events[0]["eventId"] if gen_events else None,
            "terminate_event": term_events[0]["eventId"] if term_events else None,
        }

    return timelines


def build_event_effects(data):
    """各イベントが影響するBGリストを構築"""
    event_effects = defaultdict(list)
    for ev in data["events"]:
        for eg in ev.get("eGenerates", []):
            event_effects[ev["eventId"]].append({
                "targetBG": eg["targetBG"],
                "effect": eg["effect"],
                "year": ev["year"],
            })
    return event_effects


def infer_lineage(data):
    """系譜リンクを推定"""
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    timelines = build_bg_timeline(data)
    event_effects = build_event_effects(data)
    links = []
    seen = set()

    def add_link(from_bg, to_bg, kind, evidence, confidence="auto"):
        key = (from_bg, to_bg, kind)
        if key not in seen:
            seen.add(key)
            links.append({
                "from": from_bg,
                "to": to_bg,
                "kind": kind,
                "evidence": evidence,
                "confidence": confidence,
            })

    # === ルール1: 同一イベントで terminate A + generate B → transforms ===
    for evid, effects in event_effects.items():
        terminated = [e["targetBG"] for e in effects if e["effect"] == "terminate"]
        generated = [e["targetBG"] for e in effects if e["effect"] == "generate"]
        for t in terminated:
            for g in generated:
                if t != g:
                    # 同じtypeなら transforms、異なるなら branches
                    t_type = bgs.get(t, {}).get("type", "")
                    g_type = bgs.get(g, {}).get("type", "")
                    kind = "transforms" if t_type == g_type else "branches"
                    add_link(t, g, kind, evid)

    # === ルール2: 同一イベントで erode A + generate B → transforms (弱) ===
    for evid, effects in event_effects.items():
        eroded = [e["targetBG"] for e in effects if e["effect"] == "erode"]
        generated = [e["targetBG"] for e in effects if e["effect"] == "generate"]
        for e_bg in eroded:
            for g in generated:
                if e_bg != g:
                    e_type = bgs.get(e_bg, {}).get("type", "")
                    g_type = bgs.get(g, {}).get("type", "")
                    if e_type == g_type:
                        add_link(e_bg, g, "transforms", evid)

    # === ルール3: 明示的な継承関係（手動定義） ===
    # 歴史的に明確な系譜
    explicit = [
        # 政権の継承・変質
        ("BG_023", "BG_054", "transforms", "蘇我氏→天皇親政への転換"),
        ("BG_054", "BG_040", "inherits", "天皇・朝廷: 古代→平安"),
        ("BG_040", "BG_046", "inherits", "天皇・朝廷: 平安→中世"),
        ("BG_046", "BG_026", "inherits", "天皇・朝廷: 中世→近世"),

        # 皇位継承の系譜
        ("BG_027", "BG_028", "inherits", "皇位継承: 古代→平安"),
        ("BG_028", "BG_059", "inherits", "皇位継承: 平安→中世"),
        ("BG_059", "BG_082", "inherits", "皇位継承: 中世→近現代"),

        # 武士層の発展
        ("BG_057", "BG_018", "transforms", "武士層: 平安→中世（台頭）"),
        ("BG_018", "BG_042", "transforms", "武士層: 中世→近世（統治者化）"),

        # 仏教の変遷
        ("BG_011", "BG_050", "transforms", "仏教: 古代→平安"),
        ("BG_050", "BG_069", "transforms", "仏教: 平安→近世"),

        # 権力構造の系譜
        ("BG_002", "BG_053", "reinforces", "摂関家と外戚政治は同じ構造の表裏"),
        ("BG_002", "BG_014", "transforms", "摂関→院政への権力移行"),
        ("BG_014", "BG_021", "branches", "院政から平氏台頭が分岐"),
        ("BG_021", "BG_019", "branches", "平氏→源氏（対立から権力移行）"),
        ("BG_019", "BG_009", "transforms", "源氏→御家人制の制度化"),
        ("BG_009", "BG_024", "transforms", "御家人制→北条執権体制"),
        ("BG_024", "BG_077", "reinforces", "北条執権と鎌倉幕府は同じ体制の表裏"),
        ("BG_077", "BG_025", "transforms", "鎌倉幕府→足利氏への権力移行"),
        ("BG_025", "BG_070", "reinforces", "足利氏と室町幕府は同じ体制の表裏"),
        ("BG_070", "BG_072", "transforms", "室町幕府→戦国の分裂"),
        ("BG_072", "BG_001", "transforms", "戦国→織田政権による統一"),
        ("BG_001", "BG_003", "transforms", "織田→豊臣への権力移行"),
        ("BG_003", "BG_006", "transforms", "豊臣→徳川への権力移行"),
        ("BG_006", "BG_083", "reinforces", "徳川家と藩体制は同じ体制の表裏"),
        ("BG_006", "BG_067", "reinforces", "徳川家と鎖国体制は同じ体制の表裏"),
        ("BG_031", "BG_055", "transforms", "雄藩連合→明治政府"),

        # 制度の系譜
        ("BG_013", "BG_058", "reinforces", "律令制と班田収授制は連動"),
        ("BG_013", "BG_068", "reinforces", "律令制と人民把握制度は連動"),
        ("BG_013", "BG_039", "reinforces", "律令制と国司行政は連動"),
        ("BG_058", "BG_065", "transforms", "班田制の崩壊→荘園制の成立"),
        ("BG_039", "BG_047", "transforms", "国司行政→守護・地頭制"),
        ("BG_064", "BG_062", "reinforces", "明治憲法体制と議会制は連動"),
        ("BG_064", "BG_073", "transforms", "明治憲法→戦後憲法への転換"),
        ("BG_081", "BG_083", "reinforces", "検地・兵農分離と藩体制は連動"),

        # 対外関係の系譜
        ("BG_078", "BG_012", "transforms", "隋→唐との関係"),
        ("BG_012", "BG_022", "reinforces", "唐と朝鮮半島情勢は連動"),
        ("BG_037", "BG_008", "transforms", "開国と攘夷→対外関係(近代)"),
        ("BG_056", "BG_008", "reinforces", "条約体制と対外関係(近代)は連動"),

        # 南北朝
        ("BG_032", "BG_025", "transforms", "南北朝分裂→足利氏による統合"),
        ("BG_071", "BG_072", "transforms", "応仁の乱→戦国の分裂"),
    ]

    for from_bg, to_bg, kind, evidence in explicit:
        if from_bg in bgs and to_bg in bgs:
            add_link(from_bg, to_bg, kind, evidence, "manual")

    # === ルール4: 高頻度共起で同type → reinforces ===
    bg_to_events = defaultdict(set)
    for bg in data["backgroundElements"]:
        for eff in bg.get("effectLog", []):
            bg_to_events[bg["bgId"]].add(eff["eventId"])

    for a in bgs:
        for b in bgs:
            if a >= b:
                continue
            shared = bg_to_events[a] & bg_to_events[b]
            if len(shared) >= 4:
                # 既にリンクがあればスキップ
                if (a, b, "reinforces") not in seen and \
                   not any(l["from"] == a and l["to"] == b for l in links) and \
                   not any(l["from"] == b and l["to"] == a for l in links):
                    add_link(a, b, "reinforces",
                             f"共起{len(shared)}回: {','.join(sorted(shared)[:3])}...",
                             "auto-cooccurrence")

    return links


def main():
    data = load_data()

    links = infer_lineage(data)

    # リンクをデータに追加
    data["bgLineage"] = links

    # 統計
    from collections import Counter
    kinds = Counter(l["kind"] for l in links)
    confs = Counter(l["confidence"] for l in links)

    print(f"=== 背景間系譜リンク生成完了 ===")
    print(f"総リンク数: {len(links)}")
    print(f"\nkind分布:")
    for k, v in kinds.most_common():
        print(f"  {k}: {v}")
    print(f"\nconfidence分布:")
    for k, v in confs.most_common():
        print(f"  {k}: {v}")

    # リンクされたBGの数
    linked_bgs = set()
    for l in links:
        linked_bgs.add(l["from"])
        linked_bgs.add(l["to"])
    print(f"\nリンクされたBG: {len(linked_bgs)}/83")

    # サンプル表示
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    print(f"\n=== サンプル（transforms）===")
    for l in links:
        if l["kind"] == "transforms":
            f_label = bgs[l["from"]]["label"][:20]
            t_label = bgs[l["to"]]["label"][:20]
            print(f"  {l['from']}({f_label}) → {l['to']}({t_label}) [{l['confidence']}]")
            if sum(1 for ll in links if ll["kind"] == "transforms") > 10:
                break

    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
