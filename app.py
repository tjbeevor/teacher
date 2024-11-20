import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

os.environ["STREAMLIT_SERVER_WATCH_PATCHING"] = "false"

st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        .main-header {
            font-family: 'Helvetica Neue', sans-serif;
            color: #1E3A8A;
            padding: 1rem 0;
            text-align: center;
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            background-color: #1E3A8A;
            color: white;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #2563EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .chat-container {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .chat-message {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: flex-end;
        }
        .user-message {
            background-color: #E5E7EB;
            color: #374151;
            margin-right: auto;
        }
        .tutor-message {
            background-color: #E9D5FF;
            color: #4C1D95;
            margin-left: auto;
        }
        .tutor-message p {margin-bottom: 0.3rem;}
        .quiz-container {
            background-color: #f0f0f5;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

class QuizGenerator:
    def __init__(self, model):
        self.model = model

    def generate_quiz(self, subject, topic, difficulty, num_questions):
        try:
            prompt = f"""
            Generate a quiz on {topic} within {subject} with {num_questions} questions. 
            The difficulty level should be {difficulty}. 

            Structure the response as a JSON object with the following format:

            {{
              "topic": "{topic}",
              "subject": "{subject}",
              "difficulty": "{difficulty}",
              "questions": [
                {{
                  "question": "question text",
                  "options": ["option1", "option2", "option3", "option4"],
                  "answer": "correct answer (one of the options)",
                  "explanation": "detailed explanation of the answer"
                }},
                // ... more questions
              ]
            }}
            """
            response = self.model.generate(prompt)
            return json.loads(response.text)
        except Exception as e:
            return f"Error: {str(e)}"

class ProgressTracker:
    def __init__(self, file_path="progress_history.json"):
        self.file_path = file_path
        self.load_history()

    def load_history(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_progress(self, user_name, subject, topic, score):
        history = self.load_history()
        history.append({
            "user": user_name,
            "subject": subject,
            "topic": topic,
            "score": score,
            "timestamp": datetime.now().isoformat()
        })
        with open(self.file_path, "w") as f:
            json.dump(history, f)

class AITutor:
    def __init__(self, api_key):
        genai.api_key = api_key
        self.model = genai.GenerativeModel("gemini-pro")
        self.quiz_generator = QuizGenerator(self.model)
        self.progress_tracker = ProgressTracker()
        self.chat = None
        self.current_subject = None
        self.current_topic = None

    def initialize_session(self, subject, topic):
        self.chat = self.model.start_chat()
        self.current_subject = subject
        self.current_topic = topic
        return self.chat.send_message(f"I want to learn about {topic} in {subject}.")

    def send_message(self, message):
        if not self.chat:
            return "Please start a new session first."
        try:
            follow_up_prompt = f"""
            The student's response was: "{message}"

            Structure your response as follows:

            1. Acknowledge their answer directly and provide encouragement.
            2. Give specific feedback:
               - If correct: Confirm and elaborate briefly.
               - If partially correct: Clarify misunderstandings.
               - If incorrect: Gently explain why and provide the correct answer.
            3. Based on their answer, determine the next concept to teach or revisit the current one if needed.
               - Start with a clear introduction of the concept.
               - Provide a thorough explanation with multiple examples.
               - Include real-world applications and analogies.
               - Show variations or special cases, and highlight common pitfalls.
               - Give practical tips.
            4. End with a question about the concept just taught.

            Keep your response:
            - Natural and conversational, without visible section markers.
            - Rich in examples and explanations, clear and engaging.
            - Comprehensive with detailed explanations and multiple examples.
            """

            response = self.chat.send_message(follow_up_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.markdown("<h1 class='main-header'>🎓 AI Tutor</h1>", unsafe_allow_html=True)

    if "api_key" not in st.session_state:
        # Retrieve API key from secrets.toml
        api_key = st.secrets["google_gemini"]["api_key"] 
        st.session_state.api_key = api_key
        st.session_state.tutor = AITutor(api_key)
        st.experimental_rerun()  # Rerun to initialize the tutor with the API key
    else:
        # Initialize session state variables
        if 'quiz_active' not in st.session_state:
            st.session_state.quiz_active = False
        if 'current_quiz' not in st.session_state:
            st.session_state.current_quiz = None
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        if 'quiz_score' not in st.session_state:
            st.session_state.quiz_score = 0

        subject = st.sidebar.selectbox(
            "Select a subject:",
            ("Physics", "Chemistry", "Mathematics", "Biology", "History", "Computer Science")
        )
        topic = st.sidebar.text_input("Enter a topic:")
        difficulty = st.sidebar.selectbox(
            "Select difficulty:",
            ("Easy", "Medium", "Hard")
        )
        user_name = st.sidebar.text_input("Enter your name:")

        if st.sidebar.button("Start New Session"):
            if not user_name:
                st.warning("Please enter your name.")
            elif not topic:
                st.warning("Please enter a topic.")
            else:
                st.session_state.tutor.initialize_session(subject, topic)
                st.session_state.messages = []

        if st.sidebar.button("Reset Session"):
            st.session_state.tutor.chat = None
            st.session_state.messages = []
            st.session_state.quiz_active = False
            st.session_state.current_quiz = None
            st.session_state.current_question = 0
            st.session_state.quiz_score = 0

        if st.sidebar.button("Take a Quiz"):
            if not st.session_state.tutor.chat:
                st.warning("Please start a learning session first.")
            else:
                num_questions = st.sidebar.number_input("Number of questions:", min_value=1, max_value=10, value=5)
                st.session_state.current_quiz = st.session_state.tutor.quiz_generator.generate_quiz(
                    subject, topic, difficulty, num_questions
                )
                st.session_state.current_question = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_active = True

        if st.session_state.tutor.chat:
            message = st.text_input("Your message:")
            if st.button("Send"):
                if message:
                    with st.spinner("Thinking..."):
                        response = st.session_state.tutor.send_message(message)
                    st.session_state.messages.append({"role": "user", "content": message})
                    st.session_state.messages.append({"role": "tutor", "content": response})

            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-container'><div class='chat-message user-message'>{msg['content']}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-container'><div class='chat-message tutor-message'>{msg['content']}</div></div>", unsafe_allow_html=True)

            if st.session_state.quiz_active:
                question = st.session_state.current_quiz['questions'][st.session_state.current_question]
                st.markdown(f"<div class='quiz-container'><b>Question {st.session_state.current_question + 1}:</b> {question['question']}</div>", unsafe_allow_html=True)
                selected_answer = st.radio("Select your answer:", question['options'])
                if st.button("Submit Answer"):
                    if selected_answer == question['answer']:
                        st.session_state.quiz_score += 1
                        st.success(f"✅ Correct! {question['explanation']}")
                    else:
                        st.error(f"❌ Incorrect. {question['explanation']}")
                
                if st.session_state.current_question < len(st.session_state.current_quiz['questions']) - 1:
                    st.session_state.current_question += 1
                else:
                    final_score = (st.session_state.quiz_score / len(st.session_state.current_quiz['questions'])) * 100
                    st.session_state.tutor.progress_tracker.save_progress(
                        user_name,
                        subject,
                        topic,
                        final_score
                    )
                    st.session_state.quiz_active = False
                    st.success(f"🎉 Quiz completed! Score: {final_score}%")
        
        progress_data = st.session_state.tutor.progress_tracker.load_history()
        if progress_data:
            df = pd.DataFrame(progress_data)
            fig = px.line(df, x='timestamp', y='score', color='subject',
                         title='Performance Over Time',
                         template='seaborn')
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font={'color': '#1E3A8A'},
                title={'font': {'size': 20}},
                xaxis={'gridcolor': '#E2E8F0'},
                yaxis={'gridcolor': '#E2E8F0'}
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
