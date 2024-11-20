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
        As a tutor teaching {subject} at {level} level, list exactly 5 key subtopics to cover for {topic}.
        Consider the student's background: {prerequisites}
        Format your response exactly like this example:
        1. First Topic
        2. Second Topic
        3. Third Topic
        4. Fourth Topic
        5. Fifth Topic
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                # Extract topics and clean them
                topics = [line.split('. ')[1].strip() 
                         for line in response.split('\n') 
                         if line.strip() and line[0].isdigit()]
                if len(topics) == 5:
                    self.topics = topics
                    self.current_topic_index = 0
                    self.current_topic = self.topics[self.current_topic_index]
                    return f"""Let's begin our study of {topic}! 
                    
Here's what we'll cover:

1. {topics[0]}
2. {topics[1]}
3. {topics[2]}
4. {topics[3]}
5. {topics[4]}

Let's start with {self.current_topic}!"""
            return "I'm sorry, but I couldn't generate topics. Please try again."
        except Exception as e:
            st.error(f"Error initializing session: {str(e)}")
            return "I'm sorry, but I encountered an error. Please try again."

    def teach_topic(self):
        prompt = f"""
        Create a structured lesson about {self.current_topic}.
        Format your response exactly like this:

        CONCEPT
        [Write 2-3 clear, concise sentences explaining the core concept]

        EXAMPLES
        1. [Provide a specific, practical example]
        2. [Provide another example showing a different aspect]

        PRACTICE
        [Ask one clear, specific question that tests understanding of the concept]
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                sections = response.split('\n\n')
                lesson = {'lesson': '', 'examples': '', 'question': ''}
                
                for section in sections:
                    if section.startswith('CONCEPT'):
                        lesson['lesson'] = section.replace('CONCEPT\n', '')
                    elif section.startswith('EXAMPLES'):
                        lesson['examples'] = section.replace('EXAMPLES\n', '')
                    elif section.startswith('PRACTICE'):
                        lesson['question'] = section.replace('PRACTICE\n', '')
                
                return lesson
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
    .stMarkdown {
        padding: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    h1, h2, h3, h4 {
        color: #1E88E5;
        padding: 0.5rem 0;
    }
    .stAlert {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    code {
        background-color: #F5F5F5;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
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
            ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Python Programming"]
        )
        level = st.selectbox(
            "Level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        topic = st.text_input("Topic")
        prerequisites = st.text_area("Your Background (Optional)")

    # Main content area with better spacing and formatting
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "Let's begin our study" in message["content"]:
                # Special formatting for the introduction
                st.markdown(message["content"])
            elif message["role"] == "assistant" and "Key Concept" in message["content"]:
                # Format the lesson content
                content_parts = message["content"].split("###")
                
                # Topic title
                st.header(content_parts[0].replace("#", "").strip())
                
                # Key Concept
                st.subheader("🔑 Key Concept")
                concept_text = content_parts[1].replace("Key Concept", "").strip()
                st.write(concept_text)
                
                # Examples
                st.subheader("📝 Examples")
                examples_text = content_parts[2].replace("Examples", "").strip()
                st.markdown(examples_text)
                
                # Practice Question
                st.subheader("❓ Practice Question")
                question_text = content_parts[3].replace("Practice Question", "").strip()
                question_text = question_text.replace("Please type your answer below!", "").strip()
                st.info(question_text)
            else:
                # Regular message
                st.markdown(message["content"])

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
        message = f"""## {st.session_state.tutor.current_topic}

### Key Concept
{content['lesson']}

### Examples
{content['examples']}

### Practice Question
{content['question']}

Please type your answer below!"""
        st.session_state.messages.append({"role": "assistant", "content": message})
        st.session_state.last_question = content['question']
        st.session_state.teaching_state = 'wait_for_answer'
        st.rerun()

    elif st.session_state.teaching_state == 'wait_for_answer':
        # Create a container for the input box
        input_container = st.container()
        
        if prompt := st.chat_input("Type your answer here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            evaluation = st.session_state.tutor.evaluate_answer(
                st.session_state.last_question, prompt
            )
            
            # Format feedback with appropriate emoji
            if evaluation['evaluation'] == 'correct':
                feedback = f"✅ Excellent! {evaluation['feedback']}"
            else:
                feedback = f"💡 {evaluation['feedback']}"
            
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
