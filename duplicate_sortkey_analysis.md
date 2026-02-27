# Duplicate SortKey Analysis: framework_output_v3_3.json

## Summary
- **Total frameworkViews**: 221
- **Unique sortKeys**: 189
- **Groups with multiple frameworkViews**: 28
- **Total duplicates identified**: 51 frameworkView instances across 28 sortKey groups

---

## DETAILED FINDINGS BY SORTKEY

### SORTKEY: 593 (2 events) - OVERLAPPING

**Events:**
1. **EV_p0593_01**: 推古天皇が即位した
2. **EV_p0593_02**: 厩戸王が摂政に就任した

**Assessment:** OVERLAPPING
**Reasoning:** These are two sequential but distinct events in the same year (593). The first describes the empress's enthronement; the second describes Prince Shotoku's appointment as regent. They are causally related (the regent was needed because the empress lacked experience) but represent separate historical moments. Consider keeping both but clarifying the causal relationship.

---

### SORTKEY: 645 (2 events) - OVERLAPPING

**Events:**
1. **EV_p0645_01**: 乙巳の変が起き大化改新が始まった
2. **EV_p0645_02**: 大化の改新の詔が出された

**Assessment:** OVERLAPPING
**Reasoning:** Same historical event described from different angles - the Taika Reforms. EV_p0645_01 focuses on the coup (Isshi Incident) that triggered the reforms, while EV_p0645_02 focuses on the formal promulgation of reform edicts. Technically overlapping but could represent important sub-phases. Consider merging or clarifying the temporal/conceptual distinction.

**Possible Action:** Could be merged into single event with both aspects represented.

---

### SORTKEY: 743 (2 events) - TRUE DUPLICATE

**Events:**
1. **EV_p0743_01**: 墾田永年私財法が出された
2. **EV_p0743_02**: 墾田永年私財法を定めた

**Assessment:** OVERLAPPING (quasi-duplicate)
**Reasoning:** Same law (Kondeneihen Shizaiho) described with minimal wording difference: "出された" (was issued) vs "定めた" (was established). Nearly identical descriptions. Both event IDs share identical cause/result text.

**Possible Action:** **SHOULD BE MERGED** - This is essentially the same event with trivial wording variation. Keep EV_p0743_01 with "出された" as more formal.

---

### SORTKEY: 939 (2 events) - DISTINCT EVENTS

**Events:**
1. **EV_p0939_01**: 平将門の乱が起きた
2. **EV_p0939_02**: 藤原純友の乱が起きた

**Assessment:** DISTINCT EVENTS
**Reasoning:** Two separate, simultaneous rebellions that both occurred in 939 CE:
- Taira no Masakado's Rebellion in the Kanto region
- Fujiwara no Sumitomo's Rebellion in western Japan

While they occurred in the same year, they are geographically and politically distinct events with different causes and consequences. This is a legitimate case of multiple significant events in one year.

**Possible Action:** KEEP BOTH - These are genuinely different historical events that happen to share a sortKey year. No merger needed.

---

### SORTKEY: 1016 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1016_01**: 藤原道長が摂政となった
2. **EV_p1016_02**: 藤原道長が摂政に就任した

**Assessment:** OVERLAPPING (near-duplicate)
**Reasoning:** Same appointment described with minimal variation: "となった" (became) vs "に就任した" (assumed the position). These are identical events with trivial wording differences.

**Possible Action:** **SHOULD BE MERGED** - Keep one with more formal phrasing.

---

### SORTKEY: 1086 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1086_01**: 白河上皇が院政を開始した
2. **EV_p1086_02**: 院政が始まった(白河上皇)

**Assessment:** OVERLAPPING (near-duplicate)
**Reasoning:** Same beginning of "insei" (cloister government) described from agent-centric vs. system-centric perspectives. The first emphasizes the person (Shirakawa), the second emphasizes the institution. Essentially the same event.

**Possible Action:** **SHOULD BE MERGED** - Keep EV_p1086_01 as it provides agent clarity.

---

### SORTKEY: 1185 (3 events) - OVERLAPPING

**Events:**
1. **EV_p1185_01**: 壇ノ浦の戦いで平氏が滅亡した
2. **EV_p1185_02**: 守護・地頭が設置された
3. **EV_p1185_03**: 源頼朝が守護・地頭を設置した

**Assessment:** OVERLAPPING
**Reasoning:** Multiple perspectives on 1185:
- EV_p1185_01: The final military battle (Heike destruction)
- EV_p1185_02: The institutional consequence (system-centric view)
- EV_p1185_03: Same institutional consequence but agent-centric (Minamoto no Yoritomo as actor)

