import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import asyncio
import concurrent.futures
from functools import lru_cache
from typing import List, Dict, Optional

os.environ["STREAMLIT_SERVER_WATCH_PATCHING"] = "false"

st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

# Apply the same CSS styling as before
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

st.markdown("""
    <div class="main-header">
        <h1>🎓 Interactive AI Tutor</h1>
        <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
    </div>
""", unsafe_allow_html=True)

class CacheManager:
    def __init__(self):
        self.message_cache = {}
        self.session_cache = {}
    
    @lru_cache(maxsize=100)
    def get_cached_response(self, message_hash: str) -> Optional[str]:
        return self.message_cache.get(message_hash)
    
    def cache_response(self, message_hash: str, response: str):
        self.message_cache[message_hash] = response
        
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        return self.session_cache.get(session_id)
    
    def cache_session(self, session_id: str, data: Dict):
        self.session_cache[session_id] = data

class QuizGenerator:
    def __init__(self, model):
        self.model = model
        self.cache_manager = CacheManager()

    @lru_cache(maxsize=50)
    def generate_quiz(self, subject, topic, difficulty, num_questions=5):
        cache_key = f"{subject}_{topic}_{difficulty}"
        cached_quiz = self.cache_manager.get_session_data(cache_key)
        if cached_quiz:
            return cached_quiz

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
            response = self.model.generate_content(prompt)
            quiz_data = json.loads(response.text)
            self.cache_manager.cache_session(cache_key, quiz_data)
            return quiz_data
        except Exception as e:
            st.error(f"Failed to generate quiz: {str(e)}")
            return None

class ProgressTracker:
    def __init__(self):
        self.history_file = "progress_history.json"
        self.cache = {}
    
    def load_history(self):
        if self.cache:
            return self.cache
        
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.cache = json.load(f)
                    return self.cache
        except Exception as e:
            st.warning(f"Could not load progress history: {e}")
        return []
    
    def save_progress(self, user, subject, topic, quiz_score, timestamp=None):
        try:
            history = self.load_history()
            new_entry = {
                'user': user,
                'subject': subject,
                'topic': topic,
                'score': quiz_score,
                'timestamp': timestamp or datetime.now().isoformat()
            }
            history.append(new_entry)
            self.cache = history
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f)
        except Exception as e:
            st.warning(f"Could not save progress: {e}")

class OptimizedAITutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.cache_manager = CacheManager()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.quiz_generator = QuizGenerator(self.model)
        self.progress_tracker = ProgressTracker()
        self._initialize_chat_history()

    def _initialize_chat_history(self):
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

    def _hash_message(self, message: str, context: str) -> str:
        return f"{hash(message)}_{hash(context)}"

    async def _generate_response(self, message: str, context: str) -> str:
        message_hash = self._hash_message(message, context)
        
        cached_response = self.cache_manager.get_cached_response(message_hash)
        if cached_response:
            return cached_response
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.model.generate_content(self._create_prompt(message, context)).text
            )
            
            self.cache_manager.cache_response(message_hash, response)
            return response
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

    def _create_prompt(self, message: str, context: str) -> str:
        return f"""Context: {context}
        Student message: {message}
        
        Respond naturally and concisely while:
        1. Acknowledging their response
        2. Providing specific feedback
        3. Teaching the next concept
        4. Ending with a question"""

    def initialize_session(self, subject: str, level: str, prerequisites: str, topic: str) -> str:
        session_id = f"{subject}_{level}_{topic}"
        cached_session = self.cache_manager.get_session_data(session_id)
        
        if cached_session:
            return cached_session['initial_response']
        
        try:
            prompt = f"""You are a tutor teaching {subject} at {level} level.
            Background: {prerequisites}
            Topic: {topic}
            
            Provide a concise welcome and introduction."""
            
            response = self.model.generate_content(prompt).text
            
            self.cache_manager.cache_session(session_id, {
                'initial_response': response,
                'context': f"{subject} {level} {topic}"
            })
            
            return response
        except Exception as e:
            return f"Session initialization error: {str(e)}"

    async def process_message(self, message: str) -> str:
        if not hasattr(st.session_state, 'chat_history'):
            return "Please start a new session first."
        
        recent_context = self._get_recent_context(st.session_state.chat_history)
        response = await self._generate_response(message, recent_context)
        self._update_chat_history(message, response)
        return response

    def _get_recent_context(self, history: List[Dict], context_window: int = 3) -> str:
        recent_messages = history[-context_window:] if history else []
        return " ".join([msg['content'] for msg in recent_messages])

    def _update_chat_history(self, message: str, response: str):
        st.session_state.chat_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })

