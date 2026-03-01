#!/usr/bin/env python3
"""
v3.4 F要素再分類スクリプト
F-UNC-00（未分類）の208件を新カテゴリにルールベースで再分類する。

Usage:
  python3 scripts/classify_f_categories.py --dry-run   # プレビュー
  python3 scripts/classify_f_categories.py              # 上書き保存
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# --- 分類ルール ---
# (category, subCategory, description, pattern_func)
# 優先度順: 上から評価し最初にマッチしたものを採用

def make_keyword_matcher(keywords):
    """キーワードリストのいずれかを含むか判定する関数を返す"""
    def matcher(label):
        return any(kw in label for kw in keywords)
    return matcher

def make_regex_matcher(pattern):
    """正規表現でマッチするか判定する関数を返す"""
    compiled = re.compile(pattern)
    def matcher(label):
        return compiled.search(label) is not None
    return matcher

RULES = [
    # F-CNF-02: 武力衝突化（決戦テンプレート）
    ("F-CNF", "F-CNF-02", "武力衝突化",
     make_keyword_matcher(["軍事衝突が臨界に達し", "決戦化した"])),

    # F-CNF-01: 勢力間対立（対立テンプレート）
    ("F-CNF", "F-CNF-01", "勢力間対立",
     make_keyword_matcher([
         "利害対立", "武力衝突に発展",
         "豪族対立", "対立が制度内で解けず",
         "対立が深まり",
         "蜂起した", "武力蜂起",
         "闘争", "衝突", "蜂起",
         "陰謀が発覚", "弾圧",
     ])),

    # F-CTD-02: 財政・治安問題
    ("F-CTD", "F-CTD-02", "財政・治安問題",
     make_keyword_matcher([
         "財政・治安・土地支配などの問題が顕在化",
         "財政", "治安",
     ])),

    # F-CTD-01: 制度機能不全
    ("F-CTD", "F-CTD-01", "制度機能不全",
     make_keyword_matcher([
         "既存運用の矛盾や危機対応の必要から",
         "矛盾", "機能不全", "制度",
         "問題が顕在化",
         "規則", "限界",
     ])),

    # F-ACT-02: 死去・崩御
    ("F-ACT", "F-ACT-02", "死去・崩御",
     make_keyword_matcher([
         "崩御", "死去", "自害", "戦死", "没した",
         "暗殺",
     ])),

    # F-EXT-01: 対外圧力
    ("F-EXT", "F-EXT-01", "対外圧力",
     make_keyword_matcher([
         "国際環境の圧力",
         "外交方針を制度として固定",
         "外圧", "対外",
         "鎖国", "外国船",
         "条約", "国際",
         "唐・新羅からの侵攻",
         "清の敗北",
         "占領", "主権回復",
         "冷戦", "安全保障",
         "ニクソン", "返還交渉",
         "連盟総会",
         "ナショナリズム",
         "ドイツ権益",
         "サンフランシスコ平和条約",
     ])),

    # F-ACT-01: 人物の決断・行動
    ("F-ACT", "F-ACT-01", "人物の決断・行動",
     make_keyword_matcher([
         "決意", "決断", "判断",
         "挙兵", "挙事",
         "派遣", "漂着", "伝来", "上陸",
         "擁立", "即位", "就任", "昇進",
         "追放", "左遷", "降伏",
         "入京", "上洛", "入城",
         "造営", "鋳造", "編纂", "完成",
         "設置", "開い", "制定",
         "焼き払", "急襲", "滅ぼし",
         "降伏", "臣従",
         "猶子", "冊封",
         "献上", "布教",
         "実権", "主導権",
         "信任を得て",
         "摂政に就任",
         "記録所",
         "院御所で政務",
         "院庁を拠点",
         "健児として採用",
         "参陣",
         "集結",
         "動員",
         "認めさせた", "獲得",
         "鉄砲", "伝えられた",
         "キリスト教",
         "仏教",
         "鳥居耀蔵",
         "先進5か国",
         "蔵相",
         "聖断",
         "ポツダム宣言",
         "民主化",
         "占領政策",
         "断行",
     ])),
]


def classify_label(label):
    """ラベルにルールを順に適用し、最初にマッチしたカテゴリを返す。
    マッチしなければ None を返す。"""
    for category, sub_category, _desc, matcher in RULES:
        if matcher(label):
            return category, sub_category
    return None


def main():
    dry_run = "--dry-run" in sys.argv

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 統計
    total_f = 0
    unc00_count = 0
    classified = Counter()
    remaining_unc00 = []
    changes = []

    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            if elem.get("layer") != "F":
                continue
            total_f += 1
            if elem.get("subCategory") != "F-UNC-00":
                continue
            unc00_count += 1

            label = elem.get("label", "")
            result = classify_label(label)
            if result:
                cat, sub = result
                classified[sub] += 1
                changes.append({
                    "eventId": fv["eventId"],
                    "label": label[:60],
                    "old": "F-UNC/F-UNC-00",
                    "new": f"{cat}/{sub}",
                })
                if not dry_run:
                    elem["category"] = cat
                    elem["subCategory"] = sub
            else:
                remaining_unc00.append((fv["eventId"], label[:80]))

    # 結果表示
    print(f"=== v3.4 F要素再分類 {'(dry-run)' if dry_run else '(実行)'} ===")
    print(f"F要素総数: {total_f}")
    print(f"F-UNC-00対象: {unc00_count}")
    print(f"分類成功: {sum(classified.values())}")
    print(f"F-UNC-00残存: {len(remaining_unc00)}")
    print()

    print("--- 分類先の内訳 ---")
    for sub, count in sorted(classified.items()):
        print(f"  {sub}: {count}")
    print()

    print(f"--- 分類済みサンプル (先頭10件) ---")
    for ch in changes[:10]:
        print(f"  {ch['eventId']}: {ch['old']} → {ch['new']}  [{ch['label']}]")
    print()

    print(f"--- F-UNC-00残存 ({len(remaining_unc00)}件) ---")
    for eid, lab in remaining_unc00:
        print(f"  {eid}: {lab}")

    if not dry_run:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n>>> {DATA_FILE} を上書き保存しました。")
    else:
        print(f"\n>>> dry-run: ファイルは変更されていません。")


if __name__ == "__main__":
    main()
