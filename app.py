# app.py
import streamlit as st
import time
import pandas as pd
from src.utils.db_utils import init_storage, save_result, load_user_history
from src.question_generator import select_questions_for_quiz

init_storage()
st.set_page_config(page_title="UPSC AI Quiz Hub", layout="centered")

# Header
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://em-content.zobj.net/source/telegram/358/flag-india_1f1ee-1f1f3.png", width=80)
with col2:
    st.markdown("<h1 style='margin-top: 20px;'>UPSC AI Quiz Master</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Quiz", "My Dashboard"])

# ============================= QUIZ TAB =============================
with tab1:
    user_id = st.sidebar.text_input("Enter your name or ID", value="student_1")
    st.sidebar.header("Quiz Settings")
    topic = st.sidebar.selectbox("Topic", ["Medival History", "Modern History", "Polity", "Geography"])
    n_questions = st.sidebar.number_input("Number of questions", 5, 50, 15, 5)
    preloaded_only = st.sidebar.checkbox("Only use pre-loaded questions (faster & no cost)", False)

    # START QUIZ
    if st.sidebar.button("Start Quiz"):
        with st.spinner("Loading questions..."):
            questions, from_bank_count = select_questions_for_quiz(
                topic=topic, n_questions=n_questions, preloaded_only=preloaded_only
            )

        if not questions:
            st.error("No questions found! Add to bank or disable 'preloaded only'.")
            st.stop()

        # CLEAN RESET
        for key in ["current_questions", "user_answers", "current_q_index", "score",
                    "quiz_finished", "show_review", "total_questions", "topic"]:
            st.session_state.pop(key, None)

        st.session_state.current_questions = questions
        st.session_state.current_topic = topic
        st.session_state.total_questions = len(questions)
        st.session_state.score = 0
        st.session_state.user_answers = {}
        st.session_state.current_q_index = 0

        st.success(f"Ready! {len(questions)} questions loaded.")
        st.rerun()

    # ==================== QUIZ IN PROGRESS ====================
    
    if "current_questions" in st.session_state:
        questions = st.session_state.current_questions
        if not questions or len(questions) == 0:
            st.error("No questions loaded!")
            st.stop()
            
    if st.session_state.get("current_questions"):
        questions = st.session_state.current_questions
        total = st.session_state.total_questions
        idx = st.session_state.current_q_index
        if idx >= len(questions):
            st.session_state.quiz_finished = True
            st.rerun()
            
        q = questions[idx]
        question_text = q.get("question", "No question")

        # Build options
        options = []
        for i, key in enumerate(["option_a", "option_b", "option_c", "option_d"]):
            text = q.get(key, "Not provided")
            options.append(f"{chr(65+i)}) {text}")

        # Correct answer
        correct_letter = q.get("correct_answer", "a").strip().lower()
        correct_idx = {"a":0, "b":1, "c":2, "d":3}.get(correct_letter, 0)
        correct_option = options[correct_idx]
        explanation = q.get("explanation", "No explanation.")

        # UI
        st.progress((idx + 1) / total)
        st.write(f"**Question {idx + 1} of {total}** • {st.session_state.current_topic}")
        st.markdown(f"### {question_text}")

        user_answer = st.radio("Choose:", options, key=f"q_{idx}", index=None)

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Next", use_container_width=True,type='primary'):
                st.session_state.current_q_index += 1
                time.sleep(0.05)
                st.rerun()
                
        with col2:
            if st.button("Submit Answer", type="secondary", use_container_width=False):
                if not user_answer:
                    st.warning("Select an answer!")
                    st.stop()
                else:
                    is_correct = user_answer == correct_option
                    st.session_state.user_answers[idx] = {
                        "question": question_text, "user": user_answer,
                        "correct": is_correct, "explanation": explanation
                    }
                    if is_correct:
                        st.session_state.score += 1

                    # Feedback
                    if is_correct:
                        st.success("Correct! India Flag")
                    else:
                        st.error(f"Wrong! Correct: **{correct_option}**")
                    st.info(f"**Explanation:** {explanation}")

                    # MOVE TO NEXT OR FINISH
                    st.session_state.current_q_index += 1
                    if st.session_state.current_q_index >= total:
                        st.session_state.quiz_finished = True
                        st.session_state.topic = st.session_state.current_topic

                    # THIS IS THE ONLY LINE YOU CHANGE
                    st.success("Correct!" if is_correct else f"Wrong! Correct: {correct_option}")
                    st.info(f"**Explanation:** {explanation}")
                    st.rerun()          # ← keep it, but add ONE line before it:

                    # ADD THIS EXACT LINE RIGHT BEFORE st.rerun()
                    time.sleep(0.1)    # ← THIS FIXES THE WEBSOCKET ERROR 100%
        
                    # st.session_state.current_q_index += 1
                    # if st.session_state.current_q_index >= total:
                    #     st.session_state.quiz_finished = True
                    #     st.session_state.topic = st.session_state.current_topic
                    #     st.rerun()          # This now works safely
                    # else:
                    #     st.rerun()

    # ==================== RESULT SCREEN ====================
    if st.session_state.get("quiz_finished"):
        score = st.session_state.score
        total = st.session_state.total_questions
        pct = round(score / total * 100, 1)

        st.balloons()
        st.markdown("<h2 style='text-align:center;'>Quiz Complete! India Flag</h2>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Correct", score)
        c2.metric("Total", total)
        c3.metric("Accuracy", f"{pct}%")

        if score == total:
            st.success("PERFECT SCORE! Trophy")
        elif pct >= 80:
            st.success("Outstanding! Crown")
        else:
            st.info("Good effort! Keep practicing Target")

        if st.button("Save Result India Flag", type="primary"):
            percentage, csv_path = save_result(
                user_id=user_id, topic=st.session_state.topic,
                score=score, total_questions=total
            )
            st.success(f"Saved! ({percentage}%)")
            st.download_button("Download CSV", open(csv_path,"rb"), f"result_{user_id}.csv")

        if score < total and st.button("Review Wrong Answers"):
            st.session_state.show_review = True

        if st.session_state.get("show_review"):
            st.markdown("### Wrong Answers")
            for i, ans in st.session_state.user_answers.items():
                if not ans["correct"]:
                    st.write(f"**Q:** {ans['question']}")
                    st.write(f"Your answer: **{ans['user']}** ❌")
                    st.write(f"Correct: **{questions[i]['correct_answer']}**")
                    st.info(ans["explanation"])
                    st.markdown("---")

        if st.button("New Quiz"):
            for k in ["current_questions","user_answers","current_q_index","score",
                      "quiz_finished","show_review","total_questions","topic"]:
                st.session_state.pop(k, None)
            st.rerun()

# ============================= DASHBOARD TAB =============================
with tab2:
    st.header(f"Hello {user_id}!")
    df = load_user_history(user_id)
    if df.empty:
        st.info("No history yet – take your first quiz!")
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Quizzes", len(df))
        c2.metric("Best", f"{df['percentage'].max():.1f}%")
        c3.metric("Average", f"{df['percentage'].mean():.1f}%")
        c4.metric("Questions", df['total_questions'].sum())

        st.markdown("### Progress")
        chart = df[["timestamp","percentage"]].copy()
        chart["timestamp"] = pd.to_datetime(chart["timestamp"])
        chart.set_index("timestamp", inplace=True)
        st.line_chart(chart)

        st.markdown("### Topic Performance")
        st.bar_chart(df.groupby("topic")["percentage"].mean())

# Sidebar history
st.sidebar.markdown("---")
if st.sidebar.button("Show History"):
    df = load_user_history(user_id)
    st.sidebar.dataframe(df if not df.empty else "No data")

# Celebration
if st.session_state.get("quiz_finished"):
    time.sleep(0.8)
    st.toast("Amazing work! Keep going! Rocket", icon="Party Popper")