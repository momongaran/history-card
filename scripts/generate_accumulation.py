#!/usr/bin/env python3
"""
generate_accumulation.py — v3.1 B要素間 accumulation（蓄積関係）生成スクリプト

各FWのB要素間の蓄積関係をClaude APIで生成し、
同時にB要素ラベルの条件記述化・カテゴリ修正も行う。

出力: data/accumulation_v3_1.json
"""

import asyncio
import json
import os
import sys
import time
from copy import deepcopy

import anthropic

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODEL = "claude-sonnet-4-6"
MAX_CONCURRENCY = 10
MAX_RETRIES = 3

VALID_MECHANISMS = {"tension", "amplification", "constraint", "enabling", "convergence"}

MECHANISM_DEFS = """mechanism語彙（5種）:
- tension（緊張）: 二条件が逆方向に作用し構造的ストレスを生む
- amplification（増幅）: 一条件が他を強化・激化させる
- constraint（制約）: 一条件が選択肢を狭め危機に向かわせる
- enabling（促進）: 一条件が他の作動前提を作る
- convergence（収斂）: 独立した条件が同一の圧力点に集中する"""

B_CATEGORY_LIST = """B要素カテゴリ一覧:
B-PWR（権力配置）: B-PWR-01 中央集権構造, B-PWR-02 豪族間均衡, B-PWR-03 分権的配置, B-PWR-04 実権と名目の分離
B-LEG（正統性基盤）: B-LEG-01 血統的正統性, B-LEG-02 王統継承安定性, B-LEG-03 宗教的正統化, B-LEG-04 制度的正当化
B-INS（制度枠組み）: B-INS-01 官制構造, B-INS-02 税制財政制度, B-INS-03 法制度枠組み, B-INS-04 行政運用基盤, B-INS-05 軍事制度体系
B-SOC（社会構造）: B-SOC-01 身分階層構造, B-SOC-02 地域社会構造, B-SOC-03 経済階層分化, B-SOC-04 共同体結束構造
B-RES（資源基盤）: B-RES-01 財政資源, B-RES-02 軍事資源, B-RES-03 人的資源, B-RES-04 物流供給基盤
B-EXT（対外環境）: B-EXT-01 外交圧力, B-EXT-02 軍事脅威, B-EXT-03 文化流入, B-EXT-04 経済交易圏
B-MIL（軍事基盤）: B-MIL-01 軍事組織構造, B-MIL-02 軍事技術水準, B-MIL-03 動員体制, B-MIL-04 防衛拠点配置
B-NRM（価値体系）: B-NRM-01 宗教思想体系, B-NRM-02 倫理規範, B-NRM-03 統治理念, B-NRM-04 文化的象徴体系
B-INF（情報基盤）: B-INF-01 文書記録体系, B-INF-02 通信伝達網, B-INF-03 教育知識体系, B-INF-04 情報統制構造
B-GEO（地理人口条件）: B-GEO-01 地理的障壁, B-GEO-02 人口集中度, B-GEO-03 農業生産条件, B-GEO-04 交通経路条件
B-RIV（利害対立）: B-RIV-01 政治的利害対立"""


def build_prompt(fw, event_desc):
    """Build the prompt for a single FW."""
    b_elements = [e for e in fw['elements'] if e['layer'] == 'B']
    b_count = len(b_elements)

    elements_text = "\n".join(
        f"  - {e['elementId']}: label=\"{e['label']}\" category={e['category']} subCategory={e['subCategory']}"
        for e in b_elements
    )

    # Determine expected relation count
    if b_count == 2:
        relation_instruction = "relations配列に1件のペアを出力してください。"
    else:  # b_count == 3
        relation_instruction = "relations配列に1〜3件のペア（意味のあるペアのみ）を出力してください。"

    prompt = f"""以下のframeworkView（歴史事象の構造分析）について、2つのタスクを実行してください。

## 対象FW
- frameworkViewId: {fw['frameworkViewId']}
- title: {fw['title']}
- sortKey: {fw['sortKey']}
- 事象説明: {event_desc}

## B要素（{b_count}件）
{elements_text}

## タスク1: accumulation（蓄積関係）の生成

B要素間の関係を分析し、どの条件とどの条件が組み合わさってエネルギー蓄積になるかを明示してください。

{relation_instruction}

{MECHANISM_DEFS}

各relationには:
- from: 起点のelementId
- to: 終点のelementId（fromと異なること）
- mechanism: 上記5種のいずれか
- description: 20〜100文字の日本語で蓄積メカニズムを説明

summaryには全体の蓄積構造を1文（20〜100文字）で要約してください。

## タスク2: B要素ラベル・カテゴリの改訂

各B要素について:
1. **ラベル改訂**: 行為記述（〜した、〜を行った）→ 条件記述（〜していた、〜であった、〜が存在していた）に修正。事象発生「前」の背景条件として読めるようにする。既に条件記述になっている場合はそのまま。
2. **カテゴリ改訂**: 明らかに誤分類の場合のみ修正。正しい場合はそのまま。

{B_CATEGORY_LIST}

## 出力形式

以下のJSONのみを出力してください（説明文不要）:

```json
{{
  "accumulation": {{
    "relations": [
      {{
        "from": "elementId",
        "to": "elementId",
        "mechanism": "tension|amplification|constraint|enabling|convergence",
        "description": "日本語で蓄積メカニズムを説明（20〜100文字）"
      }}
    ],
    "summary": "全体の蓄積構造の要約（20〜100文字）"
  }},
  "revisions": [
    {{
      "elementId": "elementId",
      "labelRevised": "条件記述に修正したラベル",
      "categoryRevised": "B-XXX",
      "subCategoryRevised": "B-XXX-NN"
    }}
  ]
}}
```"""
    return prompt


