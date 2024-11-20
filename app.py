import streamlit as st
import google.generativeai as genai
import time
import re
from typing import Dict, List, Optional, Any

# Initialize page configuration
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# Configure Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Custom CSS styling
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
.stButton button { width: 100%; }
.topic-list { padding-left: 1.5rem; }
.topic-item { margin-bottom: 0.5rem; }
.learning-objective { margin-bottom: 0.5rem; padding-left: 1rem; border-left: 3px solid #1E88E5; }
.misconception { background-color: #FFF3E0; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
.real-world { background-color: #E8F5E9; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
.interactive { background-color: #E3F2FD; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; }
.stMarkdown { max-width: 100%; }
.element-container { max-width: 100%; }
</style>
""", unsafe_allow_html=True)

class AITutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.max_retries = 3
        self.retry_delay = 1

    def generate_with_retry(self, prompt: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    st.error(f"API Error: {str(e)}")
                    return None
                time.sleep(self.retry_delay * (attempt + 1))
        return None

    def generate_curriculum(self, subject: str, level: str, topic: str) -> List[str]:
        prompt = f"""Create a structured learning path for {topic} in {subject} at {level} level.
        Generate exactly 5 sequential subtopics that progressively build understanding.
        Format as a simple numbered list with topic names only.
        Example:
        1. Introduction to Variables
        2. Basic Data Types
        3. Type Conversion
        4. Variable Scope
        5. Best Practices
        """

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_curriculum(topic)

        try:
            topics = []
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            for line in lines:
                if line[0].isdigit() and '. ' in line:
                    topic_name = line.split('. ')[1].strip()
                    topics.append(topic_name)
            
            return topics[:5] if len(topics) >= 5 else self.get_default_curriculum(topic)
        except Exception:
            return self.get_default_curriculum(topic)

    def get_default_curriculum(self, topic: str) -> List[str]:
        return [
            f"Introduction to {topic}",
            f"Core Concepts of {topic}",
            f"Applied {topic}",
            f"Advanced {topic}",
            f"Mastering {topic}"
        ]

    def generate_lesson(self, topic: str, level: str) -> Dict[str, str]:
        prompt = f"""Create an engaging lesson about {topic} for {level} level students.
        Format with clear markdown headings and bullet points.
        
        Include:
        - 3 specific learning objectives
        - Brief introduction with a hook
        - 3 key concepts with examples
        - 2 practice examples
        - 1 thought-provoking practice question
        """

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_lesson(topic)

        try:
            sections = {}
            current_section = "introduction"
            current_content = []

            for line in response.split('\n'):
                line = line.strip()
                if line.lower().startswith('learning objectives'):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = "objectives"
                    current_content = []
                elif line.lower().startswith('key concepts') or line.lower().startswith('core concepts'):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = "core_concepts"
                    current_content = []
                elif line.lower().startswith('practice'):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = "practice"
                    current_content = []
                elif line.lower().startswith('examples'):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = "examples"
                    current_content = []
                elif line:
                    current_content.append(line)

            if current_content:
                sections[current_section] = '\n'.join(current_content)

            return {
                'objectives': sections.get('objectives', ''),
                'introduction': sections.get('introduction', ''),
                'core_concepts': sections.get('core_concepts', ''),
                'examples': sections.get('examples', ''),
                'practice': sections.get('practice', '')
            }

        except Exception as e:
            st.error(f"Error generating lesson: {str(e)}")
            return self.get_default_lesson(topic)

    def get_default_lesson(self, topic: str) -> Dict[str, str]:
        return {
            'objectives': f"• Understand basic principles of {topic}\n• Apply key concepts\n• Analyze real-world applications",
            'introduction': f"Let's explore {topic} and its importance.",
            'core_concepts': f"Key concepts of {topic}...",
            'examples': "Example 1: Basic application\nExample 2: Advanced usage",
            'practice': f"Explain how {topic} works and provide an example."
        }

    def evaluate_answer(self, question: str, answer: str, level: str) -> Dict[str, Any]:
        prompt = f"""Evaluate this {level}-level response.
        Question: {question}
        Student's Answer: {answer}
        
        Provide clear feedback in these categories:
        - Understanding (what concepts were understood)
        - Feedback (specific praise and areas for improvement)
        - Next Steps (suggested practice or review)
        - Score (1-5) for overall understanding
        - Should they move on? (yes/no)
        """

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_evaluation()

        try:
            evaluation = {}
            current_section = None
            current_content = []

            for line in response.split('\n'):
                line = line.strip()
                if line.lower().startswith('understanding'):
                    current_section = 'understanding'
                    current_content = []
                elif line.lower().startswith('feedback'):
                    if current_section:
                        evaluation[current_section] = '\n'.join(current_content)
                    current_section = 'feedback'
                    current_content = []
                elif line.lower().startswith('next steps'):
                    if current_section:
                        evaluation[current_section] = '\n'.join(current_content)
                    current_section = 'next_steps'
                    current_content = []
                elif line and current_section:
                    current_content.append(line)

            if current_section and current_content:
                evaluation[current_section] = '\n'.join(current_content)

            # Extract score and move_on from the response
            score_match = re.search(r'score.*?(\d+)', response.lower())
            score = int(score_match.group(1)) if score_match else 3
            move_on = 'yes' in response.lower()

            return {
                'evaluation': 'correct' if score >= 4 else 'partial' if score >= 3 else 'incorrect',
                'understanding': evaluation.get('understanding', ''),
                'feedback': evaluation.get('feedback', ''),
                'next_steps': evaluation.get('next_steps', ''),
                'move_on': move_on
            }

        except Exception:
            return self.get_default_evaluation()

    def get_default_evaluation(self) -> Dict[str, Any]:
        return {
            'evaluation': 'partial',
            'understanding': 'Shows basic understanding of concepts.',
            'feedback': 'Good start. Consider adding more specific examples.',
            'next_steps': 'Review core concepts and try more practice problems.',
            'move_on': False
        }

def format_message(content_type: str, content: str) -> str:
    """Format message content with consistent markdown."""
    if content_type == "intro":
        parts = content.split('\n\n')
        formatted_parts = []
        for part in parts:
            if part.startswith('# '):
                formatted_parts.append(part)
            elif part.strip():
                formatted_parts.append('## ' + part.strip())
        return '\n\n'.join(formatted_parts)
    elif content_type == "lesson":
        return content
    elif content_type == "feedback":
        return content
    return content

def init_session_state():
    """Initialize session state variables."""
    if not hasattr(st.session_state, 'initialized'):
        st.session_state.messages = []
        st.session_state.teaching_state = 'initialize'
        st.session_state.tutor = AITutor()
        st.session_state.current_topic_index = 0
        st.session_state.topics = []
        st.session_state.last_question = None
        st.session_state.lesson_generated = False
        st.session_state.initialized = True

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

        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)

        # Main teaching flow
        if st.session_state.teaching_state == 'initialize':
            if topic and st.button("Start Learning"):
                topics = st.session_state.tutor.generate_curriculum(subject, level, topic)
                st.session_state.topics = topics
                
                intro_message = f"""# 📚 Let's learn about {topic}!

## Learning Path
{chr(10).join(f'**{i+1}.** {t}' for i, t in enumerate(topics))}

Let's start with **{topics[0]}**!"""
                
                st.session_state.messages = [{"role": "assistant", "content": format_message("intro", intro_message)}]
                st.session_state.current_topic_index = 0
                st.session_state.teaching_state = 'teach_topic'
                st.session_state.lesson_generated = False
                st.rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            if not st.session_state.lesson_generated:
                current_topic = st.session_state.topics[st.session_state.current_topic_index]
                lesson = st.session_state.tutor.generate_lesson(current_topic, level)
                
                lesson_message = f"""# **{current_topic}**

## **Learning Objectives**
{lesson.get('objectives', '')}

## **Introduction**
{lesson.get('introduction', '')}

## **Core Concepts**
{lesson.get('core_concepts', '')}

## **Examples**
{lesson.get('examples', '')}

## **Practice Question**
{lesson.get('practice', '')}"""

                st.session_state.messages.append(
                    {"role": "assistant", "content": format_message("lesson", lesson_message)}
                )
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
                
                feedback_class = (
                    'feedback-positive' if evaluation['evaluation'] == 'correct'
                    else 'feedback-partial' if evaluation['evaluation'] == 'partial'
                    else 'feedback-negative'
                )

                feedback_message = f"""<div class='feedback-box {feedback_class}'>

### Understanding
{evaluation['understanding']}

### Feedback
{evaluation['feedback']}

### Next Steps
{evaluation['next_steps']}
</div>"""

                st.session_state.messages.append(
                    {"role": "assistant", "content": format_message("feedback", feedback_message)}
                )
                
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
