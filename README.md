# FocusLedger (macOS Menu Bar Time Tracker)

FocusLedger is a lightweight macOS menu bar app for tracking how you spend time across custom work modes.

## Categories (default)
- Research 🔬
- Study 🧠
- Coding 💻
- FOMO 📱
- Rest 🛌 (default on first launch)

You can switch category with one click from the menu bar.

## Menu Bar Display
Example:

`🔬 00:12 | Σ 01:34 | ΣΣ 12:48`

- First (`🔬 00:12`): current session time for the active category
- Second (`Σ 01:34`): today's total time for the active category
- Third (`ΣΣ 12:48`): all-time active tracked time

## Features
- Runs in the macOS menu bar (top-right)
- Always tracks one active category
- One-click category switching
- Built-in summaries:
  - Today
  - This Week
  - This Month
- CSV export for today
- Optional auto-start on login

---

## Install (for anyone, no OpenClaw needed)

### 1) Clone the repo
```bash
git clone https://github.com/Threedv/focusledger.git
cd focusledger
```

### 2) Run
```bash
./run.sh
```

`run.sh` will:
- create `.venv`
- install dependencies
- launch the app

> Requirements: macOS + Python 3

---

## Auto-start at Login (optional)

```bash
./install_launchagent.sh
```

This installs a LaunchAgent:
- `~/Library/LaunchAgents/com.bob.focusledger.plist`

To restart it manually:
```bash
launchctl kickstart -k gui/$(id -u)/com.bob.focusledger
```

---

## Data Storage

FocusLedger stores state/logs here:
- `~/.focusledger/state.json`
- `~/.focusledger/events.jsonl`

CSV exports:
- `~/.focusledger/today-YYYY-MM-DD.csv`

---

## Usage Tips
- Click the menu bar item to change category instantly.
- `Reset Day Session` resets only the day-session reference timer.
- Historical logs are preserved unless you delete files in `~/.focusledger/`.

---

## Tech
- Python
- [rumps](https://github.com/jaredks/rumps) for macOS menu bar integration
