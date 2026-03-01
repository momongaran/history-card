#!/usr/bin/env python3
"""
fix_label_style.py — B層ラベルの文体違反を機械的に修正するスクリプト

v3.6仕様: B層は現在形（〜している）を正とし、過去形（〜していた）は不可。

使い方:
  python scripts/fix_label_style.py --dry-run   # 変更予定を表示（ファイル変更なし）
  python scripts/fix_label_style.py              # framework_output_v3_3.json を直接更新
"""
import argparse
import json
import re
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# ── 機械的変換ルール（B層のみ適用） ──────────────────────
# 各ルール: (regex_pattern, replacement)
# 順序に意味がある: 長いパターンを先にマッチさせる
AUTO_RULES = [
    # 文法エラー修正（全層）
    (re.compile(r"なかっていた"), "なかった"),
    # B層 過去形→現在形（継続態）
    (re.compile(r"されていた($|(?=[。、）」]))"), "されている"),
    (re.compile(r"していた($|(?=[。、）」]))"), "している"),
    (re.compile(r"にあった($|(?=[。、）」]))"), "にある"),
    (re.compile(r"であった($|(?=[。、）」]))"), "である"),
    (re.compile(r"いなかった($|(?=[。、）」]))"), "いない"),
    (re.compile(r"できなかった($|(?=[。、）」]))"), "できない"),
    (re.compile(r"なっていた($|(?=[。、）」]))"), "なっている"),
    (re.compile(r"れていた($|(?=[。、）」]))"), "れている"),
    (re.compile(r"めていた($|(?=[。、）」]))"), "めている"),
    (re.compile(r"ていた($|(?=[。、）」]))"), "ている"),
    # B層 過去形→現在形（末尾パターン追加）
    (re.compile(r"つつあった$"), "つつある"),
    (re.compile(r"があった$"), "がある"),
    (re.compile(r"少なかった$"), "少ない"),
    (re.compile(r"大きかった$"), "大きい"),
    (re.compile(r"なかった$"), "ない"),
    (re.compile(r"となった$"), "となっている"),
    (re.compile(r"迫られた$"), "迫られている"),
    (re.compile(r"存在した$"), "存在する"),
]

# B層 文中パターン（個別対応）
B_MID_RULES = [
    (re.compile(r"であったため"), "であり"),
    (re.compile(r"だったが"), "だが"),
]

# 「なかっていた」は全層で修正（文法エラー）
GRAMMAR_FIX = re.compile(r"なかっていた")

# ── 手動修正検出パターン ─────────────────────────
# B層: 完了形（「〜した」で終わるラベル）
B_PAST_COMPLETE = re.compile(r"(?:した|進めた|結ばれた|行った|なった|れた|された|めた|った)$")

# B層: 不完全断片（文として成立していない可能性）
B_INCOMPLETE_EVENTS = {"EV_p1952_03", "EV_p1635_02"}

# F層: 状態記述（「〜であった」「〜していた」等）
F_STATE_PATTERN = re.compile(r"(?:であった|していた|にあった|されていた|必要があった|ていた)$")


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def apply_auto_fixes(label, layer):
    """機械的修正を適用。変更があれば (new_label, applied_rules) を返す。"""
    new_label = label
    applied = []

    # 文法エラー「なかっていた」は全層で修正
    if GRAMMAR_FIX.search(new_label):
        new_label = GRAMMAR_FIX.sub("なかった", new_label)
        applied.append("なかっていた→なかった")

    # B層のみ: 過去形→現在形
    if layer == "B":
        for pattern, replacement in AUTO_RULES[1:]:  # skip grammar fix (already done)
            m = pattern.search(new_label)
            if m:
                new_label = pattern.sub(replacement, new_label)
                applied.append(f"{pattern.pattern}→{replacement}")
        # B層 文中パターン
        for pattern, replacement in B_MID_RULES:
            m = pattern.search(new_label)
            if m:
                new_label = pattern.sub(replacement, new_label)
                applied.append(f"{pattern.pattern}→{replacement}")

    if new_label != label:
        return new_label, applied
    return None, []


def detect_manual_issues(label, layer, event_id):
    """手動修正が必要なラベルを検出。"""
    issues = []

    if layer == "B":
        # 完了形チェック
        if B_PAST_COMPLETE.search(label):
            issues.append("B完了形（手動リライト必要）")
        # 不完全断片チェック
        if event_id in B_INCOMPLETE_EVENTS:
            issues.append("B不完全断片（手動リライト必要）")

    if layer == "F":
        if F_STATE_PATTERN.search(label):
            issues.append("F状態記述（手動リライト必要）")

    return issues


def main():
    parser = argparse.ArgumentParser(description="B層ラベル文体違反の修正")
    parser.add_argument("--dry-run", action="store_true",
                        help="変更箇所を表示するが、ファイルは変更しない")
    args = parser.parse_args()

    data = load_data()

    auto_changes = []  # {elementId, eventId, old_label, new_label, rules}
    manual_issues = []  # {elementId, eventId, layer, label, issues}

    for fw in data["frameworkViews"]:
        event_id = fw["eventId"]
        for elem in fw.get("elements", []):
            eid = elem["elementId"]
            layer = elem["layer"]
            label = elem["label"]

            # 機械的修正
            new_label, rules = apply_auto_fixes(label, layer)
            if new_label:
                auto_changes.append({
                    "elementId": eid,
                    "eventId": event_id,
                    "old_label": label,
                    "new_label": new_label,
                    "rules": rules,
                })
                # 手動検出は修正後のラベルで行う
                label_for_check = new_label
            else:
                label_for_check = label

            # 手動修正検出
            issues = detect_manual_issues(label_for_check, layer, event_id)
            if issues:
                manual_issues.append({
                    "elementId": eid,
                    "eventId": event_id,
                    "layer": layer,
                    "label": label_for_check,
                    "issues": issues,
                })

    # ── 出力 ──
    print(f"=== 機械的修正: {len(auto_changes)}件 ===")
    for c in auto_changes:
        print(f"  [{c['eventId']}] {c['elementId']}")
        print(f"    旧: {c['old_label']}")
        print(f"    新: {c['new_label']}")
        print(f"    ルール: {', '.join(c['rules'])}")
        print()

    print(f"=== 手動修正候補: {len(manual_issues)}件 ===")
    for m in manual_issues:
        print(f"  [{m['eventId']}] {m['elementId']} ({m['layer']})")
        print(f"    ラベル: {m['label']}")
        print(f"    問題: {', '.join(m['issues'])}")
        print()

    if args.dry_run:
        print("(dry-run: ファイルは変更されていません)")
    else:
        # 実適用
        change_map = {c["elementId"]: c["new_label"] for c in auto_changes}
        changed = 0
        for fw in data["frameworkViews"]:
            for elem in fw.get("elements", []):
                if elem["elementId"] in change_map:
                    elem["label"] = change_map[elem["elementId"]]
                    changed += 1

        save_data(data)
        print(f"framework_output_v3_3.json を更新しました ({changed}件)")

        # 変更ログ出力
        log_path = DATA_PATH.parent / "fix_label_style_log.json"
        log_data = {
            "auto_changes": auto_changes,
            "manual_issues": manual_issues,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"変更ログ: {log_path}")


if __name__ == "__main__":
    main()
