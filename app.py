import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# First, define all classes before any execution code
class CachingSystem:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour

    @lru_cache(maxsize=100)
    def get_cached_response(self, prompt: str):
        return self.cache.get(prompt)

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
                return "I apologize, but I couldn't generate a proper response."
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return "I apologize, but I encountered an error."

class QuizGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def generate_quiz(self, subject: str, topic: str, difficulty: str, num_questions: int = 5) -> dict:
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
            response = self.api_client.generate_content(prompt)
            return json.loads(response)
        except Exception as e:
            st.error(f"Failed to generate quiz: {str(e)}")
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
            st.warning(f"Could not load progress history: {e}")
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

class AITutor:
    def __init__(self):
        self.api_client = APIClient(st.secrets["GOOGLE_API_KEY"])
        self.quiz_generator = QuizGenerator(self.api_client)
        self.progress_tracker = ProgressTracker()
        self.current_topic = None
        self.topics = []
        self.current_topic_index = 0

    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"""
        You are a friendly and encouraging tutor teaching {subject} at {level} level.
        The student's background is: {prerequisites}
        Main topic: {topic}

        Please provide a list of 5 key subtopics to cover for {topic} in {subject}.
        Format your response as a valid JSON array of strings.
        """
        response = self.api_client.generate_content(prompt)
        try:
            self.topics = json.loads(response)
            if not isinstance(self.topics, list) or len(self.topics) == 0:
                raise ValueError("Invalid response format")
            self.current_topic_index = 0
            self.current_topic = self.topics[self.current_topic_index]
            return f"Great! Let's start our lesson on {topic}. We'll cover these subtopics: {', '.join(self.topics)}. Let's begin with {self.current_topic}."
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse the response from the AI. Error: {str(e)}")
            return "I'm sorry, but I encountered an error. Let's try again."
        except ValueError as e:
            st.error(f"Invalid response format from the AI. Error: {str(e)}")
            return "I'm sorry, but I received an invalid response. Let's try again."

    def teach_topic(self):
        prompt = f"""
        Teach the subtopic: {self.current_topic}
        
        1. Provide a brief lesson (2-3 sentences).
        2. Give 1-2 examples.
        3. Ask a question to test understanding.

        Format your response as a valid JSON object with keys: 'lesson', 'examples', and 'question'.
        """
        response = self.api_client.generate_content(prompt)
        try:
            content = json.loads(response)
            if not all(key in content for key in ['lesson', 'examples', 'question']):
                raise ValueError("Missing required keys in response")
            st.session_state.last_question = content['question']
            return content
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse the lesson content. Error: {str(e)}")
            return {"lesson": "I'm sorry, but I encountered an error. Let's try again.", "examples": "", "question": ""}
        except ValueError as e:
            st.error(f"Invalid lesson content format. Error: {str(e)}")
            return {"lesson": "I'm sorry, but I received an invalid response. Let's try again.", "examples": "", "question": ""}

    def evaluate_answer(self, question, answer):
        prompt = f"""
        Question: {question}
        Student's answer: {answer}

        Evaluate the student's answer. Provide feedback and determine if the answer is correct, partially correct, or incorrect.
        If partially correct or incorrect, provide a brief explanation or hint.

        Format your response as a valid JSON object with keys: 'evaluation' (string: 'correct', 'partially_correct', or 'incorrect'), 'feedback' (string), and 'move_on' (boolean).
        """
        response = self.api_client.generate_content(prompt)
        try:
            evaluation = json.loads(response)
            if not all(key in evaluation for key in ['evaluation', 'feedback', 'move_on']):
                raise ValueError("Missing required keys in response")
            return evaluation
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse the evaluation. Error: {str(e)}")
            return {"evaluation": "incorrect", "feedback": "I'm sorry, but I encountered an error. Let's try again.", "move_on": False}
        except ValueError as e:
            st.error(f"Invalid evaluation format. Error: {str(e)}")
            return {"evaluation": "incorrect", "feedback": "I'm sorry, but I received an invalid response. Let's try again.", "move_on": False}

    def move_to_next_topic(self):
        self.current_topic_index += 1
        if self.current_topic_index < len(self.topics):
            self.current_topic = self.topics[self.current_topic_index]
            return True
        return False

# Now initialize Streamlit and session state
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

# Initialize session state variables
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
if 'last_question' not in st.session_state:
    st.session_state.last_question = None
if 'teaching_state' not in st.session_state:
    st.session_state.teaching_state = 'initialize'
if 'tutor' not in st.session_state:
    st.session_state.tutor = AITutor()

# Add your CSS styles here
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
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Interactive AI Tutor</h1>
        <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar settings
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

    # Main content area
    chat_col, viz_col = st.columns([2, 1])

    with chat_col:
        st.markdown("""
        <div class='chat-container'>
            <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
        </div>
        """, unsafe_allow_html=True)

        # Rest of your chat column code...
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
        
        # Add the rest of your states handling here...

    with viz_col:
        # Visualization column code...
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")
