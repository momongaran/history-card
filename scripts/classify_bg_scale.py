#!/usr/bin/env python3
"""
classify_bg_scale.py — G-4: BG粒度3層分類

no12「背景＝地形」メタファーに基づき、83件のBGをスケール3層に分類:
  macro   — 大地形: 長期持続する構造的基盤（律令制、天皇制、仏教、対外体制など）
  local   — 局所地形: 特定期間・勢力の権力構造・制度（特定政権、執権体制、荘園制など）
  trigger — 発火点: 短期・限定的な状況要因（後継争い、浪人問題、特定の対立など）

分類基準:
  1. 持続期間（phases）: 長い → macro
  2. effectLog件数: 多い → macro寄り
  3. bgLineage接続数: 多い → macro寄り
  4. type: institution/culture → macro寄り、conflict → trigger寄り
  5. 手動オーバーライド: 歴史的知識に基づく調整
"""

import json
from collections import Counter, defaultdict


def load_data():
    with open("data/framework_output_v3_9.json", "r") as f:
        return json.load(f)


def calc_duration(bg):
    """phasesから持続年数を推定"""
    phases = bg.get("phases", [])
    if not phases:
        return 0
    years = []
    for p in phases:
        period = p.get("period", "")
        if "-" in period:
            parts = period.split("-")
            try:
                years.extend([int(parts[0]), int(parts[1])])
            except ValueError:
                pass
    if len(years) >= 2:
        return max(years) - min(years)
    return 0


def calc_lineage_degree(bg_id, lineage):
    """bgLineageでの接続数"""
    return sum(1 for l in lineage if l["from"] == bg_id or l["to"] == bg_id)


