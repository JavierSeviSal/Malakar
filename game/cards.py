"""Card loader for the Malakar automa.

Loads all 17 solo card definitions from cards.yaml:
- 16 game cards with priority data for each turn
- 1 reshuffle card
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import SoloCard, SoulColor, LocationName, Deck

_CARDS_YAML = Path(__file__).parent / "cards.yaml"

# Valid soul color strings → SoulColor enum
_COLOR_MAP = {c.value: c for c in SoulColor}

# Valid location name strings → LocationName enum
_LOCATION_MAP = {loc.value: loc for loc in LocationName}


# ─── YAML → model converters ────────────────────────────────────────────────


def _parse_color_list(raw: list[str]) -> list[SoulColor]:
    """Convert a list of color strings to SoulColor enums."""
    result = []
    for c in raw:
        if c in _COLOR_MAP:
            result.append(_COLOR_MAP[c])
        else:
            raise ValueError(f"Unknown soul color: '{c}'")
    return result


def _parse_location(raw: str | None) -> LocationName | None:
    """Convert a location string to a LocationName enum."""
    if raw is None:
        return None
    if raw in _LOCATION_MAP:
        return _LOCATION_MAP[raw]
    raise ValueError(f"Unknown location: '{raw}'")


def _parse_solo_card(raw: dict) -> SoloCard:
    """Convert a YAML card entry into a SoloCard."""
    num = raw["number"]

    if raw.get("is_reshuffle", False):
        return SoloCard(number=num, is_reshuffle=True)

    return SoloCard(
        number=num,
        is_reshuffle=False,
        soul_priority=_parse_color_list(raw.get("soul_priority", [])),
        shield_direction=raw.get("shield_direction", "left"),
        exchange_direction=raw.get("exchange_direction", "left"),
        priority_location_free=_parse_location(raw.get("priority_location_free")),
        priority_location_special=_parse_location(raw.get("priority_location_special")),
        tie_arrow=raw.get("tie_arrow", "left"),
        tower_guest_order=_parse_color_list(raw.get("tower_guest_order", [])),
    )


# ─── Public API ──────────────────────────────────────────────────────────────


def _load_yaml(path: Path | None = None) -> dict[str, Any]:
    """Load and return the parsed YAML card data."""
    p = path or _CARDS_YAML
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_all_cards(data: dict | None = None) -> list[SoloCard]:
    """Build all 17 solo cards from YAML data."""
    if data is None:
        data = _load_yaml()
    return [_parse_solo_card(raw) for raw in data["solo_cards"]]


def create_solo_deck(data: dict | None = None) -> Deck:
    """Create the full solo deck (17 cards, unshuffled)."""
    cards = build_all_cards(data)
    return Deck(cards=cards, name="solo")


def get_card_by_number(number: int, data: dict | None = None) -> SoloCard | None:
    """Look up a specific card by number."""
    cards = build_all_cards(data)
    for card in cards:
        if card.number == number:
            return card
    return None


def get_all_cards_map(data: dict | None = None) -> dict[int, SoloCard]:
    """Return a dict mapping card number → SoloCard for all 17 cards."""
    cards = build_all_cards(data)
    return {c.number: c for c in cards}
