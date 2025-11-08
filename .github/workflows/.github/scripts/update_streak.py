#!/usr/bin/env python3
"""
Daily Streak Updater 🔥

This script is meant to be run by GitHub Actions once per day.

What it does:
- Maintains a JSON file `streak_data.json` in the repo root.
- Each run logs "today" as an active day.
- Calculates:
    - current streak
    - longest streak
    - total active days
- Updates `STREAK.md` with a nice visual & stats.
- If anything changed, the workflow commits & pushes it.

This creates a consistent daily commit pattern -> affects your GitHub contribution graph.
"""

import json
import os
from datetime import datetime, timedelta, date

DATA_FILE = "streak_data.json"
STREAK_MD = "STREAK.md"
DATE_FMT = "%Y-%m-%d"


def today_str():
    # Use UTC for consistency with GitHub Actions
    return datetime.utcnow().strftime(DATE_FMT)


def to_date(s: str) -> date:
    return datetime.strptime(s, DATE_FMT).date()


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "dates": [],
            "longest_streak": 0,
            "created_at": today_str(),
        }
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # if corrupted, reset
        return {
            "dates": [],
            "longest_streak": 0,
            "created_at": today_str(),
        }


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def normalize_dates(dates):
    return sorted(list(set(dates)))


def calculate_streak(dates_str):
    if not dates_str:
        return 0, 0

    dates = sorted(to_date(d) for d in dates_str)
    longest = 1
    current_chain = 1

    for i in range(1, len(dates)):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            current_chain += 1
        else:
            current_chain = 1
        if current_chain > longest:
            longest = current_chain

    today = datetime.utcnow().date()
    last = dates[-1]

    if last == today:
        current = current_chain
    elif last == today - timedelta(days=1):
        current = current_chain
    else:
        current = 0

    return current, longest


def add_today_if_missing(data):
    t = today_str()
    dates = data.get("dates", [])
    if t not in dates:
        dates.append(t)
    dates = normalize_dates(dates)
    data["dates"] = dates
    current, longest = calculate_streak(dates)
    data["longest_streak"] = max(data.get("longest_streak", 0), longest)
    return data, current, data["longest_streak"]


def make_bar(current, longest, width=40):
    if longest <= 0:
        return "No streak yet. Start today. 🔥"
    ratio = min(1.0, current / float(longest or 1))
    filled = int(width * ratio) if current > 0 else 0
    bar = "🔥" * filled + "·" * (width - filled)
    return f"{bar}  ({current}/{longest} days)"


def make_calendar_block(dates_str, months=3):
    if not dates_str:
        return "_No activity yet — first run just started the engine._"

    dates = set(to_date(d) for d in dates_str)

    today = datetime.utcnow().date()
    start = today - timedelta(days=months * 30)

    out_lines = []
    out_lines.append("Recent Activity Heatmap")
    out_lines.append("`Su Mo Tu We Th Fr Sa`")

    cur = start - timedelta(days=(start.weekday() + 1) % 7)
    week = []

    while cur <= today:
        if cur < start:
            cell = "  "
        else:
            cell = "██" if cur in dates else "░░"
        week.append(cell)

        if len(week) == 7:
            out_lines.append(" ".join(week))
            week = []
        cur += timedelta(days=1)

    if week:
        while len(week) < 7:
            week.append("  ")
        out_lines.append(" ".join(week))

    return "\n".join(f"`{line}`" for line in out_lines)


def render_streak_md(data, current, longest):
    total_days = len(data.get("dates", []))
    created_at = data.get("created_at", today_str())
    last_updated = today_str()

    bar = make_bar(current, longest)
    calendar = make_calendar_block(data.get("dates", []), months=4)

    content = f"""# 🔥 Automated Repo Streak

This file is auto-updated daily by **GitHub Actions** to keep track of activity in this repository.

---

## 📊 Streak Status

- **Current Streak:** `{current}` day(s)
- **Longest Streak:** `{longest}` day(s)
- **Total Active Days:** `{total_days}`
- **Tracking Since:** `{created_at}`
- **Last Updated (UTC):** `{last_updated}`

---

## 📈 Streak Progress

`{bar}`

---

## 🗓️ Activity Overview

{calendar}

---

_This streak is maintained by an automated workflow in this repo. Edit `.github/workflows/daily-streak.yml` or `.github/scripts/update_streak.py` to customize._
"""
    return content


def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        return f.read()


def write_if_changed(path, new_content):
    old = read_file(path)
    if old.strip() != new_content.strip():
        with open(path, "w") as f:
            f.write(new_content)
        return True
    return False


def main():
    data = load_data()
    data, current, longest = add_today_if_missing(data)
    save_data(data)

    new_md = render_streak_md(data, current, longest)
    changed = write_if_changed(STREAK_MD, new_md)

    if changed:
        print("✅ STREAK.md updated.")
    else:
        print("ℹ️ No changes in streak data (already up-to-date).")

    print(f"Current streak: {current}, Longest streak: {longest}, Total days: {len(data.get('dates', []))}")


if __name__ == "__main__":
    main()
