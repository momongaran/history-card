#!/usr/bin/env python3
"""
v3.8 origin拡充スクリプト

B要素のoriginフィールド（先行イベントのEから派生したことを示すリンク）を
全件走査して追加する。

既存27件に加え、プラン定義の約90件を追加。
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "archive" / "data" / "framework_output_v3_8.json"

# elementId -> sourceEventId のマッピング
# 既存originがあるものは自動スキップ
NEW_ORIGINS = {
    # === 飛鳥〜奈良時代 ===
    # 大伴金村が政権を主導: 継体天皇擁立の功績
    "EL_EV_p0512_01_1": "EV_p0507_01",
    # 崇峻天皇暗殺: 蘇我馬子が大臣として実権 ← 丁未の乱
    "EL_EV_p0592_01_7": "EV_p0587_01",
    # 推古天皇即位: 蘇我馬子が大臣として朝廷の実権 ← 丁未の乱
    "EL_EV_p0593_01_7": "EV_p0587_01",
    # 推古天皇即位: 崇峻暗殺後、皇位継承候補は限られ ← 崇峻暗殺
    "EL_EV_p0593_01_8": "EV_p0592_01",
    # 厩戸王摂政: 推古天皇は即位時…蘇我氏の血を引く ← 推古即位
    "EL_EV_p0593_02_1": "EV_p0593_01",
    # 厩戸王摂政: 推古天皇即位時、蘇我馬子は最大の基盤 ← 丁未の乱
    "EL_EV_p0593_02_2": "EV_p0587_01",
    # 遣隋使: 冠位十二階・十七条憲法など国内制度整備 ← 冠位十二階
    "EL_EV_p0607_01_2": "EV_p0603_01",
    # 大化の改新の詔: 乙巳の変で蘇我氏が排除 ← 乙巳の変
    "EL_EV_p0645_02_3": "EV_p0645_01",
    # 改新の詔: 豪族の私地私民が残存 ← 大化の改新の詔
    "EL_EV_p0646_01_1": "EV_p0645_02",
    # 八色の姓: 壬申の乱で功績を立てた豪族と旧来の序列食い違い ← 壬申の乱
    "EL_EV_p0684_01_1": "EV_p0672_01",
    # 飛鳥浄御原令: 唐の律令を参照しつつ法典 ← 八色の姓
    "EL_EV_p0689_01_2": "EV_p0684_01",
    # 藤原京: 律令国家にふさわしい恒久的な都 ← 飛鳥浄御原令
    "EL_EV_p0694_01_2": "EV_p0689_01",
    # 大宝律令: 唐の律令を範としつつ編纂 ← 飛鳥浄御原令
    "EL_EV_p0701_01_2": "EV_p0689_01",
    # 平城京遷都: 唐の長安城を模範とした都城計画 ← 藤原京
    "EL_EV_p0710_01_2": "EV_p0694_01",
    # 古事記: 天武天皇が帝紀・旧辞の誤りを正すため ← 壬申の乱
    "EL_EV_p0712_01_1": "EV_p0672_01",
    # 日本書紀: 古事記に続き編年体国史 ← 古事記
    "EL_EV_p0720_01_1": "EV_p0712_01",
    # 三世一身法: 班田収授制のもとで口分田の不足 ← 改新の詔
    "EL_EV_p0723_01_1": "EV_p0646_01",
    # 墾田永年私財法: 三世一身法では返還 ← 三世一身法
    "EL_EV_p0743_01_3": "EV_p0723_01",
    # 恵美押勝の乱: 孝謙上皇と道鏡の台頭に危機感 ← 橘奈良麻呂の乱
    "EL_EV_p0764_01_1": "EV_p0757_01",
    # 宇佐八幡神託: 称徳天皇が道鏡を重用 ← 恵美押勝の乱
    "EL_EV_p0769_01_1": "EV_p0764_01",
    # 平安京遷都: 長岡京が怨霊騒ぎと水害で不吉 ← 長岡京遷都
    "EL_EV_p0794_01_1": "EV_p0784_01",
    # 天台宗: 桓武天皇が奈良仏教の政治介入を排し ← 平安京遷都
    "EL_EV_p0805_01_2": "EV_p0794_01",

    # === 平安時代 ===
    # 摂関政治開始: 藤原良房が他氏排斥と外戚戦略 ← 承和の変
    "EL_EV_p0858_01_2": "EV_p0842_01",
    # 応天門の変: 藤原良房が事件を利用して排斥 ← 摂関政治開始
    "EL_EV_p0866_01_2": "EV_p0858_01",
    # 古今和歌集: 国風文化の興隆 ← 遣唐使中止
    "EL_EV_p0905_01_1": "EV_p0894_01",
    # 院政開始: 白河天皇が幼い堀河天皇に譲位 ← 後三条親政
    "EL_EV_p1086_01_2": "EV_p1068_01",
    # 鳥羽天皇即位: 白河法皇が幼い鳥羽天皇を即位 ← 院政開始
    "EL_EV_p1108_01_2": "EV_p1086_01",
    # 鳥羽天皇即位: 白河法皇の意向により五歳で即位 ← 院政開始
    "EL_EV_p1108_01_3": "EV_p1086_01",
    # 源平合戦: 平氏の専横に以仁王が挙兵呼びかけ ← 清盛太政大臣
    "EL_EV_p1180_01_1": "EV_p1167_01",
    # 義仲入京: 平氏が都落ちし京都が空白 ← 源平合戦勃発
    "EL_EV_p1183_01_2": "EV_p1180_01",
    # 集約: 武士が政治的決定に軍事力で介入が常態化 ← 保元の乱
    "EL_EV_p1184_01_2": "EV_p1156_01",
    # 守護地頭設置: 壇ノ浦で平氏を滅ぼし ← 壇ノ浦
    "EL_EV_p1185_03_1": "EV_p1185_01",
    # 頼朝将軍: 鎌倉を拠点に御家人制度と守護・地頭 ← 守護地頭設置
    "EL_EV_p1192_01_1": "EV_p1185_03",

    # === 鎌倉〜室町時代 ===
    # 頼朝死去: 頼朝の独裁的指導力に依存 ← 頼朝将軍
    "EL_EV_p1199_01_1": "EV_p1192_01",
    # 北条時政執権: 源頼家の独断的政治に不満 ← 頼朝死去
    "EL_EV_p1203_01_1": "EV_p1199_01",
    # 時政失脚: 北条時政が後妻と結び将軍排除を企て ← 時政が執権
    "EL_EV_p1205_01_1": "EV_p1203_01",
    # 泰時執権: 承久の乱後に全国統治の課題拡大 ← 承久の乱
    "EL_EV_p1225_01_3": "EV_p1221_02",
    # 霜月騒動: 元寇後に非常体制が解かれ内部矛盾 ← 弘安の役
    "EL_EV_p1285_01_3": "EV_p1281_01",
    # 永仁徳政令: 元寇後に恩賞なき奉公 ← 文永の役
    "EL_EV_p1297_01_3": "EV_p1274_01",
    # 幕府滅亡: 元弘の変以降の討幕運動が拡大 ← 元弘の変
    "EL_EV_p1333_01_1": "EV_p1331_01",
    # 幕府滅亡: 足利高氏が幕府を裏切り ← 元弘の変
    "EL_EV_p1333_01_2": "EV_p1331_01",
    # 建武新政: 鎌倉幕府の滅亡で天皇親政の機会 ← 幕府滅亡
    "EL_EV_p1334_01_1": "EV_p1333_01",
    # 南北朝対立: 建武の新政への武士の不満 ← 建武新政
    "EL_EV_p1336_01_1": "EV_p1334_01",
    # 尊氏将軍: 北朝の光明天皇を擁立 ← 南北朝対立
    "EL_EV_p1338_01_1": "EV_p1336_01",
    # 観応の擾乱: 尊氏と直義が幕政の運営方針で対立 ← 尊氏将軍
    "EL_EV_p1351_01_1": "EV_p1338_01",
    # 花の御所: 義満が南北朝統一と幕府権威確立推進 ← 観応の擾乱
    "EL_EV_p1378_01_1": "EV_p1351_01",
    # 応仁の乱: 家督争いが両陣営の対立に ← 嘉吉の乱
    "EL_EV_p1467_01_2": "EV_p1441_01",
    # 応仁の乱終結: 長期の戦闘で両陣営とも疲弊 ← 応仁の乱
    "EL_EV_p1477_01_1": "EV_p1467_01",

    # === 戦国〜江戸時代 ===
    # 信長入京: 美濃を制圧し畿内進出の軍事力 ← 桶狭間
    "EL_EV_p1568_01_2": "EV_p1560_01",
    # 延暦寺焼き討ち: 延暦寺が浅井・朝倉に味方 ← 信長入京
    "EL_EV_p1571_01_1": "EV_p1568_01",
    # 賤ヶ岳: 信長の後継をめぐり秀吉と勝家が対立 ← 本能寺の変
    "EL_EV_p1583_01_1": "EV_p1582_02",
    # 秀吉関白: 武家出身の秀吉には将軍就任の先例なし ← 賤ヶ岳
    "EL_EV_p1585_01_1": "EV_p1583_01",
    # 秀吉太政大臣: 関白就任後さらに最高位を目指し ← 秀吉関白
    "EL_EV_p1586_01_1": "EV_p1585_01",
    # 全国統一: 九州・四国の平定完了 ← 太政大臣
    "EL_EV_p1590_01_1": "EV_p1587_02",
    # 身分統制令: 検地と刀狩により身分固定の基盤 ← 刀狩令
    "EL_EV_p1591_01_3": "EV_p1588_01",
    # 文禄の役: 全国統一後の軍事力の向け先 ← 全国統一
    "EL_EV_p1592_01_2": "EV_p1590_01",
    # 慶長の役: 文禄の役後の講和交渉が決裂 ← 文禄の役
    "EL_EV_p1597_01_1": "EV_p1592_01",
    # 関ヶ原: 秀吉死後の政権内部対立 ← 秀吉死去
    "EL_EV_p1600_01_1": "EV_p1598_01",
    # 秀忠将軍: 将軍職の世襲を示す必要 ← 江戸幕府開設
    "EL_EV_p1605_01_1": "EV_p1603_01",
    # 大坂冬の陣: 方広寺鐘銘事件を口実に ← 秀忠将軍
    "EL_EV_p1614_01_2": "EV_p1605_01",
    # 大坂夏の陣: 冬の陣の和議で外堀埋められ ← 大坂冬の陣
    "EL_EV_p1615_02_1": "EV_p1614_01",
    # 鎖国確立: ポルトガル船は貿易と布教を同一 ← 島原の乱
    "EL_EV_p1639_01_2": "EV_p1637_01",
    # 出島移転: ポルトガル人退去後に空き地 ← 鎖国確立
    "EL_EV_p1641_01_3": "EV_p1639_01",
    # 慶安の変: 大量の浪人が社会不安 ← 大坂夏の陣
    "EL_EV_p1651_01_1": "EV_p1615_02",

    # === 幕末〜近現代 ===
    # 寛政の改革: 白河藩主として飢饉対策に成功 ← 天明の大飢饉
    "EL_EV_p1787_02_1": "EV_p1782_01",
    # レザノフ来航: ラクスマンの入港許可証を持参 ← ラクスマン来航
    "EL_EV_p1804_01_1": "EV_p1792_01",
    # レザノフ来航: ラクスマン来航以来の南下圧力 ← ラクスマン来航
    "EL_EV_p1804_01_3": "EV_p1792_01",
    # 異国船打払令: 外国船の来航・上陸が頻発 ← 大津浜事件
    "EL_EV_p1825_01_1": "EV_p1824_01",
    # 蛮社の獄: モリソン号事件で打払令の問題点 ← 異国船打払令
    "EL_EV_p1839_01_1": "EV_p1825_01",
    # 日米和親条約: 軍事的圧力の前に鎖国維持不可能 ← ペリー来航
    "EL_EV_p1854_01_3": "EV_p1853_02",
    # 安政の大獄: 条約勅許問題と将軍継嗣問題 ← 日米修好通商条約
    "EL_EV_p1858_01_1": "EV_p1858_02",
    # 桜田門外の変: 水戸藩脱藩浪士が暗殺を計画 ← 安政の大獄
    "EL_EV_p1860_01_2": "EV_p1858_01",
    # 生麦事件: 開港により外国人が自由に移動 ← 日米和親条約
    "EL_EV_p1862_01_1": "EV_p1854_01",
    # 生麦事件: 攘夷思想が高まり外国人への敵意 ← 日米修好通商条約
    "EL_EV_p1862_01_2": "EV_p1858_02",
    # 禁門の変: 八月十八日の政変で長州藩が追放 ← 薩英戦争(※)
    # ※八月十八日政変は独立イベント化されていないがplanではnull判定
    # → planでnull判定なので除外

    # 薩長同盟: 薩摩藩と長州藩が幕府への不満 ← 禁門の変
    "EL_EV_p1866_02_1": "EV_p1864_01",
    # 大政奉還: 薩長同盟の成立で武力倒幕の機運 ← 薩長同盟
    "EL_EV_p1867_01_1": "EV_p1866_02",
    # 廃藩置県: 版籍奉還後も旧藩主が実権 ← 王政復古
    "EL_EV_p1871_01_1": "EV_p1867_02",
    # 日露戦争: 日英同盟を背景に対露強硬路線 ← 日英同盟
    "EL_EV_p1904_01_2": "EV_p1902_01",
    # 一次大戦: 日英同盟を根拠にドイツに宣戦 ← 日英同盟
    "EL_EV_p1914_01_2": "EV_p1902_01",
    # 満州事変: 中国国民政府の権限拡大 ← 韓国併合
    "EL_EV_p1931_01_3": "EV_p1910_01",
    # 国際連盟脱退: リットン調査団が満州国の独立を否定 ← 満州事変
    "EL_EV_p1933_01_1": "EV_p1931_01",
    # 国際連盟脱退: 国際連盟総会で満州国不承認決議 ← 満州事変
    "EL_EV_p1933_01_2": "EV_p1931_01",
    # 日中戦争: 華北への日本軍の進出 ← 満州事変
    "EL_EV_p1937_01_1": "EV_p1931_01",
    # 三国同盟: 日中戦争の長期化でアメリカとの関係悪化 ← 日中戦争
    "EL_EV_p1940_01_1": "EV_p1937_01",
    # 太平洋戦争: 石油禁輸措置で戦争遂行能力が限界 ← 三国同盟
    "EL_EV_p1941_01_2": "EV_p1940_01",
    # GHQ占領: ポツダム宣言の受諾により降伏 ← 終戦
    "EL_EV_p1945_01_1": "EV_p1945_02",
    # 日本国憲法公布: GHQが全面改正を指示 ← GHQ占領
    "EL_EV_p1946_01_1": "EV_p1945_01",
    # SF条約: 主権回復 ← SF条約
    "EL_EV_p1952_02_1": "EV_p1951_01",
    # 主権回復: GHQが廃止され占領終了 ← SF条約
    "EL_EV_p1952_02_2": "EV_p1951_01",
    # 日米安保: 主権回復後の安全保障の空白 ← 主権回復
    "EL_EV_p1952_03_1": "EV_p1952_02",
}


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build element lookup: elementId -> element dict
    elem_lookup = {}
    elem_event = {}  # elementId -> eventId (of its frameworkView)
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            elem_lookup[elem["elementId"]] = elem
            elem_event[elem["elementId"]] = fv["eventId"]

    # Build event sortKey lookup
    event_sortkeys = {}
    for ev in data["events"]:
        event_sortkeys[ev["eventId"]] = ev["sortKey"]

    # Validate all sourceEventIds exist
    all_event_ids = set(event_sortkeys.keys())

    added = 0
    skipped = 0
    not_found = []
    errors = []

    for elem_id, source_eid in NEW_ORIGINS.items():
        if elem_id not in elem_lookup:
            not_found.append(elem_id)
            continue

        elem = elem_lookup[elem_id]

        # Skip if already has origin
        if elem.get("origin"):
            skipped += 1
            continue

        # Validate layer
        if elem.get("layer") != "B":
            errors.append(f"{elem_id}: layer is {elem.get('layer')}, not B")
            continue

        # Validate source event exists
        if source_eid not in all_event_ids:
            errors.append(f"{elem_id}: sourceEventId {source_eid} not found")
            continue

        # Validate time order (source sortKey <= target sortKey)
        target_eid = elem_event[elem_id]
        source_sk = event_sortkeys.get(source_eid, 0)
        target_sk = event_sortkeys.get(target_eid, 0)
        if source_sk > target_sk:
            errors.append(f"{elem_id}: time violation {source_eid}(sk={source_sk}) > {target_eid}(sk={target_sk})")
            continue

        elem["origin"] = {
            "sourceEventId": source_eid,
            "sourceLayer": "E"
        }
        added += 1

    # Save
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Count total origins
    total_b = 0
    total_origins = 0
    for fv in data["frameworkViews"]:
        for elem in fv.get("elements", []):
            if elem.get("layer") == "B":
                total_b += 1
                if elem.get("origin"):
                    total_origins += 1

    print(f"=== v3.8 origin拡充 ===")
    print(f"追加対象: {len(NEW_ORIGINS)}件")
    print(f"追加成功: {added}件")
    print(f"既存スキップ: {skipped}件")
    print(f"未発見: {len(not_found)}件")
    if not_found:
        for eid in not_found:
            print(f"  未発見: {eid}")
    if errors:
        print(f"エラー: {len(errors)}件")
        for e in errors:
            print(f"  {e}")
    print(f"\n--- 集計 ---")
    print(f"B要素総数: {total_b}件")
    print(f"origin総数: {total_origins}件 (既存27 + 新規{added})")
    print(f"origin率: {total_origins}/{total_b} ({100*total_origins/total_b:.1f}%)")
    print(f"\n>>> {DATA_FILE} を上書き保存しました。")


if __name__ == "__main__":
    main()
