// describe_schema ツールが返すテーブル説明。
// カラム一覧は D1 から実際に取得し、ここにある説明を付け加える。

export const TABLE_DESCRIPTIONS: Record<string, { description: string; columns: Record<string, string> }> = {
  pokemon: {
    description: "ポケモン基本情報。フォーム違い・メガシンカは別レコード。",
    columns: {
      id: "内部ID",
      pokedex_no: "全国図鑑番号（フォーム違いは同一番号）",
      name_ja: "ポケモン名（フォーム名込み、一意）。例: 'メガリザードンX', 'ウインディ(ヒスイ)'",
      name_en: "英語名",
      form_label: "フォーム名だけ（例: '(ヒスイ)'）",
      form_code: "フォーム識別コード（例: m, x, y, a, h）",
      type_primary: "タイプ1",
      type_secondary: "タイプ2（単タイプは NULL）",
      height_dm: "高さ（デシメートル）",
      weight_hg: "重さ（ヘクトグラム）",
      low_kick_power: "けたぐり・くさむすびの威力",
      is_legendary: "伝説なら 1",
      is_mythical: "幻なら 1",
      is_mega: "メガシンカ後の姿なら 1",
      base_hp: "種族値 HP (H)",
      base_atk: "種族値 攻撃 (A)",
      base_def: "種族値 防御 (B)",
      base_spa: "種族値 特攻 (C)",
      base_spd: "種族値 特防 (D)",
      base_spe: "種族値 素早さ (S)",
      remarks: "備考",
    },
  },
  abilities: {
    description: "特性マスタ。",
    columns: {
      id: "内部ID",
      name_ja: "特性名（一意）",
      effect_text: "効果説明",
    },
  },
  pokemon_abilities: {
    description: "ポケモンと特性の関連。",
    columns: {
      pokemon_id: "pokemon.id",
      ability_id: "abilities.id",
      is_hidden: "夢特性なら 1",
    },
  },
  moves: {
    description: "技マスタ。",
    columns: {
      id: "内部ID",
      name_ja: "技名（一意）",
      type_name: "技タイプ",
      damage_class: "'physical' / 'special' / 'status'（NULL あり）",
      damage_class_ja: "'物理' / '特殊' / '変化' / '-'",
      power: "威力（変化技などは NULL）",
      accuracy: "命中率（必中は NULL）",
      pp: "PP",
      priority: "優先度（通常 0）",
      contact: "接触技なら 1",
      target: "'single'（相手1体） / 'all_opponents'（相手全体） / 'all_except_self'（自分以外全員） / 'self'（自分）",
      is_spread: "ダブルの全体技補正（×0.75）対象なら 1",
      effect_text: "効果説明",
    },
  },
  pokemon_moves: {
    description: "ポケモンが覚える技の関連（習得手段は区別しない）。",
    columns: {
      pokemon_id: "pokemon.id",
      move_id: "moves.id",
    },
  },
  battle_seasons: {
    description: "Pokemon Champions 統計情報の対象シーズン・ルール。最新の1件だけを保持する。",
    columns: {
      season: "サイト上のシーズン番号",
      rule: "サイト上のルール番号（1 = ダブルバトル）",
      season_label: "シーズン名（例: 'シーズンM-6 (M-C)'）",
      rule_name: "ルール名（例: 'ダブルバトル'）",
      period_start: "期間の開始日 'YYYY-MM-DD'",
      period_end: "期間の終了日 'YYYY-MM-DD'",
      updated_at: "統計の更新日時 'YYYY-MM-DD HH:MM'",
      source_url: "ランキングページの URL",
    },
  },
  battle_rankings: {
    description: "Pokemon Champions の使用率ランキング（全件）。",
    columns: {
      season: "battle_seasons.season",
      rule: "battle_seasons.rule",
      rank: "使用率順位（1 始まり）",
      pokemon_name: "サイト表記のポケモン名（例: 'イエッサン (メス)', 'ウインディ (ヒスイ)'）。pokemon.name_ja とは表記が違うことがある",
      pokemon_id: "pokemon.id。マスターと JOIN するときはこちらを使う",
      has_detail: "battle_usages に詳細（上位50匹）があれば 1",
      source_url: "詳細ページの URL（詳細なしは NULL）",
    },
  },
  battle_usages: {
    description: "ランキング上位ポケモンの採用率（技・特性・持ち物・性格・能力ポイント）。",
    columns: {
      season: "battle_seasons.season",
      rule: "battle_seasons.rule",
      pokemon_name: "battle_rankings.pokemon_name",
      category: "'move'（技） / 'ability'（特性） / 'item'（持ち物） / 'nature'（性格） / 'stat_spread'（能力ポイント配分）",
      rank: "カテゴリ内の順位（1 始まり）",
      name: "技名・特性名・持ち物名・性格名、または能力ポイント配分（例: 'A32, S32, +余り'）",
      detail: "補足。性格なら上昇下降（例: 'C↑A↓'）",
      rate: "使用率（%、例: 44.4）",
    },
  },
};

