#!/usr/bin/env python3
"""
generate_momentum.py — v3.3 momentum（Eの解放の方向）生成スクリプト

各FWのeventTitle + E-label + accumulationを入力に、
Eの解放エネルギーの方向を記述するmomentumテキストを生成する。

出力: data/momentum_v3_3.json
"""

import asyncio
import json
import os
import sys
import time

import anthropic

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODEL = "claude-sonnet-4-6"
MAX_CONCURRENCY = 10
MAX_RETRIES = 3


def build_prompt(fw):
    """Build the prompt for a single FW."""
    # Collect elements by layer
    b_elements = [e for e in fw['elements'] if e['layer'] == 'B']
    f_elements = [e for e in fw['elements'] if e['layer'] == 'F']
    e_elements = [e for e in fw['elements'] if e['layer'] == 'E']

    b_text = "\n".join(
        f"  - {e['category']}: {e['label']}"
        for e in b_elements
    ) or "  （なし）"

    f_text = "\n".join(
        f"  - {e['category']}: {e['label']}"
        for e in f_elements
    )

    e_text = "\n".join(
        f"  - {e['category']}: {e['label']} (normalizedLabel: {e.get('normalizedLabel', '')})"
        for e in e_elements
    )

    # Accumulation summary if available
    accum_summary = ""
    accum = fw.get('accumulation')
    if accum and accum.get('summary'):
        accum_summary = f"\n## 蓄積構造（過去方向）\n{accum['summary']}"

    prompt = f"""以下の歴史事象のframeworkView（B/F/E構造分析）について、momentum（Eの解放の方向）を生成してください。

## 対象
- title: {fw['title']}
- sortKey: {fw['sortKey']}

## B要素（背景条件）
{b_text}

## F要素（起動因）
{f_text}

## E要素（解放）
{e_text}
{accum_summary}

## momentumとは
- Eの解放のエネルギーがどの方向に放出されているかを記述するもの
- accumulationの対概念: accumulation=過去方向（何が蓄積されたか）、momentum=未来方向（この解放がどこへ向かうか）
- Eの「結果」や「帰結」ではなく、解放の瞬間に内在する方向性
- 意図的か構造的帰結かを問わない
- 1イベントに1つのmomentum

## 出力形式
「〜の方向へ」の形式で、1文（15〜40文字程度）で記述してください。

例:
- 「統一権力による秩序形成の方向へ」
- 「地方武力が中央統治を代替する方向へ」
- 「武断から文治への統治原理転換の方向へ」

JSONのみを出力してください（説明文不要）:

```json
{{
  "momentum": "〜の方向へ"
}}
```"""
    return prompt


def validate_response(fw_id, result):
    """Validate a single FW response. Returns list of error messages."""
    errors = []

    if 'momentum' not in result:
        errors.append(f"{fw_id}: momentum フィールドが存在しない")
        return errors

    momentum = result['momentum']
    if not isinstance(momentum, str):
        errors.append(f"{fw_id}: momentum が文字列でない: {type(momentum)}")
        return errors

    if len(momentum) < 5:
        errors.append(f"{fw_id}: momentum が短すぎる ({len(momentum)}文字)")
    if len(momentum) > 60:
        errors.append(f"{fw_id}: momentum が長すぎる ({len(momentum)}文字)")
    if not momentum.endswith("方向へ"):
        errors.append(f"{fw_id}: momentum が「方向へ」で終わらない: {momentum}")

    return errors


async def call_api(client, sem, fw, fw_index, total):
    """Call Claude API for a single FW with retry."""
    fw_id = fw['frameworkViewId']
    prompt = build_prompt(fw)

    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.messages.create(
                    model=MODEL,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                    system="あなたは日本史の構造分析の専門家です。指示されたJSON形式のみを出力してください。",
                )

                text = response.content[0].text.strip()

                # Extract JSON from markdown code block if present
                if text.startswith("```"):
                    lines = text.split("\n")
                    json_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```") and not in_block:
                            in_block = True
                            continue
                        elif line.startswith("```") and in_block:
                            break
                        elif in_block:
                            json_lines.append(line)
                    text = "\n".join(json_lines)

                result = json.loads(text)

                # Validate
                errors = validate_response(fw_id, result)
                if errors:
                    if attempt < MAX_RETRIES - 1:
                        print(f"  [{fw_index+1}/{total}] {fw_id}: バリデーションエラー (attempt {attempt+1}), リトライ")
                        for e in errors:
                            print(f"    - {e}")
                        continue
                    else:
                        print(f"  [{fw_index+1}/{total}] {fw_id}: バリデーションエラー (最終)")
                        for e in errors:
                            print(f"    - {e}")
                        return fw_id, result, errors

                print(f"  [{fw_index+1}/{total}] {fw_id}: OK — {result['momentum']}")
                return fw_id, result, []

            except json.JSONDecodeError as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"  [{fw_index+1}/{total}] {fw_id}: JSONパースエラー (attempt {attempt+1}), リトライ")
                    continue
                else:
                    print(f"  [{fw_index+1}/{total}] {fw_id}: JSONパースエラー (最終): {e}")
                    return fw_id, None, [f"JSON parse error: {e}"]

            except anthropic.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  [{fw_index+1}/{total}] {fw_id}: APIエラー (attempt {attempt+1}), {wait}s待機")
                    await asyncio.sleep(wait)
                    continue
                else:
                    print(f"  [{fw_index+1}/{total}] {fw_id}: APIエラー (最終): {e}")
                    return fw_id, None, [f"API error: {e}"]

    return fw_id, None, ["Max retries exceeded"]


async def main():
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("エラー: ANTHROPIC_API_KEY 環境変数が設定されていません")
        sys.exit(1)

    # Load data
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_3.json')
    if not os.path.exists(fw_path):
        print(f"エラー: {fw_path} が存在しません")
        print("先に migrate_v3_3.py を実行してください")
        sys.exit(1)

    with open(fw_path, encoding='utf-8') as f:
        data = json.load(f)

    fws = data['frameworkViews']
    print(f"対象FW: {len(fws)}件")

    # Check for --pilot flag
    pilot_mode = '--pilot' in sys.argv
    if pilot_mode:
        target_fws = fws[:5]
        print(f"パイロットモード: 先頭5件のみ処理")
    else:
        target_fws = fws

    # Create async client
    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    # Process all FWs
    start_time = time.time()
    tasks = []
    for i, fw in enumerate(target_fws):
        tasks.append(call_api(client, sem, fw, i, len(target_fws)))

    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    # Collect results
    output = {
        "version": "3.3",
        "generatedBy": "generate_momentum.py",
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": {}
    }
    all_errors = []
    success_count = 0

    for fw_id, result, errors in results:
        if result is not None:
            output["items"][fw_id] = result
            success_count += 1
        all_errors.extend(errors)

    # Output
    out_path = os.path.join(BASE_DIR, 'momentum_v3_3.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"処理時間: {elapsed:.1f}秒")
    print(f"成功: {success_count}/{len(target_fws)}")
    print(f"エラー: {len(all_errors)}件")
    print(f"出力: {out_path}")

    if all_errors:
        print(f"\n=== エラー一覧 ===")
        for e in all_errors:
            print(f"  - {e}")


if __name__ == '__main__':
    asyncio.run(main())
