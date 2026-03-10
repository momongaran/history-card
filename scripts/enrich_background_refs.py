#!/usr/bin/env python3
"""
enrich_background_refs.py — A-1 + G-1: background.refs の補完と型付け

1. 空refsの61件にBG参照を推定付与
2. 全refsを {bgId, role} 形式に拡張（role: drives/pressures/supports/enables）
"""

import json
import re
from collections import defaultdict

def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)

def build_keyword_to_bg(bgs):
    """背景要素のlabelからキーワード→BG_IDマッピングを構築"""
    mapping = {}
    for bg in bgs:
        bgid = bg["bgId"]
        label = bg["label"]
        # 直接マッピング（ラベルそのもの）
        mapping[label] = bgid
        # キーワード抽出
        # 例: "摂関家(藤原氏)" → ["摂関家", "藤原氏", "摂関"]
        # 例: "豪族勢力" → ["豪族"]
        keywords = _extract_keywords(label)
        for kw in keywords:
            if kw not in mapping:
                mapping[kw] = bgid
            # 複数BGが同じキーワードを持つ場合はリストに
            elif isinstance(mapping[kw], list):
                if bgid not in mapping[kw]:
                    mapping[kw].append(bgid)
            elif mapping[kw] != bgid:
                mapping[kw] = [mapping[kw], bgid]
    return mapping

def _extract_keywords(label):
    """BGラベルからマッチ用キーワードを抽出"""
    keywords = []
    # 括弧内を分離
    main = re.sub(r'[（(].*?[)）]', '', label).strip()
    parens = re.findall(r'[（(](.*?)[)）]', label)

    keywords.append(main)
    keywords.extend(parens)

    # 個別キーワード
    kw_map = {
        "織田政権": ["織田", "信長"],
        "摂関家(藤原氏)": ["摂関", "藤原", "外戚"],
        "豊臣政権": ["豊臣", "秀吉"],
        "租税・財政": ["租税", "財政", "税", "年貢"],
        "豪族勢力": ["豪族"],
        "徳川家": ["徳川", "家康", "幕府"],
        "交易・貿易": ["交易", "貿易", "商業"],
        "対外関係(近代)": ["対外", "条約", "開国"],
        "御家人制": ["御家人"],
        "中央集権化": ["中央集権", "集権"],
        "仏教(古代)": ["仏教"],
        "唐との関係": ["唐", "遣唐"],
        "律令制": ["律令"],
        "院政体制": ["院政", "上皇"],
        "大名勢力": ["大名"],
        "対英関係": ["イギリス", "英"],
        "正統性・権威": ["正統", "権威", "正当"],
        "武士層(中世)": ["武士", "御家人"],
        "源氏": ["源", "頼朝", "義経"],
        "商業経済": ["商業", "経済"],
        "平氏": ["平氏", "平家", "清盛"],
        "朝鮮半島情勢": ["朝鮮", "百済", "新羅", "高句麗", "伽耶", "半島"],
        "蘇我氏": ["蘇我", "馬子"],
        "北条執権体制": ["北条", "執権"],
        "足利氏": ["足利"],
        "天皇・朝廷(近世)": [],
        "皇位継承(古代)": ["皇位", "継承", "皇子"],
        "皇位継承(平安)": ["皇位", "継承"],
        "九州": ["九州", "筑紫"],
        "南蛮貿易/宣教": ["南蛮", "宣教", "キリシタン"],
        "雄藩連合": ["雄藩", "薩摩", "長州", "土佐", "肥前"],
        "南北朝分裂": ["南北朝", "後醍醐"],
        "対ロシア関係": ["ロシア", "露"],
        "東北/蝦夷": ["蝦夷", "東北", "奥州"],
        "海上勢力": ["海上", "海賊", "水軍"],
        "藤原氏(奈良)": ["藤原", "四兄弟", "不比等", "奈良"],
        "開国と攘夷": ["開国", "攘夷", "黒船", "ペリー"],
        "儒学思想": ["儒学", "朱子学"],
        "国司行政": ["国司"],
        "天皇・朝廷(平安)": ["天皇", "朝廷"],
        "後継争い": ["後継", "継承争い"],
        "武士層(近世)": ["武士"],
        "防衛体制": ["防衛", "軍事"],
        "飢饉・疫病": ["飢饉", "疫病", "大飢饉"],
        "キリスト教": ["キリスト", "宣教"],
        "天皇・朝廷(中世)": ["天皇", "朝廷"],
        "守護・地頭制": ["守護", "地頭"],
        "GHQ占領": ["GHQ", "占領", "連合国"],
        "インフラ・復興": ["復興", "インフラ"],
        "仏教(平安)": ["仏教", "延暦寺", "僧兵"],
        "冷戦構造": ["冷戦", "東西"],
        "国風文化": ["国風"],
        "外戚政治": ["外戚"],
        "天皇・朝廷(古代)": ["天皇", "大王"],
        "明治政府": ["明治政府", "新政府"],
        "条約体制": ["条約"],
        "武士層(平安)": ["武士"],
        "班田収授制": ["班田"],
        "皇位継承(中世)": ["皇位", "継承"],
        "自然災害": ["災害", "地震", "噴火", "津波"],
        "蒙古の脅威": ["蒙古", "元寇", "モンゴル"],
        "議会制": ["議会", "国会"],
        "都城制": ["都城", "遷都"],
        "明治憲法体制": ["憲法", "明治憲法"],
        "荘園制": ["荘園"],
        "記紀・史書": ["記紀", "古事記", "日本書紀"],
        "鎖国体制": ["鎖国"],
        "人民把握制度": ["人民", "戸籍"],
        "仏教(近世)": ["仏教", "寺"],
        "室町幕府": ["室町", "幕府"],
        "応仁の乱と秩序崩壊": ["応仁"],
        "戦国の分裂": ["戦国"],
        "戦後憲法体制": ["戦後", "日本国憲法"],
        "朝廷統制": ["朝廷統制", "禁中"],
        "浪人問題": ["浪人"],
        "豊臣家問題": ["豊臣"],
        "鎌倉幕府": ["鎌倉"],
        "隋との関係": ["隋"],
        "対米関係": ["アメリカ", "米", "日米"],
        "承久の乱後の体制": ["承久"],
        "検地・兵農分離": ["検地", "兵農分離"],
        "皇位継承(近現代)": ["皇位"],
        "藩体制": ["藩"],
    }

    for full_label, kws in kw_map.items():
        if label == full_label or main == full_label.split("(")[0].split("（")[0]:
            keywords.extend(kws)
            break

    return keywords


