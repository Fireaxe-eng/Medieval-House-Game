"""Random event pool. Table-driven: each entry is
(id, weight, condition(state) -> bool, effect(state) -> str). Adding a new
event later is just appending another tuple -- no control-flow changes.

Births are handled separately at the year boundary (see game.py) rather
than through this pool, so heirs aren't left to a rare event roll."""

import random

import actions
import narrative
from models import GameState

FIRE_CHANCE = 0.12


def _active_houses(state: GameState) -> list:
    return [h for h in state.houses.values() if not h.extinct]


def _illness_effect(state: GameState) -> str:
    house = random.choice(_active_houses(state))
    members = house.living_members()
    if not members:
        return narrative.render("event_illness_scare", name=house.ruler().name, house=house.name)
    if random.random() < 0.5 and house.ruler().alive:
        char = house.ruler()
    else:
        char = random.choice(members)
    age = char.age(state.year)
    if age >= 55 and random.random() < 0.15:
        char.alive = False
        char.death_year = state.year
        return narrative.render("event_illness_death", name=char.name, house=house.name)
    return narrative.render("event_illness_scare", name=char.name, house=house.name)


def _windfall_effect(state: GameState) -> str:
    house = random.choice(_active_houses(state))
    house.treasury += random.randint(30, 80)
    return narrative.render("event_windfall", house=house.name)


def _scandal_effect(state: GameState) -> str:
    house = random.choice(_active_houses(state))
    actions.adjust_prestige(house, -10)
    if house.id != state.player_house_id and random.random() < 0.2:
        player = state.player_house()
        house.adjust_relation(state.player_house_id, -10)
        player.adjust_relation(house.id, -10)
        return narrative.render("event_scandal_player_implicated", house=house.name, player_house=player.name)
    return narrative.render("event_scandal", house=house.name)


def _rival_scheme_condition(state: GameState) -> bool:
    return any(h.relation_with(state.player_house_id) < -20 for h in state.ai_houses())


def _rival_scheme_effect(state: GameState) -> str:
    candidates = [h for h in state.ai_houses() if h.relation_with(state.player_house_id) < -20]
    house = random.choice(candidates)
    return actions.do_scheme_sabotage(state, house, state.player_house())


def _marriage_proposal_condition(state: GameState) -> bool:
    return state.pending_proposal is None and any(
        actions.get_proposer(h) is not None for h in state.ai_houses()
    )


def _marriage_proposal_effect(state: GameState) -> str:
    candidates = [h for h in state.ai_houses() if actions.get_proposer(h) is not None]
    house = random.choice(candidates)
    state.pending_proposal = {"house_id": house.id}
    return narrative.render(
        "event_marriage_proposal_received", house=house.name, target=state.player_house().name
    )


def _harvest_effect(state: GameState) -> str:
    for house in _active_houses(state):
        house.treasury += 5
    return narrative.render("event_harvest")


def _plague_rumor_effect(state: GameState) -> str:
    state.plague_rumor_active = True
    return narrative.render("event_plague_rumor")


def _crown_favor_effect(state: GameState) -> str:
    crown = state.crown_house()
    candidates = [h for h in state.other_houses(crown.id) if not h.extinct]
    target = random.choice(candidates)
    crown.adjust_relation(target.id, 10)
    target.adjust_relation(crown.id, 10)
    return narrative.render("crown_favor", target=target.name, crown_region=crown.region)


def _tourney_injury_condition(state: GameState) -> bool:
    return any(h.ruler().martial > 3 for h in _active_houses(state))


def _tourney_injury_effect(state: GameState) -> str:
    candidates = [h for h in _active_houses(state) if h.ruler().martial > 3]
    house = random.choice(candidates)
    house.ruler().martial -= 1
    return narrative.render("event_tournament_injury", ruler=house.ruler().name, house=house.name)


def _always(state: GameState) -> bool:
    return True


EVENT_POOL = [
    ("illness", 15, _always, _illness_effect),
    ("windfall", 15, _always, _windfall_effect),
    ("scandal", 12, _always, _scandal_effect),
    ("rival_scheme", 10, _rival_scheme_condition, _rival_scheme_effect),
    ("marriage_proposal", 10, _marriage_proposal_condition, _marriage_proposal_effect),
    ("harvest", 10, _always, _harvest_effect),
    ("plague_rumor", 8, _always, _plague_rumor_effect),
    ("crown_favor", 10, _always, _crown_favor_effect),
    ("tourney_injury", 10, _tourney_injury_condition, _tourney_injury_effect),
]


def maybe_fire_event(state: GameState) -> str | None:
    if random.random() >= FIRE_CHANCE:
        return None
    eligible = [(eid, weight, effect) for eid, weight, condition, effect in EVENT_POOL if condition(state)]
    if not eligible:
        return None
    weights = [w for _, w, _ in eligible]
    _, _, effect = random.choices(eligible, weights=weights)[0]
    return effect(state)
