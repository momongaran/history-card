#!/usr/bin/env python3
"""パターンインデックス生成: 各ノードが属するP-IDを算出し pattern_index.json に出力"""
import json
from collections import defaultdict

SYNONYMS = {
    '制度': '制度', '制度化': '制度', '制度構築': '制度',
    '武力衝突': '武力衝突', '戦闘': '武力衝突',
    '権力集中': '権力集中', '権力確立': '権力集中', '権力移行': '権力集中',
    '勢力対立': '勢力対立', '対立蓄積': '勢力対立',
    '外圧': '外圧', '外生': '外圧',
    '構造変化': '構造変化', '改革': '改革', '崩壊': '崩壊',
    '経済拡大': '経済圧', '経済成長': '経済圧', '経済圧': '経済圧',
    '硬直化': '制度疲弊', '制度疲弊': '制度疲弊',
    '制度的矛盾': '制度的矛盾', '思想潮流': '思想潮流',
    '複合背景': '複合背景', '権力分散': '権力分散', '自生': '自生',
    '外生衝撃': '外圧', '衝撃': '外圧', '蓄積': '勢力対立',
}

def norm(t):
    return SYNONYMS.get(t, t or '?')

SOURCES = [
    'data/energyabs_v2.json',
    'data/energyabs_europe_v1.json',
    'data/energyabs_middleeast_v1.json',
    'data/energyabs_india_v1.json',
    'data/energyabs_china_v1.json',
    'data/energyabs_americas_v1.json',
]

def build():
    all_nodes = {}
    all_edges = []

    for path in SOURCES:
        with open(path) as f:
            d = json.load(f)
        for n in d['nodes']:
            all_nodes[n['id']] = n
        all_edges.extend(d['edges'])

    # Build pattern groups (same logic as pattern catalog)
    groups = {}  # transKey -> { pairKey -> { instances: [...] } }
    for e in all_edges:
        src, tgt = all_nodes.get(e['from']), all_nodes.get(e['to'])
        if not src or not tgt:
            continue
        src_bg = norm(src.get('bgType', ''))
        src_rel = norm(src.get('releaseType', '') or src.get('bgType', ''))
        tgt_bg = norm(tgt.get('bgType', ''))
        tgt_rel = norm(tgt.get('releaseType', '') or tgt.get('bgType', ''))
        src_pt = src_bg + ('→' + src_rel if src.get('releaseType') else '')
        tgt_pt = tgt_bg + ('→' + tgt_rel if tgt.get('releaseType') else '')
        trans_key = src['fwType'] + '→' + tgt['fwType']
        pair_key = src_pt + '|||' + tgt_pt

        if trans_key not in groups:
            groups[trans_key] = {}
        if pair_key not in groups[trans_key]:
            groups[trans_key][pair_key] = {'instances': [], 'srcPT': src_pt, 'tgtPT': tgt_pt}
        groups[trans_key][pair_key]['instances'].append({
            'from': e['from'], 'to': e['to']
        })

    # Sort by frequency (same as pattern catalog) and assign P-IDs
    sorted_trans = sorted(groups.items(), key=lambda x: -sum(
        len(p['instances']) for p in x[1].values()
    ))

    pid_counter = 0
    node_to_pids = defaultdict(set)  # node_id -> set of P-IDs
    pid_catalog = {}  # P-ID -> { trans, srcPT, tgtPT, count }

    for trans_key, pairs in sorted_trans:
        pair_list = sorted(pairs.values(), key=lambda p: -len(p['instances']))
        for pair in pair_list:
            pid_counter += 1
            pid = f'P{pid_counter:03d}'
            pid_catalog[pid] = {
                'trans': trans_key,
                'srcPT': pair['srcPT'],
                'tgtPT': pair['tgtPT'],
                'count': len(pair['instances'])
            }
            for inst in pair['instances']:
                node_to_pids[inst['from']].add(pid)
                node_to_pids[inst['to']].add(pid)

    # Output
    output = {
        'nodeIndex': {nid: sorted(pids) for nid, pids in node_to_pids.items()},
        'patterns': pid_catalog
    }

    with open('data/pattern_index.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'Generated: {pid_counter} patterns, {len(node_to_pids)} nodes indexed')

if __name__ == '__main__':
    build()
