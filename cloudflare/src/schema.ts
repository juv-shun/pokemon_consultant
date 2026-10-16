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
};

export const QUERY_TIPS = `- SQLite（Cloudflare D1）です。スキーマ名は無いので \`champions.pokemon\` ではなく \`pokemon\` と書きます。
- 真偽値は 0 / 1 の整数です（例: \`is_mega = 1\`）。
- タイプは type_primary と type_secondary の 2 列にあるので、タイプ検索は両方を見ます（例: \`'ほのお' IN (type_primary, type_secondary)\`）。
- タイプ名: ノーマル, ほのお, みず, でんき, くさ, こおり, かくとう, どく, じめん, ひこう, エスパー, むし, いわ, ゴースト, ドラゴン, あく, はがね, フェアリー
- 特性・技は pokemon_abilities / pokemon_moves を JOIN します。
- 地面技を無効にできるのはひこうタイプと特性「ふゆう」持ちの両方です。

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
\`\`\``;
