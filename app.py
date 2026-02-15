#!/usr/bin/env python3
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import rumps

APP_NAME = "FocusLedger"
BASE_DIR = Path.home() / ".focusledger"
STATE_PATH = BASE_DIR / "state.json"
LOG_PATH = BASE_DIR / "events.jsonl"

CATEGORIES = ["Research", "Study", "Coding", "FOMO", "Rest"]
DEFAULT_CATEGORY = "Rest"


def now_local() -> datetime:
    return datetime.now().astimezone()


def fmt_hm(seconds: float) -> str:
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h:02d}:{m:02d}"


@dataclass
class State:
    current_category: str
    segment_started_at: str
    day_session_started_at: str


class FocusLedger(rumps.App):
    def __init__(self):
        super().__init__(APP_NAME, title="…", quit_button="Quit")
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.state = self._load_or_init_state()

        self.category_items = {}
        self.menu.add(rumps.MenuItem("Current: -", callback=None))
        self.menu.add(rumps.separator)

        for cat in CATEGORIES:
            item = rumps.MenuItem(cat, callback=self._on_pick_category)
            self.category_items[cat] = item
            self.menu.add(item)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Today Summary", callback=self._show_today))
        self.menu.add(rumps.MenuItem("This Week Summary", callback=self._show_week))
        self.menu.add(rumps.MenuItem("This Month Summary", callback=self._show_month))
        self.menu.add(rumps.MenuItem("Export CSV", callback=self._export_csv))
        self.menu.add(rumps.MenuItem("Reset Day Session", callback=self._reset_day_session))

        self.timer = rumps.Timer(self._tick, 1)
        self.timer.start()
        self._refresh_ui()

    def _load_or_init_state(self) -> State:
        if STATE_PATH.exists():
            data = json.loads(STATE_PATH.read_text())
            return State(**data)

        t = now_local().isoformat()
        st = State(
            current_category=DEFAULT_CATEGORY,
            segment_started_at=t,
            day_session_started_at=t,
        )
        self._save_state(st)
        return st

    def _save_state(self, state: State):
        STATE_PATH.write_text(json.dumps(state.__dict__, indent=2))

    def _append_event(self, category: str, start_iso: str, end_iso: str):
        evt = {"category": category, "start": start_iso, "end": end_iso}
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def _parse_iso(self, s: str) -> datetime:
        return datetime.fromisoformat(s)

    def _current_segment_seconds(self) -> float:
        return (now_local() - self._parse_iso(self.state.segment_started_at)).total_seconds()

    def _day_session_seconds(self) -> float:
        return (now_local() - self._parse_iso(self.state.day_session_started_at)).total_seconds()

    def _all_time_seconds(self) -> float:
        total = 0.0
        for e in self._events():
            try:
                st = self._parse_iso(e["start"])
                ed = self._parse_iso(e["end"])
            except Exception:
                continue
            if ed > st:
                total += (ed - st).total_seconds()

        # ongoing segment
        st = self._parse_iso(self.state.segment_started_at)
        ed = now_local()
        if ed > st:
            total += (ed - st).total_seconds()
        return total

    def _today_category_seconds(self, category: str) -> float:
        now = now_local()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        totals = self._aggregate(start, now)
        return totals.get(category, 0.0)

    def _on_pick_category(self, sender):
        new_cat = sender.title
        if new_cat == self.state.current_category:
            return

        t = now_local().isoformat()
        self._append_event(
            category=self.state.current_category,
            start_iso=self.state.segment_started_at,
            end_iso=t,
        )
        self.state.current_category = new_cat
        self.state.segment_started_at = t
        self._save_state(self.state)
        self._refresh_ui()

    def _events(self) -> List[dict]:
        if not LOG_PATH.exists():
            return []
        out = []
        with LOG_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def _aggregate(self, since: datetime, until: datetime) -> Dict[str, float]:
        totals = {c: 0.0 for c in CATEGORIES}
        for e in self._events():
            cat = e.get("category")
            if cat not in totals:
                continue
            try:
                st = self._parse_iso(e["start"])
                ed = self._parse_iso(e["end"])
            except Exception:
                continue
            overlap_start = max(st, since)
            overlap_end = min(ed, until)
            if overlap_end > overlap_start:
                totals[cat] += (overlap_end - overlap_start).total_seconds()

        # include ongoing segment
        st = self._parse_iso(self.state.segment_started_at)
        ed = now_local()
        overlap_start = max(st, since)
        overlap_end = min(ed, until)
        if overlap_end > overlap_start:
            totals[self.state.current_category] += (overlap_end - overlap_start).total_seconds()

        return totals

    def _summary_text(self, totals: Dict[str, float], title: str) -> str:
        lines = [title, ""]
        total_all = sum(totals.values())
        for cat in CATEGORIES:
            sec = totals.get(cat, 0.0)
            pct = (sec / total_all * 100) if total_all > 0 else 0.0
            lines.append(f"• {cat}: {fmt_hm(sec)} ({pct:.1f}%)")
        lines.append("")
        lines.append(f"Total tracked: {fmt_hm(total_all)}")
        return "\n".join(lines)

    def _show_today(self, _):
        now = now_local()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        totals = self._aggregate(start, now)
        rumps.alert(title=APP_NAME, message=self._summary_text(totals, "Today"))

    def _show_week(self, _):
        now = now_local()
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        totals = self._aggregate(start, now)
        rumps.alert(title=APP_NAME, message=self._summary_text(totals, "This Week"))

    def _show_month(self, _):
        now = now_local()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        totals = self._aggregate(start, now)
        rumps.alert(title=APP_NAME, message=self._summary_text(totals, "This Month"))

    def _export_csv(self, _):
        now = now_local()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        totals = self._aggregate(start, now)
        out = BASE_DIR / f"today-{now.strftime('%Y-%m-%d')}.csv"
        with out.open("w", encoding="utf-8") as f:
            f.write("category,seconds,hhmm\n")
            for cat in CATEGORIES:
                sec = int(totals.get(cat, 0))
                f.write(f"{cat},{sec},{fmt_hm(sec)}\n")
        rumps.notification(APP_NAME, "Exported", str(out))

    def _reset_day_session(self, _):
        t = now_local().isoformat()
        self.state.day_session_started_at = t
        self._save_state(self.state)
        rumps.notification(APP_NAME, "Day Session", "Day session timer reset")
        self._refresh_ui()

    def _tick(self, _):
        self._refresh_ui()

    def _refresh_ui(self):
        cur = self.state.current_category
        seg = fmt_hm(self._current_segment_seconds())
        today_cur = fmt_hm(self._today_category_seconds(cur))
        active = fmt_hm(self._all_time_seconds())

        short = {
            "Research": "🔬",
            "Study": "🧠",
            "Coding": "💻",
            "FOMO": "📱",
            "Rest": "🛌",
        }.get(cur, "❓")

        self.title = f"{short} {seg} | Σ {today_cur} | ΣΣ {active}"

        # first menu item is current status
        keys = list(self.menu.keys())
        if keys:
            self.menu[keys[0]].title = f"Current: {cur} | Session: {seg} | Today({cur}): {today_cur} | Active: {active}"

        for cat, item in self.category_items.items():
            item.state = 1 if cat == cur else 0


if __name__ == "__main__":
    FocusLedger().run()
