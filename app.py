import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Security check for API key
if 'GOOGLE_API_KEY' not in st.secrets:
    st.error('Error: GOOGLE_API_KEY not found in secrets.')
    st.markdown("""
        ### Configuration Required
        1. Create `.streamlit/secrets.toml` from the example file
        2. Add your Google Gemini API key to the secrets file
        3. Restart the application
    """)
    st.stop()

# Configure Gemini API
genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])

# Configure page
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better UI
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

class QuizGenerator:
    def __init__(self, model):
        self.model = model

    def generate_quiz(self, subject, topic, difficulty, num_questions=5):
        prompt = f"""Generate a quiz about {topic} in {subject} at {difficulty} level.
        Create {num_questions} questions in the following JSON format:
        {{
            "questions": [
                {{
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "Correct option",
                    "explanation": "Explanation of the answer"
                }}
            ]
        }}"""
        
        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except:
            st.error("Failed to generate quiz. Please try again.")
            return None

class ProgressTracker:
    def __init__(self):
        self.history_file = "progress_history.json"
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Could not load progress history: {e}")
        return []
    
    def save_progress(self, user, subject, topic, quiz_score, timestamp=None):
        try:
            history = self.load_history()
            history.append({
                'user': user,
                'subject': subject,
                'topic': topic,
                'score': quiz_score,
                'timestamp': timestamp or datetime.now().isoformat()
            })
            with open(self.history_file, 'w') as f:
                json.dump(history, f)
        except Exception as e:
            st.warning(f"Could not save progress: {e}")

class AITutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.quiz_generator = QuizGenerator(self.model)
        self.progress_tracker = ProgressTracker()
        self.chat = None
        self.current_subject = None
        self.current_topic = None
    
    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"""Act as an expert tutor in {subject}. You are teaching a student at {level} who has {prerequisites}.
        Current topic: {topic}
        
        Teaching Style:
        - Use the Socratic method
        - Break down complex concepts
        - Provide examples
        - Check understanding frequently
        - Adjust difficulty based on responses
        
        Start by introducing the topic and asking an assessment question."""
        
        try:
            self.chat = self.model.start_chat(history=[])
            self.current_subject = subject
            self.current_topic = topic
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Error initializing session: {str(e)}"
    
    def send_message(self, message):
        if not self.chat:
            return "Please start a new session first."
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.title("🎓 AI Tutor")
    
    # Initialize session state
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False
    
    # Sidebar for session configuration
    with st.sidebar:
        st.header("Session Settings")
        
        # User information
        user_name = st.text_input("Your Name", key="user_name")
        
        # Subject selection
        subjects = ["Python Programming", "Mathematics", "Physics", "Chemistry", "History"]
        subject = st.selectbox("Subject", subjects)
        
        # Level selection
        levels = ["Beginner", "Intermediate", "Advanced"]
        level = st.selectbox("Level", levels)
        
        # Topic input
        topic = st.text_input("Specific Topic")
        
        # Prerequisites input
        prerequisites = st.text_area("Prerequisites")
        
        start_session = st.button("Start New Session")
        if start_session:
            if not topic or not prerequisites:
                st.error("Please fill in both Topic and Prerequisites")
            else:
                with st.spinner("Initializing session..."):
                    response = st.session_state.tutor.initialize_session(
                        subject, level, prerequisites, topic
                    )
                    st.session_state.messages = []
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.quiz_active = False
                st.success("Session started!")
    
    # Main chat interface
    chat_col, viz_col = st.columns([2, 1])
    
    with chat_col:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask your question..."):
            if not st.session_state.quiz_active:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Thinking..."):
                    response = st.session_state.tutor.send_message(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    with viz_col:
        st.header("Learning Progress")
        
        # Quiz button
        if st.button("Take Quiz"):
            st.session_state.quiz_active = True
            with st.spinner("Generating quiz..."):
                quiz_data = st.session_state.tutor.quiz_generator.generate_quiz(
                    subject,
                    topic,
                    level
                )
            if quiz_data:
                st.session_state.current_quiz = quiz_data
                st.session_state.quiz_score = 0
                st.session_state.current_question = 0
        
        # Display quiz if active
        if st.session_state.quiz_active and hasattr(st.session_state, 'current_quiz'):
            question = st.session_state.current_quiz['questions'][st.session_state.current_question]
            
            st.subheader(f"Question {st.session_state.current_question + 1}")
            st.write(question['question'])
            
            answer = st.radio("Select your answer:", question['options'], key=f"q_{st.session_state.current_question}")
            
            if st.button("Submit Answer"):
                if answer == question['correct_answer']:
                    st.session_state.quiz_score += 1
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. {question['explanation']}")
                
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
                    st.success(f"Quiz completed! Score: {final_score}%")
        
        # Display progress graph
        progress_data = st.session_state.tutor.progress_tracker.load_history()
        if progress_data:
            df = pd.DataFrame(progress_data)
            fig = px.line(df, x='timestamp', y='score', color='subject',
                         title='Learning Progress Over Time')
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
