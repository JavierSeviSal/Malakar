"""Save/load game state to/from JSON files."""

from __future__ import annotations

import os
import json
import time
from datetime import datetime
from typing import Optional

from .models import (
    GameState,
    GamePhase,
    DifficultyMode,
    SoloCard,
    SoulColor,
    LocationName,
    Deck,
)
from .cards import create_solo_deck, get_all_cards_map

SAVES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves"
)


def ensure_saves_dir(saves_dir: str | None = None):
    os.makedirs(saves_dir or SAVES_DIR, exist_ok=True)


def save_game(
    state: GameState, slot_name: str = "autosave", saves_dir: str | None = None
) -> dict:
    """Save the full game state to a JSON file."""
    target = saves_dir or SAVES_DIR
    ensure_saves_dir(target)

    save_data = {
        "meta": {
            "slot_name": slot_name,
            "timestamp": time.time(),
            "date": datetime.now().isoformat(),
            "turn": state.turn_number,
            "phase": state.phase.value,
        },
        "state": _serialize_full_state(state),
    }

    filepath = os.path.join(target, f"{slot_name}.json")
    with open(filepath, "w") as f:
        json.dump(save_data, f, indent=2)

    return {
        "status": "ok",
        "message": f"Game saved to '{slot_name}'.",
        "filepath": filepath,
    }


def load_game(slot_name: str, saves_dir: str | None = None) -> Optional[GameState]:
    """Load game state from a JSON file."""
    target = saves_dir or SAVES_DIR
    ensure_saves_dir(target)
    filepath = os.path.join(target, f"{slot_name}.json")

    if not os.path.exists(filepath):
        return None

    with open(filepath, "r") as f:
        save_data = json.load(f)

    return _deserialize_full_state(save_data["state"])


def list_saves(saves_dir: str | None = None) -> list[dict]:
    """List all saved games with metadata."""
    target = saves_dir or SAVES_DIR
    ensure_saves_dir(target)
    saves = []
    for filename in sorted(os.listdir(target)):
        if filename.endswith(".json"):
            filepath = os.path.join(target, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                meta = data.get("meta", {})
                saves.append(
                    {
                        "slot_name": meta.get("slot_name", filename[:-5]),
                        "date": meta.get("date", ""),
                        "turn": meta.get("turn", 0),
                        "phase": meta.get("phase", ""),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue
    return saves


def delete_save(slot_name: str, saves_dir: str | None = None) -> dict:
    """Delete a saved game."""
    target = saves_dir or SAVES_DIR
    filepath = os.path.join(target, f"{slot_name}.json")

    if os.path.exists(filepath):
        os.remove(filepath)
        return {"status": "ok", "message": f"Save '{slot_name}' deleted."}
    return {"status": "error", "message": f"Save '{slot_name}' not found."}


# ─── Serialization ───────────────────────────────────────────────────────────


def _serialize_card_ref(card: SoloCard | None) -> dict | None:
    """Serialize a card as a minimal reference."""
    if card is None:
        return None
    return {"number": card.number}


def _serialize_deck(deck: Deck) -> dict:
    """Serialize a deck to a list of card number references."""
    return {
        "name": deck.name,
        "card_numbers": [c.number for c in deck.cards],
    }


def _serialize_full_state(state: GameState) -> dict:
    """Serialize the full game state to a JSON-compatible dict."""
    return {
        "turn_number": state.turn_number,
        "phase": state.phase.value,
        "difficulty": state.difficulty.value,
        "language": state.language,
        "solo_deck": _serialize_deck(state.solo_deck),
        "discard_pile": _serialize_deck(state.discard_pile),
        "current_card": _serialize_card_ref(state.current_card),
        "previous_card": _serialize_card_ref(state.previous_card),
        "reshuffle_triggered": state.reshuffle_triggered,
        "pending_input": state.pending_input,
        "next_phase_after_input": state.next_phase_after_input,
        "action_log": state.action_log,
        "_log_counter": state._log_counter,
    }


def _deserialize_full_state(data: dict) -> GameState:
    """Reconstruct a GameState from a serialized dict."""
    cards_map = get_all_cards_map()

    state = GameState()
    state.turn_number = data.get("turn_number", 0)
    state.phase = GamePhase(data.get("phase", "setup"))
    state.difficulty = DifficultyMode(data.get("difficulty", "normal"))
    state.language = data.get("language", "en")
    state.reshuffle_triggered = data.get("reshuffle_triggered", False)
    state.pending_input = data.get("pending_input")
    state.next_phase_after_input = data.get("next_phase_after_input")
    state.action_log = data.get("action_log", [])
    state._log_counter = data.get("_log_counter", 0)

    # Rebuild current/previous card
    cur = data.get("current_card")
    state.current_card = cards_map.get(cur["number"]) if cur else None
    prev = data.get("previous_card")
    state.previous_card = cards_map.get(prev["number"]) if prev else None

    # Rebuild decks
    def _rebuild_deck(deck_data: dict) -> Deck:
        if not deck_data:
            return Deck(name="unknown")
        return Deck(
            cards=[
                cards_map[n]
                for n in deck_data.get("card_numbers", [])
                if n in cards_map
            ],
            name=deck_data.get("name", "unknown"),
        )

    state.solo_deck = _rebuild_deck(data.get("solo_deck", {}))
    state.discard_pile = _rebuild_deck(data.get("discard_pile", {}))

    return state
