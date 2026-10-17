"""Fetch Pokemon Champions battle data from champs.pokedb.tokyo and write SQL for the D1 battle_* tables."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


BASE_URL = "https://champs.pokedb.tokyo"
DEFAULT_RULE = 1
DETAIL_LIMIT = 50
D1_DATABASE = "pokemon-master"
REPO_ROOT = Path(__file__).resolve().parents[4]
CLOUDFLARE_DIR = REPO_ROOT / "cloudflare"
CATEGORIES = ("move", "ability", "item", "nature", "stat_spread")


@dataclass(frozen=True)
class Season:
    """Season option parsed from the Pokemon list page."""

    value: int
    label: str
    period: str
    start_date: dt.date
    end_date: dt.date


@dataclass(frozen=True)
class RankingRow:
    """Ranking row parsed from the Pokemon list page."""

    rank: int
    name: str
    href: str


def fetch_text(url: str) -> str:
    """Fetch a URL as UTF-8 text.

    Args:
        url: URL to fetch.

    Returns:
        Response body.

    Raises:
        RuntimeError: If the request fails.
    """

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "pokemon-consultant-battle-data-updater/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to fetch {url}: {exc}") from exc


def clean_text(value: str) -> str:
    """Strip HTML tags, decode entities, and normalize whitespace."""

    without_tags = re.sub(r"<[^>]*>", "", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def parse_date(value: str) -> dt.date:
    """Parse a YYYY/M/D date."""

    return dt.datetime.strptime(value, "%Y/%m/%d").date()


def parse_seasons(list_html: str) -> list[Season]:
    """Parse season selector options from list page HTML."""

    seasons: list[Season] = []
    option_pattern = re.compile(r'<option value="(\d+)"[^>]*>([\s\S]*?)</option>')
    period_pattern = re.compile(
        r"(\d{4}/\d{1,2}/\d{1,2})\s*-\s*(\d{4}/\d{1,2}/\d{1,2})"
    )
    for match in option_pattern.finditer(list_html):
        value = int(match.group(1))
        text = clean_text(match.group(2))
        period_match = period_pattern.search(text)
        if not period_match:
            continue
        period = period_match.group(0)
        label = text.replace(period, "").strip()
        seasons.append(
            Season(
                value=value,
                label=label,
                period=period,
                start_date=parse_date(period_match.group(1)),
                end_date=parse_date(period_match.group(2)),
            )
        )
    return seasons


def choose_season(seasons: Sequence[Season], today: dt.date) -> Season:
    """Choose the season that contains today, falling back to latest known season."""

    for season in seasons:
        if season.start_date <= today <= season.end_date:
            return season
    past_or_current = [season for season in seasons if season.start_date <= today]
    if past_or_current:
        return max(past_or_current, key=lambda season: season.start_date)
    if seasons:
        return max(seasons, key=lambda season: season.start_date)
    raise RuntimeError("season selector was not found")


def parse_update_time(list_html: str) -> str:
    """Parse update timestamp from list page HTML."""

    match = re.search(
        r'<span class="tag is-light is-info">更新日</span>\s*'
        r'<span class="tag is-light">([^<]+)</span>',
        list_html,
    )
    if not match:
        raise RuntimeError("update timestamp was not found")
    return clean_text(match.group(1))


def parse_ranking(list_html: str, season: int, rule: int) -> list[RankingRow]:
    """Parse Pokemon ranking rows from list page HTML."""

    rows: list[RankingRow] = []
    row_pattern = re.compile(
        rf'<a href="(/pokemon/show/[^?"]+\?season={season}&rule={rule})" '
        r'class="list-pokemon[\s\S]*?'
        r'<div class="pokemon-rank[^>]*">\s*(\d+)\s*</div>[\s\S]*?'
        r'<div class="pokemon-name">([^<]+)</div>'
    )
    for match in row_pattern.finditer(list_html):
        rows.append(
            RankingRow(
                rank=int(match.group(2)),
                name=clean_text(match.group(3)),
                href=html.unescape(match.group(1)),
            )
        )
    rows.sort(key=lambda row: row.rank)
    if not rows:
        raise RuntimeError("ranking rows were not found")
    return rows


def parse_usage_arrays(detail_html: str) -> dict[str, list[dict[str, object]]]:
    """Parse Alpine usagePieChart data arrays."""

    result: dict[str, list[dict[str, object]]] = {}
    pattern = re.compile(
        r'pokemon-trend__column-(abilities|personalities|items)[\s\S]*?'
        r'x-data="window\.usagePieChart\((\[[\s\S]*?\])\)"'
    )
    for match in pattern.finditer(detail_html):
        key = match.group(1)
        json_like = html.unescape(match.group(2))
        result[key] = json.loads(json_like)
    return result


def parse_moves(detail_html: str) -> list[list[str]]:
    """Parse move usage rows from detail page HTML."""

    rows: list[list[str]] = []
    pattern = re.compile(
        r'pokemon-trend__move-item[\s\S]*?'
        r'pokemon-trend__move-name">([\s\S]*?)</span>[\s\S]*?'
        r'pokemon-trend__move-rate[^>]*>\s*([0-9.]+)\s*<small>%</small>'
    )
    for match in pattern.finditer(detail_html):
        rows.append([clean_text(match.group(1)), f"{match.group(2)}%"])
    return rows


def parse_stat_spreads(detail_html: str) -> list[list[str]]:
    """Parse aggregated stat spread rows from detail page HTML."""

    start = detail_html.find("pokemon-trend__column-stats")
    if start < 0:
        return []
    section = detail_html[start : detail_html.find("</section>", start)]
    aggregated_start = section.find("x-show=\"statViewMode === 'aggregated'\"")
    raw_start = section.find("x-show=\"statViewMode === 'raw'\"")
    if aggregated_start >= 0 and raw_start > aggregated_start:
        section = section[aggregated_start:raw_start]

    rows: list[list[str]] = []
    row_pattern = re.compile(
        r'<li class="usage-list-item usage-list-item--stats"[\s\S]*?'
        r'<span class="usage-rank[^>]*">\s*(\d+)\s*</span>[\s\S]*?'
        r'<span class="usage-name usage-name--stats">([\s\S]*?)</span>[\s\S]*?'
        r'<span class="usage-rate[^>]*">\s*([0-9.]+%)\s*</span>'
        r'([\s\S]*?)(?=<li class="usage-list-item usage-list-item--stats"|</ul>)'
    )
    chip_pattern = re.compile(
        r'pokemon-stat-spread__label">\s*([HABCDS+])\s*</span>[\s\S]*?'
        r'pokemon-stat-spread__value[^>]*">\s*([^<\s]+)\s*</span>'
    )
    for match in row_pattern.finditer(section):
        chip_html = match.group(4).split("pokemon-stat-spread__details")[0]
        chips = []
        for chip_match in chip_pattern.finditer(chip_html):
            label = chip_match.group(1)
            value = chip_match.group(2)
            chips.append("+余り" if label == "+" else f"{label}{value}")
        rows.append([match.group(1), ", ".join(chips) or clean_text(match.group(2)), match.group(3)])
    return rows


@dataclass(frozen=True)
class UsageRow:
    """One usage row of a Pokemon detail page."""

    category: str
    rank: int
    name: str
    detail: str | None
    rate: float


# サイト表記とポケモンマスター (pokemon.name_ja) の表記が機械的に揃わないもの。
MASTER_NAME_OVERRIDES = {
    "フラエッテ:永遠": "フラエッテ(えいえん)",
    "ギルガルド": "ギルガルド(シールド)",
    "イルカマン": "イルカマン(マイティ)",
    "ケンタロス:格": "ケンタロス(パルデア単)",
    "ケンタロス:炎": "ケンタロス(パルデア炎)",
    "ケンタロス:水": "ケンタロス(パルデア水)",
    "イキリンコ (グリーン)": "イキリンコ",
    "イキリンコ (イエロー)": "イキリンコ",
    "パンプジン (こだま)": "パンプジン(小)",
    "パンプジン (ちゅうだま)": "パンプジン(普通)",
    "パンプジン (おおだま)": "パンプジン(大)",
    "パンプジン (ギガだま)": "パンプジン(特大)",
}


def to_master_name(name: str) -> str:
    """Convert a site Pokemon name to pokemon.name_ja of the master database."""

    if name in MASTER_NAME_OVERRIDES:
        return MASTER_NAME_OVERRIDES[name]
    name = name.replace(" (オス)", "♂").replace(" (メス)", "♀")
    return re.sub(r" \((.+)\)$", r"(\1)", name)


def parse_rate(value: str) -> float:
    """Parse a usage rate such as '44.4%'."""

    return float(value.strip().rstrip("%"))


def parse_detail(detail_html: str) -> list[UsageRow]:
    """Parse all usage rows from detail page HTML."""

    rows = [
        UsageRow("move", index, name, None, parse_rate(rate))
        for index, (name, rate) in enumerate(parse_moves(detail_html), start=1)
    ]
    usage = parse_usage_arrays(detail_html)
    for key, category in (("abilities", "ability"), ("items", "item"), ("personalities", "nature")):
        for index, item in enumerate(usage.get(key, []), start=1):
            decoration = clean_text(str(item.get("decoration", ""))).strip("() ")
            rows.append(
                UsageRow(
                    category,
                    int(item.get("rank") or index),
                    str(item.get("name", "")),
                    decoration or None,
                    round(float(item.get("rate", 0.0)), 1),
                )
            )
    rows.extend(
        UsageRow("stat_spread", int(rank), spread, None, parse_rate(rate))
        for rank, spread, rate in parse_stat_spreads(detail_html)
    )
    return rows


def sql_literal(value: object) -> str:
    """Render a Python value as a SQLite literal."""

    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def sql_datetime(value: str) -> str:
    """Convert 'YYYY/M/D H:MM' to 'YYYY-MM-DD HH:MM'."""

    return dt.datetime.strptime(value, "%Y/%m/%d %H:%M").strftime("%Y-%m-%d %H:%M")


def build_sql(
    *,
    season: Season,
    rule: int,
    rule_name: str,
    update_time: str,
    source_url: str,
    ranking: Sequence[RankingRow],
    details: dict[str, list[UsageRow]],
) -> str:
    """Build SQL that replaces the battle_* tables with the given snapshot."""

    key = f"{season.value}, {rule}"
    lines = [
        "-- Pokemon Champions 統計データ（update-battle-data スキルが生成。手で編集しない）",
        f"-- 対象: {season.label} / {rule_name}  期間: {season.period}  更新日: {update_time}",
        "-- 過去分は保持しないため、既存データを消してから入れ直す。",
        "DELETE FROM battle_usages;",
        "DELETE FROM battle_rankings;",
        "DELETE FROM battle_seasons;",
        "",
        "INSERT INTO battle_seasons (season, rule, season_label, rule_name, period_start, period_end, updated_at, source_url) VALUES",
        f"({key}, {sql_literal(season.label)}, {sql_literal(rule_name)}, "
        f"{sql_literal(season.start_date.isoformat())}, {sql_literal(season.end_date.isoformat())}, "
        f"{sql_literal(sql_datetime(update_time))}, {sql_literal(source_url)});",
        "",
    ]
    ranking_values = [
        f"({key}, {row.rank}, {sql_literal(row.name)}, "
        f"(SELECT id FROM pokemon WHERE name_ja = {sql_literal(to_master_name(row.name))}), "
        f"{1 if row.name in details else 0}, {sql_literal(BASE_URL + row.href if row.href else None)})"
        for row in ranking
    ]
    for start in range(0, len(ranking_values), 100):
        lines.append("INSERT INTO battle_rankings (season, rule, rank, pokemon_name, pokemon_id, has_detail, source_url) VALUES")
        lines.append(",\n".join(ranking_values[start : start + 100]) + ";")
        lines.append("")
    for row in ranking:
        usages = details.get(row.name)
        if not usages:
            continue
        lines.append(f"-- {row.rank}位 {row.name}")
        lines.append("INSERT INTO battle_usages (season, rule, pokemon_name, category, rank, name, detail, rate) VALUES")
        lines.append(
            ",\n".join(
                f"({key}, {sql_literal(row.name)}, {sql_literal(usage.category)}, {usage.rank}, "
                f"{sql_literal(usage.name)}, {sql_literal(usage.detail)}, {usage.rate!r})"
                for usage in usages
            )
            + ";"
        )
        lines.append("")
    return "\n".join(lines)


def update_battle_data(args: argparse.Namespace) -> None:
    """Fetch the latest battle data and write it as SQL for the battle_* tables."""

    today = args.today or dt.date.today()
    initial_url = f"{BASE_URL}/pokemon/list?rule={args.rule}&q="
    initial_html = fetch_text(initial_url)
    seasons = parse_seasons(initial_html)
    season = next((item for item in seasons if item.value == args.season), None) if args.season else None
    if season is None:
        season = choose_season(seasons, today)

    list_url = f"{BASE_URL}/pokemon/list?season={season.value}&rule={args.rule}&q="
    list_html = fetch_text(list_url)
    update_time = parse_update_time(list_html)
    ranking = parse_ranking(list_html, season.value, args.rule)
    rule_name = "ダブルバトル" if args.rule == 1 else "シングルバトル"

    print(f"season={season.value} {season.label}")
    print(f"period={season.period}")
    print(f"updated_at={update_time}")
    print(f"ranking_count={len(ranking)}")
    print(f"detail_count={DETAIL_LIMIT}")

    if args.dry_run:
        return

    details = {
        pokemon.name: parse_detail(fetch_text(f"{BASE_URL}{pokemon.href}"))
        for pokemon in ranking[:DETAIL_LIMIT]
    }
    for name, usages in details.items():
        counts = {category: sum(1 for usage in usages if usage.category == category) for category in CATEGORIES}
        missing = [category for category, count in counts.items() if count == 0]
        if missing:
            print(f"warning: {name} has no rows for {', '.join(missing)}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        build_sql(
            season=season,
            rule=args.rule,
            rule_name=rule_name,
            update_time=update_time,
            source_url=list_url,
            ranking=ranking,
            details=details,
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.output}")

    if args.apply:
        apply_to_d1(args.output, args.apply)


def apply_to_d1(sql_path: Path, target: str) -> None:
    """Run the generated SQL against the D1 database with wrangler.

    Args:
        sql_path: Generated SQL file.
        target: 'local' or 'remote'.

    Raises:
        RuntimeError: If wrangler fails.
    """

    command = [
        "npx",
        "wrangler",
        "d1",
        "execute",
        D1_DATABASE,
        f"--{target}",
        f"--file={sql_path.resolve()}",
    ]
    print(f"running {' '.join(command)} (cwd={CLOUDFLARE_DIR})")
    if subprocess.run(command, cwd=CLOUDFLARE_DIR, check=False).returncode != 0:
        raise RuntimeError(f"wrangler d1 execute --{target} failed")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, help="Season id. Auto-detected from today's date when omitted.")
    parser.add_argument("--rule", type=int, default=DEFAULT_RULE, help="Battle rule. 1 is double battle.")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data/battle/battle_data.sql",
        help="Output SQL file for the battle_* tables of the D1 database (git-ignored).",
    )
    parser.add_argument(
        "--apply",
        choices=("local", "remote"),
        help="Also run the generated SQL against the local or remote D1 database with wrangler.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print detected metadata without writing files.")
    parser.add_argument(
        "--today",
        type=parse_date,
        help="Override today's date for season detection. Format: YYYY/M/D.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the updater CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        update_battle_data(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