def check_api_key():
    if 'GOOGLE_API_KEY' not in st.secrets:
        st.error("🔑 GOOGLE_API_KEY not found in secrets!")
        st.info("""
        ### How to fix this:
        1. Go to your Streamlit Cloud dashboard
        2. Find this app and click on the three dots (...)
        3. Select 'Settings'
        4. Under 'Secrets', add your API key like this:
        ```
        GOOGLE_API_KEY = "your-actual-key-here-with-quotes"
        ```
        5. Click 'Save'
        6. Restart the app
        """)
        return False
    try:
        genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Test")
        return True
    except Exception as e:
        st.error(f"🚨 Error with API key: {str(e)}")
        return False

def display_chat_messages():
    message_container = st.container()
    
    with message_container:
        messages_to_display = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
        
        for message in messages_to_display:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

async def handle_chat_input(tutor: OptimizedAITutor):
    if prompt := st.chat_input("💭 Type your response here..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = await tutor.process_message(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

async def main():
    if not check_api_key():
        st.stop()
    
    if 'tutor' not in st.session_state:
        try:
            st.session_state.tutor = OptimizedAITutor()
        except Exception as e:
            st.error(f"Failed to initialize tutor: {str(e)}")
            st.stop()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False

    # Sidebar configuration
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding-bottom: 1rem;'>
                <h3 style='color: #1E3A8A;'>Session Configuration</h3>
            </div>
        """, unsafe_allow_html=True)
        
        user_name = st.text_input("👤 Your Name", key="user_name")
        
        subjects = [
            "Python Programming",
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "History",
            "Literature",
            "Economics"
        ]
        subject = st.selectbox("📚 Select Subject", subjects)
        
        levels = ["Beginner", "Intermediate", "Advanced"]
        level = st.selectbox("📊 Select Level", levels)
        
        topic = st.text_input("🎯 Specific Topic")
        
        prerequisites = st.text_area("🔍 Your Background/Prerequisites")
        
        st.markdown("---")
        
        if st.button("🚀 Start New Session"):
            if not topic or not prerequisites:
                st.error("⚠️ Please fill in both Topic and Prerequisites")
            else:
                with st.spinner("🔄 Initializing your session..."):
                    response = st.session_state.tutor.initialize_session(
                        subject, level, prerequisites, topic
                    )
                    st.session_state.messages = []
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.quiz_active = False
                st.success("✨ Session started!")
        
        st.markdown("---")
        if st.button("🔄 Reset Session"):
            st.session_state.messages = []
            st.session_state.quiz_active = False
            st.session_state.tutor = OptimizedAITutor()
            st.rerun()

    # Main content area
   chat_col, viz_col = st.columns([2, 1])
    
    with chat_col:
        st.markdown(
            """
            <div class='chat-container'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        display_chat_messages()
        await handle_chat_input(st.session_state.tutor)
    
    with viz_col:
        st.markdown(
            """
            <div class='chat-container'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>📈 Learning Progress</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("📝 Take Quiz"):
            if not topic:
                st.error("⚠️ Please start a session first")
            else:
                st.session_state.quiz_active = True
                with st.spinner("⚙️ Generating quiz..."):
                    quiz_data = st.session_state.tutor.quiz_generator.generate_quiz(
                        subject,
                        topic,
                        level
                    )
                if quiz_data:
                    st.session_state.current_quiz = quiz_data
                    st.session_state.quiz_score = 0
                    st.session_state.current_question = 0
        
        if st.session_state.quiz_active and hasattr(st.session_state, 'current_quiz'):
            question = st.session_state.current_quiz['questions'][st.session_state.current_question]
            
            st.subheader(f"Question {st.session_state.current_question + 1}")
            st.write(question['question'])
            
            answer = st.radio("Select your answer:", question['options'], key=f"q_{st.session_state.current_question}")
            
            if st.button("Submit Answer"):
                if answer == question['correct_answer']:
                    st.session_state.quiz_score += 1
                    st.success("✅ Correct!")
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
        
        # Efficient progress visualization with caching
        @st.cache_data(ttl=300)  # Cache for 5 minutes
        def get_progress_chart(progress_data):
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
                return fig
            return None

        progress_data = st.session_state.tutor.progress_tracker.load_history()
        if progress_data:
            chart = get_progress_chart(progress_data)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

async def run_app():
    """Wrapper function to run the async main function"""
    try:
        await main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    # Set up asyncio event loop and run the application
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_app())
    finally:
        loop.close()
                    
