"""Shared action resolution. These functions are used by the player's menu
choices, AI house behavior (ai.py), and the Crown (crown.py) alike -- one set
of formulas, no duplicated logic. Each function mutates GameState and returns
a chronicle-style line of text."""

import random

import names
import narrative
from models import Character, House, GameState, clamp, next_character_id, relation_label

MARRIAGE_BASE = 30
MARRIAGE_RELATION_DIVISOR = 2
FEAST_SINGLE_COST = 50
FEAST_GRAND_COST = 120
SPY_BASE = 40
SABOTAGE_BASE = 25
ENVOY_BASE = 35
ALLIANCE_THRESHOLD = 60
TREASURY_BAND_LABELS = [(100, "meager"), (300, "modest"), (600, "comfortable")]


def adjust_prestige(house: House, delta: int) -> None:
    house.prestige = max(0, house.prestige + delta)


def treasury_band(amount: int) -> str:
    for threshold, label in TREASURY_BAND_LABELS:
        if amount < threshold:
            return label
    return "wealthy"


# --- marriage ---------------------------------------------------------------

def get_proposer(house: House) -> Character | None:
    """The house's own ruler if unmarried, else their oldest unmarried child."""
    ruler = house.ruler()
    if ruler.alive and not ruler.spouse_id:
        return ruler
    candidates = [
        house.members[cid] for cid in ruler.children_ids
        if cid in house.members and house.members[cid].alive and not house.members[cid].spouse_id
    ]
    if candidates:
        return min(candidates, key=lambda c: c.birth_year)
    return None


def get_marriage_target(state: GameState, target_house: House) -> Character:
    """The target house's ruler if unmarried, else an unmarried child, else a
    freshly generated kinsman -- marriage should never be a dead end."""
    ruler = target_house.ruler()
    if ruler.alive and not ruler.spouse_id:
        return ruler
    candidates = [
        target_house.members[cid] for cid in ruler.children_ids
        if cid in target_house.members and target_house.members[cid].alive
        and not target_house.members[cid].spouse_id
    ]
    if candidates:
        return min(candidates, key=lambda c: c.birth_year)
    sex = names.random_sex()
    name = f"{names.random_given_name(sex)} of {target_house.name}"
    age = random.randint(18, 35)
    char = Character(
        id=next_character_id(), name=name, sex=sex,
        birth_year=state.year - age, house_id=target_house.id,
        diplomacy=random.randint(6, 14), martial=random.randint(6, 14),
        stewardship=random.randint(6, 14), intrigue=random.randint(6, 14),
    )
    target_house.members[char.id] = char
    return char


