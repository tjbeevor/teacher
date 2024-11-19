import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import asyncio
import aiohttp
from functools import lru_cache
from typing import Dict, List, Optional
import redis
from concurrent.futures import ThreadPoolExecutor

# Configuration
os.environ["STREAMLIT_SERVER_WATCH_PATCHING"] = "false"

# Redis configuration for caching
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(REDIS_URL)

# Page configuration
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

# Apply the same CSS styles as before
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

class APICache:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.cache_ttl = 3600  # 1 hour cache

    def get_cache_key(self, prompt: str) -> str:
        return f"ai_tutor:{hash(prompt)}"

    def get_cached_response(self, prompt: str) -> Optional[str]:
        cache_key = self.get_cache_key(prompt)
        return self.redis_client.get(cache_key)

    def cache_response(self, prompt: str, response: str):
        cache_key = self.get_cache_key(prompt)
        self.redis_client.setex(cache_key, self.cache_ttl, response)

class AsyncAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = APICache(redis_client)
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    @lru_cache(maxsize=100)
    async def generate_content(self, prompt: str) -> str:
        # Check cache first
        cached_response = self.cache.get_cached_response(prompt)
        if cached_response:
            return cached_response.decode('utf-8')

        # If not in cache, make API call
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Run API call in thread pool to prevent blocking
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: model.generate_content(prompt).text
            )
            
            # Cache the response
            self.cache.cache_response(prompt, response)
            return response
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None

class QuizGenerator:
    def __init__(self, api_client: AsyncAPIClient):
        self.api_client = api_client

    async def generate_quiz(self, subject: str, topic: str, difficulty: str, num_questions: int = 5) -> Dict:
        prompt = f"""Create a quiz about {topic} in {subject} at {difficulty} level.
        Generate exactly {num_questions} questions based on what we've discussed.
        
        Format each question like this:
        {{
            "questions": [
                {{
                    "question": "Write a clear, focused question about a single concept",
                    "options": [
                        "A) First option",
                        "B) Second option",
                        "C) Third option",
                        "D) Fourth option"
                    ],
                    "correct_answer": "A) First option",
                    "explanation": "Brief explanation of why this answer is correct"
                }}
            ]
        }}"""
        
        try:
            response = await self.api_client.generate_content(prompt)
            return json.loads(response)
        except Exception as e:
            st.error(f"Failed to generate quiz: {str(e)}")
            return None

class ProgressTracker:
    def __init__(self):
        self.history_file = "progress_history.json"
    
    def load_history(self) -> List[Dict]:
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Could not load progress history: {e}")
        return []
    
    def save_progress(self, user: str, subject: str, topic: str, quiz_score: float, timestamp: Optional[str] = None):
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
    def __init__(self, api_client: AsyncAPIClient):
        self.api_client = api_client
        self.quiz_generator = QuizGenerator(api_client)
        self.progress_tracker = ProgressTracker()
        self.chat_history = []
        self.current_subject = None
        self.current_topic = None

    async def initialize_session(self, subject: str, level: str, prerequisites: str, topic: str) -> str:
        prompt = f"""You are a helpful and encouraging tutor teaching {subject} at {level} level.
        The student's background is: {prerequisites}
        Current topic: {topic}

        Begin by:
        1. Warmly welcome the student
        2. Very briefly introduce the topic
        3. Start teaching the first key concept
        4. Ask one simple question to check understanding

        Keep your responses:
        - Natural and conversational
        - Clear and focused
        - One concept at a time
        - Without any special formatting
        
        Start the lesson now."""
        
        try:
            self.current_subject = subject
            self.current_topic = topic
            response = await self.api_client.generate_content(prompt)
            self.chat_history = [{"role": "assistant", "content": response}]
            return response
        except Exception as e:
            return f"Error initializing session: {str(e)}"

    async def send_message(self, message: str) -> str:
        if not self.chat_history:
            return "Please start a new session first."
        
        try:
            follow_up_prompt = f"""
            The student's response was: "{message}"
        
            Structure your response in these parts:
            1. First, acknowledge their answer directly with encouragement
            2. Provide specific feedback
            3. Teach the next concept in detail
            4. End with a thought-provoking question
            
            Keep your response natural and conversational."""
            
            response = await self.api_client.generate_content(follow_up_prompt)
            return response
        except Exception as e:
            return f"Error: {str(e)}"

async def main():
    if 'api_client' not in st.session_state:
        api_key = st.secrets.get('GOOGLE_API_KEY')
        if not api_key:
            st.error("🔑 GOOGLE_API_KEY not found in secrets!")
            st.stop()
        
        st.session_state.api_client = AsyncAPIClient(api_key)
        await st.session_state.api_client.initialize()

    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor(st.session_state.api_client)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False

    # Rest of the UI code remains the same...
    # (Previous UI code continues here)

if __name__ == "__main__":
    asyncio.run(main())
