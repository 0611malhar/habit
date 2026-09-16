"""
75-Day Vibe Habit Tracker
Single-file Streamlit frontend integrated with SQLite backend & streak engine.
Deployment ready with user-friendly error handling and custom CSS aesthetics.
"""

from datetime import date, datetime, timedelta
import streamlit as st
import db
import streak

# Page configuration
st.set_page_config(
    page_title="Habit Tracker",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for modern glassmorphism dark aesthetic
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Background styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }

    /* Glassmorphism Cards */
    .habit-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 14px;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
    }
    .habit-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 12px 36px 0 rgba(99, 102, 241, 0.15);
    }

    /* Streak Badges */
    .badge-streak {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(234, 88, 12, 0.2) 100%);
        border: 1px solid rgba(249, 115, 22, 0.4);
        color: #fb923c;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-best {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.2) 0%, rgba(202, 138, 4, 0.2) 100%);
        border: 1px solid rgba(234, 179, 8, 0.4);
        color: #facc15;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-freq {
        display: inline-flex;
        align-items: center;
        background: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Challenge Header Hero */
    .hero-container {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        text-align: center;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #818cf8, #c084fc, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 16px;
    }

    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        border-radius: 10px;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize database safely
try:
    db.init_db()
except Exception as e:
    st.error("Could not load habit data. Please refresh the page.")


