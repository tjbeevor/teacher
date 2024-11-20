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
        Create an engaging, conversational lesson about {self.current_topic}
        
        Format your response exactly as follows:
        
        [KEY CONCEPT]
        Write a friendly, conversational explanation of the topic.
        Break it down into 3-4 key points that are easy to understand.
        Use everyday analogies where possible.
        
        [EXAMPLES]
        Give 2-3 real-world examples that demonstrate the concept.
        Make them relatable and practical.
        
        [PRACTICE]
        Ask a conversation-style question that checks understanding.
        Make it feel like a natural dialogue rather than a formal test.
        The question should be answerable in a few sentences.
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                parts = response.split('[')
                lesson = {}
                
                for part in parts:
                    if 'KEY CONCEPT]' in part:
                        lesson['lesson'] = part.split(']')[1].strip()
                    elif 'EXAMPLES]' in part:
                        lesson['examples'] = part.split(']')[1].strip()
                    elif 'PRACTICE]' in part:
                        lesson['question'] = part.split(']')[1].strip()
                
                return lesson
            
            raise ValueError("No response generated")
            
        except Exception as e:
            st.error(f"Error in lesson generation: {str(e)}")
            # Provide conversational default content
            return {
                'lesson': """Hey there! Let's talk about Python - it's a really friendly programming language that's perfect for beginners. 

Think of Python as the "English" of programming languages. Just like English tries to be clear and readable, Python uses simple, straightforward commands that almost read like regular sentences.

Here are the key things that make Python special:

1. It's Super Readable
   Imagine writing instructions for a friend - that's how Python code looks! It uses spacing and simple words instead of complicated symbols.

2. It's Flexible
   Python is like a Swiss Army knife - it can do almost anything! Whether you want to build websites, analyze data, or create games, Python's got you covered.

3. It Has Amazing Tools
   Think of Python like a huge toolkit where other programmers have already created lots of useful tools (we call them libraries) that you can use in your own projects.

4. It's Forgiving
   Unlike some other programming languages that need you to be super specific about everything, Python is more relaxed. It tries to figure out what type of data you're using automatically!""",
                
                'examples': """Let me show you what I mean with some everyday examples:

1. Say Hi to Python
   When you want to show something on the screen, it's as simple as:
   ```python
   print("Hi there!")
   ```
   That's it! Just like telling someone "Hi there!" in real life.

2. Working with Information
   Let's say you're keeping track of temperatures:
   ```python
   morning_temp = 65
   afternoon_temp = 75
   print(f"The temperature rose {afternoon_temp - morning_temp} degrees today!")
   ```
   Python makes it easy to work with numbers just like you would in your head.

3. Making Simple Decisions
   Python can help make decisions, just like you do:
   ```python
   time = 12
   if time < 12:
       print("Good morning!")
   else:
       print("Good afternoon!")
   ```""",
                
                'question': """Now, let's chat! Imagine you're explaining to a friend what makes Python different from other programming languages. What would you say are its two biggest advantages? There's no right or wrong answer - I'd love to hear your thoughts! 😊"""
            }

    def evaluate_answer(self, question, answer):
        prompt = f"""
        Question: {question}
        Student's answer: {answer}
        
        Evaluate this answer and provide:
        1. Whether it's correct (yes/no)
        2. Detailed feedback explaining why
        3. Whether to move to the next topic (yes/no)
        
        Format: 
        [CORRECT]
        yes or no
        [FEEDBACK]
        your feedback here
        [MOVE]
        yes or no
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                parts = response.split('[')
                evaluation = {}
                
                for part in parts:
                    if 'CORRECT]' in part:
                        is_correct = 'yes' in part.split(']')[1].lower()
                        evaluation['evaluation'] = 'correct' if is_correct else 'incorrect'
                    elif 'FEEDBACK]' in part:
                        evaluation['feedback'] = part.split(']')[1].strip()
                    elif 'MOVE]' in part:
                        evaluation['move_on'] = 'yes' in part.split(']')[1].lower()
                
                return evaluation
            
            raise ValueError("No response generated")
            
        except Exception as e:
            st.error(f"Error in evaluation: {str(e)}")
            return {
                'evaluation': 'incorrect',
                'feedback': "I couldn't properly evaluate your answer. Please try again.",
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
.concept-header {
    color: #1E88E5;
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
.concept-content {
    background-color: #F8F9FA;
    padding: 1em;
    border-left: 4px solid #1E88E5;
    margin-bottom: 1.5em;
}
.example-header {
    color: #43A047;
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
.example-content {
    background-color: #F8F9FA;
    padding: 1em;
    border-left: 4px solid #43A047;
    margin-bottom: 1.5em;
}
.question-header {
    color: #FB8C00;
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
.question-content {
    background-color: #FFF3E0;
    padding: 1em;
    border-left: 4px solid #FB8C00;
    margin-bottom: 1.5em;
}
code {
    padding: 0.2em 0.4em;
    background-color: #E3F2FD;
    border-radius: 3px;
}
pre {
    padding: 1em;
    background-color: #E3F2FD;
    border-radius: 5px;
    margin: 1em 0;
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
        with st.spinner("Preparing your lesson..."):
            content = st.session_state.tutor.teach_topic()
        
        message = f"""## {st.session_state.tutor.current_topic}

