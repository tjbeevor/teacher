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
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

class APIClient:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generate_content(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None

class AITutor:
    def __init__(self):
        self.api_client = APIClient()
        self.current_topic = None
        self.topics = []
        self.current_topic_index = 0

    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"""
        As a tutor teaching {subject} at {level} level, provide 5 key subtopics to cover for {topic}.
        Consider the student's background: {prerequisites}
        Format as a simple comma-separated list.
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                # Split the response into topics
                self.topics = [t.strip() for t in response.split(',')]
                if len(self.topics) > 0:
                    self.current_topic_index = 0
                    self.current_topic = self.topics[self.current_topic_index]
                    return f"Great! Let's start our lesson on {topic}. We'll cover: {', '.join(self.topics)}. Let's begin with {self.current_topic}."
            return "I'm sorry, but I couldn't generate topics. Please try again."
        except Exception as e:
            st.error(f"Error initializing session: {str(e)}")
            return "I'm sorry, but I encountered an error. Please try again."

    def teach_topic(self):
        prompt = f"""
        Teach this topic: {self.current_topic}
        Provide:
        1. A brief lesson (2-3 sentences)
        2. An example
        3. A practice question
        Separate each part with '|||'
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                parts = response.split('|||')
                if len(parts) >= 3:
                    return {
                        'lesson': parts[0].strip(),
                        'examples': parts[1].strip(),
                        'question': parts[2].strip()
                    }
            return {
                'lesson': "I couldn't generate the lesson properly.",
                'examples': "No examples available.",
                'question': "No question available."
            }
        except Exception as e:
            st.error(f"Error teaching topic: {str(e)}")
            return {
                'lesson': "An error occurred while generating the lesson.",
                'examples': "No examples available.",
                'question': "No question available."
            }

    def evaluate_answer(self, question, answer):
        prompt = f"""
        Question: {question}
        Student's answer: {answer}
        Evaluate the answer and provide:
        1. Whether it's correct or incorrect
        2. Feedback
        Separate with '|||'
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                parts = response.split('|||')
                is_correct = 'correct' in parts[0].lower()
                return {
                    'evaluation': 'correct' if is_correct else 'incorrect',
                    'feedback': parts[1].strip() if len(parts) > 1 else "No feedback available.",
                    'move_on': is_correct
                }
            return {
                'evaluation': 'incorrect',
                'feedback': "Couldn't evaluate the answer.",
                'move_on': False
            }
        except Exception as e:
            st.error(f"Error evaluating answer: {str(e)}")
            return {
                'evaluation': 'incorrect',
                'feedback': "An error occurred during evaluation.",
                'move_on': False
            }

    def move_to_next_topic(self):
        self.current_topic_index += 1
        if self.current_topic_index < len(self.topics):
            self.current_topic = self.topics[self.current_topic_index]
            return True
        return False

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'teaching_state' not in st.session_state:
    st.session_state.teaching_state = 'initialize'
if 'tutor' not in st.session_state:
    st.session_state.tutor = AITutor()
if 'last_question' not in st.session_state:
    st.session_state.last_question = None

# Page config
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# Add CSS
st.markdown("""
<style>
.stButton>button {
    width: 100%;
    background-color: #4CAF50;
    color: white;
    padding: 10px;
    border-radius: 5px;
}
.chat-message {
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🎓 AI Tutor")
    
    # Sidebar
    with st.sidebar:
        st.header("Learning Settings")
        subject = st.selectbox(
            "Subject",
            ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
        )
        level = st.selectbox(
            "Level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        topic = st.text_input("Topic")
        prerequisites = st.text_area("Your Background (Optional)")

    # Main content
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.teaching_state == 'initialize':
        if topic and st.button("Start Learning"):
            response = st.session_state.tutor.initialize_session(
                subject, level, prerequisites, topic
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.teaching_state = 'teach_topic'
            st.rerun()

    elif st.session_state.teaching_state == 'teach_topic':
        content = st.session_state.tutor.teach_topic()
        message = f"""
        📚 Lesson: {content['lesson']}
        
        📝 Example: {content['examples']}
        
        ❓ Question: {content['question']}
        """
        st.session_state.messages.append({"role": "assistant", "content": message})
        st.session_state.last_question = content['question']
        st.session_state.teaching_state = 'wait_for_answer'
        st.rerun()

    elif st.session_state.teaching_state == 'wait_for_answer':
        if prompt := st.chat_input("Your answer"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            evaluation = st.session_state.tutor.evaluate_answer(
                st.session_state.last_question, prompt
            )
            
            feedback = f"💭 {evaluation['feedback']}"
            st.session_state.messages.append({"role": "assistant", "content": feedback})
            
            if evaluation['move_on']:
                if st.session_state.tutor.move_to_next_topic():
                    st.session_state.teaching_state = 'teach_topic'
                else:
                    st.session_state.teaching_state = 'finished'
            st.rerun()

    elif st.session_state.teaching_state == 'finished':
        st.success("🎉 Congratulations! You've completed all topics!")
        if st.button("Start New Topic"):
            st.session_state.teaching_state = 'initialize'
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
