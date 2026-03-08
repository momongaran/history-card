#!/usr/bin/env python3
"""
v3.9 ドラフト生成スクリプト

v3.8データ + BGグルーピング結果を使い、v3.9形式のドラフトを生成する。
- 各イベントのB要素をBG参照 + エネルギーB に変換
- eGeneratesをドラフト生成（隣接イベントのBG変化から推定）
- 人間レビュー必須のドラフト出力

Usage: python3 scripts/build_v39_draft.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
V38_FILE = ROOT / "archive" / "data" / "framework_output_v3_8.json"
CORR_FILE = ROOT / "archive" / "data" / "default_correspondences_v3_8.json"
BG_FILE = ROOT / "archive" / "data" / "v3_9_bg_candidates.json"
PATTERNS_FILE = ROOT / "data" / "v3_9_causal_patterns.json"
OUT_FILE = ROOT / "archive" / "data" / "v3_9_full_draft.json"
REPORT_FILE = ROOT / "archive" / "data" / "v3_9_full_draft_report.md"

# Causal pattern role definitions
# Each pattern defines how B and F should be interpreted
PATTERN_ROLES = {
    'A_pressure_release': {
        'B_role': 'pressure',        # B = 蓄積された圧力
        'F_role': 'trigger',         # F = 引き金
        'E_role': 'release',         # E = 解放
    },
    'B_deliberate_action': {
        'B_role': 'situation',       # B = 状況認知・条件
        'F_role': 'judgment',        # F = 判断・意思決定
        'E_role': 'action_outcome',  # E = 行為の帰結
    },
    'C_exogenous_shock': {
        'B_role': 'receiving_state', # B = 衝撃を受ける側の状態
        'F_role': 'shock',           # F = 外部からの衝撃
        'E_role': 'adaptation',      # E = 適応・対応結果
    },
    'D_contradiction_exposure': {
        'B_role': 'latent_contradiction',  # B = 潜在的矛盾
        'F_role': 'exposure_trigger',      # F = 矛盾が顕在化する契機
        'E_role': 'structural_change',     # E = 構造変化
    },
    'E_power_transition': {
        'B_role': 'power_vacuum',    # B = 権力空白・前体制の状態
        'F_role': 'succession',      # F = 後継手続・争い
        'E_role': 'new_regime',      # E = 新体制の成立
    },
    'F_contingency': {
        'B_role': 'vulnerability',   # B = システムの脆弱性
        'F_role': 'accident',        # F = 偶発事象
        'E_role': 'cascade_result',  # E = 連鎖反応の帰結
    },
    'X_unclassified': {
        'B_role': 'background',
        'F_role': 'catalyst',
        'E_role': 'outcome',
    },
}

# Import entity extraction from grouping script
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import sys
sys.path.insert(0, str(ROOT / "archive" / "scripts"))
from group_bg_elements import ENTITY_PATTERNS, ENERGY_RE, MERGE_RULES, EXCLUDE_LABELS

# Effect inference keywords
EFFECT_KEYWORDS = {
    'generate': [
        r'制定|成立|確立|開始|創設|設置|導入|発布|施行|公布|制度化|法制化|完成|整備',
        r'新た[なに]|初めて|創始|建設|樹立|開設|設立|発足|誕生',
    ],
    'reinforce': [
        r'強化|拡大|発展|充実|促進|推進|加速|深化|定着|普及|浸透|拡充|増強',
        r'立て直し|再建|復興|再整備|安定|確認|確保|維持',
    ],
    'erode': [
        r'弱体|衰退|形骸|崩壊|動揺|後退|縮小|制限|制約|損[なう]|低下|失墜',
        r'侵食|圧迫|浸食|空洞|骨抜き|有名無実',
    ],
    'terminate': [
        r'廃止|終了|消滅|解体|撤廃|廃絶|断絶|崩壊|終焉|滅亡|壊滅',
        r'放棄|否定|破棄|取消|無効',
    ],
    'redirect': [
        r'変質|変容|転換|改変|再編|組替|方向転換|修正|調整|整理',
        r'抑制|牽制|規制|統制|管理',
    ],
}
EFFECT_COMPILED = {
    eff: re.compile('|'.join(patterns))
    for eff, patterns in EFFECT_KEYWORDS.items()
}


def extract_entities_for_element(label, sort_key=0):
    """B要素のlabelからBG候補を抽出"""
    matches = []
    for priority, pattern, bg_type, bg_label in ENTITY_PATTERNS:
        if re.search(pattern, label):
            matches.append((priority, bg_type, bg_label))

    if not matches:
        return []

    merged = []
    for pri, bg_type, bg_label in matches:
        canonical = MERGE_RULES.get(bg_label, bg_label)
        if canonical is not None:
            merged.append((pri, bg_type, canonical))

    if not merged:
        return []

    best = {}
    for pri, bg_type, bg_label in merged:
        if bg_label not in best or pri > best[bg_label][0]:
            best[bg_label] = (pri, bg_type)

    max_pri = max(v[0] for v in best.values())
    if max_pri >= 3:
        best = {k: v for k, v in best.items() if v[0] >= 2}
    elif max_pri >= 2:
        best = {k: v for k, v in best.items() if v[0] >= 1}

    if '藤原氏' in best and sort_key > 0:
        if sort_key < 800:
            best['藤原氏(奈良)'] = best.pop('藤原氏')
        elif sort_key < 1200:
            best['摂関家(藤原氏)'] = best.pop('藤原氏')

    return [bg_label for bg_label in best if bg_label not in EXCLUDE_LABELS]


def infer_effect(e_label, bg_label):
    """E要素のlabelとBGラベルからeffectを推定"""
    combined = e_label + ' ' + bg_label
    scores = {}
    for eff, pattern in EFFECT_COMPILED.items():
        matches = pattern.findall(combined)
        scores[eff] = len(matches)

    if max(scores.values()) == 0:
        return 'reinforce'  # default

    return max(scores, key=scores.get)


def synthesize_energy_label(bg_labels, event_title, f_labels, structure_b_labels):
    """B要素のlabelを合成する。

    戦略: F(trigger)の内容 + 構造B要素のキーワードから力学表現を生成
    """
    # F要素+タイトルから圧の種類を推定
    pressure_type = ''
    f_text = ' '.join(f_labels) + ' ' + event_title
    if re.search(r'死|崩御|断絶|不在|空[白位]|子がな|滅亡|消滅|失脚', f_text):
        pressure_type = '権力空白の圧'
    elif re.search(r'専権|独占|排斥|弾圧|抑圧|暗殺|謀反|讒言|陰謀', f_text):
        pressure_type = '専権への反発圧'
    elif re.search(r'失敗|破綻|崩壊|限界|行き詰|機能不全|不安定', f_text):
        pressure_type = '制度的行き詰まりの圧'
    elif re.search(r'侵攻|脅威|圧迫|攻撃|進出|襲来|再襲|来航|上陸|開国|来日|伝来', f_text):
        pressure_type = '外圧への対応圧'
    elif re.search(r'改革|転換|刷新|変革|遷都|改新|改正|改元', f_text):
        pressure_type = '秩序再編の圧'
    elif re.search(r'対立|争|衝突|分裂|内紛|交戦|戦い|乱|変|役', f_text):
        pressure_type = '対立・衝突の圧'
    elif re.search(r'編纂|成立|造営|制度化|公布|施行|開設', f_text):
        pressure_type = '制度整備の必要'
    elif re.search(r'震災|地震|津波|災害|大火', f_text):
        pressure_type = '災害への対応圧'
    elif re.search(r'占領|降伏|受諾|終戦', f_text):
        pressure_type = '体制転換の圧'
    elif re.search(r'統制|管理|禁止|追放|鎖国', f_text):
        pressure_type = '秩序維持の圧'
    elif re.search(r'即位|就任|摂政|将軍|開府|征夷', f_text):
        pressure_type = '権力移行の圧'
    elif re.search(r'鋳造|造営|建立|整理|田文|編纂|成立', f_text):
        pressure_type = '制度整備の圧'
    elif re.search(r'追放|左遷|流罪', f_text):
        pressure_type = '政治排除の圧'
    elif re.search(r'令|法|条例|法度', f_text):
        pressure_type = '法的統制の圧'

    # 構造B要素から具体的な状況キーワードを抽出
    b_text = ' '.join(structure_b_labels)
    situation = ''
    if re.search(r'専権|実権|主導|支配|掌握', b_text):
        situation = '権力集中'
    elif re.search(r'皇位|後継|継承|跡目', b_text):
        situation = '継承問題'
    elif re.search(r'疲弊|困窮|負担|飢|疫', b_text):
        situation = '社会疲弊'
    elif re.search(r'軍事|兵|武力|動員', b_text):
        situation = '軍事的緊張'
    elif re.search(r'貿易|交易|経済|商', b_text):
        situation = '経済変動'

    # 組み合わせてラベル生成
    if pressure_type and situation:
        base = f"{situation}のもとでの{pressure_type}"
    elif pressure_type:
        base = pressure_type
    elif situation:
        base = f"{situation}に起因する構造的緊張"
    else:
        # フォールバック: イベントタイトルから圧を推定
        base = f"{event_title}を生む構造的条件の圧"

    # BG名を括弧で付記
    if bg_labels:
        bg_note = '・'.join(bg_labels[:3])
        return f"{base}（{bg_note}の複合）"
    return base


def build_v39_draft():
    with open(V38_FILE) as f:
        v38 = json.load(f)
    with open(BG_FILE) as f:
        bg_data = json.load(f)

    # Load causal patterns
    pattern_map = {}
    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE) as f:
            patterns_data = json.load(f)
        for ev in patterns_data['events']:
            pattern_map[ev['eventId']] = ev['causalPattern']
        print(f'Loaded {len(pattern_map)} causal pattern assignments')
    else:
        print('WARNING: No causal patterns file found, all events will be X_unclassified')

    # Build BG lookup: label -> bgId
    bg_lookup = {}
    bg_by_id = {}
    for bg in bg_data['bgCandidates']:
        bg_lookup[bg['label']] = bg['bgId']
        bg_by_id[bg['bgId']] = bg

    # Build event info
    event_info = {}
    for fw in v38['frameworkViews']:
        event_info[fw['eventId']] = {
            'title': fw['title'],
            'sortKey': fw['sortKey'],
            'era': fw.get('era', ''),
        }

    # Process each event
    v39_views = []
    stats = {
        'total_events': 0,
        'events_with_energy_b': 0,
        'events_needing_b_synthesis': 0,
        'total_e_generates': 0,
        'events_without_e_generates': 0,
    }

    for fw in v38['frameworkViews']:
        eid = fw['eventId']
        sort_key = fw['sortKey']
        stats['total_events'] += 1

        # Extract E and F (keep as-is)
        e_elements = []
        f_elements = []
        b_elements_raw = []
        for el in fw['elements']:
            if el['layer'] == 'E':
                e_elements.append({
                    'code': el.get('category', '') + '-' + el.get('subCategory', ''),
                    'label': el['label'],
                })
            elif el['layer'] == 'F':
                f_elements.append({
                    'code': el.get('category', '') + '-' + el.get('subCategory', ''),
                    'label': el['label'],
                })
            elif el['layer'] == 'B':
                b_elements_raw.append(el)

        # Classify each B element
        energy_bs = []  # will become B in v3.9
        structure_bs = []  # will be mapped to BGs
        event_bg_refs = set()  # all BG labels referenced by this event

        for b_el in b_elements_raw:
            is_energy = bool(ENERGY_RE.search(b_el['label']))
            bg_labels = extract_entities_for_element(b_el['label'], sort_key)

            if is_energy:
                # This is an energy B — find its contributing BGS
                contributing = []
                for bl in bg_labels:
                    if bl in bg_lookup:
                        contributing.append(bg_lookup[bl])
                        event_bg_refs.add(bl)

                # If no BGs found from label, try co-occurrence with other B elements
                if not contributing:
                    for other_b in b_elements_raw:
                        if other_b is not b_el:
                            other_bgs = extract_entities_for_element(other_b['label'], sort_key)
                            for obl in other_bgs:
                                if obl in bg_lookup:
                                    contributing.append(bg_lookup[obl])
                                    event_bg_refs.add(obl)

                contributing = list(dict.fromkeys(contributing))  # dedup preserving order
                energy_bs.append({
                    'label': b_el['label'],
                    'contributingBG': contributing[:4],  # max 4
                    'note': '',
                    '_original_id': b_el['elementId'],
                    '_needs_review': len(contributing) == 0,
                })
            else:
                # Structure B — maps to BG
                for bl in bg_labels:
                    if bl in bg_lookup:
                        event_bg_refs.add(bl)
                structure_bs.append({
                    'label': b_el['label'],
                    'mapped_bgs': bg_labels,
                    '_original_id': b_el['elementId'],
                })

        # If no energy B found, synthesize one from structure BGS
        if not energy_bs:
            stats['events_needing_b_synthesis'] += 1
            all_bg_ids = []
            all_bg_labels = []
            for sb in structure_bs:
                for bl in sb['mapped_bgs']:
                    if bl in bg_lookup and bg_lookup[bl] not in all_bg_ids:
                        all_bg_ids.append(bg_lookup[bl])
                        all_bg_labels.append(bl)

            f_labels = [f['label'] for f in f_elements]
            struct_b_labels = [sb['label'] for sb in structure_bs]

            if all_bg_ids:
                synth_label = synthesize_energy_label(
                    all_bg_labels[:3], fw['title'], f_labels, struct_b_labels)
                energy_bs.append({
                    'label': synth_label,
                    'contributingBG': all_bg_ids[:4],
                    'note': '自動合成: 要レビュー',
                    '_synthesized': True,
                    '_needs_review': True,
                })
            else:
                energy_bs.append({
                    'label': f"（{fw['title']}の背景圧 — BG未特定）",
                    'contributingBG': [],
                    'note': '自動合成失敗: BGマッピングなし',
                    '_synthesized': True,
                    '_needs_review': True,
                })
        else:
            stats['events_with_energy_b'] += 1

        # Generate eGenerates
        e_generates = []
        all_event_bg_labels = set(event_bg_refs)

        # Also extract BGS from E and F labels
        for el_list in [e_elements, f_elements]:
            for el in el_list:
                e_bgs = extract_entities_for_element(el['label'], sort_key)
                for bl in e_bgs:
                    if bl in bg_lookup:
                        all_event_bg_labels.add(bl)

        # Also extract from event title
        title_bgs = extract_entities_for_element(fw['title'], sort_key)
        for bl in title_bgs:
            if bl in bg_lookup:
                all_event_bg_labels.add(bl)

        if e_elements and all_event_bg_labels:
            e_label = e_elements[0]['label']  # primary E
            for bl in all_event_bg_labels:
                if bl in bg_lookup:
                    effect = infer_effect(e_label, bl)
                    e_generates.append({
                        'targetBG': bg_lookup[bl],
                        'effect': effect,
                        'description': f"（{effect}の推定: 要レビュー）",
                        '_needs_review': True,
                    })
                    stats['total_e_generates'] += 1

        if not e_generates:
            stats['events_without_e_generates'] += 1

        # Determine causal pattern
        cp = pattern_map.get(eid, 'X_unclassified')
        roles = PATTERN_ROLES.get(cp, PATTERN_ROLES['X_unclassified'])

        # Build v3.9 view
        v39_view = {
            'eventId': eid,
            'title': fw['title'],
            'year': sort_key,
            'causalPattern': cp,
            'causalFramework': {
                'E': e_elements,
                'F': f_elements,
                'B': energy_bs,
                'patternRoles': {
                    'B_role': roles['B_role'],
                    'F_role': roles['F_role'],
                    'E_role': roles['E_role'],
                },
            },
            'eGenerates': e_generates,
            '_structureBs_mapped': [
                {'label': sb['label'][:60], 'bgs': sb['mapped_bgs']}
                for sb in structure_bs
            ],
        }
        v39_views.append(v39_view)

    # Build backgroundElements from BG candidates
    background_elements = []
    for bg in bg_data['bgCandidates']:
        background_elements.append({
            'bgId': bg['bgId'],
            'type': bg['type'],
            'label': bg['label'],
            'description': '',
            'generatedBy': None,
            'effectLog': [],
            'phases': [],
            '_eventCount': bg['eventCount'],
            '_yearRange': bg['yearRange'],
        })

    # Causal pattern stats
    from collections import Counter
    pattern_dist = Counter(v['causalPattern'] for v in v39_views)
    stats['causal_patterns'] = dict(sorted(pattern_dist.items()))

    # Output
    output = {
        '_meta': {
            'description': 'v3.9 全件ドラフト（自動変換、人間レビュー必須）',
            'date': '2026-03-08',
            'source': 'framework_output_v3_8.json + v3_9_bg_candidates.json + v3_9_causal_patterns.json',
            'stats': stats,
            'patternRoleDefinitions': PATTERN_ROLES,
        },
        'backgroundElements': background_elements,
        'frameworkViews': v39_views,
    }

    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Report
    needs_review = sum(
        1 for v in v39_views
        if any(b.get('_needs_review') for b in v['causalFramework']['B'])
    )
    eg_needs_review = sum(
        1 for v in v39_views
        if any(eg.get('_needs_review') for eg in v['eGenerates'])
    )

    lines = [
        '# v3.9 全件ドラフト変換レポート',
        '',
        '## 統計',
        '',
        f"- 総イベント数: {stats['total_events']}",
        f"- v3.8からエネルギーB抽出成功: {stats['events_with_energy_b']}",
        f"- B合成が必要だった: {stats['events_needing_b_synthesis']}",
        f"- eGenerates総数: {stats['total_e_generates']}",
        f"- eGeneratesなし: {stats['events_without_e_generates']}",
        f"- Bレビュー必要: {needs_review}件",
        f"- eGeneratesレビュー必要: {eg_needs_review}件",
        f"- BG要素数: {len(background_elements)}",
        '',
        '## 因果パターン分布',
        '',
    ]
    pattern_names = {
        'A_pressure_release': '圧力解放型',
        'B_deliberate_action': '主体的行為型',
        'C_exogenous_shock': '外生衝撃型',
        'D_contradiction_exposure': '矛盾露呈型',
        'E_power_transition': '権力移行型',
        'F_contingency': '偶発連鎖型',
        'X_unclassified': '未分類',
    }
    for pat, count in sorted(pattern_dist.items()):
        name = pattern_names.get(pat, pat)
        lines.append(f"- {pat} ({name}): {count}件")
    lines += [
        '',
        '## レビュー必要なイベント（B合成）',
        '',
    ]

    for v in v39_views:
        synth = [b for b in v['causalFramework']['B'] if b.get('_synthesized')]
        if synth:
            lines.append(f"### {v['eventId']} ({v['year']}) {v['title']}")
            for b in synth:
                lines.append(f"  - B: {b['label']}")
                lines.append(f"    contributingBG: {b['contributingBG']}")
            lines.append('')

    # Sample of good conversions
    lines += [
        '',
        '## 変換サンプル（最初の5件）',
        '',
    ]
    for v in v39_views[:5]:
        lines.append(f"### {v['eventId']} ({v['year']}) {v['title']}")
        for b in v['causalFramework']['B']:
            review = ' ⚠️REVIEW' if b.get('_needs_review') else ''
            lines.append(f"  B: {b['label']}{review}")
            lines.append(f"    contributingBG: {b['contributingBG']}")
        for eg in v['eGenerates']:
            lines.append(f"  eGen: {eg['targetBG']} → {eg['effect']}")
        lines.append('')

    report = '\n'.join(lines)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f'Output: {OUT_FILE}')
    print(f'Report: {REPORT_FILE}')
    print(f'Events: {stats["total_events"]}')
    print(f'Energy B found: {stats["events_with_energy_b"]}')
    print(f'B synthesis needed: {stats["events_needing_b_synthesis"]}')
    print(f'eGenerates: {stats["total_e_generates"]}')
    print(f'No eGenerates: {stats["events_without_e_generates"]}')
    print(f'BG elements: {len(background_elements)}')
    print(f'Causal patterns: {dict(sorted(pattern_dist.items()))}')


if __name__ == '__main__':
    build_v39_draft()
