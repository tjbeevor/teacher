import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        }}
        
        Guidelines:
        - Each question should test understanding of a specific concept
        - Make options clear and distinct
        - Include only one correct answer
        - Keep explanations concise and helpful
        - Ensure the correct_answer exactly matches one of the options"""
        
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
        prompt = f"""You are an expert tutor in {subject}, teaching a student at {level} level who has {prerequisites} as background.
        Current topic: {topic}
        
        Follow this structured approach:
        1. Start with a brief, friendly introduction
        2. Present a clear outline of what we'll cover about {topic}
        3. Begin teaching the first concept, using:
           - Clear explanations
           - Relevant examples
           - Real-world applications
           - Simple analogies when helpful
        4. After explaining each concept, ask ONE simple question to check understanding
        5. Wait for the student's response before moving forward
        
        Teaching guidelines:
        - Break complex ideas into smaller chunks
        - Use conversational, engaging language
        - Don't present multiple questions at once
        - Don't provide answers immediately
        - Focus on one concept at a time
        - Let the student think and respond
        
        Start now with your introduction and the first concept about {topic}."""
        
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
            Respond to the student's input, then:
            1. Provide helpful feedback on their response
            2. Clarify any misconceptions if needed
            3. Present the next relevant concept
            4. Ask ONE question to check understanding
            
            Remember:
            - Stay focused on one concept at a time
            - Don't provide multiple questions
            - Let the student think and respond
            - Keep the conversation natural and engaging
            """
            response = self.chat.send_message(message + "\n\n" + follow_up_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.title("🎓 AI Tutor")
    
    # Check API key first
    if not check_api_key():
        st.stop()
    
    # Initialize session state
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
    
    # Sidebar for session configuration
    with st.sidebar:
        st.header("Session Settings")
        
        # User information
        user_name = st.text_input("Your Name", key="user_name")
        
        # Subject selection
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
        subject = st.selectbox("Subject", subjects)
        
        # Level selection
        levels = ["Beginner", "Intermediate", "Advanced"]
        level = st.selectbox("Level", levels)
        
        # Topic input
        topic = st.text_input("Specific Topic")
        
        # Prerequisites input
        prerequisites = st.text_area("Your Background/Prerequisites")
        
        if st.button("Start New Session"):
            if not topic or not prerequisites:
                st.error("Please fill in both Topic and Prerequisites")
            else:
                with st.spinner("Initializing your tutoring session..."):
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
            if not topic:
                st.error("Please start a session first")
            else:
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
