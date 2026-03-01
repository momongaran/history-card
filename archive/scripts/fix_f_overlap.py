#!/usr/bin/env python3
"""
fix_f_overlap.py — F/E重複問題47件のうち39件のFテキストを修正する。
8件は維持（修正不要）。

修正対象:
- framework_output_v3_8.json: F要素の label, normalizedLabel, category, subCategory
- f_e_overlap_issues.json: resolved, fixedFText フィールド追加
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FRAMEWORK_FILE = DATA_DIR / "framework_output_v3_8.json"
ISSUES_FILE = DATA_DIR / "f_e_overlap_issues.json"

# 39件の修正データ: eventId -> { label, normalizedLabel, subCategory }
FIXES = {
    # === HIGH CONFIDENCE 33件 ===
    "EV_p0512_01": {
        "label": "朝鮮半島情勢の緊迫化により即応可能な軍事・外交の調整者が急務となった",
        "normalizedLabel": "半島情勢緊迫で調整者急務",
        "subCategory": "F-CTD-01",
        "category": "F-CTD",
    },
    "EV_p0538_01": {
        "label": "百済が高句麗・新羅の軍事圧迫で追い詰められ、倭との同盟強化のため最大級の文化的贈与を決断した",
        "normalizedLabel": "百済が軍事圧迫下で仏教献上を決断",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p0587_01": {
        "label": "物部守屋が天皇擁立に独自に動き、蘇我馬子との権力分担の余地が消滅した",
        "normalizedLabel": "物部守屋の独自行動で権力分担消滅",
        "subCategory": "F-CNF-02",
        "category": "F-CNF",
    },
    "EV_p0607_01": {
        "label": "隋が高句麗遠征を準備中で、倭国が冊封体制に組み込まれる前に独自の外交姿勢を示す時間的猶予が限られた",
        "normalizedLabel": "隋の高句麗遠征準備で外交猶予縮小",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p0630_01": {
        "label": "唐が律令制を完成させ東アジアの国際秩序が再編される中、制度導入の遅れが倭国の不利に直結する状況が生じた",
        "normalizedLabel": "唐の律令完成で制度導入遅れが不利に",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p0647_01": {
        "label": "班田収授の実施により個別農民が国家に直接把握され、逃れ得ない徴税対象として確定した",
        "normalizedLabel": "班田収授で農民が徴税対象に確定",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0648_01": {
        "label": "白村江の敗戦後、唐・新羅の侵攻に備え九州沿岸の防衛体制強化が命じられた",
        "normalizedLabel": "白村江敗戦後の防衛体制強化命令",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p0694_01": {
        "label": "持統天皇が天武天皇の構想を引き継ぎ、律令国家の首都建設を決断した",
        "normalizedLabel": "持統天皇が首都建設を決断",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0710_01": {
        "label": "藤原京の水害と排水問題が深刻化し、元明天皇が新都への移転を決断した",
        "normalizedLabel": "藤原京の水害で元明天皇が遷都決断",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0712_01": {
        "label": "元明天皇が太安万侶に天武朝以来中断していた国史編纂の完成を命じた",
        "normalizedLabel": "元明天皇が国史編纂完成を命令",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0720_01": {
        "label": "天武天皇が川島皇子・舎人親王らに帝紀・上古諸事の記録を命じた",
        "normalizedLabel": "天武天皇が帝紀記録を命令",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0759_01": {
        "label": "大伴家持が越中国守として各地の歌を収集する機会を得、散逸する和歌の保存に着手した",
        "normalizedLabel": "大伴家持が和歌保存に着手",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p0792_01": {
        "label": "蝦夷征討で郡司子弟の志願兵が徴兵農民兵より有効と判明し、軍団制の費用対効果の逆転が明白となった",
        "normalizedLabel": "蝦夷征討で軍団制の費用対効果逆転",
        "subCategory": "F-CTD-01",
        "category": "F-CTD",
    },
    "EV_p0806_01": {
        "label": "嵯峨天皇が空海の密教の加持祈祷に強い関心を示し、宮中での活動を許可した",
        "normalizedLabel": "嵯峨天皇が空海の宮中活動を許可",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1052_01": {
        "label": "暦算により1052年が釈迦入滅後二千年目（末法元年）に当たると算定された",
        "normalizedLabel": "1052年が末法元年と算定",
        "subCategory": "F-UNC-02",
        "category": "F-UNC",
    },
    "EV_p1086_01": {
        "label": "白河天皇が8歳の善仁親王への譲位を決断し、上皇として政務に関与する意思を示した",
        "normalizedLabel": "白河天皇が善仁親王への譲位を決断",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1167_01": {
        "label": "後白河法皇との協調関係が成立し、清盛の昇進を阻む政治的障壁が消滅した",
        "normalizedLabel": "後白河法皇との協調で昇進障壁消滅",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1203_01": {
        "label": "比企能員が頼家の病に乗じて一族の権力独占を図り、北条氏との共存が不可能となった",
        "normalizedLabel": "比企能員の権力独占で北条氏と共存不可能",
        "subCategory": "F-CNF-01",
        "category": "F-CNF",
    },
    "EV_p1205_01": {
        "label": "時政が後妻・牧の方と共謀し将軍実朝の廃立を画策していることが義時・政子に発覚した",
        "normalizedLabel": "時政の将軍廃立画策が発覚",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1285_01": {
        "label": "安達泰盛の御家人重視改革が得宗被官の既得権を直接脅かし、平頼綱が先制攻撃を決断した",
        "normalizedLabel": "安達改革への反発で平頼綱が先制攻撃",
        "subCategory": "F-CNF-02",
        "category": "F-CNF",
    },
    "EV_p1334_01": {
        "label": "鎌倉幕府滅亡により武家政権が消滅し、後醍醐天皇が親政実現の障害を失った",
        "normalizedLabel": "幕府滅亡で後醍醐天皇の親政障害消滅",
        "subCategory": "F-VAC-01",
        "category": "F-VAC",
    },
    "EV_p1336_01": {
        "label": "建武の新政への武士の不満が噴出し、足利尊氏が後醍醐天皇から離反した",
        "normalizedLabel": "武士の不満噴出で尊氏が後醍醐から離反",
        "subCategory": "F-CNF-01",
        "category": "F-CNF",
    },
    "EV_p1336_02": {
        "label": "京都制圧後、武家による新統治の正統性を示す法的根拠の整備が急がれた",
        "normalizedLabel": "京都制圧後に法的根拠整備が急務",
        "subCategory": "F-CTD-01",
        "category": "F-CTD",
    },
    "EV_p1392_01": {
        "label": "南朝の軍事力が衰退し、後亀山天皇が両統迭立の条件を受け入れる以外の選択肢を失った",
        "normalizedLabel": "南朝衰退で後亀山天皇の選択肢消滅",
        "subCategory": "F-CNF-01",
        "category": "F-CNF",
    },
    "EV_p1404_01": {
        "label": "明が倭寇禁圧の条件として日本国王の冊封と朝貢を求め、義満がこれを受諾した",
        "normalizedLabel": "明の冊封・朝貢要求を義満が受諾",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p1493_01": {
        "label": "将軍義材が河内遠征で京都を留守にし、細川政元がクーデターの機会を得た",
        "normalizedLabel": "義材の京都不在で政元がクーデター機会",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1549_02": {
        "label": "ザビエルがマラッカで日本人ヤジロウと出会い、日本布教の可能性を確信した",
        "normalizedLabel": "ザビエルがヤジロウと出会い日本布教を確信",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1573_01": {
        "label": "武田信玄の死去により信長包囲網が瓦解し、義昭を庇護する軍事勢力が消滅した",
        "normalizedLabel": "信玄死去で信長包囲網瓦解",
        "subCategory": "F-ACT-02",
        "category": "F-ACT",
    },
    "EV_p1590_01": {
        "label": "秀吉が惣無事令違反を名目に20万の大軍を小田原に動員した",
        "normalizedLabel": "秀吉が20万の大軍を小田原に動員",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1605_01": {
        "label": "関ヶ原から5年が経過し、豊臣氏が健在なうちに徳川の世襲体制を確立する時間的圧力が高まった",
        "normalizedLabel": "豊臣健在中の世襲確立に時間的圧力",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1641_01": {
        "label": "ポルトガル人追放により長崎出島が空き、外国人隔離施設の転用先が確保された",
        "normalizedLabel": "ポルトガル人追放で出島が空き転用可能に",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1914_01": {
        "label": "サラエボ事件を契機に欧州列強間の戦争が勃発し、日英同盟に基づく参戦要請が生じた",
        "normalizedLabel": "サラエボ事件で欧州戦争勃発、日英同盟で参戦要請",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    "EV_p1945_01": {
        "label": "マッカーサーが連合国軍最高司令官として厚木に到着し、日本政府に占領方針を通告した",
        "normalizedLabel": "マッカーサー到着と占領方針通告",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
    # === GRAY CONFIDENCE 修正6件 ===
    "EV_p0784_01": {
        "label": "道鏡事件に象徴される奈良仏教勢力の政治介入が限界に達し、桓武天皇が物理的離脱を決断した",
        "normalizedLabel": "奈良仏教の政治介入で桓武天皇が離脱決断",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1338_01": {
        "label": "北朝の光明天皇が尊氏の軍功に報いて征夷大将軍を任じた",
        "normalizedLabel": "光明天皇が尊氏に征夷大将軍を任命",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1378_01": {
        "label": "土岐氏の乱鎮圧により守護大名への優位が確立し、義満が恒久的統治拠点の建設を決断した",
        "normalizedLabel": "土岐氏鎮圧で義満が統治拠点建設を決断",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1603_01": {
        "label": "家康が源氏長者・征夷大将軍の宣下を朝廷に奏請した",
        "normalizedLabel": "家康が征夷大将軍宣下を奏請",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1772_01": {
        "label": "10代将軍家治が田沼意次を側用人から老中に抜擢した",
        "normalizedLabel": "将軍家治が田沼意次を老中に抜擢",
        "subCategory": "F-ACT-01",
        "category": "F-ACT",
    },
    "EV_p1792_01": {
        "label": "ロシア使節ラクスマンが漂流民大黒屋光太夫を伴い根室に入港した",
        "normalizedLabel": "ラクスマンが漂流民を伴い根室に入港",
        "subCategory": "F-EXT-01",
        "category": "F-EXT",
    },
}

# 維持（修正不要）8件
KEEP_AS_IS = [
    "EV_p1945_02",  # high: 聖断はトリガーとして機能
    "EV_p0805_01",  # gray: 桓武天皇の支援決断はトリガー
    "EV_p0905_01",  # gray: 醍醐天皇の勅命はトリガー
    "EV_p1096_01",  # gray: 白河上皇の命令はトリガー
    "EV_p1543_01",  # gray: ポルトガル商船の漂着はトリガー
    "EV_p1585_01",  # gray: 近衛前久の猶子はトリガー
    "EV_p1586_01",  # gray: 独立勢力消滅はF的
    "EV_p1867_01",  # gray: 慶喜の判断はトリガー
]


def fix_framework(data: dict) -> tuple[int, list[str]]:
    """framework_output_v3_8.json のF要素を修正する。"""
    fixed_count = 0
    log = []

    # frameworkViews セクションを探す
    frameworks = data.get("frameworkViews", [])
    for fw in frameworks:
        eid = fw.get("eventId") or fw.get("primaryEventId")
        if eid not in FIXES:
            continue

        fix = FIXES[eid]
        for elem in fw.get("elements", []):
            if elem.get("layer") != "F":
                continue

            old_label = elem["label"]
            old_sub = elem.get("subCategory", "")

            elem["label"] = fix["label"]
            elem["normalizedLabel"] = fix["normalizedLabel"]
            elem["subCategory"] = fix["subCategory"]
            elem["category"] = fix["category"]

            fixed_count += 1
            log.append(
                f"  {eid}: [{old_sub}] {old_label[:40]}... -> [{fix['subCategory']}] {fix['label'][:40]}..."
            )

    return fixed_count, log


def fix_issues(data: dict) -> int:
    """f_e_overlap_issues.json に resolved/fixedFText を追加する。"""
    updated = 0
    for issue in data.get("issues", []):
        eid = issue["eventId"]
        if eid in FIXES:
            issue["resolved"] = True
            issue["fixedFLabel"] = FIXES[eid]["label"]
            issue["fixedSubCategory"] = FIXES[eid]["subCategory"]
            updated += 1
        elif eid in KEEP_AS_IS:
            issue["resolved"] = False
            issue["resolutionNote"] = "維持（修正不要）: 現行Fはトリガーとして機能"
            updated += 1
        else:
            print(f"WARNING: {eid} not in FIXES or KEEP_AS_IS", file=sys.stderr)
    return updated


def main():
    # Load
    with open(FRAMEWORK_FILE, "r", encoding="utf-8") as f:
        fw_data = json.load(f)
    with open(ISSUES_FILE, "r", encoding="utf-8") as f:
        issues_data = json.load(f)

    # Fix framework
    fixed_count, log = fix_framework(fw_data)
    print(f"=== framework_output_v3_8.json ===")
    print(f"Modified {fixed_count} F elements (expected: {len(FIXES)})")
    for line in log:
        print(line)

    if fixed_count != len(FIXES):
        print(f"\nWARNING: Expected {len(FIXES)} fixes, got {fixed_count}!", file=sys.stderr)
        # Find missing
        found_ids = set()
        for fw in fw_data.get("frameworkViews", []):
            eid = fw.get("eventId") or fw.get("primaryEventId")
            if eid in FIXES:
                found_ids.add(eid)
        missing = set(FIXES.keys()) - found_ids
        if missing:
            print(f"Missing eventIds in frameworks: {missing}", file=sys.stderr)

    # Fix issues
    issues_updated = fix_issues(issues_data)
    print(f"\n=== f_e_overlap_issues.json ===")
    print(f"Updated {issues_updated} issues (expected: 47)")

    # Save
    with open(FRAMEWORK_FILE, "w", encoding="utf-8") as f:
        json.dump(fw_data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {FRAMEWORK_FILE}")

    with open(ISSUES_FILE, "w", encoding="utf-8") as f:
        json.dump(issues_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {ISSUES_FILE}")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Total issues: 47")
    print(f"Fixed: {fixed_count}")
    print(f"Kept as-is: {len(KEEP_AS_IS)}")
    print(f"Total resolved: {fixed_count + len(KEEP_AS_IS)}")


if __name__ == "__main__":
    main()