def match_bgs_for_label(label, bgs, keyword_to_bg):
    """背景labelからマッチするBG IDのリストを返す"""
    matched = set()

    for bg in bgs:
        bgid = bg["bgId"]
        bg_label = bg["label"]
        bg_keywords = _extract_keywords(bg_label)

        for kw in bg_keywords:
            if len(kw) >= 2 and kw in label:
                matched.add(bgid)
                break

    return sorted(matched) if matched else []


def infer_role(bname, bg_type, fnameCategory):
    """Bname + BG type + FnameCategory から role を推定"""
    # Bname別のデフォルトrole
    bname_role = {
        "権力集中": "drives",
        "外圧環境": "pressures",
        "勢力対立": "pressures",
        "思想潮流": "drives",
        "経済圧": "pressures",
        "複合背景": "drives",  # デフォルト、個別に調整
        "制度疲弊": "pressures",
        "制度的矛盾": "pressures",
    }

    role = bname_role.get(bname, "drives")

    # BG typeによる調整
    if bg_type == "institution":
        if bname in ("制度疲弊", "制度的矛盾"):
            role = "pressures"
        elif bname == "権力集中":
            role = "supports"
        else:
            role = "enables"
    elif bg_type == "external":
        role = "pressures"
    elif bg_type == "culture":
        if bname == "思想潮流":
            role = "drives"
        else:
            role = "supports"
    elif bg_type == "resource":
        if bname == "経済圧":
            role = "pressures"
        else:
            role = "supports"
    elif bg_type == "conflict":
        role = "pressures"
    elif bg_type == "demographic":
        role = "supports"
    elif bg_type == "knowledge":
        role = "enables"

    return role


def enrich(data):
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    bg_list = data["backgroundElements"]
    keyword_to_bg = build_keyword_to_bg(bg_list)

    stats = {
        "refs_filled": 0,
        "refs_typed": 0,
        "refs_already_had": 0,
        "total_backgrounds": 0,
    }

    for ev in data["events"]:
        fname_cat = ev["causalFrame"].get("fnameCategory", "")
        for bg_entry in ev["causalFrame"].get("background", []):
            stats["total_backgrounds"] += 1
            bname = bg_entry.get("bname", "")
            old_refs = bg_entry.get("refs", [])

            # Step 1: 空refsの補完
            if not old_refs:
                inferred = match_bgs_for_label(bg_entry["label"], bg_list, keyword_to_bg)
                if inferred:
                    old_refs = inferred
                    stats["refs_filled"] += 1
                else:
                    # マッチできない場合は空のまま
                    bg_entry["refs"] = []
                    continue
            else:
                stats["refs_already_had"] += 1

            # Step 2: 型付き refs に変換
            new_refs = []
            for ref in old_refs:
                bgid = ref if isinstance(ref, str) else ref.get("bgId", "")
                bg_info = bgs.get(bgid, {})
                bg_type = bg_info.get("type", "")
                role = infer_role(bname, bg_type, fname_cat)
                new_refs.append({"bgId": bgid, "role": role})
                stats["refs_typed"] += 1

            bg_entry["refs"] = new_refs

    return data, stats


def main():
    data = load_data()

    # バックアップ用に元の統計を表示
    empty_before = sum(
        1 for ev in data["events"]
        for bg in ev["causalFrame"].get("background", [])
        if not bg.get("refs")
    )
    print(f"処理前: refs空 = {empty_before}件")

    data, stats = enrich(data)

    # 処理後の統計
    empty_after = sum(
        1 for ev in data["events"]
        for bg in ev["causalFrame"].get("background", [])
        if not bg.get("refs")
    )

    print(f"処理後: refs空 = {empty_after}件")
    print(f"補完: {stats['refs_filled']}件")
    print(f"型付け: {stats['refs_typed']}件")
    print(f"既存refs: {stats['refs_already_had']}件")
    print(f"背景エントリ総数: {stats['total_backgrounds']}件")

    # role分布
    from collections import Counter
    roles = Counter()
    for ev in data["events"]:
        for bg in ev["causalFrame"].get("background", []):
            for ref in bg.get("refs", []):
                if isinstance(ref, dict):
                    roles[ref["role"]] += 1
    print(f"\nrole分布:")
    for role, count in roles.most_common():
        print(f"  {role}: {count}")

    # 出力
    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
