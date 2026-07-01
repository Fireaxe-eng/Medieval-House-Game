"""Chronicle-style flavor text. Every action/event resolver returns a
template key plus formatting kwargs and routes it through render() here,
so prose never gets built inline in game-logic modules."""

import random

TEMPLATES: dict[str, list[str]] = {
    # --- marriage ---
    "marriage_success": [
        "{proposer} of House {house} wed {target} of House {target_house}, sealing new ties between the families.",
        "Bells rang across {house} lands as {proposer} married {target} of House {target_house}; both houses toast the union.",
        "A match was made between House {house} and House {target_house} — the realm takes note of the wedding feast.",
    ],
    "marriage_failure": [
        "House {target_house} rebuffed the proposed match with House {house}, and tongues wag at the snub.",
        "{target} of House {target_house} would not have {proposer}, and the courtship ends in cold silence.",
        "Word came back from House {target_house}: the marriage proposal was declined, politely but firmly.",
    ],
    "marriage_no_candidate": [
        "House {house} has no one of marriageable age free to wed this season.",
    ],
    # --- feast ---
    "feast_single": [
        "House {house} hosted a feast in honor of House {target}, and the wine flowed freely.",
        "Musicians and minstrels filled the hall of House {house} as House {target} was feted as guests of honor.",
        "House {house} threw open its gates for a tourney, with House {target} seated at the high table.",
    ],
    "feast_grand": [
        "House {house} held a grand tourney, and lords from every house came to watch the lances splinter.",
        "The halls of House {house} overflowed with guests from every corner of the realm for a feast long remembered.",
        "House {house} spared no expense on a grand tourney, and word of its splendor spread far.",
    ],
    "feast_no_funds": [
        "House {house} cannot afford to host a feast this season.",
    ],
    # --- scheme: spy ---
    "scheme_spy_success": [
        "Agents of House {house} slipped quietly into House {target}'s confidence and returned with whispers worth knowing.",
        "A well-placed bribe let House {house} learn rather more about House {target} than House {target} would like.",
        "House {house}'s spies returned from House {target}'s halls with a full accounting of their secrets.",
    ],
    "scheme_spy_failure": [
        "House {house}'s agents found nothing of use in House {target}'s halls this season.",
    ],
    # --- scheme: sabotage ---
    "scheme_sabotage_success": [
        "A scandal engineered by House {house} broke over House {target}, and their standing at court suffered for it.",
        "House {house}'s hidden hand struck at House {target}'s coffers and reputation alike, and neither recovered quickly.",
        "Whispered rumors, planted by House {house}, did their quiet work against House {target}.",
    ],
    "scheme_sabotage_failure": [
        "House {target} uncovered the plot against them and named House {house} before the court.",
        "The scheme against House {target} unraveled, and House {house}'s hand was seen in it.",
        "House {house}'s sabotage was discovered, and House {target} will not soon forgive the betrayal.",
    ],
    # --- household ---
    "household_manage": [
        "{ruler} of House {house} spent the season auditing ledgers and mending the house's finances.",
        "Granaries were restocked and tithes collected with care under {ruler}'s watchful eye in House {house}.",
        "House {house} prospered quietly this season as {ruler} tended to roads, mills, and markets.",
    ],
    # --- envoy ---
    "envoy_success": [
        "An envoy from House {house} was warmly received at House {target}'s court, and relations between the houses warmed.",
        "House {house}'s envoy returned from House {target} with promises of goodwill exchanged.",
        "Gifts and kind words passed between House {house} and House {target} as their envoy concluded its business.",
    ],
    "envoy_success_alliance": [
        "House {house} and House {target} have sworn a formal alliance, their banners now bound together.",
        "After years of courtship, House {house} and House {target} struck a lasting pact of mutual support.",
    ],
    "envoy_failure": [
        "House {target} received House {house}'s envoy coolly, and little came of the visit.",
        "House {house}'s envoy returned from House {target} empty-handed, the overture unanswered.",
    ],
    # --- crown ---
    "crown_favor": [
        "The Crown showed favor to House {target}, and its standing at court rose for it.",
        "From the throne at {crown_region}, House {target} was singled out for royal favor.",
    ],
    "crown_summon": [
        "House {target} was summoned to court before the Crown, and the realm watched to see what would come of it.",
        "The Crown called House {target} to {crown_region} to account for itself before the throne.",
    ],
    "crown_dispute": [
        "The Crown settled a dispute between House {target} and House {target2}, and both bent the knee in acceptance.",
        "By royal decree, the Crown resolved the quarrel between House {target} and House {target2}.",
    ],
    # --- events ---
    "event_illness_scare": [
        "{name} of House {house} took ill this season, but recovered after weeks abed.",
        "A fever swept through House {house}'s halls, and {name} was laid low for a time before mending.",
    ],
    "event_illness_death": [
        "{name} of House {house} succumbed to illness, and the house mourns.",
        "Despite the best efforts of physicians, {name} of House {house} did not survive the season's fever.",
    ],
    "event_windfall": [
        "A merchant caravan paid generous tribute to House {house}, swelling its coffers.",
        "House {house}'s lands yielded an unexpected bounty this season, and its treasury grew.",
    ],
    "event_scandal": [
        "A scandal broke over House {house}'s name, and its standing at court suffered.",
        "Whispers of impropriety dogged House {house} this season, tarnishing its reputation.",
    ],
    "event_scandal_player_implicated": [
        "The scandal touching House {house} was traced back to House {player_house}, and relations soured.",
    ],
    "event_rival_scheme": [
        "House {house}, no friend to House {target}, struck at them in secret this season.",
    ],
    "event_marriage_proposal_received": [
        "An envoy from House {house} arrived bearing an unsolicited marriage proposal for House {target}.",
    ],
    "event_harvest": [
        "A bountiful harvest blessed every house in the realm this season, and granaries filled to bursting.",
    ],
    "event_plague_rumor": [
        "Rumors of plague crept through the realm this season, and every house watched its kin nervously.",
    ],
    "event_tournament_injury": [
        "{ruler} of House {house} was injured in the lists during a recent tourney, and has not fully recovered.",
    ],
    # --- aging / births / deaths ---
    "birth_player": [
        "House {house} welcomes a new child: {name}, born this year to {parent}.",
        "Cheers rang through House {house}'s halls at the birth of {name}, child of {parent}.",
    ],
    "death_old_age": [
        "{name} of House {house} has died of old age, full of years.",
        "After a long life, {name} of House {house} passed quietly this year.",
    ],
    "succession": [
        "Upon {old_ruler}'s death, {new_ruler} has risen to lead House {house}.",
        "House {house} mourns {old_ruler} even as it looks to {new_ruler}, its new ruler, to lead them forward.",
    ],
    "extinction": [
        "With no heir to be found, the line of House {house} has ended. The house is no more.",
    ],
    "ruin": [
        "Drowning in debt, House {house} has been carved up by creditors and rival houses. Its banners are lowered for the last time.",
    ],
}


def render(key: str, **kwargs) -> str:
    template = random.choice(TEMPLATES[key])
    return template.format(**kwargs)
