# FocusLedger (Menu Bar Time Tracker for macOS)

A tiny menu-bar tracker for category-based time logging.

## Categories
- Research
- Coding
- FOMO
- Rest (default)

## What it does
- Lives in top-right macOS menu bar
- One-click category switching
- Tracks:
  - current segment elapsed time
  - day session elapsed time (since app/day reset)
- Summaries for Today / Week / Month
- CSV export (today)

## First run
```bash
cd ~/.openclaw/workspace/menubar-time-tracker
./run.sh
```

This creates a local `.venv`, installs dependencies, and launches the app.

## Data location
All logs/state are stored at:
- `~/.focusledger/state.json`
- `~/.focusledger/events.jsonl`

## Menu tips
- Click category to switch instantly.
- `Reset Day Session` resets only the day-session clock, not historical logs.
- `Export CSV` writes `~/.focusledger/today-YYYY-MM-DD.csv`.