Events 2 and 3 are near-duplicates (same action, different framing). Event 1 is causally related but distinct.

**Possible Action:**
- Keep EV_p1185_01 (the battle - distinct event)
- Merge EV_p1185_02 and EV_p1185_03 into single event (keep EV_p1185_03 for clarity)

---

### SORTKEY: 1221 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1221_01**: 承久の乱が起きた
2. **EV_p1221_02**: 承久の乱が起き幕府が朝廷に勝利した

**Assessment:** OVERLAPPING
**Reasoning:** Same rebellion described at different levels of specificity. The second event adds the outcome (bakufu victory). Could be seen as the event + its immediate result.

**Possible Action:** Could merge, with the more complete description being: "承久の乱が起き幕府が朝廷に勝利した" (captures both event and key outcome).

---

### SORTKEY: 1274 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1274_01**: 元寇(文永の役)が起きた
2. **EV_p1274_02**: 文永の役(元寇)が起きた

**Assessment:** OVERLAPPING (near-duplicate)
**Reasoning:** Same Mongol invasion (First Mongol Invasion of Japan / Bunei Campaign) described with name order variation. One uses "Genkou" (Mongol Invasion) as primary term with "Bunei no Eki" in parentheses; the other reverses this.

**Possible Action:** **SHOULD BE MERGED** - Standardize terminology, likely preferring "元寇(文永の役)が起きた" or similar unified naming.

---

### SORTKEY: 1336 (3 events) - OVERLAPPING

**Events:**
1. **EV_p1336_01**: 南北朝の対立が始まった
2. **EV_p1336_02**: 足利尊氏が室町幕府を開いた(建武式目)
3. **EV_p1336_03**: 足利尊氏が新政から離反した

**Assessment:** OVERLAPPING
**Reasoning:** Multiple cascading events of 1336:
- The beginning of North-South Court split
- Ashikaga's establishment of Muromachi bakufu
- Ashikaga's defection from Restoration government

These represent different phases/moments of 1336 (which was chaotic). Events 2 and 3 are closely linked causally.

**Possible Action:** Could consolidate the Ashikaga events, but the period's complexity may justify keeping separate.

---

### SORTKEY: 1549 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1549_01**: キリスト教が伝来した(フランシスコ・ザビエル)
2. **EV_p1549_02**: フランシスコ・ザビエルが来日しキリスト教が伝来した

**Assessment:** OVERLAPPING
**Reasoning:** Same arrival of Christianity via Francis Xavier. The first emphasizes the religion; the second emphasizes both the person and the religion. Essentially identical events.

**Possible Action:** **SHOULD BE MERGED** - Keep the more comprehensive version (EV_p1549_02).

---

### SORTKEY: 1582 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1582_01**: 山崎の戦いで羽柴秀吉が勝利した
2. **EV_p1582_02**: 本能寺の変が起きた

