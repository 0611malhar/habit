# Habit Tracker

A minimal, friction-free habit tracking engine built for high-accountability challenges (like the 75-Day Hard challenge). Engineered to solve the core morning routine problem: immediate visibility of scheduled tasks, one-click logging, resilient streak mathematics, and clutter management.

---

## Key Features

* **Today-Only Focus:** Automatically filters down to tasks that are actually scheduled for the current day.
* **Flexible Schedules:** Supports `Daily` and `Weekdays` (Mon–Fri) frequencies with automatic weekend handling.
* **Resilient Streak Engine:** Dynamic date-based calculation for **Current Streak** and **Best Streak**. Streaks do not break on unscheduled days (e.g., weekends for weekday habits).
* **Soft Archiving:** Declutter abandoned habits without deleting completion history or corrupting historical stats.
* **In-Memory Substring Search:** Fast real-time habit filtering for large habit sets.
* **Zero-Config Local Persistence:** Powered by SQLite with guaranteed relational integrity.

---

## Tech Stack

* **Language:** Python 3.10+
* **Framework:** Streamlit (UI, state reactivity, dialogs)
* **Database:** SQLite3 (Native Python, zero external drivers needed)

---

## Quick Start

### 1. Prerequisites

Ensure Python 3.10 or above is installed on your system.

### 2. Install Dependencies

pip install streamlit

### 3. Run the Application

streamlit run app.py

The app will open automatically in your default browser at http://localhost:8501.

---

## Database Architecture

The application uses an embedded relational SQLite database (`habits.db`) with two tables:

### `habits`

| Column | Type | Description |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Unique habit identifier |
| `name` | `TEXT NOT NULL` | Title of the habit |
| `emoji` | `TEXT DEFAULT '🎯'` | Visual icon marker |
| `frequency` | `TEXT CHECK(frequency IN ('daily', 'weekdays'))` | Schedule cadence |
| `archived` | `INTEGER DEFAULT 0` | Soft-delete flag (`0` Active, `1` Hidden) |

### `completions`

| Column | Type | Description |
| --- | --- | --- |
| `habit_id` | `INTEGER` | Foreign key referencing `habits(id)` |
| `completed_date` | `TEXT` | Completion date in ISO format (`YYYY-MM-DD`) |

> **Integrity Note:** A composite primary key `(habit_id, completed_date)` prevents duplicate completion logs on the same calendar day.

---

## Streak Calculation Logic

Streaks are **never stored as static integer counters**; they are dynamically computed on each run using the historical completion records:

1. **Schedule Awareness:** Days that fall outside the habit's frequency (e.g., Saturday/Sunday for weekday habits) are skipped in the verification sequence.
2. **Grace Period (Active Day):** A streak does not reset to zero at the start of an incomplete day. As long as the *previous scheduled day* was completed, the streak remains alive.
3. **Historical Scan:** The all-time completion set is traversed chronologically to evaluate continuous valid day chains and compute the **All-Time Best Streak**.

## Initialization and setup

1. python -m venv venv
2. venv\Scripts\activate
3. pip install -r requirements.txt
4. streamlit run app.py