def validate_response(fw_id, result, b_element_ids):
    """Validate a single FW response. Returns list of error messages."""
    errors = []

    # Check accumulation exists
    if 'accumulation' not in result:
        errors.append(f"{fw_id}: accumulation フィールドが存在しない")
        return errors

    accum = result['accumulation']
    if 'relations' not in accum:
        errors.append(f"{fw_id}: relations が存在しない")
        return errors

    for i, rel in enumerate(accum['relations']):
        # Check required fields
        for field in ('from', 'to', 'mechanism', 'description'):
            if field not in rel:
                errors.append(f"{fw_id}: relation[{i}] に {field} がない")
                continue

        # Check from/to are valid B element IDs
        if rel.get('from') not in b_element_ids:
            errors.append(f"{fw_id}: relation[{i}].from '{rel.get('from')}' は当該FWのB要素ではない")
        if rel.get('to') not in b_element_ids:
            errors.append(f"{fw_id}: relation[{i}].to '{rel.get('to')}' は当該FWのB要素ではない")

        # Check self-reference
        if rel.get('from') == rel.get('to'):
            errors.append(f"{fw_id}: relation[{i}] self-reference: {rel.get('from')}")

        # Check mechanism
        if rel.get('mechanism') not in VALID_MECHANISMS:
            errors.append(f"{fw_id}: relation[{i}].mechanism '{rel.get('mechanism')}' は無効")

        # Check description length
        desc = rel.get('description', '')
        if len(desc) < 10:
            errors.append(f"{fw_id}: relation[{i}].description が短すぎる ({len(desc)}文字)")
        if len(desc) > 150:
            errors.append(f"{fw_id}: relation[{i}].description が長すぎる ({len(desc)}文字)")

    # Check summary
    summary = accum.get('summary', '')
    if len(summary) < 10:
        errors.append(f"{fw_id}: summary が短すぎる ({len(summary)}文字)")

    # Check revisions
    if 'revisions' not in result:
        errors.append(f"{fw_id}: revisions フィールドが存在しない")
    else:
        for rev in result['revisions']:
            if rev.get('elementId') not in b_element_ids:
                errors.append(f"{fw_id}: revision elementId '{rev.get('elementId')}' は当該FWのB要素ではない")

    return errors


async def call_api(client, sem, fw, event_desc, fw_index, total):
    """Call Claude API for a single FW with retry."""
    fw_id = fw['frameworkViewId']
    b_elements = [e for e in fw['elements'] if e['layer'] == 'B']
    b_element_ids = {e['elementId'] for e in b_elements}
    prompt = build_prompt(fw, event_desc)

    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.messages.create(
                    model=MODEL,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                    system="あなたは日本史の構造分析の専門家です。指示されたJSON形式のみを出力してください。",
                )

                text = response.content[0].text.strip()

                # Extract JSON from markdown code block if present
                if text.startswith("```"):
                    lines = text.split("\n")
                    # Remove first and last lines (``` markers)
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
                errors = validate_response(fw_id, result, b_element_ids)
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

                print(f"  [{fw_index+1}/{total}] {fw_id}: OK")
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
    fw_path = os.path.join(BASE_DIR, 'framework_output_v3_0_bfe.json')
    with open(fw_path, encoding='utf-8') as f:
        data = json.load(f)

    events = {ev['eventId']: ev for ev in data['events']}
    fws = data['frameworkViews']

    # Filter to FWs with B>=2
    target_fws = []
    skip_fws = []
    for fw in fws:
        b_count = sum(1 for e in fw['elements'] if e['layer'] == 'B')
        if b_count >= 2:
            target_fws.append(fw)
        else:
            skip_fws.append(fw)

    print(f"対象FW: {len(target_fws)}件 (B>=2)")
    print(f"スキップ: {len(skip_fws)}件 (B<=1)")

    # Check for --pilot flag
    pilot_mode = '--pilot' in sys.argv
    if pilot_mode:
        target_fws = target_fws[:5]
        print(f"パイロットモード: 先頭5件のみ処理")

    # Create async client
    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    # Process all FWs
    start_time = time.time()
    tasks = []
    for i, fw in enumerate(target_fws):
        event_id = fw.get('eventId') or fw.get('primaryEventId')
        event = events.get(event_id, {})
        event_desc = event.get('description', fw.get('title', ''))
        tasks.append(call_api(client, sem, fw, event_desc, i, len(target_fws)))

    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    # Collect results
    output = {
        "version": "3.1",
        "generatedBy": "generate_accumulation.py",
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

    # Add null entries for skipped FWs (B<=1)
    for fw in skip_fws:
        output["items"][fw['frameworkViewId']] = {
            "accumulation": None,
            "revisions": []
        }

    # Output
    out_path = os.path.join(BASE_DIR, 'accumulation_v3_1.json')
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

    # Print mechanism distribution
    mech_counts = {}
    for fw_id, result, _ in results:
        if result and result.get('accumulation') and result['accumulation'].get('relations'):
            for rel in result['accumulation']['relations']:
                m = rel.get('mechanism', 'unknown')
                mech_counts[m] = mech_counts.get(m, 0) + 1

    if mech_counts:
        total_rels = sum(mech_counts.values())
        print(f"\n=== mechanism分布 ===")
        for m, c in sorted(mech_counts.items(), key=lambda x: -x[1]):
            pct = c / total_rels * 100
            flag = " ⚠️" if pct > 60 else ""
            print(f"  {m}: {c} ({pct:.1f}%){flag}")


if __name__ == '__main__':
    asyncio.run(main())
