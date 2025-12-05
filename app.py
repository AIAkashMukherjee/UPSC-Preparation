# app.py
import streamlit as st
from src.utils.db_utils import init_storage, save_result, load_user_history
from src.question_generator import select_questions_for_quiz
# Initialize DB and folders once
init_storage()

st.title("UPSC Quiz")

# ---- Step 4: User Identification ----
user_id = st.sidebar.text_input("Enter your name or ID", value="student_1")

# ... your quiz logic (loading questions_bank.json, running quiz, computing score) ...

st.sidebar.header("Quiz Settings")

topic = st.sidebar.selectbox(
    "Topic",
    ["Medieval History", "Modern History", "Polity", "Geography"],
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["easy", "medium", "hard"],
)

n_questions = st.sidebar.number_input(
    "Number of questions",
    min_value=5,
    max_value=50,
    value=15,
    step=5,
)

preloaded_only = st.sidebar.checkbox(
    "Only use pre-loaded questions (faster & no cost)",
    value=False,
)

if st.sidebar.button("Start Quiz"):
    try:
        questions, from_bank_count = select_questions_for_quiz(
            topic=topic,
            difficulty=difficulty,
            n_questions=n_questions,
            preloaded_only=preloaded_only,
        )
    except NotImplementedError:
        st.error("Groq integration not implemented yet in generate_questions_with_groq().")
        st.stop()

    if preloaded_only and len(questions) < n_questions:
        st.warning(
            f"Only {len(questions)} questions available for {topic} – {difficulty}. "
            "Quiz shortened to available questions (no API used)."
        )

    st.session_state.current_questions = questions
    st.session_state.current_topic = topic
    st.session_state.current_difficulty = difficulty

    st.success(
        f"Loaded {len(questions)} questions "
        f"({from_bank_count} from bank/cache, {len(questions) - from_bank_count} new)."
    )




if "quiz_finished" in st.session_state and st.session_state.quiz_finished:
    if st.button("Save my result"):
        percentage, csv_path = save_result(
            user_id=user_id,
            topic=st.session_state.topic,
            difficulty=st.session_state.difficulty,
            score=st.session_state.score,
            total_questions=st.session_state.total_questions,
        )
        st.success(f"Result saved! Score: {st.session_state.score}/{st.session_state.total_questions} ({percentage}%).")
        st.caption(f"CSV saved at: {csv_path}")

# ---- Step 5: View History ----
st.sidebar.markdown("---")
if st.sidebar.button("Show my quiz history"):
    hist_df = load_user_history(user_id)
    if hist_df.empty:
        st.sidebar.write("No attempts found yet.")
    else:
        st.sidebar.write("Your quiz history:")
        st.sidebar.dataframe(hist_df)

        # Optional: simple score-over-time chart
        st.sidebar.line_chart(hist_df.set_index("timestamp")["percentage"])
