#!/usr/bin/env python3
"""
classify_fname_params.py — B-1 + B-3: fnamePattern・slotFunction の付与

既存のfname・params.typeは保持したまま、上位分類フィールドを追加:
- causalFrame.fnamePattern — 帰結パターン（20種）
- causalFrame.params[].slotFunction — スロット機能（8種）
"""

import json
from collections import Counter, defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


# === fnamePattern 分類ルール ===
# 優先度順に評価（最初にマッチしたものを採用）
FNAME_PATTERN_RULES = [
    # (パターン名, キーワードリスト)
    ("蜂起反乱", ["蜂起", "反乱", "暴動", "武力で反発"]),
    ("権力排除", ["排除", "暗殺", "粛清", "処罰", "廃立", "讒言", "斬殺"]),
    ("武力衝突", ["武力衝突", "武力決着", "武力対決", "軍事衝突", "会戦", "決戦",
                 "戦争", "開戦", "全面戦争", "砲撃", "内乱", "武力抗争",
                 "武力対立", "大乱", "内戦", "軍事的対峙"]),
    ("軍事征討", ["征討", "鎮圧", "制圧", "遠征", "打払", "奇襲", "急襲",
                 "包囲", "撃退", "襲撃", "敗北", "防衛", "防塁"]),
    ("降伏統一", ["降伏", "統一を完了", "屈服", "壊走", "併合"]),
    ("政権崩壊", ["崩壊", "壊滅", "滅", "消滅", "失脚", "断絶", "離反",
                 "寝返", "瓦解", "分裂", "決裂"]),
    ("権力継承", ["後継", "即位", "譲位", "返上", "就任", "擁立", "世襲",
                 "権威者の死", "崩御"]),
    ("権力掌握", ["実権を掌握", "権力を確立", "主導権を握", "実権を握",
                 "補佐者として", "摂政", "独占", "補佐者を任じ",
                 "勢力基盤を確立"]),
    ("政権転換", ["クーデタ", "転換", "路線", "親政", "復権"]),
    ("外圧解放", ["として解放される", "として矛盾を露呈"]),
    ("制度制定", ["制定", "法典", "成文", "体系化", "施行", "法令",
                 "法的に固定", "制度として固定"]),
    ("制度改革", ["改革", "是正", "改変", "方針化", "債務免除", "補填"]),
    ("制度矛盾", ["矛盾", "露呈", "限界", "欠陥", "形骸", "無効化"]),
    ("対外接触", ["来航", "伝来", "渡航", "派遣", "通交", "上陸",
                 "無断", "危機意識"]),
    ("外交対応", ["外交", "条約", "同盟", "講和", "鎖国", "開国",
                 "通商", "禁輸", "封鎖", "朝貢", "窓口", "占領",
                 "返還", "施政権"]),
    ("文化事業", ["編纂", "国史", "記紀", "文化", "大仏", "出版",
                 "イベントを開催", "学習を開始"]),
    ("宗教変動", ["仏教", "宗教", "キリスト", "布教", "宣教", "弾圧",
                 "末法", "終末"]),
    ("建設遷都", ["建設", "造営", "城", "都城", "遷都", "移転",
                 "離脱"]),
    ("社会変動", ["飢饉", "地震", "噴火", "津波", "災害", "疫病",
                 "大衆化", "困窮", "直訴", "負担"]),
    ("統治確立", ["統治", "支配", "統制", "把握", "検地", "分離",
                 "制度の基盤", "中央集権", "行政", "既成事実"]),
]


def classify_fname_pattern(fname):
    """fnameから帰結パターンを分類"""
    for pattern_name, keywords in FNAME_PATTERN_RULES:
        if any(kw in fname for kw in keywords):
            return pattern_name
    return "その他"


