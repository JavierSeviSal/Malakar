/* ═══════════════════════════════════════════════════════════════════════
   Malakar — Main Application JS
   Card-guided solo automa companion for Inferno
   ═══════════════════════════════════════════════════════════════════════ */

// ─── Session ID ────────────────────────────────────────────────────────
function _getSessionId() {
  let sid = sessionStorage.getItem("malakar_sid");
  if (!sid) {
    sid = crypto.randomUUID().replace(/-/g, "");
    sessionStorage.setItem("malakar_sid", sid);
  }
  return sid;
}

const API = {
  async post(url, data = {}) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": _getSessionId(),
      },
      credentials: "include",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const text = await res.text();
      console.error(`API POST ${url} failed (${res.status}):`, text);
      throw new Error(`Server error ${res.status}`);
    }
    return res.json();
  },
  async get(url) {
    const res = await fetch(url, {
      cache: "no-store",
      headers: { "X-Session-ID": _getSessionId() },
      credentials: "include",
    });
    if (!res.ok) {
      const text = await res.text();
      console.error(`API GET ${url} failed (${res.status}):`, text);
      throw new Error(`Server error ${res.status}`);
    }
    return res.json();
  },
  async del(url) {
    const res = await fetch(url, {
      method: "DELETE",
      headers: { "X-Session-ID": _getSessionId() },
      credentials: "include",
    });
    if (!res.ok) {
      const text = await res.text();
      console.error(`API DELETE ${url} failed (${res.status}):`, text);
      throw new Error(`Server error ${res.status}`);
    }
    return res.json();
  },
};

// ─── State ─────────────────────────────────────────────────────────────

let gameState = null;
let gameActive = false;

// ─── DOM refs ──────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const welcomeScreen = $("#welcome-screen");
const gameScreen = $("#game-screen");
const menuOverlay = $("#menu-overlay");
const setupOverlay = $("#setup-overlay");
const loadOverlay = $("#load-overlay");
const cardOverlay = $("#card-overlay");
const inputSection = $("#input-section");
const rulesOverlay = $("#rules-overlay");

const turnBadge = $("#turn-badge");
const phaseBadge = $("#phase-badge");
const statusMsg = $("#status-msg");
const btnAdvance = $("#btn-advance");
const btnLang = $("#btn-lang");

// ─── Init ──────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  applyI18n();
  bindEvents();
  tryAutoLoad();
});

function bindEvents() {
  // Welcome
  $("#btn-welcome-new").onclick = () => showOverlay(setupOverlay);
  $("#file-welcome-upload").onchange = uploadSaveFromDevice;

  // Top bar
  $("#btn-menu").onclick = () => showOverlay(menuOverlay);
  $("#btn-undo").onclick = doUndo;
  btnLang.onclick = () => {
    toggleLang();
    btnLang.textContent = t("btn_lang");
    if (gameActive) refreshState();
  };

  // Menu
  $("#btn-menu-new").onclick = () => {
    hideOverlay(menuOverlay);
    showOverlay(setupOverlay);
  };
  $("#btn-menu-save").onclick = () => {
    hideOverlay(menuOverlay);
    showSaveOverlay();
  };
  $("#btn-menu-load").onclick = () => {
    hideOverlay(menuOverlay);
    showLoadOverlay();
  };
  $("#btn-menu-download").onclick = () => {
    hideOverlay(menuOverlay);
    downloadSaveToDevice();
  };
  $("#btn-menu-upload").onchange = (e) => {
    hideOverlay(menuOverlay);
    uploadSaveFromDevice(e);
  };
  $("#btn-menu-rules").onclick = () => {
    hideOverlay(menuOverlay);
    showRulesOverlay();
  };
  $("#btn-close-menu").onclick = () => hideOverlay(menuOverlay);

  // Setup (new game)
  $("#btn-start-game").onclick = startNewGame;
  $("#btn-cancel-setup").onclick = () => hideOverlay(setupOverlay);

  // Difficulty selection
  $$(".difficulty-option").forEach((opt) => {
    opt.onclick = () => {
      $$(".difficulty-option").forEach((o) => o.classList.remove("selected"));
      opt.classList.add("selected");
    };
  });

  // Load overlay
  $("#btn-close-load").onclick = () => hideOverlay(loadOverlay);
  $("#btn-download-save").onclick = downloadSaveToDevice;
  $("#file-upload-save").onchange = uploadSaveFromDevice;

  // Card zoom
  cardOverlay.onclick = (e) => {
    if (e.target !== $("#card-zoom-img")) hideOverlay(cardOverlay);
  };
  $("#btn-close-card").onclick = () => hideOverlay(cardOverlay);

  // Rules overlay
  if ($("#btn-close-rules")) {
    $("#btn-close-rules").onclick = () => hideOverlay(rulesOverlay);
  }

  // Advance phase (also handles submit when waiting for input)
  btnAdvance.onclick = advancePhase;

  // Input submit (hidden button, kept for internal use)
  $("#btn-submit-input").onclick = submitInput;

  // Toggle collapsible input section
  $("#input-header").onclick = toggleInputBody;

  // Collapse input section on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && inputSection.classList.contains("expanded")) {
      collapseInputBody();
    }
  });
}

