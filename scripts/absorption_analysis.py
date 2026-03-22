#!/usr/bin/env python3
"""
知識吸収の分析ツール
- エントロピー計測（マージ前後の比較）
- 構造的緊張分析（マージ前のソースとターゲットの関係）
- 変更履歴（マージ後の差分サマリ）
"""
import json
import math
import sys
from collections import Counter

def load(path):
    with open(path) as f:
        return json.load(f)

# ============================
# ② エントロピー計測
# ============================
def shannon_entropy(counts):
    """カウントリストからシャノンエントロピーを計算"""
    total = sum(counts)
    if total == 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)

def graph_entropy(data):
    """グラフの複数のエントロピー指標を計算"""
    nodes = data['nodes']
    edges = data['edges']

    # 1. fwType分布エントロピー
    fw_counts = Counter(n['fwType'] for n in nodes)
    fw_entropy = shannon_entropy(list(fw_counts.values()))

    # 2. edge role分布エントロピー
    role_counts = Counter(e['role'] for e in edges)
    role_entropy = shannon_entropy(list(role_counts.values()))

    # 3. 入次数分布エントロピー
    in_deg = Counter()
    for n in nodes:
        in_deg[n['id']] = 0
    for e in edges:
        in_deg[e['to']] += 1
    in_counts = Counter(in_deg.values())
    in_deg_entropy = shannon_entropy(list(in_counts.values()))

    # 4. 出次数分布エントロピー
    out_deg = Counter()
    for n in nodes:
        out_deg[n['id']] = 0
    for e in edges:
        out_deg[e['from']] += 1
    out_counts = Counter(out_deg.values())
    out_deg_entropy = shannon_entropy(list(out_counts.values()))

    # 5. bgType分布エントロピー
    bg_counts = Counter(n.get('bgType', '不明') for n in nodes)
    bg_entropy = shannon_entropy(list(bg_counts.values()))

    # 総合エントロピー（加重平均）
    composite = (fw_entropy + role_entropy + in_deg_entropy + out_deg_entropy + bg_entropy) / 5

    return {
        'fwType分布': {'entropy': fw_entropy, 'distribution': dict(fw_counts)},
        'edgeRole分布': {'entropy': role_entropy, 'distribution': dict(role_counts)},
        '入次数分布': {'entropy': in_deg_entropy, 'distribution': dict(in_counts)},
        '出次数分布': {'entropy': out_deg_entropy, 'distribution': dict(out_counts)},
        'bgType分布': {'entropy': bg_entropy, 'distribution': dict(bg_counts)},
        '総合エントロピー': composite,
        'ノード数': len(nodes),
        'エッジ数': len(edges),
        'E/N比': len(edges) / len(nodes) if nodes else 0
    }

def compare_entropy(before, after, source=None):
    """マージ前後のエントロピー比較"""
    ent_b = graph_entropy(before)
    ent_a = graph_entropy(after)

    print("=" * 70)
    print("② エントロピー比較")
    print("=" * 70)

    if source:
        ent_s = graph_entropy(source)
        print(f"\n【ソース】 {source['meta'].get('description','')[:60]}")
        print(f"  ノード: {ent_s['ノード数']}, エッジ: {ent_s['エッジ数']}, E/N比: {ent_s['E/N比']:.2f}")
        print(f"  総合エントロピー: {ent_s['総合エントロピー']:.3f}")

    print(f"\n{'指標':<20s} {'マージ前':>10s} {'マージ後':>10s} {'変化':>10s}")
    print("-" * 55)

    for key in ['fwType分布', 'edgeRole分布', '入次数分布', '出次数分布', 'bgType分布', '総合エントロピー']:
        if key == '総合エントロピー':
            vb, va = ent_b[key], ent_a[key]
        else:
            vb, va = ent_b[key]['entropy'], ent_a[key]['entropy']
        delta = va - vb
        sign = '+' if delta > 0 else ''
        print(f"  {key:<18s} {vb:>9.3f}  {va:>9.3f}  {sign}{delta:>8.3f}")

    print(f"\n  {'ノード数':<18s} {ent_b['ノード数']:>9d}  {ent_a['ノード数']:>9d}  +{ent_a['ノード数']-ent_b['ノード数']}")
    print(f"  {'エッジ数':<18s} {ent_b['エッジ数']:>9d}  {ent_a['エッジ数']:>9d}  +{ent_a['エッジ数']-ent_b['エッジ数']}")
    print(f"  {'E/N比':<18s} {ent_b['E/N比']:>9.2f}  {ent_a['E/N比']:>9.2f}  {ent_a['E/N比']-ent_b['E/N比']:>+8.2f}")

    return ent_b, ent_a

