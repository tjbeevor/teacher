import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor

# Configuration
os.environ["STREAMLIT_SERVER_WATCH_PATCHING"] = "false"

# Streamlit Page Config
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Caching System
class CachingSystem:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=3600)  # 1-hour TTL

    def get_cached_response(self, prompt: str):
        return self.cache.get(prompt)

    def cache_response(self, prompt: str, response: str):
        self.cache[prompt] = response

# API Client
class APIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = CachingSystem()
        self.executor = ThreadPoolExecutor(max_workers=4)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_content(self, prompt: str) -> str:
        if not prompt:
            return "I need a prompt to generate a response."

        cached_response = self.cache.get_cached_response(prompt)
        if cached_response:
            return cached_response

        try:
            response = self.executor.submit(lambda: self.model.generate_content(prompt)).result()
            if response and hasattr(response, 'text'):
                self.cache.cache_response(prompt, response.text)
                return response.text
            return "I couldn't generate a response."
        except Exception as e:
            return f"Error: {str(e)}"

# Quiz Generator
class QuizGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def generate_quiz(self, subject, topic, level, num_questions=5):
        prompt = f"Create a {level} quiz on {topic} in {subject} with {num_questions} questions."
        response = self.api_client.generate_content(prompt)
        try:
            return json.loads(response)
        except Exception as e:
            st.error(f"Failed to parse quiz response: {str(e)}")
            return None

# AITutor Class
class AITutor:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.quiz_generator = QuizGenerator(api_client)

    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"Introductory message for {level} {subject} on {topic}. Prerequisites: {prerequisites}"
        return self.api_client.generate_content(prompt)

    def send_message(self, message):
        prompt = f"Respond as a tutor for {message}"
        return self.api_client.generate_content(prompt)

# Main Function
def main():
    # Initialize Session State
    if 'tutor' not in st.session_state:
        if 'GOOGLE_API_KEY' not in st.secrets:
            st.error("Missing GOOGLE_API_KEY in secrets!")
            return
        st.session_state.tutor = AITutor(APIClient(st.secrets['GOOGLE_API_KEY']))

    st.title("🎓 Interactive AI Tutor")

    # Sidebar Inputs
    with st.sidebar:
        st.header("Session Configuration")
        user_name = st.text_input("Your Name")
        subject = st.selectbox("Subject", ["Math", "Science", "History"])
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
        topic = st.text_input("Topic")
        prerequisites = st.text_area("Prerequisites")

        if st.button("Start Session"):
            if not topic or not prerequisites:
                st.warning("Please provide topic and prerequisites.")
            else:
                st.session_state.messages = []
                response = st.session_state.tutor.initialize_session(subject, level, prerequisites, topic)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.success("Session Started!")

    # Chat Interface
    for message in st.session_state.get('messages', []):
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = st.session_state.tutor.send_message(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()