# === slotFunction 分類ルール ===
SLOT_FUNCTION_RULES = [
    ("前提状態", ["状態", "基盤", "前提", "構造", "秩序", "体制", "情勢",
                 "環境", "均衡", "安定", "支配", "統治", "存続", "維持"]),
    ("トリガー", ["危機", "不在", "空白", "崩壊", "死去", "消滅", "弱体",
                 "衰退", "来航", "侵攻", "噴火", "地震", "飢饉", "疫病",
                 "急死", "断絶", "失脚", "発覚", "露顕", "密告", "脅威",
                 "決裂", "行き詰", "接近", "上陸"]),
    ("行為主体", ["権力者", "実力者", "外戚", "将軍", "天皇", "朝廷",
                 "幕府", "大名", "武士", "僧", "民衆", "商人", "知識人",
                 "指導者", "補佐者", "側近", "高官", "国司", "守護"]),
    ("圧力源", ["圧力", "不満", "緊張", "対立", "矛盾", "反発", "圧迫",
               "恐怖", "不安", "窮乏", "困窮", "恩賞不足", "挑発"]),
    ("行為手段", ["排除", "暗殺", "蜂起", "武力", "軍事", "遠征", "改革",
                 "制定", "建設", "編纂", "征討", "奇襲", "弾圧", "禁止",
                 "没収", "処罰", "統制", "動員", "襲撃", "斬殺", "焼討",
                 "征服", "侵略", "砲撃", "布教", "渡航", "派遣"]),
    ("対象", ["政敵", "抵抗", "対抗", "反対", "敵対", "障害", "残存",
             "反逆", "異端"]),
    ("解放形態", ["戦争", "暴動", "条約", "同盟", "法令", "弾圧として",
                 "蜂起として", "開戦", "講和", "一揆", "打払"]),
    ("帰結", ["統一", "確立", "崩壊", "壊滅", "転換", "成立", "開始",
             "終結", "降伏", "即位", "就任", "完成", "施行", "滅亡",
             "独立", "自治", "復活", "合意", "合流", "形成"]),
]


def classify_slot_function(param_type):
    """params.typeからスロット機能を分類"""
    for func_name, keywords in SLOT_FUNCTION_RULES:
        if any(kw in param_type for kw in keywords):
            return func_name
    return "状況記述"  # デフォルト: 具体的状況の記述


def main():
    data = load_data()

    # === Phase 1: fnamePattern ===
    pattern_dist = Counter()
    for ev in data["events"]:
        cf = ev["causalFrame"]
        pattern = classify_fname_pattern(cf["fname"])
        cf["fnamePattern"] = pattern
        pattern_dist[pattern] += 1

    print("=== fnamePattern 分布 ===")
    for p, c in pattern_dist.most_common():
        print(f"  {p:12s}: {c:3d}件")
    print(f"  合計: {sum(pattern_dist.values())}件, パターン数: {len(pattern_dist)}種")

    # === Phase 2: slotFunction ===
    func_dist = Counter()
    pos_func = Counter()
    for ev in data["events"]:
        for i, p in enumerate(ev["causalFrame"].get("params", [])):
            func = classify_slot_function(p["type"])
            p["slotFunction"] = func
            func_dist[func] += 1
            pos_func[(i + 1, func)] += 1

    print(f"\n=== slotFunction 分布 ===")
    for f, c in func_dist.most_common():
        print(f"  {f:8s}: {c:3d}件")
    print(f"  合計: {sum(func_dist.values())}件, 機能数: {len(func_dist)}種")

    print(f"\n=== 位置別slotFunction ===")
    for pos in [1, 2, 3]:
        items = [(f, c) for (p, f), c in pos_func.items() if p == pos]
        if items:
            print(f"  [%{pos}]: ", end="")
            for f, c in sorted(items, key=lambda x: -x[1])[:4]:
                print(f"{f}({c}) ", end="")
            print()

    # === Phase 3: fnamePattern × fnameCategory クロス集計 ===
    print(f"\n=== fnamePattern × fnameCategory ===")
    cross = Counter()
    for ev in data["events"]:
        cf = ev["causalFrame"]
        cross[(cf["fnamePattern"], cf["fnameCategory"])] += 1

    cats = ["圧力解放", "主体的行為", "矛盾露呈", "外生衝撃", "偶発連鎖", "権力移行"]
    print(f"{'Pattern':<14s}", end="")
    for c in cats:
        print(f" {c[:4]:>5s}", end="")
    print(f" {'計':>4s}")
    for pat in [p for p, _ in pattern_dist.most_common()]:
        print(f"{pat:<14s}", end="")
        total = 0
        for c in cats:
            v = cross.get((pat, c), 0)
            total += v
            print(f" {v:5d}", end="")
        print(f" {total:4d}")

    # 書き込み
    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