def do_marriage(state: GameState, house: House, target_house: House) -> str:
    proposer = get_proposer(house)
    if proposer is None:
        return narrative.render("marriage_no_candidate", house=house.name)

    target = get_marriage_target(state, target_house)
    relation = house.relation_with(target_house.id)
    chance = clamp(MARRIAGE_BASE + proposer.diplomacy * 2 + relation // MARRIAGE_RELATION_DIVISOR, 5, 95)
    roll = random.randint(1, 100)

    if roll <= chance:
        proposer.spouse_id = target.id
        target.spouse_id = proposer.id
        house.adjust_relation(target_house.id, 15)
        target_house.adjust_relation(house.id, 15)
        adjust_prestige(house, 10)
        return narrative.render(
            "marriage_success", proposer=proposer.name, house=house.name,
            target=target.name, target_house=target_house.name,
        )
    else:
        house.adjust_relation(target_house.id, -5)
        target_house.adjust_relation(house.id, -5)
        return narrative.render(
            "marriage_failure", proposer=proposer.name, house=house.name,
            target=target.name, target_house=target_house.name,
        )


def resolve_pending_proposal(state: GameState, accept: bool) -> str:
    proposal = state.pending_proposal
    state.pending_proposal = None
    suitor_house = state.houses[proposal["house_id"]]
    player_house = state.player_house()

    if accept:
        proposer = get_proposer(suitor_house)
        target = get_proposer(player_house)
        if proposer is None or target is None:
            return narrative.render("marriage_no_candidate", house=player_house.name)
        proposer.spouse_id = target.id
        target.spouse_id = proposer.id
        player_house.adjust_relation(suitor_house.id, 15)
        suitor_house.adjust_relation(player_house.id, 15)
        adjust_prestige(player_house, 10)
        return narrative.render(
            "marriage_success", proposer=target.name, house=player_house.name,
            target=proposer.name, target_house=suitor_house.name,
        )
    else:
        player_house.adjust_relation(suitor_house.id, -5)
        suitor_house.adjust_relation(player_house.id, -5)
        return narrative.render(
            "marriage_failure", proposer="Your house", house=player_house.name,
            target=suitor_house.ruler().name, target_house=suitor_house.name,
        )


# --- feast / tourney ---------------------------------------------------------

def do_feast_single(state: GameState, house: House, target_house: House) -> str:
    if house.treasury < FEAST_SINGLE_COST:
        return narrative.render("feast_no_funds", house=house.name)
    house.treasury -= FEAST_SINGLE_COST
    adjust_prestige(house, 8)
    house.adjust_relation(target_house.id, 5)
    target_house.adjust_relation(house.id, 5)
    return narrative.render("feast_single", house=house.name, target=target_house.name)


def do_feast_grand(state: GameState, house: House) -> str:
    if house.treasury < FEAST_GRAND_COST:
        return narrative.render("feast_no_funds", house=house.name)
    house.treasury -= FEAST_GRAND_COST
    adjust_prestige(house, 15)
    for other in state.other_houses(house.id):
        house.adjust_relation(other.id, 5)
        other.adjust_relation(house.id, 5)
    return narrative.render("feast_grand", house=house.name)


# --- scheme -------------------------------------------------------------------

def do_scheme_spy(state: GameState, house: House, target_house: House, reveal: bool = True) -> str:
    ruler = house.ruler()
    target_ruler = target_house.ruler()
    chance = clamp(SPY_BASE + ruler.intrigue * 2 - target_ruler.intrigue, 10, 90)
    roll = random.randint(1, 100)
    if roll <= chance:
        line = narrative.render("scheme_spy_success", house=house.name, target=target_house.name)
        if not reveal:
            return line
        relation = target_house.relation_with(house.id)
        intel = (
            f"    Intel on House {target_house.name}: "
            f"Diplomacy {target_ruler.diplomacy}, Martial {target_ruler.martial}, "
            f"Stewardship {target_ruler.stewardship}, Intrigue {target_ruler.intrigue} | "
            f"Relation toward {house.name}: {relation_label(relation).value} ({relation}) | "
            f"Treasury: {treasury_band(target_house.treasury)}"
        )
        return line + "\n" + intel
    return narrative.render("scheme_spy_failure", house=house.name, target=target_house.name)


def do_scheme_sabotage(state: GameState, house: House, target_house: House) -> str:
    ruler = house.ruler()
    target_ruler = target_house.ruler()
    chance = clamp(SABOTAGE_BASE + ruler.intrigue * 2 - target_ruler.intrigue, 5, 80)
    roll = random.randint(1, 100)
    if roll <= chance:
        adjust_prestige(target_house, -10)
        target_house.treasury -= random.randint(40, 100)
        adjust_prestige(house, 5)
        return narrative.render("scheme_sabotage_success", house=house.name, target=target_house.name)
    else:
        house.adjust_relation(target_house.id, -25)
        target_house.adjust_relation(house.id, -25)
        adjust_prestige(house, -5)
        return narrative.render("scheme_sabotage_failure", house=house.name, target=target_house.name)


# --- household ------------------------------------------------------------

def do_household(state: GameState, house: House) -> str:
    ruler = house.ruler()
    house.income = min(house.income + ruler.stewardship // 4, 60)
    house.treasury += ruler.stewardship * 3
    return narrative.render("household_manage", ruler=ruler.name, house=house.name)


# --- envoy ------------------------------------------------------------------

def do_envoy(state: GameState, house: House, target_house: House) -> str:
    ruler = house.ruler()
    relation = house.relation_with(target_house.id)
    chance = clamp(ENVOY_BASE + ruler.diplomacy * 2 + relation // 3, 10, 90)
    roll = random.randint(1, 100)
    if roll <= chance:
        house.adjust_relation(target_house.id, 10)
        target_house.adjust_relation(house.id, 10)
        new_relation = house.relation_with(target_house.id)
        if new_relation >= ALLIANCE_THRESHOLD and target_house.id not in house.allies:
            house.allies.add(target_house.id)
            target_house.allies.add(house.id)
            return narrative.render("envoy_success_alliance", house=house.name, target=target_house.name)
        return narrative.render("envoy_success", house=house.name, target=target_house.name)
    else:
        house.adjust_relation(target_house.id, -5)
        target_house.adjust_relation(house.id, -5)
        return narrative.render("envoy_failure", house=house.name, target=target_house.name)
