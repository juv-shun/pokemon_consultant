"""ポケモンのステータス(実数値)を計算するスクリプト。

ポケモンチャンピオンズの計算式:
- HP: 種族値 + 努力値 + 75
- その他: floor(性格補正 × (種族値 + 努力値 + 20))

Usage:
    python scripts/calc_stats.py --base 90 --ev 32
    python scripts/calc_stats.py --base 90 --ev 32 --nature up
    python scripts/calc_stats.py --base 90 --ev 32 --nature down
    python scripts/calc_stats.py --base 90 --ev 32 --hp
"""

import argparse
import math


def calc_hp(base: int, ev: int) -> int:
    """HPの実数値を計算する。"""
    return base + ev + 75


def calc_stat(base: int, ev: int, nature: float = 1.0) -> int:
    """HP以外のステータスの実数値を計算する。"""
    return math.floor(nature * (base + ev + 20))


NATURE_MODIFIER = {
    "up": 1.1,
    "down": 0.9,
    "neutral": 1.0,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="ポケモンのステータス(実数値)を計算する")
    parser.add_argument("--base", type=int, required=True, help="種族値")
    parser.add_argument("--ev", type=int, default=0, help="努力値 (デフォルト: 0)")
    parser.add_argument(
        "--nature",
        choices=["up", "down", "neutral"],
        default="neutral",
        help="性格補正 (up=1.1倍, down=0.9倍, neutral=補正なし)",
    )
    parser.add_argument("--hp", action="store_true", help="HPとして計算する")
    args = parser.parse_args()

    if args.ev < 0 or args.ev > 32:
        parser.error("--ev は 0〜32 の範囲で指定してください")

    if args.hp:
        result = calc_hp(args.base, args.ev)
        print(f"HP: {result}")
    else:
        nature = NATURE_MODIFIER[args.nature]
        result = calc_stat(args.base, args.ev, nature)
        nature_label = {"up": "↑1.1倍", "down": "↓0.9倍", "neutral": "補正なし"}
        print(f"実数値: {result} (性格補正: {nature_label[args.nature]})")


if __name__ == "__main__":
    main()
