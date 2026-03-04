"""Data models for the Malakar automa — Inferno solo opponent."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import random
import copy
import json


# ─── Enums ───────────────────────────────────────────────────────────────────


class GamePhase(Enum):
    SETUP = "setup"
    DRAW_CARD = "draw_card"
    HELL_PHASE = "hell_phase"
    FLORENCE_PHASE = "florence_phase"
    TURN_END = "turn_end"
    GAME_OVER = "game_over"
    WAITING_FOR_INPUT = "waiting_for_input"


class DifficultyMode(Enum):
    NORMAL = "normal"
    HARD = "hard"
    DEMONIC = "demonic"

    def label(self) -> str:
        return self.name.capitalize()

    def label_es(self) -> str:
        _labels = {"NORMAL": "Normal", "HARD": "Difícil", "DEMONIC": "Demoníaco"}
        return _labels.get(self.name, self.name.capitalize())


class SoulColor(Enum):
    """The 9 soul / sin colors matching the circles of Hell (top to bottom)."""

    BEIGE = "beige"  # Circle 1 - Limbo (pagans)
    PURPLE = "purple"  # Circle 2 - Lust
    GREEN = "green"  # Circle 3 - Gluttony
    YELLOW = "yellow"  # Circle 4 - Greed
    BLUE = "blue"  # Circle 5 - Sloth
    ORANGE = "orange"  # Circle 6 - Heresy
    RED = "red"  # Circle 7 - Violence
    GRAY = "gray"  # Circle 8 - Fraud
    ICE_BLUE = "ice_blue"  # Circle 9 - Treason

    def label(self) -> str:
        _labels = {
            "beige": "Beige",
            "purple": "Purple",
            "green": "Green",
            "yellow": "Yellow",
            "blue": "Blue",
            "orange": "Orange",
            "red": "Red",
            "gray": "Gray",
            "ice_blue": "Ice Blue",
        }
        return _labels.get(self.value, self.value.capitalize())

    def label_es(self) -> str:
        _labels = {
            "beige": "Beige",
            "purple": "Púrpura",
            "green": "Verde",
            "yellow": "Amarillo",
            "blue": "Azul",
            "orange": "Naranja",
            "red": "Rojo",
            "gray": "Gris",
            "ice_blue": "Azul Hielo",
        }
        return _labels.get(self.value, self.value.capitalize())

    def sin_name(self) -> str:
        _sins = {
            "beige": "Limbo",
            "purple": "Lust",
            "green": "Gluttony",
            "yellow": "Greed",
            "blue": "Sloth",
            "orange": "Heresy",
            "red": "Violence",
            "gray": "Fraud",
            "ice_blue": "Treason",
        }
        return _sins.get(self.value, "Unknown")

    def sin_name_es(self) -> str:
        _sins = {
            "beige": "Limbo",
            "purple": "Lujuria",
            "green": "Gula",
            "yellow": "Avaricia",
            "blue": "Pereza",
            "orange": "Herejía",
            "red": "Violencia",
            "gray": "Fraude",
            "ice_blue": "Traición",
        }
        return _sins.get(self.value, "Desconocido")

    def circle_number(self) -> int:
        """Return the circle of Hell number (1-9)."""
        _circles = {
            "beige": 1,
            "purple": 2,
            "green": 3,
            "yellow": 4,
            "blue": 5,
            "orange": 6,
            "red": 7,
            "gray": 8,
            "ice_blue": 9,
        }
        return _circles.get(self.value, 0)

    def emoji(self) -> str:
        _emojis = {
            "beige": "🏛️",
            "purple": "💜",
            "green": "💚",
            "yellow": "💛",
            "blue": "💙",
            "orange": "🧡",
            "red": "❤️",
            "gray": "🩶",
            "ice_blue": "🩵",
        }
        return _emojis.get(self.value, "⚪")


class LocationType(Enum):
    FREE_ACCESS = "free_access"
    SPECIAL = "special"


class LocationName(Enum):
    """The 8 Florence locations."""

    # Free-access locations
    HAYSTACK = "haystack"
    BANQUET = "banquet"
    BANK = "bank"
    COURTYARD = "courtyard"
    # Special locations
    BONFIRE = "bonfire"
    WALL = "wall"
    MARKET = "market"
    PALACE = "palace"

    def label(self) -> str:
        return self.name.replace("_", " ").title()

    def label_es(self) -> str:
        _labels = {
            "haystack": "Pajar",
            "banquet": "Banquete",
            "bank": "Banco",
            "courtyard": "Patio",
            "bonfire": "Hoguera",
            "wall": "Muralla",
            "market": "Mercado",
            "palace": "Palacio",
        }
        return _labels.get(self.value, self.value.title())

    def location_type(self) -> LocationType:
        if self.value in ("haystack", "banquet", "bank", "courtyard"):
            return LocationType.FREE_ACCESS
        return LocationType.SPECIAL

    def sin_color(self) -> SoulColor:
        """Which sin/soul color sinners at this location produce."""
        _colors = {
            "haystack": SoulColor.PURPLE,  # Lust
            "banquet": SoulColor.GREEN,  # Gluttony
            "bank": SoulColor.YELLOW,  # Greed
            "courtyard": SoulColor.BLUE,  # Sloth
            "bonfire": SoulColor.ORANGE,  # Heresy
            "wall": SoulColor.RED,  # Violence
            "market": SoulColor.GRAY,  # Fraud
            "palace": SoulColor.ICE_BLUE,  # Treason
        }
        return _colors.get(self.value, SoulColor.BEIGE)


# ─── Quartiere mapping ───────────────────────────────────────────────────────

# Each quartiere has one free-access + one special location
QUARTIERI = {
    "porta_san_piero": {
        "free_access": LocationName.HAYSTACK,
        "special": LocationName.BONFIRE,
    },
    "porta_del_duomo": {
        "free_access": LocationName.BANQUET,
        "special": LocationName.WALL,
    },
    "san_pier_scheraggio": {
        "free_access": LocationName.BANK,
        "special": LocationName.MARKET,
    },
    "il_borgo": {
        "free_access": LocationName.COURTYARD,
        "special": LocationName.PALACE,
    },
}


# ─── Card model ──────────────────────────────────────────────────────────────


@dataclass
class SoloCard:
    """One of the 16 game cards (or the reshuffle card) in the Malakar solo deck.

    Each card encodes Malakar's priorities for the current turn:
    - soul_priority: ordered list of soul colors for tie-breaking
    - shield_direction: "left" or "right" — which side of a Hell circle to place souls
    - exchange_direction: "left" (exchange 1 Florin) or "right" (exchange max)
    - priority_location: which Florence locations Malakar prefers
    - tie_arrow: "left" or "right" — for Fraud card tie-breaking
    - tower_guest_order: guest color priorities for tower reorganization
    """

    number: int  # 1-16 for game cards, 17 for reshuffle
    is_reshuffle: bool = False

    # Priority data (only for game cards 1-16)
    soul_priority: list[SoulColor] = field(default_factory=list)
    shield_direction: str = "left"  # "left" or "right"
    exchange_direction: str = "left"  # "left" (1 Florin) or "right" (max)
    priority_location_free: Optional[LocationName] = None
    priority_location_special: Optional[LocationName] = None
    tie_arrow: str = "left"  # "left" or "right"
    tower_guest_order: list[SoulColor] = field(default_factory=list)

    @property
    def image(self) -> str:
        return f"/static/cards/card{self.number}.png"

    @property
    def image_back(self) -> str:
        return "/static/cards/back.png"

    def to_dict(self) -> dict:
        d = {
            "number": self.number,
            "is_reshuffle": self.is_reshuffle,
            "image": self.image,
            "image_back": self.image_back,
        }
        if not self.is_reshuffle:
            d.update(
                {
                    "soul_priority": [c.value for c in self.soul_priority],
                    "shield_direction": self.shield_direction,
                    "exchange_direction": self.exchange_direction,
                    "priority_location_free": (
                        self.priority_location_free.value
                        if self.priority_location_free
                        else None
                    ),
                    "priority_location_special": (
                        self.priority_location_special.value
                        if self.priority_location_special
                        else None
                    ),
                    "tie_arrow": self.tie_arrow,
                    "tower_guest_order": [c.value for c in self.tower_guest_order],
                }
            )
        return d


# ─── Deck ────────────────────────────────────────────────────────────────────


@dataclass
class Deck:
    """A deck of SoloCards with standard operations."""

    cards: list[SoloCard] = field(default_factory=list)
    name: str = "deck"

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Optional[SoloCard]:
        if self.cards:
            return self.cards.pop(0)
        return None

    def peek(self) -> Optional[SoloCard]:
        return self.cards[0] if self.cards else None

    def place_under(self, card: SoloCard):
        self.cards.append(card)

    def place_on_top(self, card: SoloCard):
        self.cards.insert(0, card)

    def size(self) -> int:
        return len(self.cards)

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def add_all(self, cards: list[SoloCard]):
        self.cards.extend(cards)

    def clear(self) -> list[SoloCard]:
        cards = list(self.cards)
        self.cards.clear()
        return cards

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size(),
            "cards": [c.to_dict() for c in self.cards],
        }

    def to_snapshot_dict(self) -> dict:
        """Minimal representation for undo snapshots."""
        return {
            "name": self.name,
            "card_numbers": [c.number for c in self.cards],
        }


# ─── Game State ──────────────────────────────────────────────────────────────


@dataclass
class GameState:
    """Full state of a Malakar solo game."""

    # ── Meta ──
    turn_number: int = 0
    phase: GamePhase = GamePhase.SETUP
    difficulty: DifficultyMode = DifficultyMode.NORMAL
    language: str = "en"

    # ── Decks ──
    solo_deck: Deck = field(default_factory=lambda: Deck(name="solo"))
    discard_pile: Deck = field(default_factory=lambda: Deck(name="discard"))

    # ── Current turn state ──
    current_card: Optional[SoloCard] = None
    previous_card: Optional[SoloCard] = None
    reshuffle_triggered: bool = False

    # ── Input ──
    pending_input: Optional[dict] = None
    next_phase_after_input: Optional[str] = None

    # ── Action log ──
    action_log: list[dict] = field(default_factory=list)
    _log_counter: int = 0

    # ── Undo ──
    _undo_snapshot: Optional[dict] = None

    def log(self, message: str, category: str = "info", message_es: str = ""):
        """Append a log entry."""
        self._log_counter += 1
        self.action_log.append(
            {
                "id": self._log_counter,
                "turn": self.turn_number,
                "phase": self.phase.value,
                "category": category,
                "message": message,
                "message_es": message_es or message,
            }
        )

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the full state."""
        return {
            "turn_number": self.turn_number,
            "phase": self.phase.value,
            "difficulty": self.difficulty.value,
            "language": self.language,
            "solo_deck": self.solo_deck.to_dict(),
            "discard_pile": self.discard_pile.to_dict(),
            "current_card": self.current_card.to_dict() if self.current_card else None,
            "previous_card": (
                self.previous_card.to_dict() if self.previous_card else None
            ),
            "reshuffle_triggered": self.reshuffle_triggered,
            "pending_input": self.pending_input,
            "next_phase_after_input": self.next_phase_after_input,
            "action_log": self.action_log[-50:],  # Last 50 entries
            "guidance": self._build_guidance(),
        }

    def _build_guidance(self) -> Optional[dict]:
        """Build a guidance block for the current card (used by the frontend)."""
        if not self.current_card or self.current_card.is_reshuffle:
            return None

        card = self.current_card
        lang = self.language

        return {
            "soul_priority": [
                {
                    "color": c.value,
                    "label": c.label() if lang == "en" else c.label_es(),
                    "sin": c.sin_name() if lang == "en" else c.sin_name_es(),
                    "emoji": c.emoji(),
                    "circle": c.circle_number(),
                }
                for c in card.soul_priority
            ],
            "shield_direction": card.shield_direction,
            "exchange_direction": card.exchange_direction,
            "exchange_label": (
                ("Exchange 1 Florin" if lang == "en" else "Cambiar 1 Florín")
                if card.exchange_direction == "left"
                else (
                    "Exchange max Florins" if lang == "en" else "Cambiar máx. Florines"
                )
            ),
            "priority_location_free": (
                {
                    "name": (
                        card.priority_location_free.value
                        if card.priority_location_free
                        else None
                    ),
                    "label": (
                        card.priority_location_free.label()
                        if card.priority_location_free and lang == "en"
                        else (
                            card.priority_location_free.label_es()
                            if card.priority_location_free
                            else None
                        )
                    ),
                }
                if card.priority_location_free
                else None
            ),
            "priority_location_special": (
                {
                    "name": (
                        card.priority_location_special.value
                        if card.priority_location_special
                        else None
                    ),
                    "label": (
                        card.priority_location_special.label()
                        if card.priority_location_special and lang == "en"
                        else (
                            card.priority_location_special.label_es()
                            if card.priority_location_special
                            else None
                        )
                    ),
                }
                if card.priority_location_special
                else None
            ),
            "tie_arrow": card.tie_arrow,
            "tower_guest_order": [
                {
                    "color": c.value,
                    "label": c.label() if lang == "en" else c.label_es(),
                    "emoji": c.emoji(),
                }
                for c in card.tower_guest_order
            ],
        }

    def save_snapshot(self):
        """Save a lightweight snapshot for undo."""
        self._undo_snapshot = {
            "turn_number": self.turn_number,
            "phase": self.phase.value,
            "difficulty": self.difficulty.value,
            "language": self.language,
            "solo_deck": self.solo_deck.to_snapshot_dict(),
            "discard_pile": self.discard_pile.to_snapshot_dict(),
            "current_card_number": (
                self.current_card.number if self.current_card else None
            ),
            "previous_card_number": (
                self.previous_card.number if self.previous_card else None
            ),
            "reshuffle_triggered": self.reshuffle_triggered,
            "pending_input": (
                copy.deepcopy(self.pending_input) if self.pending_input else None
            ),
            "next_phase_after_input": self.next_phase_after_input,
            "action_log": copy.deepcopy(self.action_log),
            "_log_counter": self._log_counter,
        }
