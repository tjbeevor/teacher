import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
import re

# Initialize page configuration
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# Configure Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Custom CSS styling
css = """
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
"""
st.markdown(css, unsafe_allow_html=True)

class AITutor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.topics = []
        self.current_topic_index = 0
        self.current_topic = None
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
        
        Format EXACTLY as:
        1. [Topic Name] - Brief description
        2. [Topic Name] - Brief description
        3. [Topic Name] - Brief description
        4. [Topic Name] - Brief description
        5. [Topic Name] - Brief description
        
        Each topic should:
        - Build on previous knowledge
        - Be specific and focused
        - Lead to mastery of {topic}
        - Be appropriate for {level} level
        """

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_curriculum(topic)

        try:
            topics = []
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            for line in lines:
                if line[0].isdigit() and '. ' in line and ' - ' in line:
                    topic_name = line.split(' - ')[0].split('. ')[1].strip()
                    topics.append(topic_name)
            
            return topics if len(topics) == 5 else self.get_default_curriculum(topic)
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

[OBJECTIVES]
List 3 clear learning objectives using Bloom's Taxonomy verbs.

[INTRODUCTION]
Create an engaging hook and overview of {topic}.

[CORE CONCEPTS]
Break down {topic} into 3 main ideas:
1. [Fundamental Concept]
   • Clear explanation
   • Simple example
   • Key terms defined
2. [Key Principle]
   • Detailed explanation
   • Real-world example
   • Common applications
3. [Advanced Application]
   • Complex concepts
   • Practical usage
   • Problem-solving approaches

[EXAMPLES]
Provide 2 clear examples:
1. Basic example with step-by-step explanation
2. Advanced example showing practical application

[PRACTICE]
Create a thought-provoking question that:
• Tests understanding of multiple concepts
• Relates to real-world scenarios
• Requires critical thinking
• Has multiple valid approaches

Format all content in clear, engaging language appropriate for {level} level."""

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_lesson(topic)

        try:
            sections = {}
            current_section = None
            current_content = []

            for line in response.split('\n'):
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    if current_section and current_content:
                        sections[current_section.lower()] = '\n'.join(current_content)
                    current_section = line.strip()[1:-1]
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line.strip())

            if current_section and current_content:
                sections[current_section.lower()] = '\n'.join(current_content)

            return {
                'objectives': sections.get('objectives', ''),
                'introduction': sections.get('introduction', ''),
                'core_concepts': sections.get('core concepts', ''),
                'examples': sections.get('examples', ''),
                'practice': sections.get('practice', '')
            }

        except Exception:
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

Provide evaluation in this format:

[UNDERSTANDING]
• List concepts understood correctly
• Identify any misconceptions
• Note innovative thinking

[FEEDBACK]
• Specific praise for strong points
• Areas for improvement
• Suggested corrections

[NEXT STEPS]
• Topics to review
• Practice suggestions
• Extension questions

[MASTERY]
Score each area (1-5):
• Concept Understanding: [1-5]
• Application: [1-5]
• Communication: [1-5]

[MOVE_ON]
yes/no (Based on demonstrated understanding)"""

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_evaluation()

        try:
            evaluation = {}
            current_section = None
            current_content = []

            for line in response.split('\n'):
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    if current_section and current_content:
                        evaluation[current_section.lower()] = '\n'.join(current_content)
                    current_section = line.strip()[1:-1]
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line.strip())

            if current_section and current_content:
                evaluation[current_section.lower()] = '\n'.join(current_content)

            scores = []
            mastery_text = evaluation.get('mastery', '')
            score_matches = re.findall(r': (\d+)', mastery_text)
            scores = [int(score) for score in score_matches if score.isdigit()]
            average_score = sum(scores) / len(scores) if scores else 3

            move_on = 'yes' in evaluation.get('move_on', '').lower()
            
            return {
                'evaluation': 'correct' if average_score >= 4 else 'partial' if average_score >= 3 else 'incorrect',
                'understanding': evaluation.get('understanding', ''),
                'feedback': evaluation.get('feedback', ''),
                'next_steps': evaluation.get('next steps', ''),
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

def init_session_state():
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

        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Main teaching flow
        if st.session_state.teaching_state == 'initialize':
            if topic and st.button("Start Learning"):
                # Generate curriculum
                topics = st.session_state.tutor.generate_curriculum(subject, level, topic)
                st.session_state.topics = topics
                
                # Format introduction message
                intro_message = f"""# 📚 Let's learn about {topic}!

## Learning Path
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(topics))}

Let's start with {topics[0]}!"""
                
                st.session_state.messages = [{"role": "assistant", "content": intro_message}]
                st.session_state.current_topic_index = 0
                st.session_state.teaching_state = 'teach_topic'
                st.session_state.lesson_generated = False
                st.rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            if not st.session_state.lesson_generated:
                current_topic = st.session_state.topics[st.session_state.current_topic_index]
                lesson = st.session_state.tutor.generate_lesson(current_topic, level)
                
                # Debug print
                st.write("Debug - Raw lesson content:", lesson)
                
                lesson_message = f"""# {current_topic}

{lesson['objectives']}

{lesson['introduction']}

{lesson['core_concepts']}

{lesson['examples']}

{lesson['practice']}"""

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
                
                feedback_class = (
                    'feedback-positive' if evaluation['evaluation'] == 'correct'
                    else 'feedback-partial' if evaluation['evaluation'] == 'partial'
                    else 'feedback-negative'
                )

                feedback = f"""<div class='feedback-box {feedback_class}'>

### Understanding
{evaluation['understanding']}

### Feedback
{evaluation['feedback']}

### Next Steps
{evaluation['next_steps']}</div>"""

                st.session_state.messages.append({"role": "assistant", "content": feedback})
                
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
