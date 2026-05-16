"""ポケモンのダメージを計算するスクリプト。

ポケモンチャンピオンズの前提条件:
- レベル: 50固定
- レベル補正値: 22 (= floor(50×2÷5+2))

攻撃・防御の実数値は事前に calc_stats.py で算出したものを入力する。

Usage:
    python scripts/calc_damage.py --power 80 --attack 182 --defense 128
    python scripts/calc_damage.py --power 80 --attack 182 --defense 128 --stab
    python scripts/calc_damage.py --power 80 --attack 182 --defense 128 --stab --effectiveness 2.0
    python scripts/calc_damage.py --power 80 --attack 182 --defense 128 --spread --weather sun --weather-boosted
"""

import argparse
import math

LEVEL_FACTOR = 22  # floor(50 * 2 / 5 + 2)

# 乱数: 0.85〜1.00の16段階
RANDOM_FACTORS = [i / 100 for i in range(85, 101)]


def calc_base_damage(power: int, attack: int, defense: int) -> int:
    """基本ダメージを計算する（レベル50固定）。

    Args:
        power: 技の威力
        attack: 攻撃側の実数値（こうげき or とくこう）
        defense: 防御側の実数値（ぼうぎょ or とくぼう）

    Returns:
        基本ダメージ値
    """
    return math.floor(math.floor(LEVEL_FACTOR * power * attack / defense) / 50) + 2


def calc_final_damage(
    base_damage: int, modifiers: list[float]
) -> tuple[int, int]:
    """乱数込みの最終ダメージを計算する。

    Args:
        base_damage: 基本ダメージ
        modifiers: 各種補正倍率のリスト

    Returns:
        (最小ダメージ, 最大ダメージ) のタプル
    """
    modified = base_damage
    for mod in modifiers:
        modified = math.floor(modified * mod)

    damages = [max(1, math.floor(modified * r)) for r in RANDOM_FACTORS]
    return min(damages), max(damages)


def get_weather_modifier(
    weather: str, boosted: bool, weakened: bool
) -> float:
    """天候補正を返す。

    Args:
        weather: 天候 (sun/rain/none)
        boosted: 天候で強化される技タイプか
        weakened: 天候で弱化される技タイプか

    Returns:
        天候補正倍率
    """
    if weather == "none":
        return 1.0
    if boosted:
        return 1.5
    if weakened:
        return 0.5
    return 1.0


def get_wall_modifier(wall: str) -> float:
    """壁補正を返す。

    Args:
        wall: 壁の種類 (single/double/none)

    Returns:
        壁補正倍率
    """
    if wall == "single":
        return 0.5
    if wall == "double":
        return 2 / 3
    return 1.0


def main() -> None:
    parser = argparse.ArgumentParser(description="ポケモンのダメージを計算する")
    parser.add_argument("--power", type=int, required=True, help="技の威力")
    parser.add_argument(
        "--attack", type=int, required=True, help="攻撃側の実数値（こうげき or とくこう）"
    )
    parser.add_argument(
        "--defense", type=int, required=True, help="防御側の実数値（ぼうぎょ or とくぼう）"
    )
    parser.add_argument("--stab", action="store_true", help="タイプ一致 (×1.5)")
    parser.add_argument(
        "--effectiveness", type=float, default=1.0, help="タイプ相性倍率 (デフォルト: 1.0)"
    )
    parser.add_argument("--critical", action="store_true", help="急所 (×1.5)")
    parser.add_argument("--burn", action="store_true", help="やけど状態 (×0.5)")
    parser.add_argument(
        "--weather",
        choices=["sun", "rain", "none"],
        default="none",
        help="天候 (デフォルト: none)",
    )
    parser.add_argument(
        "--weather-boosted", action="store_true", help="天候で強化される技タイプか"
    )
    parser.add_argument(
        "--weather-weakened", action="store_true", help="天候で弱化される技タイプか"
    )
    parser.add_argument(
        "--wall",
        choices=["single", "double", "none"],
        default="none",
        help="壁 (single=シングル0.5倍, double=ダブル2/3倍)",
    )
    parser.add_argument(
        "--spread", action="store_true", help="ダブルバトル全体技 (×0.75)"
    )
    parser.add_argument(
        "--item",
        choices=["type-boost"],
        default=None,
        help="持ち物 (type-boost=タイプ強化アイテム×1.2)",
    )
    parser.add_argument(
        "--other", type=float, default=1.0, help="その他の補正倍率 (デフォルト: 1.0)"
    )
    args = parser.parse_args()

    base_damage = calc_base_damage(args.power, args.attack, args.defense)

    # 補正を収集
    modifiers: list[float] = []
    modifier_labels: list[str] = []

    if args.spread:
        modifiers.append(0.75)
        modifier_labels.append("全体技×0.75")

    weather_mod = get_weather_modifier(
        args.weather, args.weather_boosted, args.weather_weakened
    )
    if weather_mod != 1.0:
        modifiers.append(weather_mod)
        label = "晴れ" if args.weather == "sun" else "雨"
        modifier_labels.append(f"天候({label})×{weather_mod}")

    if args.critical:
        modifiers.append(1.5)
        modifier_labels.append("急所×1.5")

    if args.stab:
        modifiers.append(1.5)
        modifier_labels.append("タイプ一致×1.5")

    if args.effectiveness != 1.0:
        modifiers.append(args.effectiveness)
        modifier_labels.append(f"相性×{args.effectiveness}")

    if args.burn:
        modifiers.append(0.5)
        modifier_labels.append("やけど×0.5")

    wall_mod = get_wall_modifier(args.wall)
    if wall_mod != 1.0:
        modifiers.append(wall_mod)
        wall_label = "シングル" if args.wall == "single" else "ダブル"
        modifier_labels.append(f"壁({wall_label})×{wall_mod:.4g}")

    if args.item == "type-boost":
        modifiers.append(1.2)
        modifier_labels.append("タイプ強化アイテム×1.2")

    if args.other != 1.0:
        modifiers.append(args.other)
        modifier_labels.append(f"その他×{args.other}")

    min_dmg, max_dmg = calc_final_damage(base_damage, modifiers)

    print(f"ダメージ: {min_dmg} 〜 {max_dmg}")
    if modifier_labels:
        print(f"(適用補正: {', '.join(modifier_labels)})")


if __name__ == "__main__":
    main()
