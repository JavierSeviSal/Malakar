"""Game engine for the Malakar automa — card-guided solo assistant for Inferno.

Handles the turn flow:
  SETUP → DRAW_CARD → HELL_PHASE → FLORENCE_PHASE → TURN_END → DRAW_CARD → ...

The engine does NOT track full board state. It draws cards from the solo deck,
presents Malakar's priorities to the player, and waits for acknowledgment
before proceeding.
"""

from __future__ import annotations
from typing import Optional

from .models import (
    GameState,
    GamePhase,
    DifficultyMode,
    SoloCard,
    Deck,
)
from .cards import create_solo_deck, get_all_cards_map


class GameEngine:
    """Manages the state machine and executes the Malakar solo automa."""

    def __init__(self, state: Optional[GameState] = None):
        self.state = state or GameState()
        self._cards_map: dict[int, SoloCard] | None = None

    def _get_cards_map(self) -> dict[int, SoloCard]:
        """Lazy-load the master card lookup."""
        if self._cards_map is None:
            self._cards_map = get_all_cards_map()
        return self._cards_map

    # ─── Game setup ──────────────────────────────────────────────────────

    def new_game(
        self,
        difficulty: str = "normal",
        language: str = "en",
    ) -> dict:
        """Initialize a new game."""
        self.state = GameState()
        self.state.difficulty = DifficultyMode(difficulty)
        self.state.language = language

        # Create and shuffle the solo deck
        deck = create_solo_deck()
        deck.shuffle()
        self.state.solo_deck = deck
        self.state.discard_pile = Deck(name="discard")

        self.state.phase = GamePhase.SETUP
        self.state.turn_number = 0
        self.state.current_card = None
        self.state.previous_card = None

        # Log setup
        diff = self.state.difficulty
        self.state.log(
            "New game started!",
            "setup",
            "¡Nueva partida iniciada!",
        )
        self.state.log(
            f"Difficulty: {diff.label()}",
            "setup",
            f"Dificultad: {diff.label_es()}",
        )

        if diff == DifficultyMode.NORMAL:
            self.state.log(
                "Normal Mode: Both you and Malakar use an Apprentice card.",
                "setup",
                "Modo Normal: Tanto tú como Malakar usan una carta de Aprendiz.",
            )
        elif diff == DifficultyMode.HARD:
            self.state.log(
                "Hard Mode: You use a Family card. Place a starting skull on the Sin Track shown on your card.",
                "setup",
                "Modo Difícil: Usas una carta de Familia. Coloca una calavera inicial en la Pista del Pecado indicada en tu carta.",
            )
        elif diff == DifficultyMode.DEMONIC:
            self.state.log(
                "Demonic Mode: You use a Family card. Malakar places an additional skull on the Sin Track shown on your Apprentice card. The suffering has just begun!",
                "setup",
                "Modo Demoníaco: Usas una carta de Familia. Malakar coloca una calavera adicional en la Pista del Pecado indicada en tu carta de Aprendiz. ¡El sufrimiento acaba de comenzar!",
            )

        self.state.log(
            f"Solo deck: {self.state.solo_deck.size()} cards shuffled.",
            "setup",
            f"Mazo solitario: {self.state.solo_deck.size()} cartas barajadas.",
        )

        self.state.log(
            "Remember: Malakar places his 4 colored disks on the Walls of Dis at the start.",
            "setup",
            "Recuerda: Malakar coloca sus 4 discos de colores en las Murallas de Dis al inicio.",
        )

        self.state.log(
            "Place skulls of an unused color next to Infamy points in each Hell circle (except beige).",
            "setup",
            "Coloca calaveras de un color no usado junto a los puntos de Infamia en cada círculo del Infierno (excepto beige).",
        )

        # Build setup prompt from logged messages so player can review
        setup_entries = [
            e for e in self.state.action_log if e.get("category") == "setup"
        ]
        prompt_en = (
            "GAME SETUP\n\n"
            + "\n".join(f"• {e['message']}" for e in setup_entries)
            + "\n\nPrepare the board as described above, then click Continue."
        )
        prompt_es = (
            "PREPARACIÓN DEL JUEGO\n\n"
            + "\n".join(f"• {e.get('message_es', e['message'])}" for e in setup_entries)
            + "\n\nPrepara el tablero como se describe arriba, luego haz clic en Continuar."
        )

        self.state.pending_input = {
            "type": "setup_done",
            "prompt": prompt_en,
            "prompt_es": prompt_es,
            "fields": [],
        }
        self.state.phase = GamePhase.WAITING_FOR_INPUT
        self.state.next_phase_after_input = GamePhase.SETUP.value

        return {
            "status": "ok",
            "message": "Game initialized. Review setup steps, then click Continue.",
            "input_needed": self.state.pending_input,
        }

    # ─── Phase execution ─────────────────────────────────────────────────

    def advance_phase(self) -> dict:
        """Advance to the next phase in the turn cycle."""
        self.state.save_snapshot()

        handlers = {
            GamePhase.SETUP: self._do_setup_advance,
            GamePhase.DRAW_CARD: self._do_draw_card,
            GamePhase.HELL_PHASE: self._do_hell_phase,
            GamePhase.FLORENCE_PHASE: self._do_florence_phase,
            GamePhase.TURN_END: self._do_turn_end,
            GamePhase.WAITING_FOR_INPUT: self._do_resume_after_input,
        }

        handler = handlers.get(self.state.phase)
        if handler is None:
            return {
                "status": "error",
                "message": f"Cannot advance from {self.state.phase.value}",
            }

        return handler()

    def process_input(self, input_data: dict) -> dict:
        """Process player input (acknowledgements, confirmations)."""
        self.state.save_snapshot()
        input_type = input_data.get("type", "")
        return self._dispatch_input(input_type, input_data)

    # ─── Undo ────────────────────────────────────────────────────────────

    def undo(self) -> dict:
        """Restore the previous snapshot."""
        if not self.state._undo_snapshot:
            return {"status": "error", "message": "Nothing to undo."}

        snap = self.state._undo_snapshot
        cards_map = self._get_cards_map()

        # Restore basic fields
        self.state.turn_number = snap["turn_number"]
        self.state.phase = GamePhase(snap["phase"])
        self.state.difficulty = DifficultyMode(snap["difficulty"])
        self.state.language = snap["language"]
        self.state.reshuffle_triggered = snap["reshuffle_triggered"]
        self.state.pending_input = snap["pending_input"]
        self.state.next_phase_after_input = snap["next_phase_after_input"]
        self.state.action_log = snap["action_log"]
        self.state._log_counter = snap["_log_counter"]

        # Restore cards
        self.state.current_card = (
            cards_map.get(snap["current_card_number"])
            if snap["current_card_number"]
            else None
        )
        self.state.previous_card = (
            cards_map.get(snap["previous_card_number"])
            if snap["previous_card_number"]
            else None
        )

        # Restore decks
        def _rebuild_deck(snap_deck: dict) -> Deck:
            return Deck(
                cards=[
                    cards_map[n] for n in snap_deck["card_numbers"] if n in cards_map
                ],
                name=snap_deck["name"],
            )

        self.state.solo_deck = _rebuild_deck(snap["solo_deck"])
        self.state.discard_pile = _rebuild_deck(snap["discard_pile"])
        self.state._undo_snapshot = None

        return {"status": "ok", "message": "Undo successful."}

    # ─── Phase handlers ──────────────────────────────────────────────────

    def _do_setup_advance(self) -> dict:
        """Transition from SETUP to the first card draw."""
        self.state.phase = GamePhase.DRAW_CARD
        self.state.log(
            "Setup complete. Drawing the first card...",
            "phase",
            "Preparación completa. Robando la primera carta...",
        )
        return self._do_draw_card()

    def _do_draw_card(self) -> dict:
        """Draw the next card from the solo deck."""
        card = self.state.solo_deck.draw()

        if card is None:
            # Deck empty — shouldn't happen as reshuffle card handles this
            self.state.phase = GamePhase.GAME_OVER
            self.state.log(
                "Solo deck is empty. Game over!",
                "error",
                "El mazo solitario está vacío. ¡Fin del juego!",
            )
            return {"status": "game_over", "message": "Solo deck is empty."}

        # Check for reshuffle card
        if card.is_reshuffle:
            return self._handle_reshuffle(card)

        # Normal game card
        self.state.previous_card = self.state.current_card
        self.state.current_card = card
        self.state.turn_number += 1

        self.state.log(
            f"Turn {self.state.turn_number}: Drew card #{card.number}.",
            "draw",
            f"Turno {self.state.turn_number}: Robada carta #{card.number}.",
        )

        # Proceed to Hell Phase
        self.state.phase = GamePhase.HELL_PHASE
        return self._present_hell_phase()

    def _handle_reshuffle(self, reshuffle_card: SoloCard) -> dict:
        """Handle the reshuffle card: reshuffle deck, draw again."""
        self.state.reshuffle_triggered = True

        self.state.log(
            "🔄 Reshuffle card drawn! Shuffling deck and drawing again...",
            "reshuffle",
            "🔄 ¡Carta de Rebarajar robada! Barajando mazo y robando de nuevo...",
        )

        # Collect discard pile + remaining solo deck into new deck
        all_cards = []
        all_cards.extend(self.state.discard_pile.clear())
        all_cards.extend(self.state.solo_deck.clear())
        # Add the reshuffle card back
        all_cards.append(reshuffle_card)

        self.state.solo_deck = Deck(cards=all_cards, name="solo")
        self.state.solo_deck.shuffle()
        self.state.discard_pile = Deck(name="discard")

        # Prompt player to acknowledge reshuffle
        self.state.pending_input = {
            "type": "acknowledge_reshuffle",
            "prompt": "Reshuffle card drawn! All discards have been shuffled back into the deck.\n\nClick Continue to draw the next card.",
            "prompt_es": "¡Carta de Rebarajar robada! Todos los descartes se han barajado de vuelta al mazo.\n\nHaz clic en Continuar para robar la siguiente carta.",
            "fields": [],
        }
        self.state.phase = GamePhase.WAITING_FOR_INPUT
        self.state.next_phase_after_input = GamePhase.DRAW_CARD.value
        return {
            "status": "waiting",
            "input_needed": self.state.pending_input,
        }

    def _present_hell_phase(self) -> dict:
        """Present the Hell Phase guidance to the player."""
        card = self.state.current_card
        lang = self.state.language

        if not card or card.is_reshuffle:
            return {"status": "error", "message": "No active card for Hell Phase."}

        # Build the Hell Phase guidance text
        soul_colors = ", ".join(
            f"{c.emoji()} {c.label() if lang == 'en' else c.label_es()}"
            for c in card.soul_priority
        )
        shield_list = ", ".join(
            f"{s.emoji()} {s.label() if lang == 'en' else s.label_es()}"
            for s in card.shield_priority
        )
        direction = card.arrow_direction
        dir_label = "far left" if direction == "left" else "far right"
        dir_label_es = "extremo izquierdo" if direction == "left" else "extremo derecho"

        prompt_en = (
            f"HELL PHASE — Card #{card.number}\n\n"
            f"Malakar moves a Soul in Hell following these priorities:\n\n"
            f"1. Choose a raised Soul that can descend onto its matching color.\n"
            f"   → If multiple: choose the one on the LOWEST circle.\n\n"
            f"2. Choose a Soul from the Graveyard (pay 1 Drachma) that can descend onto its matching color.\n"
            f"   → If only beige can be placed on its color, choose it.\n"
            f"   → If no Drachmas, borrow first.\n\n"
            f"3. If no Drachmas left and a raised Soul can move: choose one that CANNOT descend onto its color.\n"
            f"   → If multiple: choose the one on the HIGHEST circle that descends the LEAST.\n\n"
            f"4. Choose a Soul from the Graveyard (pay 1 Drachma) that cannot descend onto its color.\n"
            f"   → Place on the highest possible circle.\n\n"
            f"TIE-BREAKING:\n"
            f"  Color priority: {soul_colors}\n"
            f"  Shield priority: {shield_list}\n"
            f"  Arrow placement: {dir_label} of the circle\n\n"
            f"FIRST SOUL BONUS: When Malakar lays his first Soul in a circle, remove the skull marker and advance his skull on the matching Sin Track.\n\n"
            f"Resolve the Hell Phase on the board, then click Continue."
        )

        prompt_es = (
            f"FASE DEL INFIERNO — Carta #{card.number}\n\n"
            f"Malakar mueve un Alma en el Infierno siguiendo estas prioridades:\n\n"
            f"1. Elige un Alma levantada que pueda descender a su color correspondiente.\n"
            f"   → Si hay varias: elige la del círculo MÁS BAJO.\n\n"
            f"2. Elige un Alma del Cementerio (paga 1 Dracma) que pueda descender a su color.\n"
            f"   → Si solo la beige puede colocarse en su color, elígela.\n"
            f"   → Si no tiene Dracmas, pide prestado primero.\n\n"
            f"3. Si no quedan Dracmas y un Alma levantada puede moverse: elige una que NO pueda descender a su color.\n"
            f"   → Si hay varias: elige la del círculo MÁS ALTO que descienda MENOS.\n\n"
            f"4. Elige un Alma del Cementerio (paga 1 Dracma) que no pueda descender a su color.\n"
            f"   → Colócala en el círculo más alto posible.\n\n"
            f"DESEMPATE:\n"
            f"  Prioridad de color: {soul_colors}\n"
            f"  Prioridad de escudo: {shield_list}\n"
            f"  Dirección de flecha: {dir_label_es} del círculo\n\n"
            f"BONIFICACIÓN PRIMERA ALMA: Cuando Malakar coloca su primera Alma en un círculo, retira el marcador de calavera y avanza su calavera en la Pista del Pecado correspondiente.\n\n"
            f"Resuelve la Fase del Infierno en el tablero, luego haz clic en Continuar."
        )

        self.state.pending_input = {
            "type": "hell_phase_done",
            "prompt": prompt_en,
            "prompt_es": prompt_es,
            "fields": [],
        }
        self.state.phase = GamePhase.WAITING_FOR_INPUT
        self.state.next_phase_after_input = GamePhase.FLORENCE_PHASE.value

        return {
            "status": "waiting",
            "input_needed": self.state.pending_input,
        }

    def _do_hell_phase(self) -> dict:
        """Transition into the Hell Phase (presents guidance)."""
        return self._present_hell_phase()

    def _present_florence_phase(self) -> dict:
        """Present the Florence Phase guidance to the player."""
        card = self.state.current_card
        lang = self.state.language

        if not card or card.is_reshuffle:
            return {"status": "error", "message": "No active card for Florence Phase."}

        soul_colors = ", ".join(
            f"{c.emoji()} {c.label() if lang == 'en' else c.label_es()}"
            for c in card.soul_priority
        )

        shield_list = ", ".join(
            f"{s.emoji()} {s.label() if lang == 'en' else s.label_es()}"
            for s in card.shield_priority
        )

        loc_type = card.priority_location
        if loc_type == "special":
            loc_en = "Special Location"
            loc_es = "Ubicación Especial"
        else:
            loc_en = "Free-access Location"
            loc_es = "Ubicación de Libre Acceso"

        prompt_en = (
            f"FLORENCE PHASE — Card #{card.number}\n\n"
            f"Malakar performs the Florence Phase at a priority location:\n"
            f"  Priority: {loc_en}\n\n"
            f"He prioritizes ACCUSING if conditions are met, otherwise performs the LOCATION ACTION.\n"
            f"If neither is possible at the priority area, tries the other area.\n"
            f"If he can place an Urchin at a Special location to avoid paying a Florin, he does so.\n\n"
            f"LOCATION ACTIONS SUMMARY:\n"
            f"  • Haystack: Adopt an Urchin (if any remain)\n"
            f"  • Banquet: Add a Tower floor (if any remain)\n"
            f"  • Bank: Gain Florins (always valid)\n"
            f"  • Courtyard: Accuse here normally; only do action if has family in Tower or can't accuse/act at Special\n"
            f"  • Bonfire: Exchange, Phlegethon, River Styx (if possible)\n"
            f"  • Wall: Exchange, Barrel movement (if possible), Fraud card (if possible)\n"
            f"  • Market: Steal a Barrel (if has free Tower space and Barrels remain)\n"
            f"  • Palace: Host a Guest (if has free Tower space and Guests remain)\n\n"
            f"FAMILY COUNCIL (if nothing possible):\n"
            f"  Malakar loses NO Infamy. Try these in order:\n"
            f"  1) Move family member to home  2) Return resource/Guest  3) (other)\n\n"
            f"PHLEGETHON: Move cube right on a track not at max. Priority:\n"
            f"  1) Track with his Diploma  2) His skull ahead of yours  3) Same level\n\n"
            f"RIVER STYX: Send back max Souls, advance on priority color track.\n\n"
            f"TOWER PLACEMENT:\n"
            f"  Placing: Level without Guest → Level with existing Barrel/member → Lowest level\n"
            f"  Removing: Level with full Guest → Level with Guest + free spot → Highest level\n"
            f"  Guests: As high as possible, on levels with remaining space or without existing Guest\n\n"
            f"COLOR PRIORITIES: {soul_colors}\n"
            f"SHIELD PRIORITIES: {shield_list}\n\n"
            f"Note: Beige Barrel = Yellow Soul priority; Burgundy Barrel = Purple Soul priority.\n\n"
            f"Resolve the Florence Phase on the board, then click Continue."
        )

        prompt_es = (
            f"FASE DE FLORENCIA — Carta #{card.number}\n\n"
            f"Malakar realiza la Fase de Florencia en una ubicación prioritaria:\n"
            f"  Prioridad: {loc_es}\n\n"
            f"Prioriza ACUSAR si se cumplen las condiciones, sino realiza la ACCIÓN del lugar.\n"
            f"Si no es posible en el área prioritaria, intenta en la otra.\n"
            f"Si puede colocar un Pilluelo en un lugar Especial para no pagar un Florín, lo hace.\n\n"
            f"RESUMEN DE ACCIONES:\n"
            f"  • Pajar: Adoptar un Pilluelo (si quedan)\n"
            f"  • Banquete: Añadir piso a la Torre (si quedan)\n"
            f"  • Banco: Obtener Florines (siempre válido)\n"
            f"  • Patio: Acusar normalmente; solo acción si tiene familia en Torre o no puede acusar/actuar en Especial\n"
            f"  • Hoguera: Cambiar, Flegetonte, Río Estigia (si es posible)\n"
            f"  • Muralla: Cambiar, mover Barril (si es posible), carta Fraude (si es posible)\n"
            f"  • Mercado: Robar un Barril (si tiene espacio en Torre y quedan Barriles)\n"
            f"  • Palacio: Alojar un Invitado (si tiene espacio en Torre y quedan Invitados)\n\n"
            f"CONSEJO FAMILIAR (si nada es posible):\n"
            f"  Malakar NO pierde Infamia. Intenta en orden:\n"
            f"  1) Mover familiar a casa  2) Devolver recurso/Invitado  3) (otro)\n\n"
            f"FLEGETONTE: Mover cubo a la derecha en una pista no al máximo. Prioridad:\n"
            f"  1) Pista con su Diploma  2) Su calavera por delante  3) Mismo nivel\n\n"
            f"RÍO ESTIGIA: Devolver máx. Almas, avanzar en pista de color prioritario.\n\n"
            f"COLOCACIÓN EN TORRE:\n"
            f"  Colocando: Nivel sin Invitado → Nivel con Barril/miembro existente → Nivel más bajo\n"
            f"  Retirando: Nivel con Invitado lleno → Nivel con Invitado con hueco → Nivel más alto\n"
            f"  Invitados: Lo más alto posible, en niveles con espacio o sin Invitado existente\n\n"
            f"PRIORIDADES DE COLOR: {soul_colors}\n"
            f"PRIORIDADES DE ESCUDO: {shield_list}\n\n"
            f"Nota: Barril beige = prioridad Alma amarilla; Barril burdeos = prioridad Alma púrpura.\n\n"
            f"Resuelve la Fase de Florencia en el tablero, luego haz clic en Continuar."
        )

        self.state.pending_input = {
            "type": "florence_phase_done",
            "prompt": prompt_en,
            "prompt_es": prompt_es,
            "fields": [],
        }
        self.state.phase = GamePhase.WAITING_FOR_INPUT
        self.state.next_phase_after_input = GamePhase.TURN_END.value

        return {
            "status": "waiting",
            "input_needed": self.state.pending_input,
        }

    def _do_florence_phase(self) -> dict:
        """Transition into the Florence Phase (presents guidance)."""
        return self._present_florence_phase()

    def _do_turn_end(self) -> dict:
        """End the current turn: discard the card and prepare for next draw."""
        card = self.state.current_card

        if card and not card.is_reshuffle:
            self.state.discard_pile.place_under(card)
            self.state.log(
                f"Turn {self.state.turn_number} complete. Card #{card.number} discarded.",
                "turn_end",
                f"Turno {self.state.turn_number} completo. Carta #{card.number} descartada.",
            )

        # Ask if the game should continue or if Dante has reached the end
        lang = self.state.language
        self.state.pending_input = {
            "type": "turn_end_check",
            "prompt": "Has Dante reached his final stop? (End the game?)",
            "prompt_es": "¿Ha llegado Dante a su última parada? (¿Terminar el juego?)",
            "fields": [
                {
                    "name": "game_over",
                    "label": "End the game" if lang == "en" else "Terminar el juego",
                    "label_es": "Terminar el juego",
                    "type": "select",
                    "options": [
                        {
                            "value": "no",
                            "label": (
                                "No, continue playing"
                                if lang == "en"
                                else "No, seguir jugando"
                            ),
                        },
                        {
                            "value": "yes",
                            "label": (
                                "Yes, Dante has reached the end"
                                if lang == "en"
                                else "Sí, Dante ha llegado al final"
                            ),
                        },
                    ],
                    "default": "no",
                }
            ],
        }
        self.state.phase = GamePhase.WAITING_FOR_INPUT
        self.state.next_phase_after_input = GamePhase.DRAW_CARD.value

        return {
            "status": "waiting",
            "input_needed": self.state.pending_input,
        }

    def _do_resume_after_input(self) -> dict:
        """Resume from WAITING_FOR_INPUT when there's a next phase set."""
        next_phase = self.state.next_phase_after_input
        if not next_phase:
            return {"status": "error", "message": "No phase to resume to."}

        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase(next_phase)

        # Re-dispatch to the new phase handler
        return self.advance_phase()

    # ─── Input dispatch ──────────────────────────────────────────────────

    def _dispatch_input(self, input_type: str, data: dict) -> dict:
        """Route player input to the appropriate handler."""

        if input_type == "setup_done":
            return self._handle_setup_done(data)

        elif input_type == "hell_phase_done":
            return self._handle_hell_phase_done(data)

        elif input_type == "florence_phase_done":
            return self._handle_florence_phase_done(data)

        elif input_type == "acknowledge_reshuffle":
            return self._handle_acknowledge_reshuffle(data)

        elif input_type == "turn_end_check":
            return self._handle_turn_end_check(data)

        elif input_type == "acknowledge":
            return self._handle_acknowledge(data)

        return {"status": "error", "message": f"Unknown input type: {input_type}"}

    def _handle_setup_done(self, data: dict) -> dict:
        """Player confirmed setup is complete — advance to first card draw."""
        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase.SETUP
        return self._do_setup_advance()

    def _handle_hell_phase_done(self, data: dict) -> dict:
        """Player confirmed Hell Phase is resolved."""
        self.state.log(
            f"Hell Phase resolved for card #{self.state.current_card.number if self.state.current_card else '?'}.",
            "hell",
            f"Fase del Infierno resuelta para carta #{self.state.current_card.number if self.state.current_card else '?'}.",
        )
        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase.FLORENCE_PHASE
        return self._present_florence_phase()

    def _handle_florence_phase_done(self, data: dict) -> dict:
        """Player confirmed Florence Phase is resolved."""
        self.state.log(
            f"Florence Phase resolved for card #{self.state.current_card.number if self.state.current_card else '?'}.",
            "florence",
            f"Fase de Florencia resuelta para carta #{self.state.current_card.number if self.state.current_card else '?'}.",
        )
        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase.TURN_END
        return self._do_turn_end()

    def _handle_acknowledge_reshuffle(self, data: dict) -> dict:
        """Player acknowledged the reshuffle and tower reorganization."""
        self.state.reshuffle_triggered = False
        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase.DRAW_CARD
        return self._do_draw_card()

    def _handle_turn_end_check(self, data: dict) -> dict:
        """Player answered whether the game should end."""
        game_over = data.get("game_over", "no")

        if game_over == "yes":
            self.state.phase = GamePhase.GAME_OVER
            self.state.pending_input = None
            self.state.next_phase_after_input = None

            self.state.log(
                "🏁 Game Over! Dante has reached the final stop. Proceed to final scoring.",
                "game_over",
                "🏁 ¡Fin del juego! Dante ha llegado a la última parada. Procede al recuento final.",
            )

            self.state.log(
                "ENDGAME REMINDERS:\n"
                "• Malakar's starting Fraud cards are now revealed.\n"
                "• Perform Instant Effects immediately, End of Game Effects during scoring.\n"
                "• Malakar always chooses the first possible reward for each Effect.\n"
                "• For ½ Diplomas: Malakar places each Diploma on the Track giving most points (where he doesn't have one), tie-broken by current card colors.\n"
                "• Count points normally (Fraud cards → Phlegethon adjustment → Additional Diplomas → Diploma scoring → Loans → No Reputation points for Malakar).",
                "game_over",
                "RECORDATORIOS DE FIN DE PARTIDA:\n"
                "• Las cartas de Fraude iniciales de Malakar se revelan ahora.\n"
                "• Realiza los Efectos Instantáneos inmediatamente, los Efectos de Fin de Partida durante el recuento.\n"
                "• Malakar siempre elige la primera recompensa posible para cada Efecto.\n"
                "• Para ½ Diplomas: Malakar coloca cada Diploma en la Pista que le dé más puntos (donde no tenga uno), desempatando con los colores de la carta actual.\n"
                "• Cuenta puntos normalmente (Cartas Fraude → Ajuste Flegetonte → Diplomas adicionales → Puntuación Diplomas → Préstamos → Sin puntos de Reputación para Malakar).",
            )

            return {
                "status": "game_over",
                "message": "Game over! Proceed to final scoring.",
            }

        # Continue playing
        self.state.pending_input = None
        self.state.next_phase_after_input = None
        self.state.phase = GamePhase.DRAW_CARD
        return self._do_draw_card()

    def _handle_acknowledge(self, data: dict) -> dict:
        """Generic acknowledgement — proceed to the next phase."""
        next_phase = self.state.next_phase_after_input
        self.state.pending_input = None
        self.state.next_phase_after_input = None

        if next_phase:
            self.state.phase = GamePhase(next_phase)
            return self.advance_phase()

        return {"status": "ok", "message": "Acknowledged."}
