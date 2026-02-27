#!/usr/bin/env python3
"""
v3.6 パイロット: B記述改革（失敗学原則の適用）

原則:
1. Bには「その時点で当事者が観察しえた事実」だけを書く
2. 後知恵的な診断（「〜が不在であった」「〜という矛盾があった」）を排除する
3. Fと完全一致するB要素は削除する（B要素数を可変に）
4. イベント内容そのものであるB要素は削除する

パイロット対象: 10イベント
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# === 削除対象: FのコピーまたはE内容であるB要素 ===
DELETE_ELEMENTS = [
    # B-EXT-03がFの完全コピー
    ("EV_p0805_01", "EL_EV_p0805_01_3"),  # 最澄: F内容のコピー
    ("EV_p0806_01", "EL_EV_p0806_01_3"),  # 空海: F内容のコピー
    ("EV_p1543_01", "EL_EV_p1543_01_3"),  # 鉄砲: F内容のコピー
    ("EV_p1603_01", "EL_EV_p1603_01_3"),  # 江戸幕府: F内容のコピー
    ("EV_p1853_01", "EL_EV_p1853_01_3"),  # ペリー: F内容のコピー

    # イベント内容そのもの
    ("EV_p0708_01", "EL_EV_p0708_01_3"),  # 和同開珎: 「鋳造された」はイベントそのもの

    # 「方針が固まっていた」はEの予告（当時の観察ではない）
    ("EV_p0967_01", "EL_EV_p0967_01_3"),  # 延喜式: 三代格式の集大成として…整備された
    ("EV_p1633_01", "EL_EV_p1633_01_3"),  # 鎖国: 奉書船以外の渡航を禁止する方針が固まっていた
]

# === 書き換え対象: 後知恵 → 当時の観察 ===
REWRITES = [
    # 継体天皇
    ("EV_p0507_01", "EL_EV_p0507_01_7",
     # 旧: 武烈天皇が後嗣なく崩御し王統が断絶状態にある
     # 問題: 「断絶状態にある」はF(空位発生)と重複。「断絶」は結果からの命名
     "武烈天皇に子がなく、大王家の直系の男子が極めて少なかった"),

    ("EV_p0507_01", "EL_EV_p0507_01_2",
     # 旧: 大伴金村・物部麁鹿火ら有力豪族が擁立の主導権を握っている
     # 問題: 「擁立の主導権」は後知恵。崩御前は「擁立」は議題ではない
     "大伴金村・物部麁鹿火ら大連・大臣が大王家の政務を実質的に主導していた"),

    # 八色の姓
    ("EV_p0684_01", "EL_EV_p0684_01_1",
     # 旧: 壬申の乱で新たな功臣群が…整合的に序列化できない状態にあった
     # 問題: 「序列化できない」「語彙がない」は後知恵的な制度分析
     "壬申の乱で功績を立てた豪族と、旧来の氏姓による序列が食い違っていた"),

    # 和同開珎
    ("EV_p0708_01", "EL_EV_p0708_01_1",
     # 旧: 律令制度は唐の貨幣経済を前提に設計されていたが…根本矛盾があった
     # 問題: 「根本矛盾があった」は後知恵的な診断
     "律令の位禄や庸調の制度は銭貨での計算を前提としていたが、国内の交換は稲・布・鉄による物々交換が主流であった"),

    # 延喜式
    ("EV_p0967_01", "EL_EV_p0967_01_1",
     # 旧: 律令の施行細則が散在・不統一のまま…汚職と属人化を許容していた
     # 問題: 「制度的空白が汚職と属人化を許容していた」は後知恵の因果分析
     "律令の施行細則が弘仁式・貞観式など複数に散在し、国ごとに運用の差が大きかった"),

    ("EV_p0967_01", "EL_EV_p0967_01_2",
     # 旧: 醍醐天皇の命で編纂が始まり約50年をかけて完成していた
     # 問題: これはイベントの経過記述。Bではない
     "国司の交代のたびに行政の細則が変わり、地方の実務担当者が混乱していた"),

    # 鎖国令
    ("EV_p1633_01", "EL_EV_p1633_01_1",
     # 旧: キリシタン大名が教皇の命令に従いうる幕府外の忠誠系統を持ち…
     # 問題: 「幕藩体制外の権力基盤が形成されつつあった」は構造分析
     "九州のキリシタン大名が南蛮貿易の利益を通じて独自の財源と人的つながりを拡大していた"),

    ("EV_p1633_01", "EL_EV_p1633_01_2",
     # 旧: 海外渡航者が外国勢力と結ぶ危険性が懸念されていた
     # これは当時の認識としてOKだが、もう少し具体的に
     "日本人商人が東南アジアの日本町に定住し、現地勢力や宣教師と接触する事例が増えていた"),

    # ペリー来航
    ("EV_p1853_01", "EL_EV_p1853_01_1",
     # 旧: アメリカが太平洋航路の中継基地を必要としていた
     # これは当時の観察としてOK。ただしもう少し具体的に
     "アメリカの捕鯨船・貿易船が北太平洋で活動を拡大し、燃料・水・食料の補給拠点を求めていた"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build lookup
    elem_index = {}  # (eventId, elementId) -> (fv, elem, idx)
    for fv in data["frameworkViews"]:
        for i, elem in enumerate(fv.get("elements", [])):
            elem_index[(fv["eventId"], elem.get("elementId"))] = (fv, elem, i)

    # === Delete ===
    deleted = 0
    delete_not_found = []
    for eid, elem_id in DELETE_ELEMENTS:
        key = (eid, elem_id)
        if key not in elem_index:
            delete_not_found.append(key)
            continue
        fv, elem, idx = elem_index[key]
        fv["elements"].remove(elem)
        deleted += 1

    # === Rewrite ===
    rewritten = 0
    rewrite_not_found = []
    for eid, elem_id, new_label in REWRITES:
        key = (eid, elem_id)
        if key not in elem_index:
            rewrite_not_found.append(key)
            continue
        fv, elem, idx = elem_index[key]
        elem["label"] = new_label
        rewritten += 1

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== v3.6 パイロット: B記述改革 ===")
    print(f"削除: {deleted}/{len(DELETE_ELEMENTS)}件")
    print(f"書き換え: {rewritten}/{len(REWRITES)}件")
    if delete_not_found:
        print(f"削除未発見: {delete_not_found}")
    if rewrite_not_found:
        print(f"書換未発見: {rewrite_not_found}")

    # Show results
    print(f"\n--- 結果確認 ---")
    pilot_ids = set()
    for eid, _ in DELETE_ELEMENTS:
        pilot_ids.add(eid)
    for eid, _, _ in REWRITES:
        pilot_ids.add(eid)

    for fv in data["frameworkViews"]:
        if fv["eventId"] in pilot_ids:
            b_count = sum(1 for el in fv.get("elements", []) if el["layer"] == "B")
            print(f"\n{fv['eventId']}: {fv['title']} (B={b_count})")
            for el in sorted(fv.get("elements", []), key=lambda x: x["layer"]):
                print(f"  [{el['layer']}] {el.get('subCategory','')} | {el['label'][:70]}")

    print(f"\n>>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
