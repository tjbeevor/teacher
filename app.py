import streamlit as st
import google.generativeai as genai
from datetime import datetime

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Page config
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

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

    # [Previous method definitions remain the same]

    def teach_topic(self):
        current_topic = self.current_topic
        
        prompt = f"""You are an expert Python programming tutor. Create a detailed lesson about {current_topic}.
        Structure your response exactly as shown below:

[LESSON]
# {current_topic}

## Overview
[Write a thorough introduction explaining the concept]

## Key Components
[List and explain all major components and concepts]

## Detailed Explanation
[Provide in-depth technical details and explanations]

## Common Pitfalls and Best Practices
[List important considerations and recommendations]

[EXAMPLES]
# Basic Usage
```python
[Include basic example code]
```
[Explain the basic example]

# Intermediate Usage
```python
[Include intermediate example code]
```
[Explain the intermediate example]

# Advanced Usage
```python
[Include advanced example code]
```
[Explain the advanced example]

[PRACTICE]
[Create a practical, real-world scenario question]
[Include specific points to consider]
"""
        
        try:
            response = self.api_client.generate_content(prompt)
            if not response:
                return None

            content = response
            lesson_section = ""
            examples_section = ""
            practice_section = ""

            if "[LESSON]" in content and "[EXAMPLES]" in content and "[PRACTICE]" in content:
                parts = content.split("[LESSON]")[1].split("[EXAMPLES]")
                lesson_section = parts[0].strip()
                remaining = parts[1].split("[PRACTICE]")
                examples_section = remaining[0].strip()
                practice_section = remaining[1].strip()

            return {
                'lesson': lesson_section if lesson_section else "Content generation failed.",
                'examples': examples_section if examples_section else "Examples not available.",
                'question': practice_section if practice_section else "Practice question not available."
            }

        except Exception as e:
            st.error(f"Error in lesson generation: {str(e)}")
            return None

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'teaching_state' not in st.session_state:
    st.session_state.teaching_state = 'initialize'
if 'tutor' not in st.session_state:
    st.session_state.tutor = AITutor()
if 'last_question' not in st.session_state:
    st.session_state.last_question = None

def main():
    st.title("🎓 AI Tutor")
    
    with st.sidebar:
        st.header("Learning Settings")
        subject = st.selectbox(
            "Subject",
            ["Python Programming", "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
        )
        level = st.selectbox(
            "Level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        topic = st.text_input("Topic")
        prerequisites = st.text_area("Your Background (Optional)")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
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
        if content:
            message = f"""# {st.session_state.tutor.current_topic}

## 🔑 Key Concepts
{content['lesson']}

## 📝 Examples
{content['examples']}

## ❓ Practice Question
{content['question']}"""
            st.session_state.messages.append({"role": "assistant", "content": message})
            st.session_state.last_question = content['question']
            st.session_state.teaching_state = 'wait_for_answer'
            st.rerun()

    elif st.session_state.teaching_state == 'wait_for_answer':
        prompt = st.chat_input("Share your thoughts...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            evaluation = st.session_state.tutor.evaluate_answer(
                st.session_state.last_question, prompt
            )
            
            feedback = "✨ Great thinking! " + evaluation['feedback'] if evaluation['evaluation'] == 'correct' else "💭 Interesting perspective! " + evaluation['feedback']
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
