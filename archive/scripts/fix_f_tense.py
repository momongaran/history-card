#!/usr/bin/env python3
"""
v3.7b F要素の時制修正

原則: F（揺らぎ）は「何かが起きた」瞬間を表す → 「〜した」「〜なった」（完了）
     「〜していた」「〜なっていた」（状態継続）はB（背景）の表現

16件を修正。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "framework_output_v3_3.json"

# (eventId, elementId, new_label)
REWRITES = [
    # 継体天皇 — 「空位となっていた」→「空位となった」
    ("EV_p0507_01", "EL_EV_p0507_01_1",
     "武烈天皇が後継なく崩御し大王位が空位となった"),

    # 墾田永年私財法 — 「低迷していた」→ トリガーらしく変更
    ("EV_p0743_02", "EL_EV_p0743_02_F",
     "三世一身法の期限切れ返還を嫌い開墾放棄が相次ぎ、口分田不足が深刻化した"),

    # 白河院政 — 「保持していた」→ トリガーとなる出来事に
    ("EV_p1086_01", "EL_EV_p1086_01_F",
     "白河天皇が幼い堀河天皇に譲位し、上皇として院庁を設けた"),

    # 院政の定着・武士台頭 — 「動揺させていた」→「動揺させた」
    ("EV_p1184_01", "EL_EV_p1184_01_F",
     "荘園制の矛盾と地方武士の台頭が既存の政権構造を動揺させた"),

    # 北条泰時 — 「超えていた」→ トリガーとなる出来事に
    ("EV_p1225_01", "EL_EV_p1225_01_F",
     "義時が急死し、承久の乱後に急増した訴訟・行政を処理する体制の再構築が迫られた"),

    # 江戸幕府 — 「進んでいた」→「進んだ」
    ("EV_p1603_01", "EL_EV_p1603_01_F",
     "関ヶ原の勝利後、豊臣政権の形式的存続のもとで家康への実権移行が決定的となった"),

    # 島原の乱 — 「広がっていた」→「広がった」
    ("EV_p1637_01", "EL_EV_p1637_01_2",
     "飢饉による社会不安が広がり、重税への不満が爆発寸前に達した"),

    # 田沼意次 — 「対処しきれなくなっていた」→ トリガーとなる出来事に
    ("EV_p1772_01", "EL_EV_p1772_01_F",
     "幕府財政の窮乏が限界に達し、農本主義的緊縮策の行き詰まりが明白となった"),

    # レザノフ来航 — 「続いていた」→ トリガーとなる出来事に
    ("EV_p1804_01", "EL_EV_p1804_01_F",
     "ロシア皇帝アレクサンドル1世の命を受けたレザノフが通商を求めて長崎に入港した"),

    # 大塩平八郎 — 「放置していた」→「放置した」
    ("EV_p1837_01", "EL_EV_p1837_01_F",
     "天保の飢饉で餓死者が続出する中、大坂町奉行所が米商人の買い占めを放置した"),

    # 蛮社の獄 — 「持っていた」→ トリガーとなる出来事に
    ("EV_p1839_01", "EL_EV_p1839_01_F",
     "渡辺崋山・高野長英らがモリソン号事件を批判する著作を執筆し、目付鳥居耀蔵がこれを摘発した"),

    # ペリー来航 — 「与えていた」→ トリガーとなる出来事に
    ("EV_p1853_01", "EL_EV_p1853_01_F",
     "アメリカ東インド艦隊司令長官ペリーが大統領親書を携え浦賀沖に来航した"),

    # 廃藩置県 — 「可能となっていた」→「可能となった」
    ("EV_p1871_01", "EL_EV_p1871_01_F",
     "薩長土の藩兵を御親兵として集結させ、武力を背景とした断行が可能となった"),

    # 沖縄返還 — 「行っていた」→「合意した」
    ("EV_p1972_01", "EL_EV_p1972_01_F",
     "佐藤栄作首相とニクソン大統領が1969年の日米首脳会談で1972年の沖縄返還に合意した"),

    # プラザ合意 — 「集まっていた」→ トリガーに
    ("EV_p1985_01", "EL_EV_p1985_01_F",
     "ドル高の是正を目的に先進5か国の蔵相・中央銀行総裁がニューヨークで緊急会合を開いた"),

    # 令和改元 — 「制定されていた」→「制定された」
    ("EV_p2019_01", "EL_EV_p2019_01_1",
     "天皇の退位等に関する皇室典範特例法が制定され、生前退位の法的根拠が整った"),
]


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    elem_index = {}
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            elem_index[(fv["eventId"], elem.get("elementId"))] = elem

    rewritten = 0
    not_found = []
    for eid, elem_id, new_label in REWRITES:
        key = (eid, elem_id)
        if key not in elem_index:
            not_found.append(key)
            continue
        elem_index[key]["label"] = new_label
        rewritten += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Verify
    import re
    state_pattern = re.compile(r'(ていた|でいた|なっていた)$')
    remaining = 0
    for fv in data["frameworkViews"]:
        for el in fv.get("elements", []):
            if el["layer"] == "F" and state_pattern.search(el["label"]):
                remaining += 1
                print(f"  残存: {fv['eventId']} | {el['label'][-30:]}")

    print(f"\n=== v3.7b F時制修正 ===")
    print(f"書き換え: {rewritten}/{len(REWRITES)}件")
    if not_found:
        print(f"未発見: {not_found}")
    print(f"「〜ていた」残存: {remaining}件")
    print(f">>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
