#!/usr/bin/env python3
"""
v3.9ドラフトへの手動修正適用スクリプト

build_v39_draft.py の出力に対して、人間レビュー済みの修正を適用する。
build後に毎回実行すること。

Usage: python3 scripts/apply_manual_fixes.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DRAFT_FILE = ROOT / "archive" / "data" / "v3_9_full_draft.json"

# ===== B Synthesis Fixes =====
# eventId -> fixed label
B_LABEL_FIXES = {
    'EV_p0647_01': '律令的賦役制度による農民への過重負担の圧（班田収授制・租税・財政・防衛体制の複合）',
    'EV_p0792_01': '軍団制の機能不全と辺境防衛の圧（東北/蝦夷の複合）',
    'EV_p0897_01': '摂関政治への対抗として天皇親政を志向する圧（摂関家(藤原氏)・律令制の複合）',
    'EV_p1086_01': '摂関家の権力独占に対する天皇家の対抗圧（摂関家(藤原氏)・院政体制の複合）',
    'EV_p1184_01': '武士勢力の台頭と院政権力の動揺（摂関家(藤原氏)・院政体制の複合）',
    'EV_p1392_01': '南朝の軍事的衰退による南北朝並立の維持不能圧（南北朝分裂・正統性・権威の複合）',
    'EV_p1576_01': '天下統一事業における拠点整備の必要（織田政権の複合）',
    'EV_p1614_01': '豊臣勢力の残存に対する権力統合の圧（豊臣家問題・豊臣政権・浪人問題の複合）',
    'EV_p1688_01': '泰平下の経済成長と町人文化隆盛の勢い（商業経済の複合）',
    'EV_p1782_01': '異常気象と農業構造の脆弱性による飢饉圧（飢饉・疫病・東北/蝦夷・商業経済の複合）',
    'EV_p1839_01': '対外認識をめぐる幕閣内の対立圧（開国と攘夷の複合）',
    'EV_p1862_01': '攘夷意識と外国人居留の衝突圧（雄藩連合・対英関係の複合）',
    'EV_p1871_01': '中央集権化のために藩体制を解体する必要の圧（藩体制・中央集権化の複合）',
    'EV_p1933_01': '満州事変後の国際的孤立と国内強硬論の圧（対外関係(近代)・対英関係の複合）',
}

# ===== eGenerates Effect Fixes =====
# (eventId, bg_label) -> new effect
EFFECT_FIXES = {
    ('EV_p0604_01', '豪族勢力'): 'redirect',
    ('EV_p1167_01', '院政体制'): 'erode',
    ('EV_p1177_01', '院政体制'): 'erode',
    ('EV_p1183_01', '平氏'): 'erode',
    ('EV_p1933_01', '対英関係'): 'erode',
}

# ===== eGenerates to Remove (wrong BG references) =====
REMOVE_EGENERATES = {
    ('EV_p0741_01', '守護・地頭制'),  # 741年に守護地頭は存在しない
    ('EV_p0607_01', '南北朝分裂'),     # 遣隋使と南北朝は無関係
}

# ===== contributingBG Manual Assignments =====
# eventId -> list of bgIds to assign
CONTRIBUTING_BG_FIXES = {
    'EV_p0752_01': {
        'label': '国家的仏教事業への資源動員の圧（仏教(古代)・租税・財政の複合）',
        'bgs': ['BG_011', 'BG_004'],  # 仏教(古代), 租税・財政
    },
    'EV_p0805_01': {
        'bgs': ['BG_011'],  # 仏教(古代) — 既存Bラベルは良好、BGリンクのみ追加
    },
    'EV_p1221_02': {
        'label': '朝廷と幕府の権力二重構造の矛盾圧（天皇・朝廷(中世)・鎌倉幕府の複合）',
        'bgs': ['BG_046', 'BG_077'],  # 天皇・朝廷(中世), 鎌倉幕府
    },
    'EV_p1331_01': {
        'label': '天皇親政回復の意志と幕府支配への抵抗圧（天皇・朝廷(中世)・鎌倉幕府の複合）',
        'bgs': ['BG_046', 'BG_077'],  # 天皇・朝廷(中世), 鎌倉幕府
    },
    'EV_p1428_01': {
        'bgs': ['BG_072', 'BG_004'],  # 戦国の分裂, 租税・財政
    },
    'EV_p1860_01': {
        'bgs': ['BG_037', 'BG_031'],  # 開国と攘夷, 雄藩連合
    },
    'EV_p1941_01': {
        'bgs': ['BG_008', 'BG_079'],  # 対外関係(近代), 対米関係
    },
    'EV_p1972_01': {
        'bgs': ['BG_079', 'BG_051'],  # 対米関係, 冷戦構造 — 既にBG沖縄/琉球なし(34=東北)
    },
    'EV_p1989_01': {
        'bgs': ['BG_082'],  # 皇位継承(近現代)
    },
}

# ===== eGenerates Manual Additions =====
# eventId -> list of {targetBG, effect, description}
ADD_EGENERATES = {
    'EV_p0752_01': [
        {'targetBG': 'BG_011', 'effect': 'reinforce', 'description': '国家仏教の象徴として仏教権威を強化'},
        {'targetBG': 'BG_004', 'effect': 'erode', 'description': '大規模造営事業による国家財政の圧迫'},
    ],
    'EV_p1331_01': [
        {'targetBG': 'BG_077', 'effect': 'erode', 'description': '討幕挙兵により鎌倉幕府の統制力が動揺'},
        {'targetBG': 'BG_046', 'effect': 'reinforce', 'description': '天皇親政への動きが朝廷権威を回復'},
    ],
    'EV_p1428_01': [
        {'targetBG': 'BG_072', 'effect': 'reinforce', 'description': '土一揆の頻発が中世秩序の崩壊を加速'},
        {'targetBG': 'BG_070', 'effect': 'erode', 'description': '幕府の統治力への信頼低下'},
    ],
    'EV_p1860_01': [
        {'targetBG': 'BG_006', 'effect': 'erode', 'description': '大老暗殺により幕府の統治威信が失墜'},
        {'targetBG': 'BG_031', 'effect': 'reinforce', 'description': '幕府弱体化で雄藩の発言力が増大'},
    ],
    'EV_p1972_01': [
        {'targetBG': 'BG_079', 'effect': 'redirect', 'description': '沖縄返還で日米関係が新段階に移行'},
    ],
    'EV_p1989_01': [
        {'targetBG': 'BG_082', 'effect': 'generate', 'description': '平成への改元により新たな皇位継承が実現'},
    ],
}


def infer_phases(effect_log, year_range):
    """effectLog（事実）からphases（状態遷移の解釈）を推論する。

    推論ルール:
    - 最初のgenerate → emerging（以降のgenerateはreinforceと同等に扱う）
    - reinforce/generate(2回目以降) → established（未確立なら確立へ）
    - erode → strained（初回）→ declining（2回目以降）
    - terminate → terminated（その後のgenerate/reinforceで再emergingも可）
    - redirect → 単独ではphase変化しない（前後のerode等と組み合わさる場合のみ）

    振動防止: 同一年内の複数effectは最も支配的なものだけを採用。
    短期phase除去: 5年未満のphaseは前後に吸収。
    """
    if not effect_log:
        return []

    # Parse year range
    try:
        parts = year_range.split('-')
        start_year = int(parts[0])
        end_year = int(parts[-1]) if len(parts) > 1 else start_year
    except (ValueError, IndexError):
        start_year = effect_log[0]['year']
        end_year = effect_log[-1]['year']

    # Aggregate effects by year (take most impactful)
    PRIORITY = {'terminate': 5, 'erode': 4, 'redirect': 3, 'generate': 2, 'reinforce': 1}
    by_year = {}
    for entry in effect_log:
        y = entry['year']
        if y not in by_year or PRIORITY.get(entry['effect'], 0) > PRIORITY.get(by_year[y], 0):
            by_year[y] = entry['effect']

    sorted_years = sorted(by_year.keys())

    # Build raw phases
    raw_phases = []
    current_phase = None
    phase_start = start_year
    seen_first_generate = False
    erode_count = 0

    for year in sorted_years:
        effect = by_year[year]
        new_phase = None

        if effect == 'generate':
            if not seen_first_generate and current_phase != 'terminated':
                new_phase = 'emerging'
                seen_first_generate = True
            elif current_phase == 'terminated':
                # Re-emergence after termination
                new_phase = 'emerging'
            else:
                # Subsequent generate = reinforce
                if current_phase == 'emerging':
                    new_phase = 'established'
        elif effect == 'reinforce':
            if current_phase in (None, 'emerging'):
                new_phase = 'established'
            elif current_phase in ('strained',):
                pass  # reinforce during strain doesn't reset
        elif effect == 'erode':
            erode_count += 1
            if current_phase in ('established', 'expanding', 'emerging', None):
                new_phase = 'strained'
            elif current_phase == 'strained' and erode_count >= 2:
                new_phase = 'declining'
        elif effect == 'terminate':
            new_phase = 'terminated'
            erode_count = 0
        elif effect == 'redirect':
            pass  # redirect alone doesn't change phase

        if new_phase and new_phase != current_phase:
            if current_phase is not None:
                raw_phases.append({
                    'period': f"{phase_start}-{year}",
                    'phase': current_phase,
                })
            current_phase = new_phase
            phase_start = year

    # Close last phase
    if current_phase is not None:
        if current_phase == 'terminated':
            raw_phases.append({
                'period': str(phase_start),
                'phase': 'terminated',
            })
        else:
            raw_phases.append({
                'period': f"{phase_start}-{end_year}",
                'phase': current_phase,
            })

    # Merge short phases (< 5 years) into neighbors, then merge consecutive same-phase
    if len(raw_phases) <= 1:
        return raw_phases

    # Step 1: absorb short phases into predecessor
    absorbed = [raw_phases[0]]
    for p in raw_phases[1:]:
        parts = p['period'].split('-')
        try:
            p_start = int(parts[0])
            p_end = int(parts[-1])
        except ValueError:
            absorbed.append(p)
            continue

        if p['phase'] == 'terminated':
            absorbed.append(p)
            continue

        duration = p_end - p_start
        if duration < 5:
            prev = absorbed[-1]
            prev_parts = prev['period'].split('-')
            absorbed[-1] = {
                'period': f"{prev_parts[0]}-{p_end}",
                'phase': prev['phase'],
            }
        else:
            absorbed.append(p)

    # Step 2: merge consecutive phases with same phase name
    merged = [absorbed[0]]
    for p in absorbed[1:]:
        if p['phase'] == merged[-1]['phase']:
            prev_parts = merged[-1]['period'].split('-')
            p_parts = p['period'].split('-')
            merged[-1] = {
                'period': f"{prev_parts[0]}-{p_parts[-1]}",
                'phase': p['phase'],
            }
        else:
            merged.append(p)

    return merged


def apply_fixes():
    with open(DRAFT_FILE) as f:
        draft = json.load(f)

    bg_labels = {bg['bgId']: bg['label'] for bg in draft['backgroundElements']}

    b_fixed = 0
    b_cbg_fixed = 0
    eg_fixed = 0
    eg_removed = 0
    eg_added = 0

    for v in draft['frameworkViews']:
        eid = v['eventId']

        # Fix B labels
        if eid in B_LABEL_FIXES:
            for b in v['causalFramework']['B']:
                if b.get('_synthesized'):
                    b['label'] = B_LABEL_FIXES[eid]
                    b['_needs_review'] = False
                    b['note'] = '手動修正済み'
                    b_fixed += 1

        # Fix contributingBG assignments
        if eid in CONTRIBUTING_BG_FIXES:
            fix = CONTRIBUTING_BG_FIXES[eid]
            for b in v['causalFramework']['B']:
                if not b.get('contributingBG') or b.get('_synthesized'):
                    b['contributingBG'] = fix['bgs']
                    b['_needs_review'] = False
                    if 'label' in fix:
                        b['label'] = fix['label']
                        b['_synthesized'] = True
                    b['note'] = '手動BGマッピング済み'
                    b_cbg_fixed += 1
                    break  # fix first matching B only

        # Fix eGenerates effects and remove wrong refs
        new_egens = []
        for eg in v['eGenerates']:
            bg_label = bg_labels.get(eg['targetBG'], '')

            if (eid, bg_label) in REMOVE_EGENERATES:
                eg_removed += 1
                continue

            if (eid, bg_label) in EFFECT_FIXES:
                eg['effect'] = EFFECT_FIXES[(eid, bg_label)]
                eg['description'] = f"（{eg['effect']}に手動修正）"
                eg['_needs_review'] = False
                eg_fixed += 1

            new_egens.append(eg)

        # Add manual eGenerates
        if eid in ADD_EGENERATES:
            existing_targets = {eg['targetBG'] for eg in new_egens}
            for add_eg in ADD_EGENERATES[eid]:
                if add_eg['targetBG'] not in existing_targets:
                    new_egens.append({
                        'targetBG': add_eg['targetBG'],
                        'effect': add_eg['effect'],
                        'description': add_eg['description'],
                        '_needs_review': False,
                    })
                    eg_added += 1

        v['eGenerates'] = new_egens

    # Update stats
    total_eg = sum(len(v['eGenerates']) for v in draft['frameworkViews'])
    no_eg = sum(1 for v in draft['frameworkViews'] if not v['eGenerates'])
    no_cbg = sum(
        1 for v in draft['frameworkViews']
        for b in v['causalFramework']['B']
        if not b.get('contributingBG')
    )
    draft['_meta']['stats']['total_e_generates'] = total_eg
    draft['_meta']['stats']['events_without_e_generates'] = no_eg

    # ===== BG Description & Lifecycle Generation =====
    type_names = {
        'power_structure': '権力構造', 'institution': '制度',
        'resource': '資源・経済', 'culture': '文化・思想',
        'external': '対外関係', 'demographic': '人口・地域',
        'conflict': '紛争・対立', 'knowledge': '知識・記録',
    }

    # Collect BG->event mappings
    bg_events = {}
    for v in draft['frameworkViews']:
        bgs_in_event = set()
        for b in v['causalFramework']['B']:
            for bgid in b.get('contributingBG', []):
                bgs_in_event.add(bgid)
        for eg in v['eGenerates']:
            bgs_in_event.add(eg['targetBG'])
        for bgid in bgs_in_event:
            bg_events.setdefault(bgid, []).append(
                (v['year'], v['eventId'], v['title']))

    bg_updated = 0
    for bg in draft['backgroundElements']:
        bgid = bg['bgId']
        events = sorted(bg_events.get(bgid, []))
        type_ja = type_names.get(bg['type'], bg['type'])
        bg['description'] = (
            f"{bg['_yearRange']}に影響を持つ{type_ja}要素。{len(events)}件のイベントに関与。"
            if events else f"{type_ja}要素。"
        )

        # Build effectLog from eGenerates (factual record)
        effect_log = []
        for v in draft['frameworkViews']:
            for eg in v['eGenerates']:
                if eg['targetBG'] == bgid:
                    effect_log.append({
                        'eventId': v['eventId'],
                        'year': v['year'],
                        'effect': eg['effect'],
                    })
        effect_log.sort(key=lambda x: x['year'])

        # Infer phases from effectLog (interpretive)
        phases = infer_phases(effect_log, bg.get('_yearRange', ''))

        # Replace old lifecycle with new structure
        bg.pop('lifecycle', None)
        bg['generatedBy'] = events[0][1] if events else None
        bg['effectLog'] = effect_log
        bg['phases'] = phases
        bg_updated += 1

    with open(DRAFT_FILE, 'w') as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    print(f'B labels fixed: {b_fixed}')
    print(f'B contributingBG fixed: {b_cbg_fixed}')
    print(f'eGenerates effects fixed: {eg_fixed}')
    print(f'eGenerates removed: {eg_removed}')
    print(f'eGenerates added: {eg_added}')
    print(f'Total eGenerates: {total_eg}')
    print(f'Events without eGenerates: {no_eg}')
    print(f'B without contributingBG: {no_cbg}')
    print(f'BG descriptions/lifecycles updated: {bg_updated}')


if __name__ == '__main__':
    apply_fixes()
