"""AI house behavior: simple weighted-random action choice, resolved through
the same actions.py formulas the player uses. No persistent memory or
personality -- just stateless heuristic nudges on top of base weights."""

import random

import actions
from models import GameState, House

BASE_WEIGHTS = {
    "marriage": 15,
    "feast": 20,
    "scheme": 15,
    "household": 30,
    "envoy": 20,
}


def compute_weights(state: GameState, house: House) -> dict[str, float]:
    weights = dict(BASE_WEIGHTS)
    player_relation = house.relation_with(state.player_house_id)

    if house.treasury < 50:
        weights["feast"] = 0
        weights["household"] *= 2
    if player_relation < -20:
        weights["scheme"] *= 2
    if 20 <= player_relation < 60:
        weights["envoy"] *= 1.5
    if not house.ruler().spouse_id:
        weights["marriage"] *= 2

    return weights


def pick_target(state: GameState, house: House) -> House:
    others = [h for h in state.other_houses(house.id) if not h.extinct]
    weights = []
    for other in others:
        weights.append(3.0 if other.id == state.player_house_id else 1.0)
    return random.choices(others, weights=weights)[0]


def take_ai_turn(state: GameState, house: House) -> str:
    weights = compute_weights(state, house)
    action_types = list(weights.keys())
    action_weights = list(weights.values())
    if sum(action_weights) <= 0:
        action = "household"
    else:
        action = random.choices(action_types, weights=action_weights)[0]

    if action == "household":
        return actions.do_household(state, house)

    target = pick_target(state, house)

    if action == "marriage":
        return actions.do_marriage(state, house, target)
    if action == "feast":
        return actions.do_feast_single(state, house, target)
    if action == "envoy":
        return actions.do_envoy(state, house, target)
    if action == "scheme":
        relation = house.relation_with(target.id)
        prefer_sabotage = relation < 0
        roll = random.random()
        use_sabotage = roll < (0.7 if prefer_sabotage else 0.3)
        if use_sabotage:
            return actions.do_scheme_sabotage(state, house, target)
        return actions.do_scheme_spy(state, house, target, reveal=False)

    return actions.do_household(state, house)
