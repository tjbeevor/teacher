import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from cachetools import TTLCache
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

# Apply CSS styles
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
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}
.stChat {border-radius: 8px; margin-bottom: 1rem;}
.stTextInput>div>div>input {border-radius: 8px;}
.quiz-container {
    background-color: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-top: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.stSelectbox {margin-bottom: 1rem;}
.stRadio > label {
    background-color: #f8fafc;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Classes for caching, API, quiz generation, and progress tracking
class CachingSystem:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self._get_cached_response = lru_cache(maxsize=100)(self._get_cached_response)

    def _get_cached_response(self, prompt: str):
        return self.cache.get(prompt)

    def get_cached_response(self, prompt: str):
        return self._get_cached_response(prompt)

    def cache_response(self, prompt: str, response: str):
        self.cache[prompt] = response

class APIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = CachingSystem()
        self.executor = ThreadPoolExecutor(max_workers=4)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_content(self, prompt: str) -> str:
        if not prompt:
            return "I apologize, but I need a prompt to generate a response."

        cached_response = self.cache.get_cached_response(prompt)
        if cached_response:
            return cached_response

        try:
            response = self.executor.submit(
                lambda: self.model.generate_content(prompt)
            ).result()
            if response and response.text:
                self.cache.cache_response(prompt, response.text)
                return response.text
            else:
                return "I couldn't generate a proper response. Let me try a different approach."
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return "I encountered an error while generating content."

class QuizGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def generate_quiz(self, subject: str, topic: str, difficulty: str, num_questions: int = 5) -> dict:
        prompt = f"""Create a quiz about {topic} in {subject} at {difficulty} level. 
        Generate {num_questions} questions. Format: JSON list of questions with options, correct answer, and explanation."""
        try:
            response = self.api_client.generate_content(prompt)
            return json.loads(response)
        except Exception as e:
            st.error(f"Quiz generation failed: {str(e)}")
            return None

class ProgressTracker:
    def __init__(self):
        self.history_file = "progress_history.json"

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load history: {e}")
            return []

    def save_progress(self, user, subject, topic, quiz_score, timestamp=None):
        history = self.load_history()
        history.append({
            'user': user,
            'subject': subject,
            'topic': topic,
            'score': quiz_score,
            'timestamp': timestamp or datetime.now().isoformat()
        })
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f)
        except Exception as e:
            st.warning(f"Could not save progress: {e}")

# AI Tutor Class
class AITutor:
    def __init__(self):
        if 'GOOGLE_API_KEY' not in st.secrets:
            st.error("🔑 GOOGLE_API_KEY not found in secrets!")
            st.stop()
        self.api_client = APIClient(st.secrets['GOOGLE_API_KEY'])
        self.quiz_generator = QuizGenerator(self.api_client)
        self.progress_tracker = ProgressTracker()
        self.current_subject = None
        self.current_topic = None

    def initialize_session(self, subject: str, level: str, prerequisites: str, topic: str) -> str:
        self.current_subject = subject
        self.current_topic = topic
        prompt = f"""Create an introduction for a {level} level student learning {topic} in {subject}. Background: {prerequisites}."""
        return self.api_client.generate_content(prompt)

    def send_message(self, message: str) -> str:
        prompt = f"""As a tutor teaching {self.current_topic} in {self.current_subject}, respond to: {message}."""
        return self.api_client.generate_content(prompt)

# Main Function
def main():
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()

    # Add your sidebar, chat UI, quiz handling, and data visualization logic here
    # Example: starting a session
    if st.button("🚀 Start New Session"):
        st.session_state.tutor.initialize_session(
            "Mathematics", "Beginner", "Basic Algebra", "Linear Equations"
        )

if __name__ == "__main__":
    main()
