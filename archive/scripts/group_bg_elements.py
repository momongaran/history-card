#!/usr/bin/env python3
"""
BG要素グルーピングスクリプト

v3.8のB要素を分析し、v3.9のBG（背景要素）候補を生成する。
3段階のグルーピング:
  1. L-PRQチェーンでイベント群を分割
  2. チェーン内でsubCategoryによるグルーピング
  3. キーワード抽出による統合・分割

Usage: python3 scripts/group_bg_elements.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
V38_FILE = ROOT / "data" / "framework_output_v3_8.json"
CORR_FILE = ROOT / "data" / "default_correspondences_v3_8.json"
OUT_FILE = ROOT / "data" / "v3_9_bg_candidates.json"
REPORT_FILE = ROOT / "data" / "v3_9_bg_grouping_report.md"

# ── Entity extraction patterns ──
# Priority levels: higher = more specific, wins over lower
# (priority, regex, bg_type, bg_label)
# Within same element, ALL matched patterns are kept (multi-label).
# But if a high-priority and low-priority pattern produce the SAME bg_label, dedup.
ENTITY_PATTERNS = [
    # === Priority 3: Most specific (named entities, era-specific) ===
    # 幕府を時代別に分割
    (3, r'鎌倉幕府|頼朝.+幕|鎌倉.+幕|幕府.+鎌倉', 'institution', '鎌倉幕府'),
    (3, r'室町幕府|足利.+幕|幕府.+室町', 'institution', '室町幕府'),
    (3, r'江戸幕府|徳川.+幕|幕府.+徳川|幕府.+江戸', 'institution', '江戸幕府'),
    # 北条を時代別に
    (3, r'北条時政|北条義時|北条泰時|北条時頼|北条時宗|執権', 'power_structure', '北条執権体制'),
    (3, r'北条早雲|北条氏康|後北条|小田原', 'power_structure', '後北条氏'),
    # 藤原氏を時代別に
    (3, r'藤原不比等|藤原四兄弟|藤原仲麻呂|藤原広嗣|藤原百川', 'power_structure', '藤原氏(奈良)'),
    (3, r'藤原良房|藤原基経|藤原時平|藤原道長|藤原頼通|摂関', 'power_structure', '摂関家(藤原氏)'),
    # 具体的制度
    (3, r'班田|口分田|公地公民', 'institution', '班田収授制'),
    (3, r'太閤検地|検地', 'institution', '検地・兵農分離'),
    (3, r'刀狩|兵農分離', 'institution', '検地・兵農分離'),
    (3, r'参勤交代', 'institution', '参勤交代制'),
    (3, r'版籍奉還', 'institution', '中央集権化(明治)'),
    (3, r'地租改正', 'institution', '近代税制'),
    (3, r'武家諸法度|大名統制', 'institution', '武家諸法度/大名統制'),
    (3, r'禁中並公家諸法度|公家.+規定|朝廷.+統制', 'institution', '朝廷統制'),
    (3, r'日米和親|日米修好|安政.+条約|不平等条約', 'institution', '不平等条約体制'),
    (3, r'大日本帝国憲法|明治憲法|帝国憲法', 'institution', '明治憲法体制'),
    (3, r'日本国憲法|新憲法|国民主権', 'institution', '戦後憲法体制'),
    # 具体的戦争・事件
    (3, r'元[寇軍]|蒙古|フビライ', 'external', '蒙古の脅威'),
    (3, r'白村江', 'external', '白村江後の危機'),
    (3, r'壬申の乱', 'conflict', '壬申の乱後の再編'),
    (3, r'承久の乱', 'conflict', '承久の乱後の体制'),
    (3, r'応仁の乱|応仁', 'conflict', '応仁の乱と秩序崩壊'),
    (3, r'島原の乱|島原', 'conflict', '島原の乱の衝撃'),
    (3, r'ペリー|黒船', 'external', '欧米列強の開国圧'),
    (3, r'関ヶ原', 'conflict', '関ヶ原後の再編'),
    (3, r'大坂.+陣|大坂城', 'conflict', '豊臣家問題'),
    (3, r'日清戦争|日清', 'external', '日清戦争'),
    (3, r'日露戦争|日露', 'external', '日露関係'),
    (3, r'日中戦争|日華事変|支那事変', 'external', '日中戦争'),
    (3, r'太平洋戦争|大東亜|真珠湾', 'external', '太平洋戦争'),
    (3, r'朝鮮戦争', 'external', '朝鮮戦争'),

    # === Priority 2: General entities ===
    # 制度
    (2, r'律令', 'institution', '律令制'),
    (2, r'荘園', 'institution', '荘園制'),
    (2, r'国[司衙]', 'institution', '国司行政'),
    (2, r'守護|地頭', 'institution', '守護・地頭制'),
    (2, r'御家人|封建', 'institution', '御家人制'),
    (2, r'惣[村領]|土一揆|一揆.+農|徳政', 'institution', '惣村・一揆'),
    (2, r'鎖国|海禁', 'institution', '鎖国体制'),
    (2, r'藩[政閥]|藩主|知藩事|廃藩', 'institution', '藩体制'),
    (2, r'議会|国会|帝国議会', 'institution', '議会制'),
    (2, r'氏姓|氏族.+制|世襲.+豪族', 'institution', '氏姓制度'),
    (2, r'都[城宮]|遷都|平城京|平安京|藤原京|長岡京', 'institution', '都城制'),
    (2, r'南北朝|南朝|北朝|両統', 'conflict', '南北朝分裂'),
    (2, r'戦国|群雄割拠|下剋上', 'conflict', '戦国の分裂'),
    # 勢力
    (2, r'蘇我', 'power_structure', '蘇我氏'),
    (2, r'物部', 'power_structure', '物部氏'),
    (2, r'大伴', 'power_structure', '大伴氏'),
    (2, r'藤原', 'power_structure', '藤原氏'),
    (2, r'平[氏清家]|平家', 'power_structure', '平氏'),
    (2, r'源[氏頼義家]', 'power_structure', '源氏'),
    (2, r'北条', 'power_structure', '北条氏'),
    (2, r'足利', 'power_structure', '足利氏'),
    (2, r'織田|信長', 'power_structure', '織田政権'),
    (2, r'豊臣|秀吉', 'power_structure', '豊臣政権'),
    (2, r'徳川|家康', 'power_structure', '徳川家'),
    (2, r'薩[摩長]|長州|土佐|肥前|薩長|雄藩', 'power_structure', '雄藩連合'),
    (2, r'明治政府|新政府|維新', 'power_structure', '明治政府'),
    (2, r'院政|上皇|法皇', 'power_structure', '院政体制'),
    (2, r'朝廷|天皇親政|親政', 'power_structure', '天皇・朝廷'),
    (2, r'皇[位統嗣]|王[統位]|即位|譲位|退位|崩御|皇太子', 'power_structure', '皇位継承'),
    (2, r'豪族', 'power_structure', '豪族勢力'),
    # 対外
    (2, r'唐|遣唐使', 'external', '唐との関係'),
    (2, r'隋|遣隋使', 'external', '隋との関係'),
    (2, r'百済|新羅|伽耶|朝鮮半島|高句麗', 'external', '朝鮮半島情勢'),
    (2, r'明[国貿]|日明|勘合', 'external', '日明関係'),
    (2, r'ポルトガル|スペイン|イエズス|南蛮', 'external', '南蛮貿易/宣教'),
    (2, r'ロシア|露[国西]', 'external', '対ロシア関係'),
    (2, r'イギリス|英[国仏]|日英同盟', 'external', '対英関係'),
    (2, r'アメリカ|米[国艦軍]|対米', 'external', '対米関係'),
    (2, r'GHQ|占領|マッカーサー|連合国', 'external', 'GHQ占領'),
    (2, r'冷戦|ソ連|ソビエト', 'external', '冷戦構造'),
    (2, r'ドイツ|独[伊逸]|三国同盟|枢軸', 'external', '枢軸同盟'),
    # 思想・文化
    (2, r'仏教|僧[侶兵]|寺[院社]|宗[派教]|密教|浄土|禅', 'culture', '仏教'),
    (2, r'儒[学教]|朱子学|陽明学', 'culture', '儒学思想'),
    (2, r'キリスト|キリシタン|バテレン', 'culture', 'キリスト教'),
    (2, r'蘭学|洋学|西洋.+知|西洋.+学', 'knowledge', '西洋知識'),
    (2, r'尊王攘夷|攘夷|尊皇', 'culture', '尊王攘夷思想'),
    (2, r'国風|和歌|歌[集道]', 'culture', '国風文化'),
    (2, r'正統性|神器|正当|権威', 'culture', '正統性・権威'),
    # 経済
    (2, r'貿易|交易|通商', 'resource', '交易・貿易'),
    (2, r'米[価本]|年貢|石高|租庸調', 'resource', '租税・財政'),
    (2, r'商[業人]|町人|経済[力的]', 'resource', '商業経済'),
    (2, r'飢[饉餓]|不作|凶作|疫病', 'resource', '飢饉・疫病'),
    (2, r'銀[山鉱]|金[山鉱]', 'resource', '鉱山資源'),
    # 軍事
    (2, r'軍[事団制備]|兵[役士制]|徴兵|動員', 'resource', '軍事力'),
    (2, r'海[軍賊]|水軍|艦[隊船]', 'resource', '海上勢力'),
    # 社会
    (2, r'武[士家力装]|侍|武門|武勇', 'power_structure', '武士層'),
    (2, r'(?<!蘇我)蝦夷|奥州|東北', 'demographic', '東北/蝦夷'),
    (2, r'九州|筑紫|大宰府', 'demographic', '九州'),
    (2, r'沖縄|琉球', 'demographic', '沖縄/琉球'),
    (2, r'人口[増減]|人口圧', 'demographic', '人口動態'),
    (2, r'浪人|牢人', 'demographic', '浪人問題'),

    # === Priority 1: Broad but meaningful (fallback) ===
    (1, r'伊藤博文|大隈|板垣|山県', 'power_structure', '明治政府'),
    (1, r'憲法.+調査|草案|枢密院|発布', 'institution', '明治憲法体制'),
    (1, r'選挙|普通選挙|護憲', 'institution', '議会制'),
    (1, r'抗日|盧溝橋|満州|関東軍', 'external', '対外関係(近代)'),
    (1, r'昭和天皇|闘病|自粛|崩御', 'power_structure', '皇位継承'),
    (1, r'モリソン|打払|渡辺崋山|高野長英', 'external', '開国と攘夷'),
    (1, r'疲弊|撤退.+要求|戦意', 'conflict', '応仁の乱と秩序崩壊'),
    (1, r'条約', 'institution', '条約体制'),
    (1, r'地震|津波|震災|噴火|台風', 'demographic', '自然災害'),
    (1, r'大名|諸侯', 'power_structure', '大名勢力'),
    (1, r'中央集権|集権|統一', 'institution', '中央集権化'),
    (1, r'財[政源]|歳[入出]|租[税庸]', 'resource', '租税・財政'),
    (1, r'防[衛人備]|海防|城[郭砦]', 'resource', '防衛体制'),
    (1, r'記紀|古事記|日本書紀|正史|編纂', 'knowledge', '記紀・史書'),
    (1, r'戸籍|人民|把握', 'institution', '人民把握制度'),
    (1, r'末法|浄土|来世', 'culture', '末法思想'),
    (1, r'外[戚祖]|入[内嫁]', 'power_structure', '外戚政治'),
    (1, r'後継|世継|相続|跡目', 'conflict', '後継争い'),
    (1, r'包囲網|反.+連合|同盟.+敵', 'conflict', '反権力連合'),
    (1, r'新幹線|インフラ|高速|復興', 'resource', 'インフラ・復興'),
    (1, r'東京オリンピック|万博|博覧会', 'culture', '国際的地位'),
]

# BG labels to EXCLUDE (too abstract/categorical, not structural entities)
EXCLUDE_LABELS = {
    '統治体制', '軍事力', '改革', '対外関係', '幕府', '大名',
}

# Merge rules: bg_label -> canonical bg_label
MERGE_RULES = {
    '摂関家(藤原氏)': '摂関家(藤原氏)',
    '藤原氏(奈良)': '藤原氏(奈良)',
    '藤原氏': '藤原氏',  # general fallback - will be split by era context
    '北条氏': '北条執権体制',  # merge into era-specific
    '後北条氏': '後北条氏',
    '幕府': None,  # discard generic, specific ones should match first
    '南蛮貿易/宣教': '南蛮貿易/宣教',
    '検地・兵農分離': '検地・兵農分離',
}

# Energy detection
ENERGY_RE = re.compile(
    r'(圧[がをに]|矛盾|対立[がをし]|不満|歪[みがを]|危機|焦点|緊張|衝突|反発|不安[がをに定]|'
    r'脅威|限界|課題|必要[がとに]|求め|要求|迫ら|高まっ|強まっ|揺[らぎれ]|不足|欠[如乏]|困窮|'
    r'窮[乏迫]|摩擦|抵抗|障害|停滞|混乱|断絶|空白|動揺|深刻|悪化|破綻|瓦解|弱体)'
)


def load_data():
    with open(V38_FILE) as f:
        v38 = json.load(f)
    with open(CORR_FILE) as f:
        corr = json.load(f)
    return v38, corr


def extract_entities(label, sort_key=0):
    """ラベルからエンティティキーワードを抽出（優先度付き）"""
    matches = []  # (priority, bg_type, bg_label)
    for priority, pattern, bg_type, bg_label in ENTITY_PATTERNS:
        if re.search(pattern, label):
            matches.append((priority, bg_type, bg_label))

    if not matches:
        return []

    # Apply merge rules
    merged = []
    for pri, bg_type, bg_label in matches:
        canonical = MERGE_RULES.get(bg_label, bg_label)
        if canonical is not None:
            merged.append((pri, bg_type, canonical))

    if not merged:
        return []

    # Deduplicate: if same bg_label appears at multiple priorities, keep highest
    best = {}  # bg_label -> (priority, bg_type)
    for pri, bg_type, bg_label in merged:
        if bg_label not in best or pri > best[bg_label][0]:
            best[bg_label] = (pri, bg_type)

    # If a priority-3 match exists, drop priority-1 matches (too generic)
    max_pri = max(v[0] for v in best.values())
    if max_pri >= 3:
        best = {k: v for k, v in best.items() if v[0] >= 2}
    elif max_pri >= 2:
        best = {k: v for k, v in best.items() if v[0] >= 1}

    # Handle 藤原氏 ambiguity: use era context
    if '藤原氏' in best and sort_key > 0:
        if sort_key < 800:
            best['藤原氏(奈良)'] = best.pop('藤原氏')
        elif sort_key < 1200:
            best['摂関家(藤原氏)'] = best.pop('藤原氏')
        # else keep generic

    return [(bg_type, bg_label) for bg_label, (_, bg_type) in best.items()
            if bg_label not in EXCLUDE_LABELS]


def build_lprq_chains(v38, corr):
    """L-PRQリンクからイベントチェーンを構築"""
    elem_layer = {}
    for fw in v38['frameworkViews']:
        for e in fw['elements']:
            elem_layer[e['elementId']] = e['layer']

    # Build event adjacency via B-element L-PRQ links
    graph = defaultdict(set)
    for fw_key, elements in corr.items():
        src = fw_key.replace('FW_', '')
        for el_id, link in elements.items():
            tgt = link.get('eventId', '')
            if tgt != src and elem_layer.get(el_id) == 'B':
                graph[src].add(tgt)
                graph[tgt].add(src)  # bidirectional for component detection

    # Find connected components
    visited = set()
    components = []

    def bfs(start):
        queue = [start]
        comp = set()
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        return comp

    all_events = set(graph.keys())
    for ev in sorted(all_events):
        if ev not in visited:
            comp = bfs(ev)
            components.append(comp)

    return components


def group_bg_elements(v38, corr):
    """メイングルーピングロジック"""
    # Build lookups
    event_info = {}
    all_b_elements = []  # (eventId, element)
    for fw in v38['frameworkViews']:
        eid = fw['eventId']
        event_info[eid] = {'title': fw['title'], 'sortKey': fw['sortKey'], 'era': fw.get('era', '')}
        for e in fw['elements']:
            if e['layer'] == 'B':
                all_b_elements.append((eid, e))

    # Step 1: Extract entities from each B element
    b_entity_map = []  # (eventId, element, entities, is_energy)
    for eid, elem in all_b_elements:
        sk = event_info.get(eid, {}).get('sortKey', 0)
        entities = extract_entities(elem['label'], sk)
        is_energy = bool(ENERGY_RE.search(elem['label']))
        b_entity_map.append((eid, elem, entities, is_energy))

    # Step 2: Group by entity label
    entity_groups = defaultdict(list)  # bg_label -> [(eventId, element, is_energy)]
    unmatched = []

    for eid, elem, entities, is_energy in b_entity_map:
        if entities:
            for bg_type, bg_label in entities:
                entity_groups[bg_label].append({
                    'eventId': eid,
                    'elementId': elem['elementId'],
                    'label': elem['label'],
                    'category': elem.get('category', ''),
                    'subCategory': elem.get('subCategory', ''),
                    'is_energy': is_energy,
                    'bg_type': bg_type,
                })
        else:
            unmatched.append({
                'eventId': eid,
                'elementId': elem['elementId'],
                'label': elem['label'],
                'category': elem.get('category', ''),
                'subCategory': elem.get('subCategory', ''),
                'is_energy': is_energy,
            })

    # Step 3: (entity_groups built above, candidates created after co-occurrence)

    # Step 4a: Co-occurrence assignment — assign unmatched to BGS that co-occur in same event
    # Build: eventId -> set of bg_labels matched by other B elements in that event
    event_bg_map = defaultdict(set)
    for eid, elem, entities, is_energy in b_entity_map:
        if entities:
            for bg_type, bg_label in entities:
                event_bg_map[eid].add(bg_label)

    still_unmatched = []
    for item in unmatched:
        eid = item['eventId']
        co_bgs = event_bg_map.get(eid, set())
        if len(co_bgs) == 1:
            # Only one BG in this event — assign to it
            bg_label = next(iter(co_bgs))
            if bg_label in entity_groups:
                entity_groups[bg_label].append({
                    'eventId': eid,
                    'elementId': item['elementId'],
                    'label': item['label'],
                    'category': item['category'],
                    'subCategory': item['subCategory'],
                    'is_energy': item['is_energy'],
                    'bg_type': 'co_occur',
                    '_assigned_by': 'co-occurrence',
                })
            else:
                still_unmatched.append(item)
        elif len(co_bgs) > 1:
            # Multiple BGS — pick the one most specific to this era
            # Just assign to first (largest group) for now — can refine later
            best_bg = max(co_bgs, key=lambda bl: len(entity_groups.get(bl, [])))
            if best_bg in entity_groups:
                entity_groups[best_bg].append({
                    'eventId': eid,
                    'elementId': item['elementId'],
                    'label': item['label'],
                    'category': item['category'],
                    'subCategory': item['subCategory'],
                    'is_energy': item['is_energy'],
                    'bg_type': 'co_occur',
                    '_assigned_by': 'co-occurrence',
                })
            else:
                still_unmatched.append(item)
        else:
            still_unmatched.append(item)

    unmatched = still_unmatched

    # Rebuild bg_candidates from updated entity_groups
    bg_candidates = []
    bg_counter = 1
    for bg_label, items in sorted(entity_groups.items(), key=lambda x: -len(x[1])):
        type_counts = defaultdict(int)
        for item in items:
            if item['bg_type'] != 'co_occur':
                type_counts[item['bg_type']] += 1
        primary_type = max(type_counts, key=type_counts.get) if type_counts else 'unknown'

        event_ids = sorted(set(item['eventId'] for item in items),
                          key=lambda x: event_info.get(x, {}).get('sortKey', 0))
        sort_keys = [event_info[eid]['sortKey'] for eid in event_ids]

        bg_candidates.append({
            'bgId': f'BG_{bg_counter:03d}',
            'type': primary_type,
            'label': bg_label,
            'eventCount': len(event_ids),
            'elementCount': len(items),
            'yearRange': f'{min(sort_keys)}-{max(sort_keys)}' if sort_keys else '?',
            'events': event_ids,
            'energy_ratio': sum(1 for i in items if i['is_energy']) / len(items),
            'sample_labels': [item['label'][:60] for item in items[:3]],
            'lifecycle': {'generatedBy': None, 'states': []},
        })
        bg_counter += 1

    # Step 4b: Handle remaining unmatched — group by subCategory + era cluster
    if unmatched:
        era_groups = defaultdict(list)
        for item in unmatched:
            eid = item['eventId']
            era = event_info.get(eid, {}).get('era', '') or ''
            sk = event_info.get(eid, {}).get('sortKey', 0)
            # Rough era bucketing
            if sk < 600: era_bucket = '古代前期'
            elif sk < 800: era_bucket = '奈良'
            elif sk < 1185: era_bucket = '平安'
            elif sk < 1333: era_bucket = '鎌倉'
            elif sk < 1573: era_bucket = '室町'
            elif sk < 1603: era_bucket = '安土桃山'
            elif sk < 1868: era_bucket = '江戸'
            elif sk < 1945: era_bucket = '近代'
            else: era_bucket = '戦後'
            key = f'{era_bucket}:{item["subCategory"]}'
            era_groups[key].append(item)

        for key, items in sorted(era_groups.items(), key=lambda x: -len(x[1])):
            if len(items) >= 2:
                era_name, sub_cat = key.split(':', 1)
                event_ids = sorted(set(item['eventId'] for item in items),
                                  key=lambda x: event_info.get(x, {}).get('sortKey', 0))
                sort_keys = [event_info[eid]['sortKey'] for eid in event_ids]
                bg_candidates.append({
                    'bgId': f'BG_{bg_counter:03d}',
                    'type': 'unclassified',
                    'label': f'[{era_name}] {sub_cat}関連の構造的条件',
                    'eventCount': len(event_ids),
                    'elementCount': len(items),
                    'yearRange': f'{min(sort_keys)}-{max(sort_keys)}',
                    'events': event_ids,
                    'energy_ratio': sum(1 for i in items if i['is_energy']) / len(items),
                    'sample_labels': [item['label'][:60] for item in items[:3]],
                    'lifecycle': {'generatedBy': None, 'states': []},
                    '_needs_review': True,
                })
                bg_counter += 1

    # Step 5: Post-processing
    # 5a: Merge small named groups into related larger ones
    MERGE_SMALL = {
        '中央集権化(明治)': '明治政府',
        '近代税制': '明治政府',
        '尊王攘夷思想': '開国と攘夷',
        '欧米列強の開国圧': '開国と攘夷',
        '白村江後の危機': '朝鮮半島情勢',
        '関ヶ原後の再編': '徳川家',
        '島原の乱の衝撃': 'キリスト教',
        '鉱山資源': '商業経済',
        '物部氏': '豪族勢力',
        '大伴氏': '豪族勢力',
        '壬申の乱後の再編': '皇位継承',
        '後北条氏': '戦国の分裂',
        '日清戦争': '対外関係(近代)',
        '日露関係': '対外関係(近代)',
        '日中戦争': '対外関係(近代)',
        '太平洋戦争': '対外関係(近代)',
        '朝鮮戦争': '対外関係(近代)',
        '枢軸同盟': '対外関係(近代)',
        '明治憲法体制': '明治憲法体制',
        '戦後憲法体制': '戦後憲法体制',
        # Small group merges
        '人口動態': '租税・財政',
        '反権力連合': '戦国の分裂',
        '惣村・一揆': '戦国の分裂',
        '戦国の分裂': '戦国の分裂',
        '末法思想': '仏教',
        '武家諸法度/大名統制': '徳川家',  # 江戸幕府→徳川家に統合
        '氏姓制度': '豪族勢力',
        '沖縄/琉球': '対外関係(近代)',
        '西洋知識': '開国と攘夷',
        '江戸幕府': '徳川家',  # 統合
    }

    merged_bg = {}
    for bg in bg_candidates:
        label = bg['label']
        target = MERGE_SMALL.get(label)
        if target and target != label:
            if target in merged_bg:
                # Merge into existing
                merged_bg[target]['elementCount'] += bg['elementCount']
                merged_bg[target]['events'] = sorted(set(merged_bg[target]['events'] + bg['events']),
                    key=lambda x: event_info.get(x, {}).get('sortKey', 0))
                merged_bg[target]['eventCount'] = len(merged_bg[target]['events'])
                years = [event_info[e]['sortKey'] for e in merged_bg[target]['events']]
                merged_bg[target]['yearRange'] = f'{min(years)}-{max(years)}'
                merged_bg[target]['sample_labels'].extend(bg['sample_labels'])
            else:
                # Create new merged entry
                bg_copy = dict(bg)
                bg_copy['label'] = target
                merged_bg[target] = bg_copy
        else:
            if label in merged_bg:
                merged_bg[label]['elementCount'] += bg['elementCount']
                merged_bg[label]['events'] = sorted(set(merged_bg[label]['events'] + bg['events']),
                    key=lambda x: event_info.get(x, {}).get('sortKey', 0))
                merged_bg[label]['eventCount'] = len(merged_bg[label]['events'])
                years = [event_info[e]['sortKey'] for e in merged_bg[label]['events']]
                merged_bg[label]['yearRange'] = f'{min(years)}-{max(years)}'
            else:
                merged_bg[label] = dict(bg)

    # 5b: Split overly broad groups by era
    ERA_SPLIT_TARGETS = {'天皇・朝廷', '皇位継承', '武士層', '仏教'}
    ERA_BOUNDARIES = [
        (800, '古代'),
        (1185, '平安'),
        (1573, '中世'),
        (1868, '近世'),
        (9999, '近現代'),
    ]

    def get_era(sort_key):
        for boundary, name in ERA_BOUNDARIES:
            if sort_key < boundary:
                return name
        return '近現代'

    final = []
    for label, bg in merged_bg.items():
        if label in ERA_SPLIT_TARGETS and bg['elementCount'] > 15:
            # Split by era
            era_events = defaultdict(list)
            for eid in bg['events']:
                sk = event_info.get(eid, {}).get('sortKey', 0)
                era_events[get_era(sk)].append(eid)

            # Merge tiny splits (<=2 events) into adjacent era
            era_order = [n for _, n in ERA_BOUNDARIES]
            for era_name in list(era_events.keys()):
                if len(era_events[era_name]) <= 1:
                    idx = era_order.index(era_name)
                    # Try merge into next era, then previous
                    merged_into = False
                    for neighbor in [idx + 1, idx - 1]:
                        if 0 <= neighbor < len(era_order) and era_order[neighbor] in era_events:
                            era_events[era_order[neighbor]].extend(era_events.pop(era_name))
                            merged_into = True
                            break
                    if not merged_into:
                        pass  # keep as-is if no neighbor

            for era_name, eids in sorted(era_events.items(), key=lambda x: ERA_BOUNDARIES[[n for _,n in ERA_BOUNDARIES].index(x[0])][0]):
                if not eids:
                    continue
                sort_keys = [event_info[e]['sortKey'] for e in eids]
                # Estimate element count proportionally
                ratio = len(eids) / len(bg['events'])
                el_count = max(1, round(bg['elementCount'] * ratio))
                sub_bg = {
                    'bgId': '',
                    'type': bg['type'],
                    'label': f"{label}({era_name})",
                    'eventCount': len(eids),
                    'elementCount': el_count,
                    'yearRange': f'{min(sort_keys)}-{max(sort_keys)}',
                    'events': sorted(eids, key=lambda x: event_info.get(x, {}).get('sortKey', 0)),
                    'energy_ratio': bg.get('energy_ratio', 0),
                    'sample_labels': [],
                    'lifecycle': {'generatedBy': None, 'states': []},
                }
                final.append(sub_bg)
        else:
            final.append(bg)

    # Renumber bgIds
    final.sort(key=lambda x: (-x['elementCount'] if x['type'] != 'unclassified' else 0, x.get('label', '')))
    for i, bg in enumerate(final):
        bg['bgId'] = f'BG_{i+1:03d}'

    bg_candidates = final
    return bg_candidates, unmatched, b_entity_map


def main():
    v38, corr = load_data()
    bg_candidates, unmatched, b_entity_map = group_bg_elements(v38, corr)

    # Build event info for report
    event_info = {}
    for fw in v38['frameworkViews']:
        event_info[fw['eventId']] = {'title': fw['title'], 'sortKey': fw['sortKey']}

    # Stats
    classified_count = sum(1 for _, _, entities, _ in b_entity_map if entities)
    total = len(b_entity_map)
    named_bg = [bg for bg in bg_candidates if bg['type'] != 'unclassified']
    unnamed_bg = [bg for bg in bg_candidates if bg['type'] == 'unclassified']

    # Output
    output = {
        '_meta': {
            'description': 'BG候補グルーピング結果',
            'date': '2026-03-07',
            'stats': {
                'total_b_elements': total,
                'entity_matched': classified_count,
                'unmatched': len(unmatched),
                'match_rate': f'{classified_count/total*100:.1f}%',
                'bg_candidates_named': len(named_bg),
                'bg_candidates_unclassified': len(unnamed_bg),
                'bg_candidates_total': len(bg_candidates),
            }
        },
        'bgCandidates': bg_candidates,
    }

    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Report
    lines = [
        '# BG要素グルーピングレポート',
        '',
        '## グルーピング方法',
        '',
        '1. 各B要素のlabelからキーワードパターンでエンティティ抽出',
        '2. 同じエンティティを持つB要素を1つのBG候補にグルーピング',
        '3. エンティティが抽出できないものは時代×subCategoryでグルーピング',
        '',
        '## 統計',
        '',
        f'- B要素総数: {total}',
        f'- エンティティ抽出成功: {classified_count} ({classified_count/total*100:.1f}%)',
        f'- 未マッチ: {len(unmatched)} ({len(unmatched)/total*100:.1f}%)',
        f'- BG候補（エンティティ名あり）: {len(named_bg)}',
        f'- BG候補（未分類）: {len(unnamed_bg)}',
        f'- **BG候補合計: {len(bg_candidates)}**',
        '',
        '## BG候補一覧（エンティティ名あり、出現数順）',
        '',
        '| bgId | type | label | 要素数 | イベント数 | 年代範囲 | energy比率 |',
        '|------|------|-------|--------|-----------|----------|-----------|',
    ]
    for bg in sorted(named_bg, key=lambda x: -x['elementCount']):
        lines.append(
            f"| {bg['bgId']} | {bg['type']} | {bg['label']} | "
            f"{bg['elementCount']} | {bg['eventCount']} | {bg['yearRange']} | "
            f"{bg['energy_ratio']:.0%} |"
        )

    if unnamed_bg:
        lines += [
            '',
            '## 未分類BG候補（時代×subCategory）',
            '',
            '| bgId | label | 要素数 | 年代範囲 | sample |',
            '|------|-------|--------|----------|--------|',
        ]
        for bg in sorted(unnamed_bg, key=lambda x: -x['elementCount']):
            sample = bg['sample_labels'][0][:40] if bg['sample_labels'] else ''
            lines.append(
                f"| {bg['bgId']} | {bg['label']} | {bg['elementCount']} | "
                f"{bg['yearRange']} | {sample} |"
            )

    # Singleton unmatched (not grouped)
    singletons = [item for item in unmatched
                  if not any(item['eventId'] in bg['events']
                            for bg in unnamed_bg)]
    if singletons:
        lines += [
            '',
            f'## 完全未マッチ（単独、{len(singletons)}件）',
            '',
            '| eventId | subCat | label |',
            '|---------|--------|-------|',
        ]
        for item in singletons[:20]:
            lines.append(f"| {item['eventId']} | {item['subCategory']} | {item['label'][:60]} |")
        if len(singletons) > 20:
            lines.append(f'| ... | | ({len(singletons)-20}件省略) |')

    report = '\n'.join(lines)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f'Output: {OUT_FILE}')
    print(f'Report: {REPORT_FILE}')
    print(f'B elements: {total}')
    print(f'Entity matched: {classified_count} ({classified_count/total*100:.1f}%)')
    print(f'BG candidates: {len(named_bg)} named + {len(unnamed_bg)} unclassified = {len(bg_candidates)} total')


if __name__ == '__main__':
    main()
