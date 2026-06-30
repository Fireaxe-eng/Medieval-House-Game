"""New-game setup: premade house pick or custom point-buy build, plus
initialization of the AI rival houses and the Crown."""

import random

import display
import names
from models import Character, GameState, House, next_character_id

START_YEAR = 1200
STAT_NAMES = ["Diplomacy", "Martial", "Stewardship", "Intrigue"]
CUSTOM_POINT_BUDGET = 40
CUSTOM_MIN_STAT = 4
CUSTOM_MAX_STAT = 20

PLAYER_START_TREASURY = 200
PLAYER_START_PRESTIGE = 25
PLAYER_START_INCOME = 10

AI_TREASURY_RANGE = (120, 260)
AI_PRESTIGE_RANGE = (15, 35)
AI_INCOME_RANGE = (8, 14)

CROWN_START_TREASURY = 500
CROWN_START_PRESTIGE = 175
CROWN_START_INCOME = 25


def allocate_points(total: int, minimum: int, stat_names: list[str]) -> dict[str, int]:
    remaining = total
    values: dict[str, int] = {}
    for i, stat in enumerate(stat_names):
        remaining_after = len(stat_names) - i - 1
        max_for_this = min(CUSTOM_MAX_STAT, remaining - minimum * remaining_after)
        default_val = max(minimum, min(max_for_this, remaining // (remaining_after + 1)))
        while True:
            raw = display.safe_input(
                f"{stat} (min {minimum}, max {max_for_this}, {remaining} points left for {len(stat_names) - i} stats) "
                f"[default {default_val}]: "
            )
            if not raw:
                val = default_val
            else:
                try:
                    val = int(raw)
                except ValueError:
                    print("Enter a whole number.")
                    continue
            if val < minimum or val > max_for_this:
                print(f"Must be between {minimum} and {max_for_this}.")
                continue
            break
        values[stat] = val
        remaining -= val
    return values


def build_custom_house() -> dict:
    print("\n--- Building Your House ---")
    name = display.safe_input("Name your house (e.g. 'Marrow'): ") or "Newhold"
    if name.lower().startswith("house "):
        name = name[6:].strip()
    region = display.safe_input("Home region (flavor only): ") or "the Heartlands"
    words = display.safe_input("House words/motto: ") or "Our Time Will Come"
    print(f"\nDistribute {CUSTOM_POINT_BUDGET} points across your ruler's four stats (minimum {CUSTOM_MIN_STAT} each).")
    stats = allocate_points(CUSTOM_POINT_BUDGET, CUSTOM_MIN_STAT, STAT_NAMES)
    ruler_name = display.safe_input("Name your ruler: ") or f"Aldous of {name}"
    sex = (display.safe_input("Ruler's sex (M/F): ") or "M").upper()
    if sex not in ("M", "F"):
        sex = "M"
    return {
        "id": "player_house",
        "name": name,
        "region": region,
        "words": words,
        "ruler_name": ruler_name,
        "ruler_sex": sex,
        "ruler_age": random.randint(28, 45),
        "stats": stats,
    }


def choose_player_house_data() -> dict:
    print("\n=== Founding a New House ===")
    options = [
        f"House {h['name']} ({h['region']}) -- \"{h['words']}\" [{h['lean']} lean]"
        for h in names.PREMADE_HOUSES
    ]
    options.append("Build a custom house")
    idx = display.choose_from_list("Choose your house:", options)
    if idx is None or idx == len(names.PREMADE_HOUSES):
        return build_custom_house()
    return names.PREMADE_HOUSES[idx]


def _ruler_stats(data: dict) -> tuple[int, int, int, int]:
    if "stats" in data:
        s = data["stats"]
        return s["Diplomacy"], s["Martial"], s["Stewardship"], s["Intrigue"]
    if "lean" in data:
        base = {"diplomacy": 9, "martial": 9, "stewardship": 9, "intrigue": 9}
        base[data["lean"]] = 17
        return base["diplomacy"], base["martial"], base["stewardship"], base["intrigue"]
    return 14, 14, 14, 14


def make_house(data: dict, is_player: bool = False, is_crown: bool = False) -> House:
    dipl, mart, stew, intr = _ruler_stats(data)
    ruler_id = next_character_id()
    ruler = Character(
        id=ruler_id, name=data["ruler_name"], sex=data["ruler_sex"],
        birth_year=START_YEAR - data["ruler_age"], house_id=data["id"],
        diplomacy=dipl, martial=mart, stewardship=stew, intrigue=intr,
    )
    house = House(
        id=data["id"], name=data["name"], region=data["region"], words=data["words"],
        is_player=is_player, is_crown=is_crown, ruler_id=ruler_id,
    )
    house.members[ruler_id] = ruler
    return house


def new_game(seed: int | None = None) -> GameState:
    if seed is not None:
        random.seed(seed)

    player_data = choose_player_house_data()

    player_house = make_house(player_data, is_player=True)
    player_house.treasury = PLAYER_START_TREASURY
    player_house.prestige = PLAYER_START_PRESTIGE
    player_house.income = PLAYER_START_INCOME

    state = GameState(
        year=START_YEAR, season=0, houses={},
        player_house_id=player_house.id, crown_house_id=names.CROWN_HOUSE["id"],
        rng_seed=seed,
    )
    state.houses[player_house.id] = player_house

    for data in names.AI_HOUSES:
        house = make_house(data, is_player=False)
        house.treasury = random.randint(*AI_TREASURY_RANGE)
        house.prestige = random.randint(*AI_PRESTIGE_RANGE)
        house.income = random.randint(*AI_INCOME_RANGE)
        state.houses[house.id] = house

        rel = data["start_relation"]
        player_house.relations[house.id] = rel
        house.relations[player_house.id] = rel

    crown = make_house(names.CROWN_HOUSE, is_crown=True)
    crown.treasury = CROWN_START_TREASURY
    crown.prestige = CROWN_START_PRESTIGE
    crown.income = CROWN_START_INCOME
    state.houses[crown.id] = crown

    crown_rel = names.CROWN_HOUSE["start_relation"]
    player_house.relations[crown.id] = crown_rel
    crown.relations[player_house.id] = crown_rel

    print(
        f"\nHouse {player_house.name} rises in {player_house.region}, under "
        f"{player_house.ruler().name}. The Crown sits in {crown.region}, "
        f"watching every house that might one day challenge it.\n"
    )
    return state
