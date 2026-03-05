/* ──────────────────────────────────────────────────────────────────────────
   Malakar – Internationalization (EN / ES)
   ────────────────────────────────────────────────────────────────────────── */

const I18N = {
  en: {
    // Top bar
    app_title: "MALAKAR",
    app_subtitle: "Inferno Solo Automa",
    turn_label: "Turn",
    btn_menu: "☰",
    btn_lang: "ES",
    btn_undo: "↩",

    // Welcome
    welcome_title: "MALAKAR",
    welcome_tagline: "Solo Automa Companion for Inferno",
    btn_new_game: "🔥 New Game",
    btn_load_game: "📂 Load Game",

    // Setup
    setup_title: "New Game",
    difficulty_title: "Difficulty",
    diff_normal: "Normal",
    diff_normal_desc: "Both you and Malakar use an Apprentice card.",
    diff_hard: "Hard",
    diff_hard_desc: "You use a Family card. Start with a skull on the indicated Sin Track.",
    diff_demonic: "Demonic",
    diff_demonic_desc: "You use a Family card. Malakar gets an extra starting skull. The suffering begins!",
    btn_start: "Start Game",
    btn_cancel: "Cancel",

    // Game
    btn_advance: "Continue",
    btn_continue: "Continue",
    btn_submit: "Confirm",
    input_header: "📜 Solo Rules",
    setup_header: "📋 Setup Steps",
    phase_setup: "Setup",
    phase_draw_card: "Drawing Card",
    phase_hell_phase: "Hell Phase",
    phase_florence_phase: "Florence Phase",
    phase_turn_end: "Turn End",
    phase_game_over: "Game Over",
    phase_waiting_for_input: "Waiting...",

    // Card section
    current_card: "Current Card",
    deck_remaining: "Deck",
    discard_count: "Discard",
    no_card: "No card drawn yet",

    // Guidance
    guidance_hell: "🔥 Hell Phase",
    guidance_florence: "🏛️ Florence Phase",
    guidance_soul_priority: "Soul Priority",
    guidance_shield: "Shield Priority",
    guidance_arrow: "Arrow Direction",
    guidance_location: "Priority Location",

    // Info
    info_turn: "Turn",
    info_difficulty: "Difficulty",
    info_deck: "Cards in Deck",
    info_discard: "Cards in Discard",

    // Log
    log_title: "📜 Action Log",

    // Menu
    menu_title: "Menu",
    menu_save: "💾 Save Game",
    menu_load: "📂 Load Game",
    menu_download: "⬇️ Download Save",
    menu_upload: "⬆️ Upload Save",
    menu_new: "🔥 New Game",
    menu_rules: "📖 Quick Rules",

    // Save/Load
    save_title: "Save Game",
    load_title: "Load Game",
    save_name: "Save name",
    btn_save: "Save",
    btn_load: "Load",
    btn_delete: "Delete",
    no_saves: "No saved games found.",

    // Rules summary
    rules_title: "Malakar Quick Rules",
    rules_text: `• Malakar only borrows Drachmas to cross the River Acheron or pay a player.
• He never bribes Charon for 2 Drachmas and never places 2 family members in a Special Location.
• He never plays with Guardians — instead gains 2 Drachmas.
• He does NOT lose Infamy from Family Council.
• His starting Fraud cards stay face-down until end of game.
• Reshuffle card: reorganize Tower using PREVIOUS card priorities, then reshuffle.
• Beige Barrel = Yellow priority, Burgundy Barrel = Purple priority.`,
  },

  es: {
    // Top bar
    app_title: "MALAKAR",
    app_subtitle: "Automa Solitario de Inferno",
    turn_label: "Turno",
    btn_menu: "☰",
    btn_lang: "EN",
    btn_undo: "↩",

    // Welcome
    welcome_title: "MALAKAR",
    welcome_tagline: "Compañero Automa Solitario para Inferno",
    btn_new_game: "🔥 Nueva Partida",
    btn_load_game: "📂 Cargar Partida",

    // Setup
    setup_title: "Nueva Partida",
    difficulty_title: "Dificultad",
    diff_normal: "Normal",
    diff_normal_desc: "Tanto tú como Malakar usan una carta de Aprendiz.",
    diff_hard: "Difícil",
    diff_hard_desc: "Usas una carta de Familia. Empiezas con una calavera en la Pista del Pecado indicada.",
    diff_demonic: "Demoníaco",
    diff_demonic_desc: "Usas una carta de Familia. Malakar obtiene una calavera adicional. ¡El sufrimiento comienza!",
    btn_start: "Iniciar Partida",
    btn_cancel: "Cancelar",

    // Game
    btn_advance: "Continuar",
    btn_continue: "Continuar",
    btn_submit: "Confirmar",
    input_header: "📜 Reglas Solo",
    setup_header: "📋 Pasos de Preparación",
    phase_setup: "Preparación",
    phase_draw_card: "Robando Carta",
    phase_hell_phase: "Fase del Infierno",
    phase_florence_phase: "Fase de Florencia",
    phase_turn_end: "Fin de Turno",
    phase_game_over: "Fin del Juego",
    phase_waiting_for_input: "Esperando...",

    // Card section
    current_card: "Carta Actual",
    deck_remaining: "Mazo",
    discard_count: "Descarte",
    no_card: "Ninguna carta robada aún",

    // Guidance
    guidance_hell: "🔥 Fase del Infierno",
    guidance_florence: "🏛️ Fase de Florencia",
    guidance_soul_priority: "Prioridad de Almas",
    guidance_shield: "Prioridad de Escudos",
    guidance_arrow: "Dirección de Flecha",
    guidance_location: "Ubicación Prioritaria",

    // Info
    info_turn: "Turno",
    info_difficulty: "Dificultad",
    info_deck: "Cartas en Mazo",
    info_discard: "Cartas en Descarte",

    // Log
    log_title: "📜 Registro de Acciones",

    // Menu
    menu_title: "Menú",
    menu_save: "💾 Guardar Partida",
    menu_load: "📂 Cargar Partida",
    menu_download: "⬇️ Descargar Guardado",
    menu_upload: "⬆️ Subir Guardado",
    menu_new: "🔥 Nueva Partida",
    menu_rules: "📖 Reglas Rápidas",

    // Save/Load
    save_title: "Guardar Partida",
    load_title: "Cargar Partida",
    save_name: "Nombre del guardado",
    btn_save: "Guardar",
    btn_load: "Cargar",
    btn_delete: "Eliminar",
    no_saves: "No se encontraron partidas guardadas.",

    // Rules summary
    rules_title: "Reglas Rápidas de Malakar",
    rules_text: `• Malakar solo pide prestado Dracmas para cruzar el Río Aqueronte o pagar a un jugador.
• Nunca soborna a Caronte con 2 Dracmas y nunca coloca 2 miembros en un Lugar Especial.
• Nunca juega con Guardianes — en su lugar gana 2 Dracmas.
• NO pierde Infamia por Consejo Familiar.
• Sus cartas de Fraude iniciales permanecen boca abajo hasta el final.
• Carta Rebarajar: reorganiza Torre con prioridades de carta ANTERIOR, luego rebaraja.
• Barril beige = prioridad Amarillo, Barril burdeos = prioridad Púrpura.`,
  },
};

// Soul/sin color emoji icons
const SOUL_ICONS = {
  beige: "🏛️",
  purple: "💜",
  green: "💚",
  yellow: "💛",
  blue: "💙",
  orange: "🧡",
  red: "❤️",
  gray: "🩶",
  ice_blue: "🩵",
};

let currentLang = localStorage.getItem("malakar_lang") || "en";

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || I18N.en[key] || key;
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    const text = t(key);
    if (text) el.textContent = text;
  });
}

function toggleLang() {
  currentLang = currentLang === "en" ? "es" : "en";
  localStorage.setItem("malakar_lang", currentLang);
  applyI18n();
  // Notify backend
  API.post("/api/game/language", { language: currentLang });
  // Refresh UI if game is active
  if (typeof refreshState === "function" && gameActive) {
    refreshState();
  }
}
