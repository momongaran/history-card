#!/usr/bin/env python3
"""
fill_fluctuation_labels.py — F-UNC-00（揺らぎ未設定）のラベルを補充

208件の「（揺らぎ未設定）」に「なぜこのタイミングで起きたか」のラベルを生成する。
サブカテゴリはF-UNC-00のまま（カテゴリ再設計は次回）。

手法:
1. 具体的causeTextがある場合 → causeText全体を起動因ラベルとして使用
2. 汎用causeTextの場合 → B要素の記述から起動因を導出

入力/出力: data/framework_output_v3_3.json（上書き）
"""

import json
import os
import re
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def is_generic_cause(cause_text):
    """汎用的なcauseTextかどうか判定。"""
    if not cause_text:
        return True
    return '至るまでに' in cause_text or cause_text.startswith('『')


def extract_trigger_from_cause(cause_text):
    """具体的causeTextから起動因ラベルを抽出する。

    causeTextは因果の説明文。これ自体が「なぜ起きたか」の説明なので、
    そのまま使うか、長すぎる場合は前半部分を使う。
    """
    if not cause_text:
        return None

    # 複数文の場合、最初の文を使う
    first_sentence = cause_text.split('。')[0]

    # 80文字以下ならそのまま
    if len(first_sentence) <= 80:
        return first_sentence

    # 長い場合、「ため、」「ことで、」で分割して前半（原因部分）を使う
    for sep in ['ため、', 'ことで、', '結果、']:
        if sep in first_sentence:
            return first_sentence.split(sep, 1)[0]

    # それでも長い場合、最初の「、」区切りで適切な長さまで
    parts = first_sentence.split('、')
    result = parts[0]
    for part in parts[1:]:
        candidate = result + '、' + part
        if len(candidate) > 70:
            break
        result = candidate

    return result


def derive_trigger_from_b_elements(fv):
    """B要素からトリガー（起動因）を導出する。"""
    b_elements = [el for el in fv['elements'] if el['layer'] == 'B']
    title = fv['title']

    if not b_elements:
        return None

    # B要素が3つある場合、3番目が具体的なきっかけであることが多い
    if len(b_elements) >= 3:
        b3_label = b_elements[2]['label']
        # 状態記述（〜していた、〜であった）を完了形に変換
        trigger = state_to_trigger(b3_label)
        return trigger

    # B要素が2つの場合
    if len(b_elements) >= 2:
        # 2番目のB要素をトリガーとして使用
        b2_label = b_elements[1]['label']
        trigger = state_to_trigger(b2_label)
        return trigger

    # B要素が1つの場合
    trigger = state_to_trigger(b_elements[0]['label'])
    return trigger


def state_to_trigger(label):
    """状態記述（〜していた）を起動因的な記述に変換する。

    背景の状態記述をそのまま使うが、末尾を調整して
    トリガー的なニュアンスにする。
    """
    text = label.rstrip('。')

    # 「〜されていた」→「された」
    text = re.sub(r'されていた$', 'された', text)
    # 「〜していた」→「した」
    text = re.sub(r'していた$', 'した', text)
    # 「〜であった」→「であった」（そのまま — 状態は状態として使える）
    # 「〜いた」→「た」（汎用）
    text = re.sub(r'れていた$', 'れた', text)

    # 80文字超なら短縮
    if len(text) > 80:
        # 「、」で分割して適切な長さに
        parts = text.split('、')
        result = parts[0]
        for part in parts[1:]:
            candidate = result + '、' + part
            if len(candidate) > 70:
                break
            result = candidate
        text = result

    return text


def generate_normalized_label(label):
    """normalizedLabelを生成する。labelを30文字以内に短縮。"""
    if len(label) <= 30:
        return label

    # 句読点で分割して最初の部分
    for sep in ['、', 'し、']:
        if sep in label:
            first = label.split(sep)[0]
            if 8 <= len(first) <= 30:
                return first

    return label[:28] + '…'