# ============================
# ③ 構造的緊張分析
# ============================
def structural_tension(target, source):
    """ソースとターゲット間の構造的緊張を分析"""
    t_nodes = {n['id']: n for n in target['nodes']}
    s_nodes = {n['id']: n for n in source['nodes']}

    t_edges = [(e['from'], e['to'], e['role']) for e in target['edges']]
    s_edges = [(e['from'], e['to'], e['role']) for e in source['edges']]

    # 時代の重複分析
    def parse_era_rough(era):
        """eraから大雑把な世紀を抽出"""
        import re
        nums = re.findall(r'(\d+)', era)
        if not nums:
            return set()
        centuries = set()
        for n in nums:
            n = int(n)
            if n > 100:
                centuries.add(n // 100)
            else:
                centuries.add(n)
        return centuries

    print("\n" + "=" * 70)
    print("③ 構造的緊張分析（マージ前）")
    print("=" * 70)

    # 3.1 時代の重複
    print("\n【時代的重複】")
    t_eras = {}
    for n in target['nodes']:
        cs = parse_era_rough(n['era'])
        for c in cs:
            t_eras.setdefault(c, []).append(n['id'])

    s_eras = {}
    for n in source['nodes']:
        cs = parse_era_rough(n['era'])
        for c in cs:
            s_eras.setdefault(c, []).append(n['id'])

    overlap_centuries = sorted(set(t_eras.keys()) & set(s_eras.keys()))
    for c in overlap_centuries:
        t_ids = t_eras[c]
        s_ids = s_eras[c]
        print(f"  {c}世紀: ターゲット{len(t_ids)}件 × ソース{len(s_ids)}件")

    # 3.2 fwType分布の乖離
    print("\n【fwType分布の乖離】")
    t_fw = Counter(n['fwType'] for n in target['nodes'])
    s_fw = Counter(n['fwType'] for n in source['nodes'])
    all_types = sorted(set(t_fw.keys()) | set(s_fw.keys()))

    t_total = sum(t_fw.values())
    s_total = sum(s_fw.values())

    kl_divergence = 0
    print(f"  {'fwType':<14s} {'ターゲット':>12s} {'ソース':>12s} {'差異':>8s}")
    print("  " + "-" * 50)
    for ft in all_types:
        t_pct = t_fw.get(ft, 0) / t_total * 100
        s_pct = s_fw.get(ft, 0) / s_total * 100
        diff = s_pct - t_pct
        print(f"  {ft:<14s} {t_pct:>10.1f}%  {s_pct:>10.1f}%  {diff:>+6.1f}%")
        # KLダイバージェンスの近似
        if s_fw.get(ft, 0) > 0 and t_fw.get(ft, 0) > 0:
            p = s_fw[ft] / s_total
            q = t_fw[ft] / t_total
            kl_divergence += p * math.log2(p / q)

    print(f"\n  KLダイバージェンス（ソース||ターゲット）: {kl_divergence:.3f}")
    print(f"  （0に近いほど分布が類似、大きいほど視点が異なる）")

    # 3.3 接続候補（重複ノードの推定）
    print("\n【意味的重複候補】")
    overlap_count = 0
    for s_id, s_node in s_nodes.items():
        s_label = s_node['label']
        s_era_set = parse_era_rough(s_node['era'])
        for t_id, t_node in t_nodes.items():
            t_era_set = parse_era_rough(t_node['era'])
            # 時代が重なり、fwTypeまたはactorsが一致
            if s_era_set & t_era_set:
                common_actors = set(s_node.get('actors', [])) & set(t_node.get('actors', []))
                if common_actors or s_node['fwType'] == t_node['fwType']:
                    if common_actors:
                        overlap_count += 1
                        print(f"  {s_id}({s_label[:20]}) ↔ {t_id}({t_node['label'][:20]})")
                        print(f"    共通actors: {common_actors}, fwType: {s_node['fwType']}/{t_node['fwType']}")

    if overlap_count == 0:
        print("  共通actorsによる重複候補なし")

    # 3.4 歪み予測（新規ノードが既存構造に与える影響）
    print("\n【歪み予測】")
    # ソースのノードが接続されうる既存ノードの「ハブ度」を推定
    t_in_deg = Counter(e['to'] for e in target['edges'])
    t_out_deg = Counter(e['from'] for e in target['edges'])

    # ソースのeraと重なるターゲットノードのうち、エッジが多いものが影響を受けやすい
    vulnerable = []
    for t_id, t_node in t_nodes.items():
        t_era_set = parse_era_rough(t_node['era'])
        for s_node in source['nodes']:
            s_era_set = parse_era_rough(s_node['era'])
            if s_era_set & t_era_set:
                deg = t_in_deg.get(t_id, 0) + t_out_deg.get(t_id, 0)
                vulnerable.append((t_id, t_node['label'], deg))
                break

    vulnerable = sorted(set(vulnerable), key=lambda x: -x[2])[:10]
    print(f"  マージ影響を受けうるハブノード（時代重複×次数順）:")
    for t_id, label, deg in vulnerable:
        print(f"    {t_id} (次数{deg}) {label[:30]}")

    return overlap_count, kl_divergence

# ============================
# ④ 変更履歴サマリ
# ============================
def change_summary(before, after):
    """マージ前後の構造変化をサマリ"""
    b_nodes = {n['id']: n for n in before['nodes']}
    a_nodes = {n['id']: n for n in after['nodes']}

    b_edges = {(e['from'], e['to']): e for e in before['edges']}
    a_edges = {(e['from'], e['to']): e for e in after['edges']}

    print("\n" + "=" * 70)
    print("④ 変更履歴（マージによる構造変化）")
    print("=" * 70)

    # 新規ノード
    new_ids = set(a_nodes.keys()) - set(b_nodes.keys())
    if new_ids:
        print(f"\n【新規ノード】{len(new_ids)}件")
        for nid in sorted(new_ids):
            n = a_nodes[nid]
            print(f"  + {nid} [{n['fwType']}] {n['label']} ({n['era']})")

    # 削除ノード
    del_ids = set(b_nodes.keys()) - set(a_nodes.keys())
    if del_ids:
        print(f"\n【削除ノード】{len(del_ids)}件")
        for nid in sorted(del_ids):
            n = b_nodes[nid]
            print(f"  - {nid} [{n['fwType']}] {n['label']}")

    # 変更ノード（summary変更）
    mod_nodes = []
    for nid in set(b_nodes.keys()) & set(a_nodes.keys()):
        if b_nodes[nid].get('summary') != a_nodes[nid].get('summary'):
            mod_nodes.append(nid)
        elif b_nodes[nid].get('absorbed', []) != a_nodes[nid].get('absorbed', []):
            mod_nodes.append(nid)
    if mod_nodes:
        print(f"\n【加筆ノード】{len(mod_nodes)}件")
        for nid in sorted(mod_nodes):
            n = a_nodes[nid]
            changes = []
            if b_nodes[nid].get('summary') != n.get('summary'):
                changes.append('summary加筆')
            b_abs = len(b_nodes[nid].get('absorbed', []))
            a_abs = len(n.get('absorbed', []))
            if b_abs != a_abs:
                changes.append(f'absorbed {b_abs}→{a_abs}')
            print(f"  ~ {nid} {n['label'][:30]} [{", ".join(changes)}]")

    # 新規エッジ
    new_edges = set(a_edges.keys()) - set(b_edges.keys())
    if new_edges:
        print(f"\n【新規エッジ】{len(new_edges)}件")
        for (frm, to) in sorted(new_edges):
            e = a_edges[(frm, to)]
            frm_label = a_nodes.get(frm, {}).get('label', frm)[:15]
            to_label = a_nodes.get(to, {}).get('label', to)[:15]
            print(f"  + {frm}({frm_label}) --{e['role']}--> {to}({to_label})")

    # ロール変更エッジ
    role_changes = []
    for key in set(b_edges.keys()) & set(a_edges.keys()):
        if b_edges[key]['role'] != a_edges[key]['role']:
            role_changes.append((key, b_edges[key]['role'], a_edges[key]['role']))
    if role_changes:
        print(f"\n【ロール変更エッジ】{len(role_changes)}件")
        for (frm, to), old_role, new_role in role_changes:
            print(f"  Δ {frm}→{to}: {old_role} → {new_role}")

    # サマリ
    print(f"\n【変更サマリ】")
    print(f"  新規ノード: {len(new_ids)}, 削除ノード: {len(del_ids)}, 加筆ノード: {len(mod_nodes)}")
    print(f"  新規エッジ: {len(new_edges)}, ロール変更: {len(role_changes)}")
    print(f"  構造歪み度: {len(role_changes)/len(b_edges)*100:.1f}% (目標≤5%)")

# ============================
# メイン
# ============================
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python3 absorption_analysis.py <before.json> <after.json> [source.json]")
        print()
        print("  before.json:  マージ前のターゲットグラフ")
        print("  after.json:   マージ後のターゲットグラフ")
        print("  source.json:  ソース（単体FW）[省略可]")
        sys.exit(1)

    before = load(sys.argv[1])
    after = load(sys.argv[2])
    source = load(sys.argv[3]) if len(sys.argv) > 3 else None

    # ②
    compare_entropy(before, after, source)

    # ③
    if source:
        structural_tension(before, source)

    # ④
    change_summary(before, after)