**Assessment:** OVERLAPPING
**Reasoning:** These are related but consecutive events of 1582:
- Honnoji Incident (Oda Nobunaga's assassination by Akechi Mitsuhide)
- Battle of Yamashiro (Toyotomi Hideyoshi's response that consolidated power)

These are causally linked (Honnoji triggers Yamashiro) but represent distinct engagements. They could both merit inclusion as they represent the year's crucial transformation.

**Possible Action:** Could keep both if emphasizing cascading causality, or consolidate if focusing on single narrative thread.

---

### SORTKEY: 1587 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1587_01**: バテレン追放令を出した
2. **EV_p1587_02**: 豊臣秀吉が太政大臣となった

**Assessment:** OVERLAPPING
**Reasoning:** Two significant 1587 policies by Toyotomi Hideyoshi:
- Bateren (Christian) Expulsion Edict
- Appointment as Kampaku/Daijodaijin (Chancellor/Grand Minister)

These are politically related (consolidation of power and control) but distinct actions.

**Possible Action:** Could keep both as they represent different policy domains, or focus on the major event (appointment).

---

### SORTKEY: 1590 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1590_01**: 豊臣秀吉が全国を統一した
2. **EV_p1590_02**: 豊臣秀吉が小田原征伐で全国統一を進めた

**Assessment:** OVERLAPPING
**Reasoning:** Same national unification achievement described at different levels:
- General outcome: national unification
- Specific campaign: Odawara Campaign (the final major military action)

The second is a specific instance supporting the first.

**Possible Action:** Could merge with emphasis on Odawara Campaign as the concluding step.

---

### SORTKEY: 1615 (4 events) - OVERLAPPING

**Events:**
1. **EV_p1615_01**: 一国一城令を出した
2. **EV_p1615_02**: 大坂夏の陣で豊臣氏が滅亡した
3. **EV_p1615_03**: 武家諸法度を制定した
4. **EV_p1615_04**: 禁中並公家諸法度を制定した

**Assessment:** OVERLAPPING
**Reasoning:** Multiple related policies/events of 1615:
- One Castle per Domain Edict (Ikokutsujo Minrei)
- Fall of Toyotomi in Osaka Summer Campaign
- Buke Shohatto (Samurai Code)
- Kinchu Narabi Kuge Shohatto (Imperial Court and Nobility Code)

These represent the major bakufu consolidation policies following Toyotomi destruction. Events 3 and 4 are closely paired (samurai and court codes issued together). Event 1 is part of broader consolidation. Event 2 is the military prerequisite.

**Possible Action:** Events 3 and 4 could potentially merge (paired codes), but all four represent crucial aspects of 1615 consolidation. Consider how granular the framework should be.

---

### SORTKEY: 1635 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1635_01**: 参勤交代が制度化された
2. **EV_p1635_02**: 武家諸法度（寛永令）で参勤交代を制度化

**Assessment:** OVERLAPPING
**Reasoning:** Same policy (sankin-kotai / daimyo attendance system) described:
- EV_p1635_01: Generic description
- EV_p1635_02: References the specific legal instrument (Kanei Decree of Buke Shohatto)

Essentially the same event with different specificity.

**Possible Action:** **SHOULD BE MERGED** - Keep version that specifies "武家諸法度（寛永令）" as more informative.

---

### SORTKEY: 1639 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1639_01**: ポルトガル船来航禁止で鎖国体制が確立した
2. **EV_p1639_02**: 鎖国体制が強化された（ポルトガル船来航禁止）

**Assessment:** OVERLAPPING
**Reasoning:** Same sakoku (closed country) policy described as "establishment" vs "strengthening". Both focus on Portuguese ship prohibition in 1639. The distinction between "establishment" and "strengthening" is unclear - this appears to be the same action.

**Possible Action:** **SHOULD BE MERGED** - Keep one, likely EV_p1639_01 which frames it as establishment of the system.

---

### SORTKEY: 1716 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1716_01**: 享保の改革が始まった
2. **EV_p1716_02**: 徳川吉宗が享保の改革を開始した

**Assessment:** OVERLAPPING
**Reasoning:** Same reform (Kyoho Reforms) described from system-centric vs. agent-centric perspective:
- EV_p1716_01: The reform itself as protagonist
- EV_p1716_02: Tokugawa Yoshimune as the actor

Identical event, different narrative framing.

**Possible Action:** **SHOULD BE MERGED** - Keep EV_p1716_02 as it provides agent clarity.

---

### SORTKEY: 1787 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1787_01**: 寛政の改革が始まった
2. **EV_p1787_02**: 松平定信が寛政の改革を開始した

**Assessment:** OVERLAPPING
**Reasoning:** Same reform (Kansei Reforms) with identical narrative structure as 1716:
- System-centric (the reform) vs. agent-centric (Matsudaira Sadanobu)

**Possible Action:** **SHOULD BE MERGED** - Keep EV_p1787_02 for consistency.

---

### SORTKEY: 1841 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1841_01**: 天保の改革が始まった
2. **EV_p1841_02**: 水野忠邦が天保の改革を開始した

**Assessment:** OVERLAPPING
**Reasoning:** Same pattern as 1716 and 1787:
- Tenpo Reforms described system-centric vs. agent-centric (Mizuno Tadakuni)

**Possible Action:** **SHOULD BE MERGED** - Keep EV_p1841_02 for consistency with prior mergers.

---

### SORTKEY: 1853 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1853_01**: ペリーが来航した
2. **EV_p1853_02**: ペリーが浦賀に来航した

**Assessment:** OVERLAPPING (near-duplicate)
**Reasoning:** Same Perry Expedition arrival described with/without specific location (Uraga). One includes location detail, one is more generic.

**Possible Action:** **SHOULD BE MERGED** - Keep EV_p1853_02 with location (more specific).

---

### SORTKEY: 1858 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1858_01**: 安政の大獄が始まった
2. **EV_p1858_02**: 日米修好通商条約を結んだ

**Assessment:** OVERLAPPING
**Reasoning:** Two major 1858 events:
- Ansei Purge (political repression by Ii Naosuke)
- Harris Treaty (US-Japan trade agreement)

These occurred in the same year and are historically related (both products of the political crisis triggered by Perry, both represent different responses). However, they are distinct events with separate causes and consequences.

**Possible Action:** Could keep both if emphasizing the year's dual significance, or consolidate if focusing on treaty as central event.

---

### SORTKEY: 1866 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1866_01**: 外圧と国内政治の再編圧力、体制転換前夜(集約)
2. **EV_p1866_02**: 薩長同盟が成立した

**Assessment:** OVERLAPPING
**Reasoning:** Two aspects of 1866:
- General pre-Restoration political situation (summary/aggregate event)
- Specific concrete alliance (Satsuma-Choshu Alliance)

The first is a meta-description of the context; the second is a specific event within that context.

**Possible Action:** Could keep both if emphasizing narrative structure vs. concrete event, or consolidate.

---

### SORTKEY: 1867 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1867_01**: 大政奉還が行われた
2. **EV_p1867_02**: 王政復古の大号令が出された

**Assessment:** OVERLAPPING
**Reasoning:** Two sequential and causally linked events of 1867:
- Taiseihokan (return of power to imperial court)
- Osei Fukko (imperial restoration edict)

The first is Tokugawa Yoshinobu's voluntary surrender of power; the second is the imperial court's formalization of that power return. Causally linked but represent distinct moments in the Restoration.

**Possible Action:** Could keep both as they represent crucial sequential moments, or emphasize one as the primary event.

---

### SORTKEY: 1925 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1925_01**: 普通選挙法が成立した
2. **EV_p1925_02**: 治安維持法が成立した

**Assessment:** OVERLAPPING
**Reasoning:** Two significant but opposing 1925 laws:
- Universal Manhood Suffrage Law (democratic expansion)
- Peace Preservation Law (political repression)

Historically paired as examples of Japan's simultaneous liberalization and authoritarianism. They are distinct events but represent the year's political contradiction.

**Possible Action:** Both merit inclusion to show the paradox, or consolidate if simplifying the narrative.

---

### SORTKEY: 1945 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1945_01**: GHQによる占領が始まった
2. **EV_p1945_02**: 日本がポツダム宣言を受諾し終戦した

**Assessment:** OVERLAPPING
**Reasoning:** Two aspects of 1945:
- Japan's surrender (Potsdam acceptance / war ending)
- Allied occupation beginning

These are causally linked - the surrender enables the occupation. Both occurred in 1945 but at slightly different times. The second is logically prerequisite to the first.

**Possible Action:** Could emphasize surrender as the primary event, or keep both for completeness on year's transformation.

---

### SORTKEY: 1951 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1951_01**: サンフランシスコ平和条約が調印された
2. **EV_p1951_02**: サンフランシスコ講和条約が調印された

**Assessment:** OVERLAPPING (near-duplicate)
**Reasoning:** Same San Francisco Treaty described with synonym variation: "平和条約" (peace treaty) vs "講和条約" (peace/conciliation treaty). These are exact synonyms in this context.

**Possible Action:** **SHOULD BE MERGED** - "平和条約" is more standard terminology.

---

### SORTKEY: 1952 (2 events) - OVERLAPPING

**Events:**
1. **EV_p1952_02**: 日本が主権を回復した
2. **EV_p1952_03**: 日米安全保障条約が締結された

**Assessment:** OVERLAPPING (causally related but distinct)
**Reasoning:** Two aspects of Japan's post-occupation settlement:
- Sovereignty recovery (enabling independent statehood)
- US-Japan Security Treaty (the security framework accompanying independence)

These are causally linked but distinct - sovereignty recovery is the broader event; the security treaty is a consequence/accompaniment.

**Possible Action:** Both deserve inclusion as they represent the dual nature of 1952: formal independence plus continued security dependence.

---

## SUMMARY RECOMMENDATIONS

### MERGERS STRONGLY RECOMMENDED (True Duplicates/Near-Duplicates)

These should be consolidated into single events with the specified titles:

1. **SORTKEY 743** - EV_p0743_01 and EV_p0743_02 → **MERGE** (identical law, trivial wording)
   - Keep: EV_p0743_01 (墾田永年私財法が出された)

2. **SORTKEY 1016** - EV_p1016_01 and EV_p1016_02 → **MERGE** (same appointment, trivial wording)
   - Keep: EV_p1016_02 (藤原道長が摂政に就任した)

3. **SORTKEY 1086** - EV_p1086_01 and EV_p1086_02 → **MERGE** (same policy start)
   - Keep: EV_p1086_01 (白河上皇が院政を開始した)

4. **SORTKEY 1274** - EV_p1274_01 and EV_p1274_02 → **MERGE** (same invasion, name variation)
   - Keep: EV_p1274_01 (元寇(文永の役)が起きた)

5. **SORTKEY 1549** - EV_p1549_01 and EV_p1549_02 → **MERGE** (same arrival of Christianity)
   - Keep: EV_p1549_02 (フランシスコ・ザビエルが来日しキリスト教が伝来した)

6. **SORTKEY 1635** - EV_p1635_01 and EV_p1635_02 → **MERGE** (same sankin-kotai institution)
   - Keep: EV_p1635_02 (武家諸法度（寛永令）で参勤交代を制度化)

7. **SORTKEY 1639** - EV_p1639_01 and EV_p1639_02 → **MERGE** (same sakoku policy)
   - Keep: EV_p1639_01 (ポルトガル船来航禁止で鎖国体制が確立した)

8. **SORTKEY 1716** - EV_p1716_01 and EV_p1716_02 → **MERGE** (same Kyoho Reforms)
   - Keep: EV_p1716_02 (徳川吉宗が享保の改革を開始した)

9. **SORTKEY 1787** - EV_p1787_01 and EV_p1787_02 → **MERGE** (same Kansei Reforms)
   - Keep: EV_p1787_02 (松平定信が寛政の改革を開始した)

10. **SORTKEY 1841** - EV_p1841_01 and EV_p1841_02 → **MERGE** (same Tenpo Reforms)
    - Keep: EV_p1841_02 (水野忠邦が天保の改革を開始した)

11. **SORTKEY 1853** - EV_p1853_01 and EV_p1853_02 → **MERGE** (same Perry arrival)
    - Keep: EV_p1853_02 (ペリーが浦賀に来航した)

12. **SORTKEY 1951** - EV_p1951_01 and EV_p1951_02 → **MERGE** (same San Francisco Treaty)
    - Keep: EV_p1951_01 (サンフランシスコ平和条約が調印された)

### MERGERS RECOMMENDED (Near-Duplicates with Agent Focus)

For consistency with the pattern above (system-centric + agent-centric variants):

13. **SORTKEY 1185** - EV_p1185_02 and EV_p1185_03 → **MERGE** (same shugo/jito establishment)
    - Keep: EV_p1185_03 (源頼朝が守護・地頭を設置した)

### KEEP BOTH (Distinct Events Sharing Year)

These represent genuinely different historical events that occurred in the same year and should not be merged:

1. **SORTKEY 939** - Taira no Masakado and Fujiwara no Sumitomo rebellions (distinct, separate, same year)
2. **SORTKEY 593** - Empress enthronement and Regent appointment (sequential, causally related but distinct)
3. **SORTKEY 645** - Isshi Incident and Taika Reform Edict (related but represent different aspects)
4. **SORTKEY 1582** - Honnoji Incident and Yamashiro Battle (consecutive but distinct military events)
5. **SORTKEY 1336** - Multiple 1336 events (complex, cascading)
6. **SORTKEY 1925** - Universal Suffrage and Peace Preservation Laws (representing historical paradox)

### BORDERLINE CASES (REQUIRES NARRATIVE DECISION)

These pairs could go either way depending on framework goals:

1. **SORTKEY 1221** - Rebellion event + outcome specification
2. **SORTKEY 1587** - Two separate policy actions
3. **SORTKEY 1590** - General unification + specific campaign
4. **SORTKEY 1615** - Multiple consolidation policies (4 events)
5. **SORTKEY 1858** - Unrelated but simultaneous events
6. **SORTKEY 1867** - Sequential transformation events
7. **SORTKEY 1945** - Surrender + occupation start
8. **SORTKEY 1952** - Sovereignty recovery + security treaty

---

## OVERALL METRICS

- **Definite mergers:** 13 (removing 13 events, keeping 12)
- **Recommended mergers:** 1 (removing 1 event, keeping 1)
- **Potential reduction:** 14 events
- **Events to retain as distinct:** 37 (representing 9 sortKey groups with legitimate distinct events)

**Net effect of recommended mergers:** From 221 frameworkViews to approximately 207 (removing 14 duplicates).