def fill_labels(data):
    """F-UNC-00のラベルを補充する。"""
    filled_specific = 0
    filled_generic = 0
    skipped = 0

    for fv in data['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] != 'F' or el['subCategory'] != 'F-UNC-00':
                continue
            if el['label'] != '（揺らぎ未設定）':
                continue  # 既に設定済み

            cause_text = fv['meta'].get('causeText', '')

            if is_generic_cause(cause_text):
                trigger = derive_trigger_from_b_elements(fv)
                if trigger:
                    el['label'] = trigger
                    el['normalizedLabel'] = generate_normalized_label(trigger)
                    el['notes'] = {"generated": "fill_fluctuation_labels.py (B要素ベース)"}
                    filled_generic += 1
                else:
                    skipped += 1
            else:
                trigger = extract_trigger_from_cause(cause_text)
                if trigger:
                    el['label'] = trigger
                    el['normalizedLabel'] = generate_normalized_label(trigger)
                    el['notes'] = {"generated": "fill_fluctuation_labels.py (causeTextベース)"}
                    filled_specific += 1
                else:
                    skipped += 1

    return filled_specific, filled_generic, skipped


def main():
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_3.json')

    with open(fw_path, encoding='utf-8') as f:
        data = json.load(f)

    # 現状確認
    unc00_count = 0
    unc00_empty = 0
    for fv in data['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] == 'F' and el['subCategory'] == 'F-UNC-00':
                unc00_count += 1
                if el['label'] == '（揺らぎ未設定）':
                    unc00_empty += 1

    print(f"F-UNC-00: {unc00_count}件 (うち未設定: {unc00_empty}件)")

    if unc00_empty == 0:
        print("全て設定済みです。処理をスキップします。")
        return

    # ラベル補充
    print(f"\n=== ラベル補充実行 ===")
    filled_specific, filled_generic, skipped = fill_labels(data)

    print(f"  causeTextから抽出: {filled_specific}件")
    print(f"  B要素から導出: {filled_generic}件")
    print(f"  スキップ: {skipped}件")

    # 結果サンプル表示
    print(f"\n=== 結果サンプル（causeTextベース）===")
    shown = 0
    for fv in data['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] == 'F' and el['subCategory'] == 'F-UNC-00':
                notes = el.get('notes', {})
                if isinstance(notes, dict) and notes.get('generated', '').endswith('causeTextベース)'):
                    print(f"  [{fv['sortKey']:>4}] {fv['title'][:30]}")
                    print(f"    F: {el['label'][:70]}")
                    shown += 1
                    if shown >= 8:
                        break
        if shown >= 8:
            break

    print(f"\n=== 結果サンプル（B要素ベース）===")
    shown = 0
    for fv in data['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] == 'F' and el['subCategory'] == 'F-UNC-00':
                notes = el.get('notes', {})
                if isinstance(notes, dict) and notes.get('generated', '').endswith('B要素ベース)'):
                    print(f"  [{fv['sortKey']:>4}] {fv['title'][:30]}")
                    print(f"    F: {el['label'][:70]}")
                    shown += 1
                    if shown >= 8:
                        break
        if shown >= 8:
            break

    # 品質チェック
    print(f"\n=== 品質チェック ===")
    long_count = 0
    short_count = 0
    for fv in data['frameworkViews']:
        for el in fv['elements']:
            if el['layer'] == 'F' and el['subCategory'] == 'F-UNC-00':
                label = el['label']
                if label == '（揺らぎ未設定）':
                    continue
                if len(label) > 80:
                    long_count += 1
                if len(label) < 10:
                    short_count += 1
    print(f"  80文字超: {long_count}件")
    print(f"  10文字未満: {short_count}件")

    # 未設定のまま残っている件数
    still_empty = sum(
        1 for fv in data['frameworkViews']
        for el in fv['elements']
        if el['layer'] == 'F' and el['subCategory'] == 'F-UNC-00' and el['label'] == '（揺らぎ未設定）'
    )
    print(f"  未設定残存: {still_empty}件")

    # 保存
    if '--dry-run' in sys.argv:
        print(f"\n(dry-run: 保存しません)")
    else:
        with open(fw_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n出力: {fw_path}（上書き）")


if __name__ == '__main__':
    main()
