"""Crown direct actions: the royal house occasionally acts on its own,
independent of the player and the other AI houses, so the throne feels
present rather than just another entry on the relation list."""

import random

import narrative
from models import GameState

ACT_CHANCE = 0.20


def grant_favor(state: GameState) -> str | None:
    crown = state.crown_house()
    candidates = [h for h in state.other_houses(crown.id) if not h.extinct]
    if not candidates:
        return None
    target = random.choice(candidates)
    crown.adjust_relation(target.id, 10)
    target.adjust_relation(crown.id, 10)
    return narrative.render("crown_favor", target=target.name, crown_region=crown.region)


def summon_to_court(state: GameState) -> str | None:
    crown = state.crown_house()
    candidates = [h for h in state.other_houses(crown.id) if not h.extinct]
    if not candidates:
        return None
    target = random.choice(candidates)
    delta = random.randint(-5, 10)
    crown.adjust_relation(target.id, delta)
    target.adjust_relation(crown.id, delta)
    return narrative.render("crown_summon", target=target.name, crown_region=crown.region)


def settle_dispute(state: GameState) -> str | None:
    crown = state.crown_house()
    candidates = [h for h in state.other_houses(crown.id) if not h.extinct]
    if len(candidates) < 2:
        return None
    house_a, house_b = random.sample(candidates, 2)
    house_a.adjust_relation(house_b.id, 10)
    house_b.adjust_relation(house_a.id, 10)
    for house in (house_a, house_b):
        house.adjust_relation(crown.id, 5)
        crown.adjust_relation(house.id, 5)
    return narrative.render("crown_dispute", target=house_a.name, target2=house_b.name)


def maybe_act(state: GameState) -> str | None:
    """Roll for whether the Crown acts this season, and if so, do something."""
    if random.random() >= ACT_CHANCE:
        return None
    action = random.choice([grant_favor, summon_to_court, settle_dispute])
    return action(state)
