import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Configuration
os.environ["STREAMLIT_SERVER_WATCH_PATCHING"] = "false"

# Page configuration
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'quiz_active' not in st.session_state:
    st.session_state.quiz_active = False
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0

# [Previous CSS styles and class definitions remain the same...]

def main():
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    if 'teaching_state' not in st.session_state:
        st.session_state.teaching_state = 'initialize'

    # Initialize required variables
    with st.sidebar:
        st.title("📚 Learning Settings")
        user_name = st.text_input("Your Name", "Student")
        subject = st.selectbox(
            "Select Subject",
            ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
        )
        level = st.selectbox(
            "Select Level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        topic = st.text_input("Enter Topic", "")
        prerequisites = st.text_area("Your Background", "")

    chat_col, viz_col = st.columns([2, 1])

    with chat_col:
        st.markdown("""
        <div class='chat-container'>
            <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
        </div>
        """, unsafe_allow_html=True)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.teaching_state == 'initialize':
            if st.button("🚀 Start Learning"):
                with st.spinner("🔄 Preparing your lesson..."):
                    response = st.session_state.tutor.initialize_session(subject, level, prerequisites, topic)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.teaching_state = 'teach_topic'
                st.experimental_rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            with st.spinner("🔄 Preparing the next topic..."):
                topic_content = st.session_state.tutor.teach_topic()
            st.session_state.messages.append({"role": "assistant", "content": f"{topic_content['lesson']}\n\nExamples:\n{topic_content['examples']}\n\nQuestion: {topic_content['question']}"})
            st.session_state.teaching_state = 'wait_for_answer'
            st.experimental_rerun()

        elif st.session_state.teaching_state == 'wait_for_answer':
            if prompt := st.chat_input("💭 Type your answer here..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("🤔 Evaluating your answer..."):
                    evaluation = st.session_state.tutor.evaluate_answer(
                        st.session_state.last_question, prompt)
                feedback = f"{evaluation['feedback']}"
                st.session_state.messages.append({"role": "assistant", "content": feedback})
                
                if evaluation['move_on']:
                    if st.session_state.tutor.move_to_next_topic():
                        st.session_state.teaching_state = 'teach_topic'
                    else:
                        st.session_state.teaching_state = 'finished'
                st.experimental_rerun()

        elif st.session_state.teaching_state == 'finished':
            st.success("🎉 Congratulations! You've completed all topics in this lesson.")
            if st.button("📝 Take Quiz"):
                st.session_state.quiz_active = True
                with st.spinner("⚙️ Generating quiz..."):
                    quiz_data = st.session_state.tutor.quiz_generator.generate_quiz(
                        subject, topic, level
                    )
                    if quiz_data:
                        st.session_state.current_quiz = quiz_data
                        st.session_state.quiz_score = 0
                        st.session_state.current_question = 0
                st.experimental_rerun()

    with viz_col:
        st.markdown("""
        <div class='chat-container'>
            <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>📈 Learning Progress</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.quiz_active and st.session_state.current_quiz:
            quiz_data = st.session_state.current_quiz
            current_q = st.session_state.current_question

            if current_q < len(quiz_data['questions']):
                question = quiz_data['questions'][current_q]
                st.subheader(f"Question {current_q + 1}")
                st.write(question['question'])
                answer = st.radio(
                    "Select your answer:",
                    question['options'],
                    key=f"q_{current_q}"
                )

                if st.button("Submit Answer", key=f"submit_{current_q}"):
                    if answer == question['correct_answer']:
                        st.session_state.quiz_score += 1
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect. {question['explanation']}")

                    if current_q < len(quiz_data['questions']) - 1:
                        st.session_state.current_question += 1
                        st.experimental_rerun()
                    else:
                        final_score = (st.session_state.quiz_score / len(quiz_data['questions'])) * 100
                        st.session_state.tutor.progress_tracker.save_progress(
                            user_name, subject, topic, final_score
                        )
                        st.session_state.quiz_active = False
                        st.success(f"🎉 Quiz completed! Score: {final_score}%")

        try:
            progress_data = st.session_state.tutor.progress_tracker.load_history()
            if progress_data and len(progress_data) > 0:
                df = pd.DataFrame(progress_data)
                fig = px.line(
                    df, 
                    x='timestamp', 
                    y='score', 
                    color='subject',
                    title='Performance Over Time',
                    template='seaborn'
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font={'color': '#1E3A8A'},
                    title={'font': {'size': 20}},
                    xaxis={'gridcolor': '#E2E8F0'},
                    yaxis={'gridcolor': '#E2E8F0'}
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("No progress data available yet.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")
