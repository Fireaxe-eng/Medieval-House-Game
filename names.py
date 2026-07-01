"""Static flavor data: the starting house roster and given-name pools for
procedurally generated children and marriage kin."""

import random

# --- Premade player-eligible houses -----------------------------------

PREMADE_HOUSES = [
    {
        "id": "varrow",
        "name": "Varrow",
        "region": "Greenmere Vale",
        "words": "Steady the Plow",
        "lean": "stewardship",
        "ruler_name": "Edrin Varrow",
        "ruler_sex": "M",
        "ruler_age": 38,
    },
    {
        "id": "drask",
        "name": "Drask",
        "region": "Blackfen Marches",
        "words": "No Debt Unpaid",
        "lean": "intrigue",
        "ruler_name": "Mirelle Drask",
        "ruler_sex": "F",
        "ruler_age": 33,
    },
    {
        "id": "calloway",
        "name": "Calloway",
        "region": "Sunmere Coast",
        "words": "Fair Wind, Fair Word",
        "lean": "diplomacy",
        "ruler_name": "Tomas Calloway",
        "ruler_sex": "M",
        "ruler_age": 41,
    },
    {
        "id": "ashgrove",
        "name": "Ashgrove",
        "region": "Thornwood March",
        "words": "Iron Before Ink",
        "lean": "martial",
        "ruler_name": "Branwen Ashgrove",
        "ruler_sex": "F",
        "ruler_age": 36,
    },
]

# --- AI rival houses -----------------------------------------------------

AI_HOUSES = [
    {
        "id": "brennick",
        "name": "Brennick",
        "region": "Stagfell Hills",
        "words": "Loyal to the Last",
        "lean": "diplomacy",
        "ruler_name": "Aldous Brennick",
        "ruler_sex": "M",
        "ruler_age": 44,
        "start_relation": 10,
    },
    {
        "id": "voss",
        "name": "Voss",
        "region": "Coldmoor Reach",
        "words": "We Endure",
        "lean": "martial",
        "ruler_name": "Garrick Voss",
        "ruler_sex": "M",
        "ruler_age": 49,
        "start_relation": -10,
    },
    {
        "id": "pellard",
        "name": "Pellard",
        "region": "Ambervale",
        "words": "Gold Remembers",
        "lean": "stewardship",
        "ruler_name": "Henrietta Pellard",
        "ruler_sex": "F",
        "ruler_age": 52,
        "start_relation": 0,
    },
    {
        "id": "aldric",
        "name": "Aldric",
        "region": "Greywatch Downs",
        "words": "First to Rise",
        "lean": "martial",
        "ruler_name": "Roswin Aldric",
        "ruler_sex": "M",
        "ruler_age": 29,
        "start_relation": 5,
    },
    {
        "id": "sorrel",
        "name": "Sorrel",
        "region": "Mireholt Fens",
        "words": "Quiet Waters Run Deep",
        "lean": "intrigue",
        "ruler_name": "Lysandra Sorrel",
        "ruler_sex": "F",
        "ruler_age": 40,
        "start_relation": -15,
    },
    {
        "id": "fenmark",
        "name": "Fenmark",
        "region": "Hollowmere Marsh",
        "words": "Patience Is a Blade",
        "lean": "intrigue",
        "ruler_name": "Osric Fenmark",
        "ruler_sex": "M",
        "ruler_age": 47,
        "start_relation": -5,
    },
]

# --- The Crown -------------------------------------------------------------

CROWN_HOUSE = {
    "id": "tarvelle",
    "name": "Tarvelle",
    "region": "Calderwyn",
    "words": "One Realm, One Hand",
    "ruler_name": "Aurelian Tarvelle",
    "ruler_sex": "M",
    "ruler_age": 50,
    "start_relation": 0,
}

# --- Given-name pools for procedurally generated characters ----------------

MALE_NAMES = [
    "Aldwin", "Bertram", "Cedric", "Dunstan", "Eamon", "Fenwick", "Godric",
    "Hale", "Ivor", "Jasper", "Kelwin", "Lucan", "Merrick", "Nolan", "Osmund",
    "Percival", "Quentin", "Rowan", "Soren", "Tristan", "Ulric", "Wendell",
]

FEMALE_NAMES = [
    "Alaine", "Briar", "Cressida", "Delphine", "Elspeth", "Freya", "Gwendolyn",
    "Helena", "Isolde", "Jonquil", "Kira", "Liora", "Maren", "Nessa", "Odette",
    "Petra", "Rosalind", "Sybil", "Thea", "Vesper", "Wren", "Yolande",
]


def random_given_name(sex: str) -> str:
    pool = MALE_NAMES if sex == "M" else FEMALE_NAMES
    return random.choice(pool)


def random_sex() -> str:
    return random.choice(["M", "F"])
