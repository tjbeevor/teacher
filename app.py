import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Configure page and styling
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for styling (same as before)
st.markdown("""
<style>
    /* ... (keep the existing CSS) ... */
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎓 Interactive AI Tutor</h1>
    <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
</div>
""", unsafe_allow_html=True)

# Check for API key
def check_api_key():
    if 'GOOGLE_API_KEY' not in st.secrets:
        st.error("🔑 GOOGLE_API_KEY not found in secrets!")
        st.info("... (instructions on how to add the API key) ...")
        return False
    try:
        genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Test")
        return True
    except Exception as e:
        st.error(f"🚨 Error with API key: {str(e)}")
        return False

# AI Tutor class
class AITutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = None
        self.current_subject = None
        self.current_topic = None

    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"""
        You are an AI tutor specializing in {subject} at {level} level. The student's background is: {prerequisites}
        Current topic: {topic}

        Your task is to provide a comprehensive learning experience. For each concept:

        1. Give a detailed overview of the concept.
        2. Provide practical examples demonstrating its application.
        3. Ask a question to check understanding.
        4. Based on the student's response:
           - If correct: Confirm, briefly elaborate, and move to the next concept.
           - If partially correct: Clarify misunderstandings, provide additional examples, and ask follow-up questions before moving on.
           - If incorrect: Explain why, provide more information and examples, and ask custom questions to ensure understanding before proceeding.

        Begin by introducing the topic and presenting the first key concept.
        """
        self.chat = self.model.start_chat(history=[])
        self.current_subject = subject
        self.current_topic = topic
        response = self.chat.send_message(prompt)
        return response.text

    def send_message(self, message):
        if not self.chat:
            return "Please start a new session first."
        
        prompt = f"""
        The student's response was: "{message}"

        Analyze the response and:
        1. Acknowledge the answer with encouragement.
        2. Provide specific feedback:
           - If correct: Confirm and briefly elaborate.
           - If partially correct: Clarify misunderstandings and provide additional information.
           - If incorrect: Gently explain why and provide a more detailed explanation with examples.
        3. Based on the student's understanding:
           - If they've grasped the concept: Introduce the next concept in the topic.
           - If they need more clarification: Provide additional examples and explanations.
        4. Ask a new question to check understanding of the current or next concept.

        Ensure your response is:
        - Conversational and encouraging
        - Rich in examples and explanations
        - Clear and engaging
        """
        response = self.chat.send_message(prompt)
        return response.text

# Main function
def main():
    if not check_api_key():
        st.stop()

    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Sidebar for session configuration
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding-bottom: 1rem;'>
            <h3 style='color: #1E3A8A;'>Session Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        user_name = st.text_input("👤 Your Name", key="user_name")
        subject = st.selectbox("📚 Select Subject", ["Python Programming", "Mathematics", "Physics", "Chemistry", "Biology", "History", "Literature", "Economics"])
        level = st.selectbox("📊 Select Level", ["Beginner", "Intermediate", "Advanced"])
        topic = st.text_input("🎯 Specific Topic")
        prerequisites = st.text_area("🔍 Your Background/Prerequisites")

        if st.button("🚀 Start New Session"):
            if not topic or not prerequisites:
                st.error("⚠️ Please fill in both Topic and Prerequisites")
            else:
                with st.spinner("🔄 Initializing your session..."):
                    response = st.session_state.tutor.initialize_session(subject, level, prerequisites, topic)
                st.session_state.messages = []
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.success("✨ Session started!")

        if st.button("🔄 Reset Session"):
            st.session_state.messages = []
            st.session_state.tutor = AITutor()
            st.rerun()

    # Main chat interface
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
        st.rerun()

if __name__ == "__main__":
    main()
