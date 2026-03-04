---
title: Malakar
emoji: 👹
colorFrom: red
colorTo: gray
sdk: docker
app_port: 5000
pinned: false
---

# Malakar — Digital Companion

A web-based companion app for **Malakar**, the solo automa opponent for the board game **Inferno**.
Run the automa entirely from your phone or laptop — no physical solo cards needed.

---

## Features

- **Card-guided solo play** — the app draws from a 17-card solo deck, presents Malakar's priorities for the Hell Phase and Florence Phase, and walks you through every step of each turn.
- **Three difficulty levels** — Normal, Hard, and Demonic, each with specific setup rules for starting cards and skulls.
- **Reshuffle handling** — automatically detects the reshuffle card, prompts tower reorganization using the previous card's guest order, reshuffles the deck, and draws again.
- **Card data driven** — all 17 solo cards (16 game cards + 1 reshuffle) defined in a single YAML file (`game/cards.yaml`).
- **Save / Load** — persist game state to JSON; auto-save after every phase. Download/upload saves as files.
- **Undo** — step back to the previous phase.
- **Bilingual UI** — English / Spanish, togglable at any time.
- **Mobile-first responsive design** — works on phones, tablets, and desktops.

---

## Project Structure

```
Malakar/
├── app.py                   # Flask server & REST API (port 5000)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Production container (gunicorn)
├── docker-compose.yml       # Docker Compose config
│
├── game/                    # Core game logic (pure Python)
│   ├── models.py            # Data models, enums, dataclasses
│   ├── cards.py             # YAML parser → SoloCard objects
│   ├── cards.yaml           # All 17 solo cards as structured YAML data
│   ├── engine.py            # State-machine game engine
│   └── save_manager.py      # JSON serialisation / deserialisation
│
├── templates/
│   └── index.html           # Single-page app shell (Jinja2)
│
├── static/
│   ├── css/style.css        # Mobile-first dark-theme stylesheet
│   ├── js/app.js            # Frontend application logic
│   ├── js/i18n.js           # EN/ES translations
│   └── cards/               # Solo card images (PNG)
│
├── agent_support_files/     # Reference data used during development
│   └── High Resolution Printing/  # Source card images
│
└── saves/                   # Game save files (JSON, per session)
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

**Requirements:** Python 3.10+, Flask, PyYAML.

### 2. Run the server

```bash
python app.py
```

Open **http://localhost:5000** in your browser (or use your LAN IP to play from a phone on the same network).

### Docker

```bash
docker compose up --build
```

The app is served with gunicorn on port 5000.

---

## How It Works

### Turn Flow

The engine follows a strict phase cycle:

```
SETUP → DRAW_CARD → HELL_PHASE → FLORENCE_PHASE → TURN_END → DRAW_CARD → ...
```

Each turn, the app draws a solo card and guides you through two main phases before asking whether the game should continue.

### Turn Phases

1. **Draw Card** — flip the top card from the solo deck. If it's the reshuffle card, reorganize Malakar's Tower and reshuffle.
2. **Hell Phase** — Malakar moves a Soul in Hell. The app presents the full priority list for choosing which Soul to move and where to place it, including tie-breaking by color priority and shield direction.
3. **Florence Phase** — Malakar performs actions in Florence. The app shows location priorities (free-access vs. special), accusation logic, exchange direction, Fraud card selection, Phlegethon/River Styx rules, and tower placement order.
4. **Turn End** — the card is discarded. You decide whether Dante has reached the final stop (game over) or to continue playing.

### Card Data Model

Each of the 16 game cards encodes:

| Field | Description |
|-------|-------------|
| `soul_priority` | Ordered list of soul colors for tie-breaking (4 colors) |
| `shield_direction` | `left` or `right` — which side of a Hell circle to place souls |
| `exchange_direction` | `left` (1 Florin) or `right` (maximum Florins) |
| `priority_location_free` | Free-access location: haystack, banquet, bank, or courtyard |
| `priority_location_special` | Special location: bonfire, wall, market, or palace |
| `tie_arrow` | `left` or `right` — Fraud card tie-breaking direction |
| `tower_guest_order` | Ordered list of guest colors for tower reorganization (bottom→top) |

Card 17 is the reshuffle card — it triggers tower reorganization and deck reshuffle.

### Soul Colors & Circles of Hell

| Circle | Color | Sin |
|--------|-------|-----|
| 1 | Beige | Limbo |
| 2 | Purple | Lust |
| 3 | Green | Gluttony |
| 4 | Yellow | Greed |
| 5 | Blue | Sloth |
| 6 | Orange | Heresy |
| 7 | Red | Violence |
| 8 | Gray | Fraud |
| 9 | Ice Blue | Treason |

### Florence Locations

| Quartiere | Free-Access | Special |
|-----------|-------------|---------|
| Porta San Piero | Haystack | Bonfire |
| Porta del Duomo | Banquet | Wall |
| Porta Rossa | Bank | Market |
| Porta San Frediano | Courtyard | Palace |

### Difficulty Levels

| Mode | Description |
|------|-------------|
| **Normal** | Both you and Malakar use an Apprentice card. |
| **Hard** | You use a Family card. Place a starting skull on the Sin Track shown on your card. |
| **Demonic** | You use a Family card. Malakar places an additional skull on your Apprentice card's Sin Track. |

---

## API Reference

All endpoints return JSON.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/game/new` | Start a new game. Body: `{ "difficulty": "normal"\|"hard"\|"demonic", "language": "en"\|"es" }` |
| `GET`  | `/api/game/state` | Current game state (cards, phase, log) |
| `POST` | `/api/game/advance` | Advance to the next phase |
| `POST` | `/api/game/input` | Submit player input (acknowledgements, game-over check) |
| `POST` | `/api/game/undo` | Undo last phase |
| `POST` | `/api/game/language` | Switch language. Body: `{ "language": "en"\|"es" }` |
| `POST` | `/api/game/save` | Save current game. Body: `{ "slot_name": "name" }` |
| `POST` | `/api/game/load` | Load a save. Body: `{ "slot_name": "name" }` |
| `GET`  | `/api/game/saves` | List all save slots |
| `DELETE` | `/api/game/saves/<slot>` | Delete a save slot |
| `GET`  | `/api/game/download` | Download current state as a JSON file |
| `POST` | `/api/game/upload` | Upload a previously downloaded save file (multipart form) |

---

## Tech Stack

- **Backend:** Python 3.12 / Flask
- **Frontend:** Vanilla HTML, CSS, JavaScript (no build step)
- **Card data:** YAML (parsed at startup)
- **Production server:** Gunicorn (via Docker)
- **Persistence:** JSON files (per-session directories)
- **Design:** Mobile-first, dark theme, responsive

---

## License

This is a fan-made companion tool. **Inferno** is designed by Francesco Sirocchi, published by Quined Games. The Malakar solo automa is an official solo mode. All card artwork and game content belong to their respective owners.
