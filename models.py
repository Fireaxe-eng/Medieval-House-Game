"""Core data model: characters, houses, and overall game state."""

from dataclasses import dataclass, field
from enum import Enum
from itertools import count

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]

_char_id_counter = count(1)


def next_character_id() -> str:
    return f"char_{next(_char_id_counter)}"


class RelationLabel(Enum):
    HOSTILE = "Hostile"
    COLD = "Cold"
    NEUTRAL = "Neutral"
    FRIENDLY = "Friendly"
    ALLIED = "Allied"


def relation_label(value: int) -> RelationLabel:
    value = max(-100, min(100, value))
    if value <= -60:
        return RelationLabel.HOSTILE
    if value <= -20:
        return RelationLabel.COLD
    if value < 20:
        return RelationLabel.NEUTRAL
    if value < 60:
        return RelationLabel.FRIENDLY
    return RelationLabel.ALLIED


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@dataclass
class Character:
    id: str
    name: str
    sex: str  # "M" or "F" -- flavor and spouse-finding only
    birth_year: int
    house_id: str
    death_year: int | None = None
    diplomacy: int = 10
    martial: int = 10
    stewardship: int = 10
    intrigue: int = 10
    spouse_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    parent_ids: list[str] = field(default_factory=list)
    alive: bool = True

    def age(self, current_year: int) -> int:
        return current_year - self.birth_year


@dataclass
class House:
    id: str
    name: str
    region: str
    words: str
    is_crown: bool = False
    is_player: bool = False
    extinct: bool = False
    ruler_id: str = ""
    members: dict[str, Character] = field(default_factory=dict)
    treasury: int = 0
    prestige: int = 0
    income: int = 10
    relations: dict[str, int] = field(default_factory=dict)  # house_id -> -100..100
    allies: set[str] = field(default_factory=set)

    def ruler(self) -> Character:
        return self.members[self.ruler_id]

    def relation_with(self, other_house_id: str) -> int:
        return self.relations.get(other_house_id, 0)

    def adjust_relation(self, other_house_id: str, delta: int) -> None:
        current = self.relations.get(other_house_id, 0)
        self.relations[other_house_id] = clamp(current + delta, -100, 100)

    def living_members(self) -> list[Character]:
        return [c for c in self.members.values() if c.alive]


@dataclass
class GameState:
    year: int
    season: int  # index into SEASONS
    houses: dict[str, House]
    player_house_id: str
    crown_house_id: str
    turn_log: list[str] = field(default_factory=list)
    pending_proposal: dict | None = None  # queued unsolicited marriage proposal, if any
    plague_rumor_active: bool = False  # bumps the next year-boundary death roll
    ruin_counter: int = 0  # consecutive seasons the player's treasury has been deeply negative
    game_over: bool = False
    end_reason: str | None = None
    rng_seed: int | None = None

    def player_house(self) -> House:
        return self.houses[self.player_house_id]

    def crown_house(self) -> House:
        return self.houses[self.crown_house_id]

    def other_houses(self, house_id: str) -> list[House]:
        return [h for h in self.houses.values() if h.id != house_id]

    def ai_houses(self) -> list[House]:
        """All non-player, non-crown houses still in play."""
        return [
            h for h in self.houses.values()
            if not h.is_player and not h.is_crown and not h.extinct
        ]

    def season_name(self) -> str:
        return SEASONS[self.season]

    def find_character(self, character_id: str) -> Character | None:
        for house in self.houses.values():
            if character_id in house.members:
                return house.members[character_id]
        return None


def find_heir(state: "GameState", house: House) -> Character | None:
    """Oldest living child of the ruler, else the ruler's living spouse, else None.

    Children always live in the ruling house's `members` dict, but a spouse
    who married in from elsewhere may still be recorded under their birth
    house, so spouse lookup goes through the full game state.
    """
    ruler = house.ruler()
    candidates = [
        house.members[cid]
        for cid in ruler.children_ids
        if cid in house.members and house.members[cid].alive
    ]
    if candidates:
        return min(candidates, key=lambda c: c.birth_year)
    if ruler.spouse_id:
        spouse = state.find_character(ruler.spouse_id)
        if spouse and spouse.alive:
            return spouse
    return None
