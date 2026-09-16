# REASONING.md — Architecture & Engineering Decisions

## 1. Problem Deconstruction & Product Focus

Ananya's 75-day challenge is not a standard task checklist; it is an endurance loop driven by psychological momentum. Under a strict **2.5-hour development window**, building a bloated full-stack application (auth, external servers, complex cloud state) introduces failure points that derail core execution.

Instead, the product strategy anchors on a single operational premise:

**A zero-friction morning ritual that loads instantly, displays only today's actionable habits, enables one-click logging, and accurately protects streak integrity.**

---

## 2. Tech Stack Selection: Python & Streamlit

Traditional architectures split into separate frontend and backend layers, requiring API contracts, CORS handling, client-side state sync, and deployment pipelines.

To ship a rock-solid, production-grade MVP in 150 minutes:

* **Python + Streamlit:** Streamlit executes as a unified reactive engine. UI components, state management, and backend logic execute within a single runtime. A UI action (like checking a box) triggers an immediate re-evaluation of the view without manual DOM manipulation or REST boilerplate.
* **SQLite (`sqlite3`):** In-memory state or flat JSON files risk corruption during concurrent writes or sudden reloads. SQLite provides zero-configuration, ACID-compliant persistence directly on disk, ensuring Ananya’s historical logging survives process restarts with zero infrastructure overhead.

---

## 3. Data Modeling: Computed State vs. Static Counters

A common anti-pattern in habit tracking apps is storing mutable integer counters:

```json
{ "current_streak": 5, "best_streak": 12 }

```

This pattern fails rapidly due to desynchronization, off-by-one errors, missed day handling, and time-zone boundary shifts.

### The Ledger Pattern

The system models completions as an immutable append-only event ledger:

* **`habits`**: Entity metadata (`id`, `name`, `emoji`, `frequency`, `archived`).
* **`completions`**: Execution log containing unique composite pairs of `(habit_id, completed_date)`.

Streaks are **never manually incremented or stored directly**. They are dynamically computed on each run using the completion dates set. This guarantees 100% data consistency even if habits are edited, days are reviewed retroactively, or historical logs are audited.

---

## 4. The Streak Calculation Engine

The streak algorithm solves two non-trivial domain edge cases: **non-daily schedules (weekdays)** and **same-day pending status**.

### Calendar-Aware Traversal

A standard habit breaks if yesterday's log is absent. However, a weekday-only habit (`frequency = 'weekdays'`) must treat Friday to Monday as a direct, contiguous progression:

* Valid calendar cycles evaluate only scheduled days:
$$\text{Scheduled Day} = (\text{frequency} = \text{'daily'}) \lor (\text{weekday} \in \{0, 1, 2, 3, 4\})$$


* On Saturday and Sunday, weekday habits are omitted from the active daily denominator, preventing false streak breaks or inaccurate completion percentages.

### Graceful Pending State (Psychological Safety)

If a user opens the app at 8:00 AM, today's habit is not yet completed. Dropping the streak to zero in the morning creates unjustified negative reinforcement.

* **Logic:** The streak evaluation pointer checks if today is completed. If incomplete, it steps back to the most recent scheduled day. If that previous day was completed, the current streak remains alive and intact. The streak only resets if an antecedent scheduled day was missed.

### Dual Metric Output

* **Current Streak:** Backward crawl from current date/previous scheduled day until the first missing completion.
* **Best Streak:** Contiguous sliding-window evaluation over sorted historical completions, counting consecutive scheduled periods across all-time usage.

---

## 5. Feature Prioritization (2.5-Hour Scope Management)

To ensure high engineering quality within 150 minutes, architectural boundaries were strictly enforced:

| Decision | Implementation | Why |
| --- | --- | --- |
| **Storage** | Single SQLite file | Zero-config, zero latency, atomic commits. |
| **Soft Delete** | `archived = 1` flag | Removes abandoned habits from active view without destroying historical streak records. |
| **Scheduling** | `daily` vs `weekdays` | Addresses scheduling friction directly without building calendar-rule complexity. |
| **Search** | Substring filter on loaded set | Instant UI-level search for fast habit editing/updating without round-trip query delays. |
| **Excluded** | Auth, Cloud DB, Push Reminders | Scope killers that jeopardize core logging and streak accuracy under tight deadlines. |

---

## 6. Execution Verification

The solution meets three core reliability checks:

1. **Cold Start & Persistence:** Checking off a habit commits immediately to SQLite; killing and restarting the server maintains all states and streaks.
2. **Weekend Boundary Verification:** Friday completion + Monday completion yields a continuous streak of 2 for weekday habits, completely ignoring the weekend gap.
3. **Auditability:** Archiving a habit immediately recalculates the active completion progress for the day while preserving raw rows in `completions`.
