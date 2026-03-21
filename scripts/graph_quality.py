#!/usr/bin/env python3
"""
graph_quality.py — EnergyAbsグラフの品質指標を計算する

6つの指標でグラフの「ほどよさ」を定量評価する:
  1. トリガー孤立率: 揺らぎはあるが背景が見えないノードの比率 → 低いほど良い
  2. 平均背景本数: triggers持ちノードの背景の豊かさ → 1-2が目安
  3. バイパス率: 中間ノードの入力が出力先にも直接つながっている率 → 低いほど良い(10%前後)
  4. 推移的冗長率: A→B→CかつA→Cの比率 → 適度が良い(5-15%)
  5. エッジ/ノード比: グラフの疎密 → 1.3-2.0が目安
  6. role比率: amplifies/triggers/transforms/sustainsのバランス

使い方:
  python3 scripts/graph_quality.py
  python3 scripts/graph_quality.py -i other.json
  python3 scripts/graph_quality.py --json

設計:
  - 任意のEnergyAbsデータに適用可能
  - 読み取り専用（データは変更しない）
  - 目安値はv2日本史データから導出。世界史展開時に再検証が必要
"""

import json
import argparse
from collections import defaultdict, Counter


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def calc_metrics(data: dict) -> dict:
    nodes_list = data["nodes"]
    edges = data["edges"]
    nodes = {n["id"]: n for n in nodes_list}
    N = len(nodes_list)
    E = len(edges)

    edges_to = defaultdict(list)
    edges_from = defaultdict(list)
    edge_set = set()
    for e in edges:
        edges_to[e["to"]].append(e)
        edges_from[e["from"]].append(e)
        edge_set.add((e["from"], e["to"]))

    # ── 1. トリガー孤立率 ──
    triggered = []
    for n in nodes_list:
        inc = edges_to[n["id"]]
        has_trig = any(e["role"] == "triggers" for e in inc)
        if has_trig:
            n_bg = sum(
                1 for e in inc if e["role"] in ("amplifies", "sustains")
            )
            triggered.append({"id": n["id"], "bg_count": n_bg})

    isolated = [t for t in triggered if t["bg_count"] == 0]
    isolation_rate = (
        len(isolated) / len(triggered) * 100 if triggered else 0
    )
    avg_bg = (
        sum(t["bg_count"] for t in triggered) / len(triggered)
        if triggered
        else 0
    )

    # ── 2. バイパス率（合成価値） ──
    synthesis_scores = []
    for n in nodes_list:
        nid = n["id"]
        inputs = {e["from"] for e in edges_to[nid]}
        outputs = {e["to"] for e in edges_from[nid]}
        if not inputs or not outputs:
            continue
        bypass = sum(
            1
            for inp in inputs
            for out in outputs
            if (inp, out) in edge_set
        )
        total = len(inputs) * len(outputs)
        if total > 0:
            synthesis_scores.append(bypass / total)

    avg_bypass = (
        sum(synthesis_scores) / len(synthesis_scores) * 100
        if synthesis_scores
        else 0
    )

    # ── 3. 推移的冗長率 ──
    trans_total = 0
    trans_redundant = 0
    for n in nodes_list:
        for e1 in edges_from[n["id"]]:
            for e2 in edges_from[e1["to"]]:
                trans_total += 1
                if (n["id"], e2["to"]) in edge_set:
                    trans_redundant += 1

    trans_rate = (
        trans_redundant / trans_total * 100 if trans_total else 0
    )

    # ── 4. role比率 ──
    role_counts = Counter(e["role"] for e in edges)

    return {
        "nodes": N,
        "edges": E,
        "e_per_n": round(E / N, 2),
        "trigger_isolation_rate": round(isolation_rate, 1),
        "triggered_nodes": len(triggered),
        "isolated_triggers": len(isolated),
        "avg_bg_per_trigger": round(avg_bg, 1),
        "bypass_rate": round(avg_bypass, 1),
        "transitive_redundancy": round(trans_rate, 1),
        "role_counts": dict(role_counts),
    }


def print_report(m: dict):
    print(f"\n{'='*50}")
    print(f"EnergyAbsグラフ品質指標")
    print(f"{'='*50}")
    print(f"  ノード: {m['nodes']}, エッジ: {m['edges']}")
    print(f"  E/N比: {m['e_per_n']}  (目安: 1.3-2.0)")
    print()
    print(f"  トリガー孤立率: {m['trigger_isolation_rate']}%  (→低)")
    print(f"    triggers持ち: {m['triggered_nodes']}ノード, "
          f"うち背景なし: {m['isolated_triggers']}")
    print(f"  平均背景本数: {m['avg_bg_per_trigger']}  (目安: 1-2)")
    print()
    print(f"  バイパス率: {m['bypass_rate']}%  (目安: ≤15%)")
    print(f"  推移的冗長率: {m['transitive_redundancy']}%  (目安: 5-15%)")
    print()
    print(f"  role比率:")
    total = sum(m["role_counts"].values())
    for role in ["amplifies", "transforms", "triggers", "sustains", "inherits"]:
        cnt = m["role_counts"].get(role, 0)
        print(f"    {role}: {cnt} ({cnt/total*100:.0f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="EnergyAbsグラフ品質指標"
    )
    parser.add_argument(
        "-i", "--input",
        default="data/energyabs_v2.json",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = load_data(args.input)
    m = calc_metrics(data)

    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
    else:
        print_report(m)


if __name__ == "__main__":
    main()