export const QUERY_TIPS = `- SQLite（Cloudflare D1）です。スキーマ名は無いので \`champions.pokemon\` ではなく \`pokemon\` と書きます。
- 真偽値は 0 / 1 の整数です（例: \`is_mega = 1\`）。
- タイプは type_primary と type_secondary の 2 列にあるので、タイプ検索は両方を見ます（例: \`'ほのお' IN (type_primary, type_secondary)\`）。
- タイプ名: ノーマル, ほのお, みず, でんき, くさ, こおり, かくとう, どく, じめん, ひこう, エスパー, むし, いわ, ゴースト, ドラゴン, あく, はがね, フェアリー
- 特性・技は pokemon_abilities / pokemon_moves を JOIN します。
- 地面技を無効にできるのはひこうタイプと特性「ふゆう」持ちの両方です。
- 対戦環境（流行・使用率）は battle_* テーブルです。battle_rankings.pokemon_id で pokemon と JOIN します。採用率の詳細は has_detail = 1 のポケモンだけにあります。
- battle_* は最新シーズン・ルールの1件分だけを保持します。回答では battle_seasons のシーズン名・ルール・更新日時を添えます。
- battle_rankings / battle_usages の pokemon_name はサイト表記です。マスターの名前から探すときは pokemon_id で JOIN します。
- has_detail = 0 のポケモンは採用傾向を断定せず、順位だけを根拠にします。使用率が無い項目を推測で補いません。
- stat_spread（能力ポイント配分）はサイトが合算した代表行だけで、内訳はありません。

例: 素早さ種族値100以上で特性「いかく」を持つポケモン
\`\`\`sql
SELECT p.name_ja, p.base_spe
FROM pokemon p
JOIN pokemon_abilities pa ON pa.pokemon_id = p.id
JOIN abilities a ON a.id = pa.ability_id
WHERE p.base_spe >= 100 AND a.name_ja = 'いかく'
ORDER BY p.base_spe DESC;
\`\`\`

例: 「ねこだまし」と「とんぼがえり」を両方覚えるポケモン
\`\`\`sql
SELECT p.name_ja
FROM pokemon p
JOIN pokemon_moves pm ON pm.pokemon_id = p.id
JOIN moves m ON m.id = pm.move_id
WHERE m.name_ja IN ('ねこだまし', 'とんぼがえり')
GROUP BY p.id
HAVING COUNT(DISTINCT m.id) = 2;
\`\`\`

例: 使用率上位20匹のうち、持ち物1位が「きあいのタスキ」のポケモン
\`\`\`sql
SELECT r.rank, r.pokemon_name, u.rate
FROM battle_rankings r
JOIN battle_usages u ON u.season = r.season AND u.rule = r.rule AND u.pokemon_name = r.pokemon_name
WHERE r.rank <= 20 AND u.category = 'item' AND u.rank = 1 AND u.name = 'きあいのタスキ'
ORDER BY r.rank;
\`\`\``;
