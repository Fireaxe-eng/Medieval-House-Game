"""Entry point and turn loop. Run with `python game.py` (optionally
`--seed N` for a reproducible run)."""

import argparse
import random

import ai
import crown
import display
import events
import narrative
import names
import setup
from models import Character, GameState, clamp, find_heir, next_character_id

RUIN_THRESHOLD = -200
RUIN_SEASONS = 4
BIRTH_CHANCE = 0.25
FERTILE_AGE_RANGE = (18, 45)
PLAGUE_DEATH_BUMP = 0.05


def death_chance(age: int) -> float:
    if age < 50:
        return 0.0
    if age < 65:
        return 0.02
    if age < 80:
        return 0.05
    return 0.12


def advance_season(state: GameState) -> None:
    state.season += 1
    if state.season >= 4:
        state.season = 0
        state.year += 1


def _spawn_child(state: GameState, house, parent_a: Character, parent_b: Character) -> Character:
    sex = names.random_sex()
    child_name = f"{names.random_given_name(sex)} {house.name}"

    def avg_stat(a: int, b: int) -> int:
        return clamp(round((a + b) / 2) + random.randint(-3, 3), 1, 20)

    child = Character(
        id=next_character_id(), name=child_name, sex=sex,
        birth_year=state.year, house_id=house.id,
        diplomacy=avg_stat(parent_a.diplomacy, parent_b.diplomacy),
        martial=avg_stat(parent_a.martial, parent_b.martial),
        stewardship=avg_stat(parent_a.stewardship, parent_b.stewardship),
        intrigue=avg_stat(parent_a.intrigue, parent_b.intrigue),
    )
    house.members[child.id] = child
    parent_a.children_ids.append(child.id)
    parent_b.children_ids.append(child.id)
    return child


def do_aging_deaths_and_births(state: GameState) -> list[str]:
    """Runs once per in-game year, at the Winter -> Spring boundary."""
    lines: list[str] = []
    plague_bump = PLAGUE_DEATH_BUMP if state.plague_rumor_active else 0.0
    state.plague_rumor_active = False

    for house in state.houses.values():
        if house.extinct:
            continue
        for char in house.living_members():
            chance = death_chance(char.age(state.year)) + plague_bump
            if chance > 0 and random.random() < chance:
                char.alive = False
                char.death_year = state.year
                if char.id == house.ruler_id or house.is_player:
                    lines.append(narrative.render("death_old_age", name=char.name, house=house.name))

    processed_couples: set[frozenset] = set()
    for house in state.houses.values():
        if house.extinct:
            continue
        ruler = house.ruler()
        if not ruler.alive or not ruler.spouse_id:
            continue
        spouse = state.find_character(ruler.spouse_id)
        if spouse is None or not spouse.alive:
            continue
        couple_key = frozenset({ruler.id, spouse.id})
        if couple_key in processed_couples:
            continue
        processed_couples.add(couple_key)

        ruler_age = ruler.age(state.year)
        spouse_age = spouse.age(state.year)
        fertile = (
            FERTILE_AGE_RANGE[0] <= ruler_age <= FERTILE_AGE_RANGE[1]
            or FERTILE_AGE_RANGE[0] <= spouse_age <= FERTILE_AGE_RANGE[1]
        )
        if fertile and random.random() < BIRTH_CHANCE:
            child = _spawn_child(state, house, ruler, spouse)
            if house.is_player:
                lines.append(
                    narrative.render("birth_player", house=house.name, name=child.name, parent=ruler.name)
                )

    return lines


def check_succession(state: GameState) -> None:
    for house in list(state.houses.values()):
        if house.extinct:
            continue
        ruler = house.ruler()
        if ruler.alive:
            continue
        heir = find_heir(state, house)
        if heir is None:
            if house.id == state.player_house_id:
                state.game_over = True
                state.end_reason = "extinction"
                state.turn_log.append(narrative.render("extinction", house=house.name))
            else:
                house.extinct = True
                state.turn_log.append(f"With no heir to be found, House {house.name}'s line has ended.")
            continue
        old_name = ruler.name
        if heir.id not in house.members:
            house.members[heir.id] = heir  # spouse inheriting from outside the house's own record
        house.ruler_id = heir.id
        if house.id == state.player_house_id:
            state.turn_log.append(
                narrative.render("succession", old_ruler=old_name, new_ruler=heir.name, house=house.name)
            )


def check_ruin(state: GameState) -> None:
    player = state.player_house()
    if player.treasury <= RUIN_THRESHOLD:
        state.ruin_counter += 1
    else:
        state.ruin_counter = 0
    if state.ruin_counter >= RUIN_SEASONS:
        state.game_over = True
        state.end_reason = "ruin"
        state.turn_log.append(narrative.render("ruin", house=player.name))


def run_season(state: GameState) -> None:
    state.turn_log = []

    proposal_line = display.prompt_pending_proposal(state)
    if proposal_line:
        state.turn_log.append(proposal_line)

    display.show_status(state)

    actions_left = 2
    while actions_left > 0 and not state.game_over:
        line = display.show_menu_and_resolve(state, actions_left)
        if line is None:
            break
        state.turn_log.append(line)
        actions_left -= 1

    ai_pool = state.ai_houses()
    if ai_pool:
        narrate_count = min(random.randint(1, 2), len(ai_pool))
        narrated_ids = {h.id for h in random.sample(ai_pool, narrate_count)}
        for house in ai_pool:
            line = ai.take_ai_turn(state, house)
            if house.id in narrated_ids:
                state.turn_log.append(line)

    crown_line = crown.maybe_act(state)
    if crown_line:
        state.turn_log.append(crown_line)

    event_line = events.maybe_fire_event(state)
    if event_line:
        state.turn_log.append(event_line)

    for house in state.houses.values():
        if not house.extinct:
            house.treasury += house.income

    advance_season(state)
    if state.season == 0:
        state.turn_log.extend(do_aging_deaths_and_births(state))

    check_succession(state)
    check_ruin(state)

    display.print_log(state.turn_log)


def main() -> None:
    parser = argparse.ArgumentParser(description="A medieval house intrigue chronicle.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for a reproducible run")
    args = parser.parse_args()

    print("=" * 64)
    print("  THE CHRONICLE OF HOUSES")
    print("=" * 64)

    state = setup.new_game(seed=args.seed)

    while not state.game_over:
        run_season(state)

    display.show_end_screen(state)


if __name__ == "__main__":
    main()
