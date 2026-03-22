# エネルギーだまり修正ルール

解放型ノード（battle/collapse/reform/power/shock）は、蓄積型ノード（drift/conflict）から
amplifies または sustains のエッジ入力を持つべき。これが「エネルギーだまり」の原則。

## 問題パターンと修正方法

### パターンA: 解放型に蓄積入力なし（最多）

**症状**: battle/collapse/reform/power/shock ノードに drift/conflict からの amplifies/sustains がない

**修正方法**:
1. そのイベントの「なぜ起きたか」を問う
2. 背景にある緊張・蓄積・漂流・対立を特定する
3. 既存ノードに該当があればエッジ追加、なければ drift/conflict ノードを新設

**典型例**:
- 戦争(battle) ← 対立の蓄積(conflict) が必要
- 崩壊(collapse) ← 制度の漂流・疲弊(drift) が必要
- 改革(reform) ← 矛盾の蓄積(drift/conflict) が必要
- 権力確立(power) ← 権力闘争や構造変化(conflict/drift) が必要
- 外生衝撃(shock) ← 衝撃を受ける側の脆弱性(drift) が必要

**注意**: shockは外部からの衝撃なので、受ける側の蓄積があるとは限らない。
ただし「なぜその衝撃が大きな影響を与えたか」には受容側の背景が必要。

### パターンB: triggers のみの入力（2番目に多い）

**症状**: 入力エッジがtriggersだけ。発火条件は示されるが背景圧力が不明。

**修正方法**:
1. triggersの入力元はそのまま残す（発火条件は正しい）
2. 別途 amplifies/sustains のエッジを追加する
3. 既存の先行ノードからエッジを引けないか検討 → 無理なら新規ノード

### パターンC: 蓄積型(drift/conflict)がtriggersのみ

**症状**: drift/conflict ノード自体が triggers 1本のみの入力。蓄積の原因が不明。

**修正方法**:
1. drift/conflict の蓄積を駆動する先行ノードを特定
2. 通常は先行する institution（制度）が sustains/amplifies で蓄積を駆動
3. または先行する別の drift が amplifies で連鎖

### パターンD: institution がtriggersのみ

**症状**: 制度化ノードに triggers 1本のみ。何が制度化を支えたかが不明。

**修正方法**:
1. 制度化の前提となる条件（軍事的勝利、合意形成、外圧など）を特定
2. 先行ノードから sustains/amplifies を追加

## 修正時の判断基準

### エッジ追加 vs ノード新設の判断
- **エッジ追加**: 既存ノードに蓄積的性質があるが接続が漏れている場合
- **ノード新設**: 蓄積過程が因果チェーン上に表現されていない場合
  - 新設ノードは drift または conflict とする
  - IDは `{prefix}{番号}b`, `{prefix}{番号}c` のように枝番

### amplifies vs sustains の使い分け
- **amplifies**: 源ノードが先ノードのエネルギーを増大させる（因果的に強める）
- **sustains**: 源ノードが先ノードの状態を維持・下支えする（条件を持続させる）
- 迷ったら amplifies（より一般的）

### roleの割り当て
- drift/conflict → 解放型: amplifies が基本
- institution → drift: sustains が基本（制度が漂流を駆動し続ける）
- shock → conflict: triggers が基本（衝撃が対立を発火させる）

## 品質チェックリスト

修正後に確認すべき項目:
1. 全解放型ノードに drift/conflict からの amplifies/sustains があるか
2. 全 drift/conflict ノードに triggers 以外の入力があるか
3. 新設ノードの bgType/releaseType/patternType が設定されているか
4. エッジの note が具体的な因果説明を含むか
5. 孤立ノード（入力0本）がないか