def classify(data):
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    lineage = data.get("bgLineage", [])

    # 各BGのメトリクス計算
    metrics = {}
    for bg in data["backgroundElements"]:
        bid = bg["bgId"]
        duration = calc_duration(bg)
        eff_count = len(bg.get("effectLog", []))
        lineage_deg = calc_lineage_degree(bid, lineage)
        metrics[bid] = {
            "duration": duration,
            "effectLog": eff_count,
            "lineage_degree": lineage_deg,
            "type": bg["type"],
            "label": bg["label"],
        }

    # === 手動分類（歴史的知識に基づく） ===
    manual = {
        # macro: 長期持続する構造的基盤
        "BG_010": "macro",   # 中央集権化 — 古代〜近代を貫く構造テーマ
        "BG_013": "macro",   # 律令制 — 7c〜10cの基盤制度
        "BG_017": "macro",   # 正統性・権威 — 全時代を貫く文化的基盤
        "BG_004": "macro",   # 租税・財政 — 全時代の資源基盤
        "BG_007": "macro",   # 交易・貿易 — 長期的経済基盤
        "BG_020": "macro",   # 商業経済 — 中世〜近世の経済基盤
        "BG_011": "macro",   # 仏教(古代) — 文化的大地形
        "BG_050": "macro",   # 仏教(平安) — 文化的大地形
        "BG_069": "macro",   # 仏教(近世) — 文化的大地形
        "BG_038": "macro",   # 儒学思想 — 思想的大地形
        "BG_066": "macro",   # 記紀・史書 — 知識基盤
        "BG_054": "macro",   # 天皇・朝廷(古代) — 政体の大地形
        "BG_040": "macro",   # 天皇・朝廷(平安) — 政体の大地形
        "BG_046": "macro",   # 天皇・朝廷(中世) — 政体の大地形
        "BG_026": "macro",   # 天皇・朝廷(近世) — 政体の大地形
        "BG_027": "macro",   # 皇位継承(古代) — 制度的大地形
        "BG_028": "macro",   # 皇位継承(平安)
        "BG_059": "macro",   # 皇位継承(中世)
        "BG_082": "macro",   # 皇位継承(近現代)
        "BG_012": "macro",   # 唐との関係 — 古代の対外大地形
        "BG_022": "macro",   # 朝鮮半島情勢 — 古代の対外大地形
        "BG_078": "macro",   # 隋との関係 — 古代の対外大地形
        "BG_063": "macro",   # 都城制 — 制度的大地形
        "BG_068": "macro",   # 人民把握制度 — 制度的大地形
        "BG_058": "macro",   # 班田収授制 — 制度的大地形
        "BG_029": "macro",   # 九州 — 地理的大地形
        "BG_034": "macro",   # 東北/蝦夷 — 地理的大地形
        "BG_060": "macro",   # 自然災害 — 環境的大地形
        "BG_044": "macro",   # 飢饉・疫病 — 環境的大地形
        "BG_043": "macro",   # 防衛体制 — 軍事的大地形

        # local: 特定期間の権力構造・制度
        "BG_002": "local",   # 摂関家(藤原氏) — 平安期の権力構造
        "BG_014": "local",   # 院政体制 — 平安末〜鎌倉初の権力構造
        "BG_053": "local",   # 外戚政治 — 平安期の権力構造
        "BG_036": "local",   # 藤原氏(奈良) — 奈良期の権力構造
        "BG_023": "local",   # 蘇我氏 — 古代の権力構造
        "BG_005": "local",   # 豪族勢力 — 古代の権力構造
        "BG_019": "local",   # 源氏 — 中世の勢力
        "BG_021": "local",   # 平氏 — 中世の勢力
        "BG_024": "local",   # 北条執権体制 — 鎌倉期の権力構造
        "BG_025": "local",   # 足利氏 — 室町期の権力構造
        "BG_001": "local",   # 織田政権 — 安土桃山期
        "BG_003": "local",   # 豊臣政権 — 安土桃山期
        "BG_006": "local",   # 徳川家 — 近世の権力構造
        "BG_015": "local",   # 大名勢力 — 中世〜近世の権力構造
        "BG_031": "local",   # 雄藩連合 — 幕末の勢力
        "BG_055": "local",   # 明治政府 — 近代の権力構造
        "BG_009": "local",   # 御家人制 — 鎌倉期の制度
        "BG_039": "local",   # 国司行政 — 古代〜中世の制度
        "BG_047": "local",   # 守護・地頭制 — 中世の制度
        "BG_065": "local",   # 荘園制 — 中世の制度
        "BG_067": "local",   # 鎖国体制 — 近世の制度
        "BG_070": "local",   # 室町幕府 — 室町期の制度
        "BG_077": "local",   # 鎌倉幕府 — 鎌倉期の制度
        "BG_083": "local",   # 藩体制 — 近世の制度
        "BG_081": "local",   # 検地・兵農分離 — 近世の制度
        "BG_074": "local",   # 朝廷統制 — 近世の制度
        "BG_056": "local",   # 条約体制 — 近代の制度
        "BG_064": "local",   # 明治憲法体制 — 近代の制度
        "BG_062": "local",   # 議会制 — 近代の制度
        "BG_073": "local",   # 戦後憲法体制 — 現代の制度
        "BG_018": "local",   # 武士層(中世) — 中世の社会構造
        "BG_042": "local",   # 武士層(近世) — 近世の社会構造
        "BG_057": "local",   # 武士層(平安) — 平安期の社会構造
        "BG_035": "local",   # 海上勢力 — 中世〜近世の勢力
        "BG_030": "local",   # 南蛮貿易/宣教 — 近世の対外
        "BG_045": "local",   # キリスト教 — 近世の文化
        "BG_052": "local",   # 国風文化 — 平安期の文化
        "BG_008": "local",   # 対外関係(近代) — 近代の対外
        "BG_016": "local",   # 対英関係 — 近代の対外
        "BG_033": "local",   # 対ロシア関係 — 近代の対外
        "BG_079": "local",   # 対米関係 — 近現代の対外
        "BG_048": "local",   # GHQ占領 — 現代の対外
        "BG_051": "local",   # 冷戦構造 — 現代の対外
        "BG_049": "local",   # インフラ・復興 — 現代の資源
        "BG_037": "local",   # 開国と攘夷 — 幕末の状況

        # trigger: 短期・限定的な状況要因
        "BG_041": "trigger", # 後継争い — 特定イベントの引き金
        "BG_032": "trigger", # 南北朝分裂 — 特定期間の対立状況
        "BG_071": "trigger", # 応仁の乱と秩序崩壊 — 特定イベント
        "BG_072": "trigger", # 戦国の分裂 — 特定期間の混乱状況
        "BG_075": "trigger", # 浪人問題 — 近世初期の限定的問題
        "BG_076": "trigger", # 豊臣家問題 — 近世初期の限定的問題
        "BG_080": "trigger", # 承久の乱後の体制 — 特定イベント後の状況
        "BG_061": "trigger", # 蒙古の脅威 — 特定期間の外圧
    }

    # 分類結果をBGに付与
    results = {}
    for bg in data["backgroundElements"]:
        bid = bg["bgId"]
        if bid in manual:
            scale = manual[bid]
        else:
            # 自動分類（フォールバック）
            m = metrics[bid]
            score = 0
            # 持続期間
            if m["duration"] >= 200:
                score += 2
            elif m["duration"] >= 80:
                score += 1
            # effectLog
            if m["effectLog"] >= 10:
                score += 2
            elif m["effectLog"] >= 5:
                score += 1
            # type
            if m["type"] in ("culture", "knowledge"):
                score += 1
            elif m["type"] == "conflict":
                score -= 1
            # lineage
            if m["lineage_degree"] >= 3:
                score += 1

            if score >= 3:
                scale = "macro"
            elif score >= 1:
                scale = "local"
            else:
                scale = "trigger"

        results[bid] = scale
        bg["scale"] = scale

    return data, results


def main():
    data = load_data()
    data, results = classify(data)

    # 統計
    dist = Counter(results.values())
    print(f"=== BG粒度3層分類完了 ===")
    print(f"  macro:   {dist['macro']}件（大地形）")
    print(f"  local:   {dist['local']}件（局所地形）")
    print(f"  trigger: {dist['trigger']}件（発火点）")

    # 各層の一覧
    bgs = {bg["bgId"]: bg for bg in data["backgroundElements"]}
    for scale in ["macro", "local", "trigger"]:
        print(f"\n--- {scale} ---")
        for bid, s in sorted(results.items()):
            if s == scale:
                bg = bgs[bid]
                print(f"  {bid} | {bg['type']:16s} | {bg['label']}")

    # 書き込み
    with open("data/framework_output_v3_9.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n書き込み完了: data/framework_output_v3_9.json")


if __name__ == "__main__":
    main()
