import streamlit as st
import google.generativeai as genai
from .ai_tutor import AITutor  # Change this line

# Initialize page configuration
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# Configure Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def format_content(content_type: str, content: str) -> str:
    """Format content with proper markdown and spacing."""
    if not content:
        return ""
        
    if content_type == "topic":
        return f"# {content}"
    elif content_type == "section":
        return f"## {content}"
    elif content_type == "subsection":
        return f"### {content}"
    elif content_type == "list":
        return "\n".join(f"* {item}" for item in content.split("\n"))
    return content

def format_lesson(topic: str, lesson: dict) -> str:
    """Format the lesson content with proper markdown structure."""
    return f"""
# {topic}

## Learning Objectives
{lesson['objectives']}

## Introduction
{lesson['introduction']}

## Core Concepts
{lesson['core_concepts']}

## Examples
{lesson['examples']}

## Practice Question
{lesson['practice']}
"""

def format_feedback(evaluation: dict) -> str:
    """Format the feedback with proper styling."""
    feedback_class = (
        'feedback-positive' if evaluation['evaluation'] == 'correct'
        else 'feedback-partial' if evaluation['evaluation'] == 'partial'
        else 'feedback-negative'
    )
    
    return f"""
<div class="feedback-box {feedback_class}">
<h3>Understanding</h3>
<p>{evaluation['understanding']}</p>

<h3>Feedback</h3>
<p>{evaluation['feedback']}</p>

<h3>Next Steps</h3>
<p>{evaluation['next_steps']}</p>
</div>
"""

def init_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'teaching_state' not in st.session_state:
        st.session_state.teaching_state = 'initialize'
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    if 'current_topic_index' not in st.session_state:
        st.session_state.current_topic_index = 0
    if 'topics' not in st.session_state:
        st.session_state.topics = []
    if 'last_question' not in st.session_state:
        st.session_state.last_question = None
    if 'lesson_generated' not in st.session_state:
        st.session_state.lesson_generated = False

def main():
    try:
        # Header
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

        # Display existing messages with proper formatting
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)

        # Main teaching flow
        if st.session_state.teaching_state == 'initialize':
            if topic and st.button("Start Learning"):
                topics = st.session_state.tutor.generate_curriculum(subject, level, topic)
                st.session_state.topics = topics
                
                intro_message = f"""
# 📚 Let's learn about {topic}!

## Learning Path
{chr(10).join(f'**{i+1}.** {t}' for i, t in enumerate(topics))}

Let's start with **{topics[0]}**!
"""
                
                st.session_state.messages = [{"role": "assistant", "content": intro_message}]
                st.session_state.current_topic_index = 0
                st.session_state.teaching_state = 'teach_topic'
                st.session_state.lesson_generated = False
                st.rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            if not st.session_state.lesson_generated:
                current_topic = st.session_state.topics[st.session_state.current_topic_index]
                lesson = st.session_state.tutor.generate_lesson(current_topic, level)
                lesson_message = format_lesson(current_topic, lesson)
                
                st.session_state.messages.append({"role": "assistant", "content": lesson_message})
                st.session_state.last_question = lesson['practice']
                st.session_state.teaching_state = 'wait_for_answer'
                st.session_state.lesson_generated = True
                st.rerun()

        elif st.session_state.teaching_state == 'wait_for_answer':
            answer = st.chat_input("Your answer...")
            if answer:
                st.session_state.messages.append({"role": "user", "content": answer})
                
                evaluation = st.session_state.tutor.evaluate_answer(
                    st.session_state.last_question,
                    answer,
                    level
                )
                
                feedback_message = format_feedback(evaluation)
                st.session_state.messages.append({"role": "assistant", "content": feedback_message})
                
                if evaluation['move_on']:
                    st.session_state.current_topic_index += 1
                    if st.session_state.current_topic_index < len(st.session_state.topics):
                        st.session_state.teaching_state = 'teach_topic'
                        st.session_state.lesson_generated = False
                    else:
                        st.session_state.teaching_state = 'finished'
                st.rerun()

        elif st.session_state.teaching_state == 'finished':
            st.success("🎉 Congratulations! You've completed all topics!")
            if st.button("Start New Topic"):
                st.session_state.clear()
                init_session_state()
                st.rerun()

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please try resetting the application using the button in the top left corner.")

if __name__ == "__main__":
    try:
        init_session_state()
        main()
    except Exception as e:
        st.error(f"Error during startup: {str(e)}")