// ─── Overlays ──────────────────────────────────────────────────────────

function showOverlay(el) {
  if (el) el.classList.remove("hidden");
}
function hideOverlay(el) {
  if (el) el.classList.add("hidden");
}

function showInputSection() {
  inputSection.classList.remove("hidden");
  inputSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
function hideInputSection() {
  inputSection.classList.add("hidden");
  inputSection.classList.remove("expanded");
}
function expandInputBody() {
  inputSection.classList.add("expanded");
  $("#input-header-chevron").textContent = "▾";
}
function collapseInputBody() {
  inputSection.classList.remove("expanded");
  $("#input-header-chevron").textContent = "▸";
}
function toggleInputBody() {
  if (inputSection.classList.contains("expanded")) {
    collapseInputBody();
  } else {
    expandInputBody();
  }
}

// ─── New Game ──────────────────────────────────────────────────────────

async function startNewGame() {
  const selected = $(".difficulty-option.selected");
  const difficulty = selected ? selected.dataset.difficulty : "normal";

  try {
    const result = await API.post("/api/game/new", {
      difficulty,
      language: currentLang,
    });

    hideOverlay(setupOverlay);
    gameActive = true;
    welcomeScreen.classList.add("hidden");
    gameScreen.classList.remove("hidden");

    await refreshState();
    setStatus(result.message);

    // Show setup steps in input section (no auto-advance)
    if (result.input_needed) {
      showInputPrompt(result.input_needed);
    }
  } catch (e) {
    console.error("startNewGame error:", e);
    setStatus("Error starting game. Please try again.");
  }
}

// ─── Game Flow ─────────────────────────────────────────────────────────

async function advancePhase() {
  // Game over — return to welcome screen
  if (gameState && gameState.phase === "game_over") {
    gameScreen.classList.add("hidden");
    welcomeScreen.classList.remove("hidden");
    gameActive = false;
    return;
  }

  // If waiting for input, delegate to submitInput instead
  if (gameState && gameState.phase === "waiting_for_input" && gameState.pending_input) {
    submitInput();
    return;
  }

  btnAdvance.disabled = true;
  try {
    const result = await API.post("/api/game/advance");
    btnAdvance.disabled = false;
    await refreshState();
    setStatus(result.message);

    // Handle waiting for input
    if (result.status === "waiting" && result.input_needed) {
      showInputPrompt(result.input_needed);
    } else {
      hideInputSection();
    }
  } catch (e) {
    console.error("advancePhase error:", e);
    btnAdvance.disabled = false;
    setStatus("Error advancing phase. Please try again.");
    await refreshState();
  }
}

async function submitInput() {
  const formData = collectInputData();
  if (!formData) return;

  hideInputSection();
  try {
    const result = await API.post("/api/game/input", formData);
    await refreshState();
    setStatus(result.message);

    if (result.status === "waiting" && result.input_needed) {
      showInputPrompt(result.input_needed);
    } else {
      hideInputSection();
    }
  } catch (e) {
    console.error("submitInput error:", e);
    setStatus("Error processing input. Please try again.");
    await refreshState();
  }
}

function collectInputData() {
  const fields = inputSection.querySelectorAll("[data-field-name]");
  const data = {};
  data.type = inputSection.dataset.inputType || "";

  fields.forEach((field) => {
    const name = field.dataset.fieldName;
    if (field.type === "checkbox") {
      if (!data[name]) data[name] = [];
      if (field.checked) data[name].push(field.value);
    } else if (field.type === "number") {
      data[name] = parseInt(field.value) || 0;
    } else {
      data[name] = field.value;
    }
  });

  return data;
}

function showInputPrompt(input) {
  const prompt =
    currentLang === "es" ? input.prompt_es || input.prompt : input.prompt;

  const promptEl = $("#input-prompt");
  // Convert newlines to <br> for proper formatting
  promptEl.innerHTML = prompt.replace(/\n/g, "<br>");

  const container = $("#input-fields");
  container.innerHTML = "";
  inputSection.dataset.inputType = input.type;

  (input.fields || []).forEach((f) => {
    const div = document.createElement("div");
    div.className = "input-field";

    const label = document.createElement("label");
    label.textContent = currentLang === "es" ? f.label_es || f.label : f.label;
    div.appendChild(label);

    if (f.type === "number") {
      const inp = document.createElement("input");
      inp.type = "number";
      inp.min = f.min ?? 0;
      inp.max = f.max ?? 999;
      inp.value = f.default ?? f.min ?? 0;
      inp.dataset.fieldName = f.name;
      div.appendChild(inp);
    } else if (f.type === "select") {
      const sel = document.createElement("select");
      sel.dataset.fieldName = f.name;
      (f.options || []).forEach((opt) => {
        const o = document.createElement("option");
        if (typeof opt === "object" && opt.value !== undefined) {
          o.value = opt.value;
          o.textContent = opt.label || opt.value;
        } else {
          o.value = opt;
          o.textContent = opt;
        }
        sel.appendChild(o);
      });
      if (f.default !== undefined) sel.value = String(f.default);
      div.appendChild(sel);
    } else if (f.type === "multiselect") {
      const group = document.createElement("div");
      group.className = "checkbox-group";
      (f.options || []).forEach((opt) => {
        const lbl = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = opt;
        cb.dataset.fieldName = f.name;
        lbl.appendChild(cb);
        lbl.appendChild(document.createTextNode(" " + opt));
        group.appendChild(lbl);
      });
      div.appendChild(group);
    }

    container.appendChild(div);
  });

  // If fields are present, auto-expand so user sees them
  const hasFields = (input.fields || []).length > 0;

  // Start collapsed by default; auto-expand if there are fields
  collapseInputBody();
  if (hasFields) {
    expandInputBody();
  }

  // Update header label based on input type
  const headerLabel = $("#input-header-label");
  if (input.type === "setup_done") {
    headerLabel.textContent = t("setup_header");
  } else {
    headerLabel.textContent = t("input_header");
  }

  showInputSection();
}

// ─── State Refresh ─────────────────────────────────────────────────────

async function refreshState() {
  gameState = await API.get("/api/game/state");
  refreshUI();
}

function refreshUI() {
  if (!gameState) return;

  // Top bar badges
  turnBadge.textContent = `${t("turn_label")} ${gameState.turn_number}`;
  phaseBadge.textContent = formatPhase(
    gameState.display_phase || gameState.phase
  );

  // Difficulty badge
  const diffBadge = $("#difficulty-badge");
  if (diffBadge) {
    const diff = gameState.difficulty;
    const diffLabels = {
      normal: currentLang === "es" ? "Normal" : "Normal",
      hard: currentLang === "es" ? "Difícil" : "Hard",
      demonic: currentLang === "es" ? "Demoníaco" : "Demonic",
    };
    diffBadge.textContent = diffLabels[diff] || diff;
    diffBadge.className = `badge difficulty diff-${diff}`;
  }

  // Card display
  updateCardDisplay();

  // Guidance panel
  updateGuidance();

  // Info cards
  updateInfoCards();

  // Action log
  updateLog();

  // Advance button
  updateAdvanceButton();
}

// ─── Card Display ──────────────────────────────────────────────────────

const PLACEHOLDER_CARD = "/static/cards/back.png";

function updateCardDisplay() {
  const cardImg = $("#current-card-img");
  const cardLabel = $("#current-card-label");
  const deckCount = $("#deck-count");
  const discardCount = $("#discard-count");

  if (gameState.current_card) {
    const card = gameState.current_card;
    cardImg.src = card.image || PLACEHOLDER_CARD;
    cardImg.alt = `Card #${card.number}`;
    cardImg.onclick = () => {
      if (card.image) {
        $("#card-zoom-img").src = card.image;
        showOverlay(cardOverlay);
      }
    };
    cardImg.classList.add("clickable");
    cardLabel.textContent = card.is_reshuffle
      ? "🔄 Reshuffle"
      : `#${card.number}`;
  } else {
    cardImg.src = PLACEHOLDER_CARD;
    cardImg.alt = t("no_card");
    cardImg.onclick = null;
    cardImg.classList.remove("clickable");
    cardLabel.textContent = t("no_card");
  }

  // Deck / discard counts
  if (gameState.solo_deck) {
    deckCount.textContent = gameState.solo_deck.size;
  }
  if (gameState.discard_pile) {
    discardCount.textContent = gameState.discard_pile.size;
  }
}

// ─── Guidance ──────────────────────────────────────────────────────────

function updateGuidance() {
  const panel = $("#guidance-panel");
  const content = $("#guidance-content");

  if (!gameState.guidance) {
    panel.classList.add("hidden");
    return;
  }

  panel.classList.remove("hidden");
  const g = gameState.guidance;
  const es = currentLang === "es";

  let html = "";

  // Soul Priority
  if (g.soul_priority && g.soul_priority.length > 0) {
    html += `<div class="guidance-section">`;
    html += `<h4>${t("guidance_soul_priority")}</h4>`;
    html += `<div class="soul-chips">`;
    g.soul_priority.forEach((s, i) => {
      html += `<span class="soul-chip color-${s.color}" title="${s.sin} (${es ? "Círculo" : "Circle"} ${s.circle})">`;
      html += `<span class="chip-rank">${i + 1}</span>`;
      html += `${s.emoji} ${s.label}`;
      html += `</span>`;
    });
    html += `</div></div>`;
  }

  // Shield Priority
  if (g.shield_priority && g.shield_priority.length > 0) {
    html += `<div class="guidance-section">`;
    html += `<h4>🛡️ ${t("guidance_shield")}</h4>`;
    html += `<div class="shield-chips">`;
    g.shield_priority.forEach((s, i) => {
      html += `<span class="shield-chip" title="${s.label}">`;
      html += `<span class="chip-rank">${i + 1}</span>`;
      html += `${s.emoji} ${s.label}`;
      html += `</span>`;
    });
    html += `</div></div>`;
  }

  // Arrow Direction + Priority Location
  html += `<div class="guidance-section guidance-row">`;
  html += `<div class="guidance-item">`;
  html += `<h4>➡️ ${t("guidance_arrow")}</h4>`;
  html += `<span class="direction-indicator dir-${g.arrow_direction}">`;
  html += g.arrow_direction === "left" ? "◀ Left" : "Right ▶";
  html += `</span>`;
  html += `</div>`;

  // Priority Location
  if (g.priority_location) {
    html += `<div class="guidance-item">`;
    html += `<h4>📍 ${t("guidance_location")}</h4>`;
    const locType = g.priority_location.type;
    const locClass = locType === "special" ? "special" : "free";
    const locIcon = locType === "special" ? "⭐" : "🏠";
    html += `<span class="location-chip ${locClass}">${locIcon} ${g.priority_location.label}</span>`;
    html += `</div>`;
  }
  html += `</div>`;

  content.innerHTML = html;
}

// ─── Info Cards ────────────────────────────────────────────────────────

function updateInfoCards() {
  // Turn
  const turnVal = $("#info-turn-value");
  if (turnVal) turnVal.textContent = gameState.turn_number;

  // Difficulty
  const diffVal = $("#info-diff-value");
  if (diffVal) {
    const labels = {
      normal: currentLang === "es" ? "Normal" : "Normal",
      hard: currentLang === "es" ? "Difícil" : "Hard",
      demonic: currentLang === "es" ? "Demoníaco" : "Demonic",
    };
    diffVal.textContent = labels[gameState.difficulty] || gameState.difficulty;
  }

  // Deck
  const deckVal = $("#info-deck-value");
  if (deckVal)
    deckVal.textContent = gameState.solo_deck
      ? gameState.solo_deck.size
      : "—";

  // Discard
  const discardVal = $("#info-discard-value");
  if (discardVal)
    discardVal.textContent = gameState.discard_pile
      ? gameState.discard_pile.size
      : "—";
}

// ─── Action Log ────────────────────────────────────────────────────────

function updateLog() {
  const container = $("#action-log");
  if (!container) return;
  container.innerHTML = "";

  const entries = gameState.action_log || [];
  // Most recent first
  [...entries].reverse().forEach((entry) => {
    const div = document.createElement("div");
    div.className = `log-entry log-${entry.category}`;

    const msg =
      currentLang === "es"
        ? entry.message_es || entry.message
        : entry.message;

    div.innerHTML = `
      <span class="log-turn">T${entry.turn}</span>
      <span class="log-category cat-${entry.category}">${categoryIcon(entry.category)}</span>
      <span class="log-msg">${msg}</span>
    `;
    container.appendChild(div);
  });
}

function categoryIcon(cat) {
  const icons = {
    setup: "⚙️",
    draw: "🃏",
    hell: "🔥",
    florence: "🏛️",
    turn_end: "⏭️",
    reshuffle: "🔄",
    game_over: "🏁",
    error: "⚠️",
    info: "ℹ️",
    phase: "▶️",
  };
  return icons[cat] || "●";
}

// ─── Advance Button ────────────────────────────────────────────────────

function updateAdvanceButton() {
  const phase = gameState.phase;

  btnAdvance.textContent = getAdvanceLabel(phase);

  if (phase === "game_over") {
    btnAdvance.disabled = false;
    btnAdvance.classList.add("pulse");
  } else if (phase === "waiting_for_input") {
    if (gameState.pending_input) {
      // btn-advance stays enabled — it now submits input
      btnAdvance.disabled = false;
      btnAdvance.classList.add("pulse");
      const hasFields = (gameState.pending_input.fields || []).length > 0;
      btnAdvance.textContent = hasFields
        ? (currentLang === "es" ? "Confirmar ▶" : "Confirm ▶")
        : getAdvanceLabel(phase);
      // Only show if not already visible (avoid re-render flicker)
      if (inputSection.classList.contains("hidden")) {
        showInputPrompt(gameState.pending_input);
      }
    } else {
      hideInputSection();
      btnAdvance.disabled = false;
      btnAdvance.classList.add("pulse");
    }
  } else {
    hideInputSection();
    btnAdvance.disabled = false;
    btnAdvance.classList.add("pulse");
  }
}

// ─── Helpers ───────────────────────────────────────────────────────────

function formatPhase(phase) {
  const key = `phase_${phase}`;
  return t(key) || phase;
}

function getAdvanceLabel(phase) {
  const es = currentLang === "es";

  if (phase === "game_over") {
    return es ? "🏁 Partida Terminada" : "🏁 Game Over";
  }
  if (phase === "setup") {
    return es ? "Iniciar Partida ▶" : "Begin Game ▶";
  }
  return es ? "Continuar ▶" : "Continue ▶";
}

function setStatus(msg) {
  if (statusMsg) statusMsg.textContent = msg || "";
}

// ─── Actions ───────────────────────────────────────────────────────────

async function doUndo() {
  hideOverlay(inputOverlay);
  try {
    const result = await API.post("/api/game/undo");
    if (result.status === "ok") {
      await refreshState();
      setStatus(
        currentLang === "es" ? "Acción deshecha." : "Action undone."
      );
    } else {
      setStatus(result.message);
    }
  } catch (e) {
    console.error("doUndo error:", e);
    setStatus("Error undoing action.");
  }
}

// ─── Save / Load ───────────────────────────────────────────────────────

async function showSaveOverlay() {
  const name = prompt(
    currentLang === "es" ? "Nombre del guardado:" : "Save name:",
    `save_turn_${gameState ? gameState.turn_number : 0}`
  );
  if (!name) return;
  try {
    const result = await API.post("/api/game/save", { slot_name: name });
    setStatus(result.message);
  } catch (e) {
    setStatus("Error saving game.");
  }
}

async function showLoadOverlay() {
  try {
    const saves = await API.get("/api/game/saves");
    const container = $("#saves-list");
    container.innerHTML = "";

    if (saves.length === 0) {
      container.innerHTML = `<p class="text-muted">${t("no_saves")}</p>`;
    } else {
      saves.forEach((save) => {
        const div = document.createElement("div");
        div.className = "save-item";
        div.innerHTML = `
          <div class="save-info" data-slot="${save.slot_name}">
            <div class="save-name">${save.slot_name}</div>
            <div class="save-meta">${t("turn_label")} ${save.turn} — ${save.date}</div>
          </div>
          <button class="save-delete" data-delete="${save.slot_name}">🗑</button>
        `;
        div.querySelector(".save-info").onclick = () =>
          loadGameSlot(save.slot_name);
        div.querySelector(".save-delete").onclick = async (e) => {
          e.stopPropagation();
          await API.del(`/api/game/saves/${save.slot_name}`);
          showLoadOverlay();
        };
        container.appendChild(div);
      });
    }

    showOverlay(loadOverlay);
  } catch (e) {
    console.error("showLoadOverlay error:", e);
    setStatus("Error loading saves list.");
  }
}

async function loadGameSlot(slotName) {
  try {
    const result = await API.post("/api/game/load", { slot_name: slotName });
    hideOverlay(loadOverlay);
    if (result.status === "ok") {
      gameActive = true;
      welcomeScreen.classList.add("hidden");
      gameScreen.classList.remove("hidden");
      await refreshState();
      setStatus(result.message);
    } else {
      setStatus(result.message);
    }
  } catch (e) {
    setStatus("Error loading game.");
  }
}

async function tryAutoLoad() {
  try {
    const result = await API.post("/api/game/load", {
      slot_name: "autosave",
    });
    if (result.status === "ok") {
      gameActive = true;
      welcomeScreen.classList.add("hidden");
      gameScreen.classList.remove("hidden");
      await refreshState();
    }
  } catch (e) {
    // No autosave — stay on welcome screen
  }
}

// ─── Download / Upload ─────────────────────────────────────────────────

function downloadSaveToDevice() {
  window.location.href = `/api/game/download?session_id=${_getSessionId()}`;
}

async function uploadSaveFromDevice(e) {
  const fileInput = e ? e.target : null;
  if (!fileInput) return;
  const file = fileInput.files[0];
  if (!file) return;

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/api/game/upload", {
      method: "POST",
      headers: { "X-Session-ID": _getSessionId() },
      credentials: "include",
      body: form,
    });
    const result = await res.json();
    if (result.status === "ok") {
      hideOverlay(loadOverlay);
      gameActive = true;
      welcomeScreen.classList.add("hidden");
      gameScreen.classList.remove("hidden");
      await refreshState();
      setStatus(result.message);
    } else {
      setStatus(result.message);
    }
  } catch (e) {
    setStatus("Upload failed: " + e.message);
  }
  fileInput.value = "";
}

// ─── Rules Quick Reference ─────────────────────────────────────────────

function showRulesOverlay() {
  const content = $("#rules-content");
  if (content) {
    content.innerHTML = t("rules_text").replace(/\n/g, "<br>");
  }
  showOverlay(rulesOverlay);
}
