"""Status summary, menus, and input prompts -- all player-facing formatting
lives here so it can be iterated on without touching game logic."""

import actions
import narrative
from models import GameState, House, relation_label

ACTION_MENU = [
    "Arrange a marriage",
    "Host a feast or tourney",
    "Scheme against a rival",
    "Manage the household",
    "Send an envoy",
    "End turn early",
]


def safe_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def choose_from_list(prompt: str, options: list[str]) -> int | None:
    for _ in range(3):
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        raw = safe_input("> ")
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("Invalid choice, try again.")
    return None


def standing_tag(ratio: float) -> str:
    if ratio < 0.15:
        return "a minor house, scarcely known at court"
    if ratio < 0.4:
        return "a rising house"
    if ratio < 0.7:
        return "a power in its own right"
    if ratio < 1.0:
        return "rivaling the throne"
    return "the realm whispers of a new crown"


def show_status(state: GameState) -> None:
    player = state.player_house()
    crown = state.crown_house()
    ruler = player.ruler()
    ratio = player.prestige / crown.prestige if crown.prestige else 1.0
    tag = standing_tag(ratio)
    if player.prestige >= crown.prestige:
        gap_text = f"ahead by {player.prestige - crown.prestige}"
    else:
        gap_text = f"gap: {crown.prestige - player.prestige}"

    print(f"\n{'=' * 64}")
    print(f"Year {state.year}, {state.season_name()} -- House {player.name}")
    print("=" * 64)

    spouse = state.find_character(ruler.spouse_id) if ruler.spouse_id else None
    spouse_text = f", wed to {spouse.name}" if spouse else ", unwed"
    heirs = ", ".join(
        player.members[cid].name for cid in ruler.children_ids if cid in player.members and player.members[cid].alive
    )
    heir_text = f" | Children: {heirs}" if heirs else ""
    print(f"Ruler: {ruler.name}, age {ruler.age(state.year)}{spouse_text}{heir_text}")
    print(
        f"Stats -- Diplomacy {ruler.diplomacy}  Martial {ruler.martial}  "
        f"Stewardship {ruler.stewardship}  Intrigue {ruler.intrigue}"
    )
    print(f"Treasury: {player.treasury} gold (income {player.income}/season)")
    print(f"Prestige: {player.prestige}  (Crown: {crown.prestige}, {gap_text}) -- \"{tag}\"")

    print("Relations:")
    for house in state.other_houses(player.id):
        rel = player.relation_with(house.id)
        label = relation_label(rel).value
        tags = []
        if house.is_crown:
            tags.append("the Crown")
        if house.id in player.allies:
            tags.append("ALLIED")
        if house.extinct:
            tags.append("EXTINCT")
        tag_text = f" [{', '.join(tags)}]" if tags else ""
        print(f"  House {house.name}: {label} ({rel:+d}){tag_text}")


def pick_target_house(state: GameState) -> House | None:
    player = state.player_house()
    others = [h for h in state.other_houses(player.id) if not h.extinct]
    labels = []
    for house in others:
        rel = player.relation_with(house.id)
        crown_tag = " (the Crown)" if house.is_crown else ""
        labels.append(f"House {house.name}{crown_tag} -- {relation_label(rel).value} ({rel:+d})")
    idx = choose_from_list("Choose a target house:", labels)
    if idx is None:
        return None
    return others[idx]


def prompt_pending_proposal(state: GameState) -> str | None:
    if state.pending_proposal is None:
        return None
    suitor = state.houses[state.pending_proposal["house_id"]]
    print(f"\nHouse {suitor.name} has sent an unsolicited marriage proposal to your house.")
    idx = choose_from_list("Do you accept the proposal?", ["Accept", "Decline"])
    accept = idx == 0
    return actions.resolve_pending_proposal(state, accept)


def show_menu_and_resolve(state: GameState, actions_left: int) -> str | None:
    print(f"\nActions remaining this season: {actions_left}")
    choice = choose_from_list("What will you do?", ACTION_MENU)
    if choice is None or choice == 5:
        return None

    player = state.player_house()

    if choice == 0:  # marriage
        target = pick_target_house(state)
        if target is None:
            return None
        return actions.do_marriage(state, player, target)

    if choice == 1:  # feast
        sub = choose_from_list(
            "Feast type:",
            [f"Single house feast ({actions.FEAST_SINGLE_COST} gold)", f"Grand feast for all houses ({actions.FEAST_GRAND_COST} gold)"],
        )
        if sub is None:
            return None
        if sub == 0:
            target = pick_target_house(state)
            if target is None:
                return None
            return actions.do_feast_single(state, player, target)
        return actions.do_feast_grand(state, player)

    if choice == 2:  # scheme
        target = pick_target_house(state)
        if target is None:
            return None
        sub = choose_from_list(
            "Scheme type:",
            ["Spy (reveal their stats/relation)", "Sabotage (risk/reward, can backfire)"],
        )
        if sub is None:
            return None
        if sub == 0:
            return actions.do_scheme_spy(state, player, target, reveal=True)
        return actions.do_scheme_sabotage(state, player, target)

    if choice == 3:  # household
        return actions.do_household(state, player)

    if choice == 4:  # envoy
        target = pick_target_house(state)
        if target is None:
            return None
        return actions.do_envoy(state, player, target)

    return None


def print_log(turn_log: list[str]) -> None:
    if not turn_log:
        print("\nThe season passed quietly.")
        return
    print("\n--- Chronicle ---")
    for line in turn_log:
        print(line)


def show_end_screen(state: GameState) -> None:
    player = state.player_house()
    print("\n" + "=" * 64)
    if state.end_reason == "extinction":
        print(narrative.render("extinction", house=player.name))
    elif state.end_reason == "ruin":
        print(narrative.render("ruin", house=player.name))
    print(f"The chronicle of House {player.name} closes in Year {state.year}.")
    print("=" * 64)
