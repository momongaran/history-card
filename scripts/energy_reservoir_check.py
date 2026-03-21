#!/usr/bin/env python3
"""エネルギーだまり診断ツール

解放型ノード(battle/collapse/reform/power/shock)に対して
蓄積型(drift/conflict)からの入力があるかを検査する。

使い方:
  python3 scripts/energy_reservoir_check.py data/energyabs_europe_v1.json
  python3 scripts/energy_reservoir_check.py data/energyabs_v2.json
"""
import json, sys
from collections import Counter

def check(path):
    with open(path) as f:
        d = json.load(f)

    NM = {n['id']: n for n in d['nodes']}
    edges_to = {}
    for e in d['edges']:
        edges_to.setdefault(e['to'], []).append(e)

    RELEASE_TYPES = {'battle', 'collapse', 'reform', 'power', 'shock'}
    ACCUM_TYPES = {'drift', 'conflict'}

    issues_severe = []
    issues_mild = []

    for n in d['nodes']:
        nid = n['id']
        incoming = edges_to.get(nid, [])
        if len(incoming) == 0:
            continue

        problems = []
        incoming_details = []

        for e in incoming:
            src = NM.get(e['from'])
            src_fw = src['fwType'] if src else '?'
            incoming_details.append(f"  {e['from']}({src_fw}) --{e['role']}-->")

        if n['fwType'] in RELEASE_TYPES:
            has_accum = any(NM.get(e['from'], {}).get('fwType') in ACCUM_TYPES for e in incoming)
            has_bg_role = any(e['role'] in ('amplifies', 'sustains') for e in incoming)

            if not has_accum:
                problems.append("蓄積型(drift/conflict)からの入力なし")
            if not has_bg_role:
                problems.append("amplifies/sustainsなし(triggersのみ)")
        else:
            roles = [e['role'] for e in incoming]
            if all(r == 'triggers' for r in roles) and len(roles) <= 1:
                problems.append("入力がtriggers×1のみ — 背景圧力が不明")

        if problems:
            entry = (nid, n['label'], n['fwType'], problems, incoming_details)
            if len(problems) >= 2:
                issues_severe.append(entry)
            else:
                issues_mild.append(entry)

    # Output
    print("=" * 80)
    print(f"エネルギーだまり診断: {path}")
    print(f"  ノード: {len(d['nodes'])}, エッジ: {len(d['edges'])}")
    print("=" * 80)

    for severity_label, issue_list in [("🔴 重度", issues_severe), ("🟡 軽度", issues_mild)]:
        if not issue_list:
            continue
        print(f"\n--- {severity_label} ({len(issue_list)}件) ---")
        for nid, name, fwt, probs, details in issue_list:
            print(f"\n{nid} {name} [{fwt}]")
            for p in probs:
                print(f"  問題: {p}")
            for det in details:
                print(f"  {det}")

    total = len(issues_severe) + len(issues_mild)
    n_nodes = len(d['nodes'])
    pct = total / n_nodes * 100 if n_nodes else 0
    print(f"\n{'=' * 80}")
    print(f"診断結果: {total}/{n_nodes}件 ({pct:.0f}%) にエネルギーだまり不足の疑い")
    print(f"  🔴 重度: {len(issues_severe)}")
    print(f"  🟡 軽度: {len(issues_mild)}")

    return issues_severe, issues_mild

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/energyabs_europe_v1.json'
    check(path)
