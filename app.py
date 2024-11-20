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

# Header
st.markdown("""
    <div class="main-header">
        <h1>🎓 Interactive AI Tutor</h1>
        <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
    </div>
""", unsafe_allow_html=True)

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
            
        # Check cache first
        cached_response = self.cache.get_cached_response(prompt)
        if cached_response:
            return cached_response

        try:
            # Execute in thread pool
            response = self.executor.submit(
                lambda: self.model.generate_content(prompt)
            ).result()
            
            # Verify response is not None and has text
            if response and response.text:
                # Cache the response
                self.cache.cache_response(prompt, response.text)
                return response.text
            else:
                return "I apologize, but I couldn't generate a proper response. Let me try a different approach to help you understand variables."
                
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return "I apologize, but I encountered an error. Let me try explaining variables in a different way."



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
        prompt = f"""You are a helpful and encouraging tutor teaching {subject} at {level} level.
        The student's background is: {prerequisites}
        Current topic: {topic}

        Give a warm welcome, briefly introduce the topic, teach the first key concept, 
        and end with a simple question to check understanding. Keep your response natural 
        and conversational."""
        
        try:
            self.current_subject = subject
            self.current_topic = topic
            response = self.api_client.generate_content(prompt)
            return response
        except Exception as e:
            return f"Error initializing session: {str(e)}"

    def send_message(self, message: str) -> str:
        if not st.session_state.messages:
            return "Please start a new session first."
        
        try:
            if 'learning_state' not in st.session_state:
                st.session_state.learning_state = {
                    'current_topic': 'variables',
                    'subtopic_index': 0,
                    'subtopics': [
                        {'name': 'variable_basics', 'covered': False},
                        {'name': 'variable_assignment', 'covered': False},
                        {'name': 'variable_naming', 'covered': False},
                        {'name': 'variable_types', 'covered': False}
                    ],
                    'phase': 'teaching',
                    'last_concept': None,
                    'last_question': None
                }

            state = st.session_state.learning_state
            current_subtopic = state['subtopics'][state['subtopic_index']]

            if message and state['phase'] == 'question':
                follow_up_prompt = f"""
                The student responded: "{message}"
                Previous concept: Variables and variable assignment
                
                Based on their response, provide:
                1. Specific acknowledgment of their correct understanding about creating variables
                2. Elaboration on variable assignment concepts
                3. A more complex example showing variable usage
                4. A follow-up question about variable manipulation
                
                Make your response:
                - Detailed and encouraging
                - Building on their understanding of variable assignment
                - Including practical examples
                - Leading to deeper concepts about variables
                
                Important: Ensure the response forms a complete, coherent explanation
                that builds on their current understanding.
                """
                state['phase'] = 'verification'
            
            elif state['phase'] == 'verification':
                follow_up_prompt = f"""
                The student is learning about variables in Python.
                Their previous answer showed basic understanding.
                
                Provide:
                1. Confirmation of their understanding
                2. A more advanced example of variable usage
                3. Explanation of a related concept (like variable reassignment)
                4. A question that tests their understanding of this new concept
                
                Make the response detailed and natural, avoiding any meta-language
                or section markers.
                """
                state['phase'] = 'question'
            
            else:
                # Default to teaching if we're in an unknown state
                follow_up_prompt = f"""
                Teach the fundamentals of variables in Python.
                Include:
                1. Clear explanation with real-world analogies
                2. Basic examples of variable creation
                3. Practical use cases
                4. A simple question to check understanding
                
                Make it conversational and engaging.
                """
                state['phase'] = 'question'

            response = self.api_client.generate_content(follow_up_prompt)
            if not response:
                return "Let me try explaining this in a different way. Variables are like labeled containers..."
                
            return response

        except Exception as e:
            return f"I apologize for the error. Let me try explaining variables again in a different way."
            
    def _get_next_topic(self, current_topic):
        topics = {
            'variables': 'data_types',
            'data_types': 'operators',
            'operators': 'control_flow',
            # Add more topic progression as needed
        }
        return topics.get(current_topic, 'review')

    def _check_answer(self, student_answer: str, expected_answer: str) -> bool:
        # Add logic to compare answers intelligently
        student_answer = student_answer.lower().strip()
        expected_answer = expected_answer.lower().strip()
        return student_answer in expected_answer or expected_answer in student_answer

    def _get_current_subtopic(self) -> str:
        for topic in st.session_state.learning_progression['subtopics']:
            if not topic['completed']:
                return topic['name']
        return "review"  # If all topics are completed

    def _get_next_uncompleted_subtopic(self) -> str:
        found_current = False
        for topic in st.session_state.learning_progression['subtopics']:
            if found_current and not topic['completed']:
                return topic['name']
            if not topic['completed']:
                found_current = True
        return "final_review"  # If all topics are completed




    
    def get_topic_content(self, topic: str) -> str:
        topic_content = {
            "variables_basics": "Introduction to variables and basic assignments",
            "data_types": "Different data types in Python (int, float, str, etc.)",
            "variable_naming": "Rules and conventions for naming variables",
            "type_conversion": "Converting between different data types",
            "variable_scope": "Understanding variable scope and lifetime",
            # Add more topics and their content
        }
        return topic_content.get(topic, "Topic content not found")


   
       
   
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

def main():
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()

    chat_col, viz_col = st.columns([2, 1])

    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding-bottom: 1rem;'>
                <h3 style='color: #1E3A8A;'>Session Configuration</h3>
            </div>
        """, unsafe_allow_html=True)
        
        user_name = st.text_input("👤 Your Name")
        
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
                st.success("✨ Session started!")

        if st.button("🔄 Reset Session"):
            st.session_state.messages = []
            st.session_state.quiz_active = False
            st.session_state.current_quiz = None
            st.session_state.quiz_score = 0
            st.session_state.current_question = 0
            st.experimental_rerun()

    with chat_col:
        st.markdown("""
            <div class='chat-container'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
            </div>
        """, unsafe_allow_html=True)
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("💭 Type your response here..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.tutor.send_message(prompt)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})

    with viz_col:
        st.markdown("""
            <div class='chat-container'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>📈 Learning Progress</h3>
            </div>
        """, unsafe_allow_html=True)
        
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
                            user_name,
                            subject,
                            topic,
                            final_score
                        )
                        st.session_state.quiz_active = False
                        st.success(f"🎉 Quiz completed! Score: {final_score}%")

        try:
            progress_data = st.session_state.tutor.progress_tracker.load_history()
            if progress_data and len(progress_data) > 0:
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
        except Exception as e:
            st.warning("No progress data available yet.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")
