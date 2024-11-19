import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Enhanced page configuration
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
    <style>
        /* Main page styling */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Header styling */
        .main-header {
            font-family: 'Helvetica Neue', sans-serif;
            color: #1E3A8A;
            padding: 1rem 0;
            text-align: center;
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f1f5f9;
            padding: 2rem 1rem;
            border-right: 1px solid #e2e8f0;
        }
        
        /* Button styling */
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
        
        /* Chat container styling */
        .chat-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        
        /* Message styling */
        .stChat {
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Input box styling */
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        
        /* Progress section styling */
        .progress-section {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Quiz styling */
        .quiz-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Success message styling */
        .success-message {
            padding: 1rem;
            border-radius: 8px;
            background-color: #dcfce7;
            color: #166534;
            margin: 1rem 0;
        }
        
        /* Error message styling */
        .error-message {
            padding: 1rem;
            border-radius: 8px;
            background-color: #fee2e2;
            color: #991b1b;
            margin: 1rem 0;
        }
        
        /* Selectbox styling */
        .stSelectbox {
            margin-bottom: 1rem;
        }
        
        /* Radio button styling */
        .stRadio > label {
            background-color: #f8fafc;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Apply custom header
st.markdown("""
    <div class="main-header">
        <h1>🎓 Interactive AI Tutor</h1>
        <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
    </div>
""", unsafe_allow_html=True)

def check_api_key():
    """Verify the API key is properly configured."""
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

class QuizGenerator:
    def __init__(self, model):
        self.model = model

    def generate_quiz(self, subject, topic, difficulty, num_questions=5):
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
            return json.loads(response.text)
        except Exception as e:
            st.error(f"Failed to generate quiz: {str(e)}")
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
        try:
            self.model = genai.GenerativeModel('gemini-pro')
            self.quiz_generator = QuizGenerator(self.model)
            self.progress_tracker = ProgressTracker()
            self.chat = None
            self.current_subject = None
            self.current_topic = None
        except Exception as e:
            st.error(f"Error initializing AI Tutor: {str(e)}")
            raise e
    
    def initialize_session(self, subject, level, prerequisites, topic):
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
            follow_up_prompt = f"""
            The student's response was: "{message}"
            
            1. First, acknowledge their answer directly
            2. Provide specific feedback:
               - If correct: Confirm and briefly elaborate
               - If partially correct: Clarify any misunderstandings
               - If incorrect: Gently explain why
            3. Then: Teach the next concept
            4. End with a new question about what you just taught
            
            Keep it natural and conversational. No special formatting."""
            
            response = self.chat.send_message(follow_up_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    # Check API key first
    if not check_api_key():
        st.stop()
    
    # Initialize session states
    if 'tutor' not in st.session_state:
        try:
            st.session_state.tutor = AITutor()
        except Exception as e:
            st.error(f"Failed to initialize tutor: {str(e)}")
            st.stop()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False
    
    # Enhanced sidebar
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
                with st.spinner("🔄 Initializing your personalized session..."):
                    response = st.session_state.tutor.initialize_session(
                        subject, level, prerequisites, topic
                    )
                    st.session_state.messages = []
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.quiz_active = False
                st.success("✨ Session started successfully!")
    
    # Main content area with enhanced styling
    chat_col, viz_col = st.columns([2, 1])
    
    with chat_col:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
            </div>
        """, unsafe_allow_html=True)
        
        message_container = st.container()
        
        with message_container:
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
            
            st.rerun()
    
    with viz_col:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
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
        
        if st.session_state.quiz_active and hasattr(st.session_state, 'current_quiz'):
            st.markdown("""
                <div class='quiz-container'>
                    <h4 style='color: #1E3A8A;'>Quiz Progress</h4>
                </div>
            """, unsafe_allow_html=True)
            
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
        
        # Enhanced progress visualization
        progress_data = st.session_state.tutor.progress_tracker.load_history()
        if progress_data:
            st.markdown("""
                <div style='margin-top: 2rem;'>
                    <h4 style='color: #1E3A8A;'>Learning Journey</h4>
                </div>
            """, unsafe_allow_html=True)
            
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



        