### 🔑 Key Concept
{content['lesson']}

### 📝 Examples
{content['examples']}

### ❓ Practice Question
{content['question']}
"""
        st.session_state.messages.append({"role": "assistant", "content": message})
        st.session_state.last_question = content['question']
        st.session_state.teaching_state = 'wait_for_answer'
        st.rerun()


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

    # Main content area
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Initial state - Topic selection
    if st.session_state.teaching_state == 'initialize':
        if topic and st.button("Start Learning"):
            with st.spinner("Preparing your learning path..."):
                response = st.session_state.tutor.initialize_session(
                    subject, level, prerequisites, topic
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.teaching_state = 'teach_topic'
                st.rerun()

    # Teaching state - Present lesson
    elif st.session_state.teaching_state == 'teach_topic':
        try:
            with st.spinner("Preparing your lesson..."):
                content = st.session_state.tutor.teach_topic()
                if content and all(key in content for key in ['lesson', 'examples', 'question']):
                    message = f"""# {st.session_state.tutor.current_topic}

## 🔑 Let's Understand This!
{content['lesson']}

## 📝 See It In Action
{content['examples']}

## ❓ Let's Chat About This
{content['question']}
"""
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.session_state.last_question = content['question']
                    st.session_state.teaching_state = 'wait_for_answer'
                    st.rerun()
                else:
                    st.error("I couldn't generate the lesson properly. Let's try again!")
                    st.session_state.teaching_state = 'initialize'
                    st.rerun()
        except Exception as e:
            st.error(f"An error occurred while preparing the lesson: {str(e)}")
            st.session_state.teaching_state = 'initialize'
            st.rerun()

    # Waiting for answer state
    elif st.session_state.teaching_state == 'wait_for_answer':
        if prompt := st.chat_input("Share your thoughts..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Thinking about your response..."):
                evaluation = st.session_state.tutor.evaluate_answer(
                    st.session_state.last_question, prompt
                )
                
                # Format feedback with appropriate emoji
                if evaluation['evaluation'] == 'correct':
                    feedback = f"✨ Great thinking! {evaluation['feedback']}"
                else:
                    feedback = f"💭 Interesting perspective! {evaluation['feedback']}"
                
                st.session_state.messages.append({"role": "assistant", "content": feedback})
                
                if evaluation['move_on']:
                    if st.session_state.tutor.move_to_next_topic():
                        st.session_state.teaching_state = 'teach_topic'
                    else:
                        st.session_state.teaching_state = 'finished'
                st.rerun()

    # Finished state
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
