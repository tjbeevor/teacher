import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
from content_generator import LessonGenerator
from assessment_engine import AssessmentEngine

# Must be the first Streamlit command
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Add custom CSS
st.markdown("""
<style>
.main-content h1 { font-size: 1.8rem; margin-bottom: 1rem; }
.main-content h2 { font-size: 1.4rem; margin-top: 1.5rem; margin-bottom: 0.8rem; color: #1E88E5; }
.main-content h3 { font-size: 1.2rem; margin-top: 1rem; margin-bottom: 0.5rem; color: #43A047; }
.main-content p, .stMarkdown p { font-size: 1rem; line-height: 1.5; margin-bottom: 1rem; }
pre { background-color: #f8f9fa; padding: 1rem; border-radius: 4px; margin: 1rem 0; }
code { font-size: 0.9rem; }
.feedback-box { padding: 1rem; border-radius: 4px; margin: 1rem 0; background-color: #f8f9fa; }
.feedback-positive { border-left: 4px solid #43A047; }
.feedback-partial { border-left: 4px solid #FB8C00; }
.feedback-negative { border-left: 4px solid #E53935; }
.stButton button { width: 100%; background-color: #1E88E5; color: white; }
.topic-list { padding-left: 1.5rem; }
.topic-item { margin-bottom: 0.5rem; }
.learning-objective { margin-bottom: 0.5rem; padding-left: 1rem; border-left: 3px solid #1E88E5; }
.misconception { background-color: #FFF3E0; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
.real-world { background-color: #E8F5E9; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
.interactive { background-color: #E3F2FD; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

class AITutor:
    def __init__(self):
        self.lesson_generator = LessonGenerator()
        self.assessment_engine = AssessmentEngine()
        self.current_topic = None
        self.topics = []
        self.current_topic_index = 0
        self.retry_count = 0
        self.max_retries = 3

    def validate_session_state(self) -> bool:
        required_states = ['current_topic', 'topics', 'current_topic_index']
        return all(hasattr(self, state) for state in required_states)

    def initialize_session(self, subject: str, level: str, prerequisites: str, topic: str) -> str:
        try:
            topics = self.lesson_generator.generate_curriculum(subject, level, topic, prerequisites)
            if not topics:
                raise ValueError("Failed to generate curriculum")

            self.topics = topics
            self.current_topic_index = 0
            self.current_topic = self.topics[self.current_topic_index]

            return f"""# 📚 Let's learn about {topic}!

## Learning Path
{self.lesson_generator.format_curriculum(topics)}

Let's start with {self.current_topic}!"""

        except Exception as e:
            st.error(f"Error initializing session: {str(e)}")
            return None

    def teach_topic(self) -> Optional[Dict[str, str]]:
        if not self.validate_session_state():
            st.error("Session state is invalid. Please restart the session.")
            return None

        try:
            content = self.lesson_generator.generate_lesson_content(
                self.current_topic,
                self.topics,
                self.current_topic_index
            )
            
            if not content:
                return None

            return content

        except Exception as e:
            st.error(f"Error generating lesson: {str(e)}")
            return None

    def evaluate_answer(self, question: str, answer: str, level: str) -> Dict[str, Any]:
        try:
            evaluation = self.assessment_engine.evaluate_response(
                question,
                answer,
                self.current_topic,
                level
            )
            
            if not evaluation:
                raise ValueError("Failed to generate evaluation")
                
            return evaluation

        except Exception as e:
            st.error(f"Error evaluating answer: {str(e)}")
            return {
                'evaluation': 'partial',
                'feedback': "I couldn't properly evaluate your answer. Please try again.",
                'move_on': False
            }

    def move_to_next_topic(self) -> bool:
        if not self.validate_session_state():
            return False
            
        self.current_topic_index += 1
        if self.current_topic_index < len(self.topics):
            self.current_topic = self.topics[self.current_topic_index]
            return True
        return False

def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'teaching_state' not in st.session_state:
        st.session_state.teaching_state = 'initialize'
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    if 'last_question' not in st.session_state:
        st.session_state.last_question = None
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0
    if 'current_level' not in st.session_state:
        st.session_state.current_level = 1

def safe_rerun():
    try:
        st.rerun()
    except Exception as e:
        st.error(f"Error during rerun: {str(e)}")
        st.session_state.error_count += 1
        if st.session_state.error_count > 3:
            st.error("Too many errors. Please refresh the page.")
            st.stop()

def main():
    try:
        # Header with reset button
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if st.button("🔄 Reset"):
                st.session_state.clear()
                st.rerun()
        with col2:
            st.title("🎓 AI Tutor")
        
        # Sidebar
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

        # Main content
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.teaching_state == 'initialize':
            if topic and st.button("Start Learning"):
                with st.spinner("Preparing your learning path..."):
                    response = st.session_state.tutor.initialize_session(
                        subject, level, prerequisites, topic
                    )
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.session_state.teaching_state = 'teach_topic'
                        safe_rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            with st.spinner("Preparing your lesson..."):
                content = st.session_state.tutor.teach_topic()
                if content:
                    message = f"""# {st.session_state.tutor.current_topic}

{content['lesson']}

## Interactive Elements
{content['interactive']}

## Real-World Applications
{content['applications']}

## Practice
{content['question']}"""
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.session_state.last_question = content['question']
                    st.session_state.teaching_state = 'wait_for_answer'
                    safe_rerun()
                else:
                    st.error("Failed to generate lesson content. Please try again.")
                    st.session_state.teaching_state = 'initialize'
                    safe_rerun()

        elif st.session_state.teaching_state == 'wait_for_answer':
            prompt = st.chat_input("Share your thoughts...")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Evaluating your answer..."):
                    evaluation = st.session_state.tutor.evaluate_answer(
                        st.session_state.last_question,
                        prompt,
                        level
                    )
                    
                    feedback_class = (
                        'feedback-positive' if evaluation['evaluation'] == 'correct'
                        else 'feedback-partial' if evaluation['evaluation'] == 'partial'
                        else 'feedback-negative'
                    )

                    feedback = f"""<div class='feedback-box {feedback_class}'>

### Understanding Analysis
{evaluation.get('understanding', 'No understanding analysis available.')}

### Detailed Feedback
{evaluation.get('feedback', 'No specific feedback available.')}

### Growth Opportunities
{evaluation.get('improvement', 'No improvement suggestions available.')}"""

                    if not evaluation['move_on']:
                        feedback += f"""

### Follow-up Challenge
{evaluation.get('challenge', 'Would you like to explore this concept further?')}"""

                    feedback += "</div>"
                    
                    st.session_state.messages.append({"role": "assistant", "content": feedback})
                    
                    if evaluation['move_on']:
                        if st.session_state.tutor.move_to_next_topic():
                            st.session_state.teaching_state = 'teach_topic'
                        else:
                            st.session_state.teaching_state = 'finished'
                    safe_rerun()

        elif st.session_state.teaching_state == 'finished':
            st.success("🎉 Congratulations! You've completed all topics!")
            if st.button("Start New Topic"):
                st.session_state.clear()
                init_session_state()
                safe_rerun()

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please try resetting the application using the button in the top left corner.")
        print(f"Error in main(): {str(e)}")
        st.session_state.error_count += 1
        if st.session_state.error_count > 3:
            st.warning("Multiple errors detected. Please refresh the page to start fresh.")
            st.stop()

if __name__ == "__main__":
    try:
        init_session_state()
        main()
    except Exception as e:
        st.error(f"Error during startup: {str(e)}")
