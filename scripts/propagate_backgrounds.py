#!/usr/bin/env python3
"""
propagate_backgrounds.py — 背景エネルギー伝播の**検証**スクリプト

EnergyAbsモデルの構造的原則:
  中間ノードは複数の構造的条件を特定の形に「合成」する。
  合成後の出力がターゲットに到達するのであって、
  原料が直接ターゲットに流れるわけではない。

  したがって自動的なエッジ追加は行わない。

  このスクリプトは以下の検証を行う:
  1. triggersエッジで単一入力しかないノードの検出（UI上で背景が薄く見える箇所）
  2. そのトリガーソースの背景の深さを表示
  → UIでの「展開表示」の候補リストを出力する

使い方:
  python3 scripts/propagate_backgrounds.py                  # 検証レポート
  python3 scripts/propagate_backgrounds.py -i other.json    # 別データ
  python3 scripts/propagate_backgrounds.py --json           # JSON出力（UI連携用）

設計:
  - 任意のEnergyAbsデータに適用可能（日本史・世界史問わず）
  - エッジの追加・変更は一切行わない（読み取り専用）
  - UI側で「展開表示」に使えるデータを生成する
"""

import json
import argparse
import sys
from collections import defaultdict


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_index(data: dict) -> tuple:
    """ノード辞書とエッジインデックスを構築"""
    nodes = {n["id"]: n for n in data["nodes"]}
    edges_to = defaultdict(list)
    edges_from = defaultdict(list)
    for e in data["edges"]:
        edges_to[e["to"]].append(e)
        edges_from[e["from"]].append(e)
    return nodes, edges_to, edges_from


def trace_backgrounds(node_id: str, edges_to: dict, depth: int = 0,
                      max_depth: int = 3, visited: set = None) -> list:
    """
    ノードの背景を再帰的にトレースする。
    Returns: list of {id, label, role, depth, path}
    """
    if visited is None:
        visited = set()
    if depth >= max_depth or node_id in visited:
        return []

    visited.add(node_id)
    results = []

    for e in edges_to.get(node_id, []):
        results.append({
            "id": e["from"],
            "role": e["role"],
            "depth": depth,
            "edge_id": e["id"],
        })
        # 再帰: amplifies/sustains の背景をさらに遡る
        if e["role"] in ("amplifies", "sustains"):
            deeper = trace_backgrounds(
                e["from"], edges_to, depth + 1, max_depth, visited
            )
            results.extend(deeper)

    return results


def find_thin_nodes(data: dict) -> list:
    """
    背景が薄く見えるノード（triggers単一入力）を検出し、
    トリガーソースの背景深度情報を付与する。
    """
    nodes, edges_to, edges_from = build_index(data)
    thin_nodes = []

    for n in data["nodes"]:
        nid = n["id"]
        incoming = edges_to[nid]

        if len(incoming) > 2:
            continue

        # triggersエッジが含まれているか
        trigger_edges = [e for e in incoming if e["role"] == "triggers"]
        if not trigger_edges:
            continue

        for t_edge in trigger_edges:
            src_id = t_edge["from"]
            src_incoming = edges_to[src_id]

            if len(src_incoming) < 2:
                continue

            # トリガーソースの背景をトレース
            bg_trace = trace_backgrounds(src_id, edges_to, depth=0, max_depth=3)

            thin_nodes.append({
                "node_id": nid,
                "node_label": n["label"],
                "existing_inputs": len(incoming),
                "trigger_source": {
                    "id": src_id,
                    "label": nodes[src_id]["label"],
                    "input_count": len(src_incoming),
                },
                "deep_backgrounds": [
                    {
                        "id": bg["id"],
                        "label": nodes[bg["id"]]["label"],
                        "role": bg["role"],
                        "depth": bg["depth"],
                    }
                    for bg in bg_trace
                ],
            })

    return thin_nodes


def print_report(thin_nodes: list, nodes: dict):
    """検出結果のレポート表示"""
    print(f"\n{'='*60}")
    print(f"背景展開候補ノード（UIで深層背景を表示すべき箇所）")
    print(f"{'='*60}")
    print(f"  候補数: {len(thin_nodes)}")
    print()

    for tn in thin_nodes:
        print(f"  {tn['node_id']} {tn['node_label']} "
              f"(入力: {tn['existing_inputs']}本)")
        ts = tn["trigger_source"]
        print(f"    triggers← {ts['id']} ({ts['label']}) "
              f"[背景{ts['input_count']}本]")

        for bg in tn["deep_backgrounds"]:
            indent = "      " + "  " * bg["depth"]
            print(f"{indent}{'└' if bg['depth'] > 0 else '├'} "
                  f"{bg['id']} ({bg['label']}) [{bg['role']}]")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="EnergyAbsモデルの背景深度検証（読み取り専用）"
    )
    parser.add_argument(
        "-i", "--input",
        default="data/energyabs_v2.json",
        help="入力JSONファイル (default: data/energyabs_v2.json)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力（UI連携用）",
    )
    args = parser.parse_args()

    data = load_data(args.input)
    nodes = {n["id"]: n for n in data["nodes"]}
    n_nodes = len(data["nodes"])
    n_edges = len(data["edges"])
    print(f"入力: {args.input}")
    print(f"  ノード: {n_nodes}, エッジ: {n_edges}")

    thin_nodes = find_thin_nodes(data)

    if args.json:
        print(json.dumps(thin_nodes, ensure_ascii=False, indent=2))
    else:
        print_report(thin_nodes, nodes)


if __name__ == "__main__":
    main()