# Dialogs
@st.dialog("✨ Add New Habit")
def add_habit_dialog():
    with st.form("add_habit_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            emoji = st.selectbox("Icon", ["💧", "🏃‍♂️", "📖", "🧘", "🥦", "💻", "🏋️", "🎯", "😴", "🎨", "🎵", "✍️", "⚡", "🥗", "🧠", "🔥"], index=0)
        with col2:
            name = st.text_input("Habit Name", placeholder="e.g. Drink 3L Water")

        frequency = st.radio("Frequency", options=["daily", "weekdays"], format_func=lambda x: "Every Day" if x == "daily" else "Weekdays Only (Mon-Fri)")

        submitted = st.form_submit_button("Create Habit", use_container_width=True, type="primary")
        if submitted:
            if not name.strip():
                st.error("Please enter a title for your habit!")
            else:
                try:
                    db.add_habit(name, emoji, frequency)
                    st.toast(f"Added habit '{name.strip()}'!")
                    st.rerun()
                except Exception:
                    st.error("Something went wrong saving your habit. Please try again.")


@st.dialog("✏️ Edit Habit")
def edit_habit_dialog(habit):
    with st.form("edit_habit_form"):
        col1, col2 = st.columns([1, 4])
        emojis = ["💧", "🏃‍♂️", "📖", "🧘", "🥦", "💻", "🏋️", "🎯", "😴", "🎨", "🎵", "✍️", "⚡", "🥗", "🧠", "🔥"]
        curr_emoji_idx = emojis.index(habit["emoji"]) if habit["emoji"] in emojis else 0
        with col1:
            emoji = st.selectbox("Icon", emojis, index=curr_emoji_idx)
        with col2:
            name = st.text_input("Habit Name", value=habit["name"])

        curr_freq_idx = 0 if habit["frequency"] == "daily" else 1
        frequency = st.radio(
            "Frequency",
            options=["daily", "weekdays"],
            index=curr_freq_idx,
            format_func=lambda x: "Every Day" if x == "daily" else "Weekdays Only (Mon-Fri)"
        )

        submitted = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
        if submitted:
            if not name.strip():
                st.error("Habit title cannot be empty!")
            else:
                try:
                    db.update_habit(habit["id"], name, emoji, frequency)
                    st.toast("Habit updated!")
                    st.rerun()
                except Exception:
                    st.error("Something went wrong updating your habit. Please try again.")


def handle_toggle(habit_id: int, date_str: str):
    try:
        db.toggle_completion(habit_id, date_str)
    except Exception:
        pass


def main():
    # Header & Date Picker
    col_head, col_date = st.columns([2, 1])
    with col_head:
        st.markdown("<h1 style='margin-bottom:0;'>🔥 Vibe Habits</h1>", unsafe_allow_html=True)
    with col_date:
        selected_date = st.date_input("Target Date", value=date.today(), max_value=date.today())
        selected_date_str = selected_date.isoformat()

    # Load data
    try:
        all_habits = db.get_habits(include_archived=True)
        completions_map = db.get_all_completions_by_habit()
        today_completed_ids = db.get_completions_for_date(selected_date_str)
        start_date = db.get_challenge_start_date()
    except Exception:
        st.error("Unable to load data right now. Please refresh the page.")
        return

    active_habits = [h for h in all_habits if h['archived'] == 0]
    archived_habits = [h for h in all_habits if h['archived'] == 1]

    # Calculate Challenge Day Counter
    challenge_day = (selected_date - start_date).days + 1
    challenge_day_clamped = max(1, min(75, challenge_day))

    # Calculate Today Scheduled & Progress
    scheduled_today = [h for h in active_habits if streak.is_scheduled_day(selected_date, h['frequency'])]
    completed_today_count = sum(1 for h in scheduled_today if h['id'] in today_completed_ids)
    total_scheduled_count = len(scheduled_today)

    progress_pct = (completed_today_count / total_scheduled_count * 100) if total_scheduled_count > 0 else 100.0

    # Hero Challenge Banner
    is_weekend = selected_date.weekday() >= 5
    weekend_note = " (Weekend Rest Day 🎉)" if is_weekend else ""

    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-title">Day {challenge_day_clamped} / 75</div>
            <div class="hero-subtitle">
                {selected_date.strftime('%A, %b %d, %Y')}{weekend_note}<br/>
                <b>{completed_today_count} of {total_scheduled_count}</b> habits completed today ({int(progress_pct)}%)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(progress_pct / 100.0)
    st.write("")

    # Actions & Search bar row
    col_search, col_add = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("Search habits...", placeholder="🔍 Search habits by title...", label_visibility="collapsed")
    with col_add:
        if st.button("➕ New Habit", use_container_width=True, type="primary"):
            add_habit_dialog()

    # Tabs for views
    tab_today, tab_all, tab_archive = st.tabs([
        f"📅 Today's Focus ({total_scheduled_count})",
        f"📋 All Active ({len(active_habits)})",
        f"📦 Archived ({len(archived_habits)})"
    ])

    # Filter by search in-memory
    def filter_habits(habit_list):
        if not search_query.strip():
            return habit_list
        q = search_query.strip().lower()
        return [h for h in habit_list if q in h['name'].lower()]

    # Render tab: Today's Focus
    with tab_today:
        filtered_today = filter_habits(scheduled_today)

        if not scheduled_today:
            st.info("🎉 No habits scheduled for today! (Weekday habits automatically rest on weekends).")
        elif not filtered_today:
            st.info("No habits match your search.")
        else:
            for habit in filtered_today:
                render_habit_card(habit, selected_date, completions_map.get(habit['id'], []), selected_date_str in completions_map.get(habit['id'], []), context="today")

    # Render tab: All Active Habits
    with tab_all:
        filtered_active = filter_habits(active_habits)
        if not filtered_active:
            if not active_habits:
                st.info("No active habits yet. Click '+ New Habit' above to create your first habit!")
            else:
                st.info("No habits match your search.")
        else:
            for habit in filtered_active:
                render_habit_card(habit, selected_date, completions_map.get(habit['id'], []), selected_date_str in completions_map.get(habit['id'], []), context="active")

    # Render tab: Archived Habits
    with tab_archive:
        filtered_archived = filter_habits(archived_habits)
        if not filtered_archived:
            if not archived_habits:
                st.info("No archived habits.")
            else:
                st.info("No archived habits match your search.")
        else:
            for habit in filtered_archived:
                render_archived_card(habit, completions_map.get(habit['id'], []))


def render_habit_card(habit, target_date: date, completion_dates: list, is_completed: bool, context: str = "default"):
    curr_streak = streak.calculate_current_streak(habit['frequency'], completion_dates, today=target_date)
    best_streak = streak.calculate_best_streak(habit['frequency'], completion_dates)

    h_id = habit['id']

    card_container = st.container()
    with card_container:
        col_check, col_info, col_streaks, col_actions = st.columns([0.6, 3, 2, 1.2])

        with col_check:
            # Checkbox toggle with instant state sync
            checked = st.checkbox(
                "Complete",
                value=is_completed,
                key=f"check_{context}_{h_id}_{target_date.isoformat()}",
                label_visibility="collapsed",
                on_change=handle_toggle,
                args=(h_id, target_date.isoformat()),
            )

        with col_info:
            freq_label = "DAILY" if habit['frequency'] == "daily" else "WEEKDAYS"
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.5rem;">{habit['emoji']}</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.05rem; color: {'#94a3b8' if is_completed else '#f8fafc'}; text-decoration: {'line-through' if is_completed else 'none'};">
                            {habit['name']}
                        </div>
                        <span class="badge-freq">{freq_label}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_streaks:
            st.markdown(
                f"""
                <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                    <span class="badge-streak" title="Current streak">🔥 {curr_streak}</span>
                    <span class="badge-best" title="Best streak ever">⭐ {best_streak}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_actions:
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("✏️", key=f"edit_{context}_{h_id}", help="Edit habit"):
                    edit_habit_dialog(habit)
            with col_act2:
                if st.button("📦", key=f"archive_{context}_{h_id}", help="Archive habit"):
                    try:
                        db.archive_habit(h_id)
                        st.toast(f"Archived '{habit['name']}'")
                        st.rerun()
                    except Exception:
                        st.error("Could not archive habit. Please try again.")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


def render_archived_card(habit, completion_dates: list):
    best_streak = streak.calculate_best_streak(habit['frequency'], completion_dates)

    st.markdown(
        f"""
        <div class="habit-card" style="opacity: 0.6;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.4rem;">{habit['emoji']}</span>
                    <div>
                        <div style="font-weight: 600;">{habit['name']} (Archived)</div>
                        <span class="badge-best">⭐ Best Streak: {best_streak}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_unarch, col_space = st.columns([1, 4])
    with col_unarch:
        if st.button("Unarchive", key=f"unarchive_{habit['id']}", type="secondary"):
            try:
                db.unarchive_habit(habit['id'])
                st.toast(f"Restored '{habit['name']}' to active habits!")
                st.rerun()
            except Exception:
                st.error("Could not unarchive habit. Please try again.")


if __name__ == "__main__":
    main()