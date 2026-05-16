"""Update Pokemon Champions battle-data references from champs.pokedb.tokyo."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


BASE_URL = "https://champs.pokedb.tokyo"
DEFAULT_RULE = 1
DETAIL_LIMIT = 50


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


def markdown_table(rows: Sequence[Sequence[str]], headers: Sequence[str]) -> str:
    """Build a Markdown table."""

    aligns = ["---:" if index == 0 and headers[0] == "順位" else "---" for index in range(len(headers))]
    if headers[-1] == "使用率":
        aligns[-1] = "---:"
    lines = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join(aligns)} |",
    ]
    lines.extend(f"| {' | '.join(row)} |" for row in rows)
    return "\n".join(lines)


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
        # The embedded payload is JSON, but use the standard library parser lazily.
        import json

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


def usage_rows(items: Sequence[dict[str, object]], name_key: str) -> list[list[str]]:
    """Convert usagePieChart items to Markdown table rows."""

    rows: list[list[str]] = []
    for item in items:
        name = str(item.get(name_key, ""))
        decoration = clean_text(str(item.get("decoration", "")))
        display_name = f"{name} {decoration}".strip()
        rate = float(item.get("rate", 0.0))
        rows.append([str(item.get("rank", "")), display_name, f"{rate:.1f}%"])
    return rows


def build_ranking_markdown(
    *,
    season: Season,
    rule_name: str,
    update_time: str,
    source_url: str,
    ranking: Sequence[RankingRow],
) -> str:
    """Build ranking.md content."""

    rows = [[str(row.rank), row.name] for row in ranking]
    return (
        "# Pokemon Champions 流行ランキング\n\n"
        f"対象: {season.label} / {rule_name}\n"
        f"期間: {season.period}\n"
        f"更新日: {update_time}\n"
        f"ソース: {source_url}\n"
        f"ランキング件数: {len(ranking)}件\n"
        f"詳細データ対象: 上位{DETAIL_LIMIT}匹\n\n"
        f"{markdown_table(rows, ['順位', 'ポケモン'])}\n"
    )


def build_detail_markdown(
    *,
    pokemon: RankingRow,
    season: Season,
    rule_name: str,
    update_time: str,
    detail_html: str,
) -> str:
    """Build a Pokemon detail Markdown file."""

    usage = parse_usage_arrays(detail_html)
    source_url = f"{BASE_URL}{pokemon.href}"
    return (
        f"# {pokemon.name}\n\n"
        f"対象: {season.label} / {rule_name}\n"
        f"順位: {pokemon.rank}位\n"
        f"更新日: {update_time}\n"
        f"ソース: {source_url}\n\n"
        "## 技\n\n"
        f"{markdown_table(parse_moves(detail_html), ['技', '使用率'])}\n\n"
        "## 特性\n\n"
        f"{markdown_table(usage_rows(usage.get('abilities', []), 'name'), ['順位', '特性', '使用率'])}\n\n"
        "## 持ち物\n\n"
        f"{markdown_table(usage_rows(usage.get('items', []), 'name'), ['順位', '持ち物', '使用率'])}\n\n"
        "## 性格\n\n"
        f"{markdown_table(usage_rows(usage.get('personalities', []), 'name'), ['順位', '性格', '使用率'])}\n\n"
        "## 能力ポイント\n\n"
        f"{markdown_table(parse_stat_spreads(detail_html), ['順位', '配分', '使用率'])}\n\n"
        "## メモ\n\n"
        "- このファイルはランキング詳細ページから取得した表示データを記録する。\n"
    )


def safe_filename(name: str) -> str:
    """Return a filesystem-safe Markdown filename."""

    return name.replace("/", ":") + ".md"


def update_battle_data(args: argparse.Namespace) -> None:
    """Update battle-data reference files."""

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

    output_root = args.output
    pokemon_dir = output_root / "pokemon"

    print(f"season={season.value} {season.label}")
    print(f"period={season.period}")
    print(f"updated_at={update_time}")
    print(f"ranking_count={len(ranking)}")
    print(f"detail_count={DETAIL_LIMIT}")

    if args.dry_run:
        return

    output_root.mkdir(parents=True, exist_ok=True)
    pokemon_dir.mkdir(parents=True, exist_ok=True)
    (output_root / "ranking.md").write_text(
        build_ranking_markdown(
            season=season,
            rule_name=rule_name,
            update_time=update_time,
            source_url=list_url,
            ranking=ranking,
        ),
        encoding="utf-8",
    )

    for old_file in pokemon_dir.glob("*.md"):
        old_file.unlink()

    for pokemon in ranking[:DETAIL_LIMIT]:
        detail_html = fetch_text(f"{BASE_URL}{pokemon.href}")
        (pokemon_dir / safe_filename(pokemon.name)).write_text(
            build_detail_markdown(
                pokemon=pokemon,
                season=season,
                rule_name=rule_name,
                update_time=update_time,
                detail_html=detail_html,
            ),
            encoding="utf-8",
        )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, help="Season id. Auto-detected from today's date when omitted.")
    parser.add_argument("--rule", type=int, default=DEFAULT_RULE, help="Battle rule. 1 is double battle.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".claude/skills/battle-data/references"),
        help="Output references directory.",
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
