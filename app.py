import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
from typing import Dict, List, Optional, Any

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
.error-message { color: #E53935; padding: 1rem; background-color: #FFEBEE; border-radius: 4px; }
.info-message { color: #1E88E5; padding: 1rem; background-color: #E3F2FD; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

class APIClient:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def generate_with_retry(self, prompt: str) -> Optional[str]:
        """Generate content with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    st.error(f"API Error after {self.max_retries} attempts: {str(e)}")
                    return None
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        return None

class AITutor:
    def __init__(self):
        self.api_client = APIClient()
        self.current_topic: Optional[str] = None
        self.topics: List[str] = []
        self.current_topic_index: int = 0
        self.retry_count: int = 0
        self.max_retries: int = 3

    def validate_session_state(self) -> bool:
        """Validate that all required session state variables are present."""
        required_states = ['current_topic', 'topics', 'current_topic_index']
        return all(hasattr(self, state) for state in required_states)

    def get_fallback_content(self, topic: str) -> Dict[str, str]:
        """Provide fallback content when API fails."""
        return {
            'lesson': f"""# Introduction to {topic}
            
            ## Core Concepts
            • Basic principles of {topic}
            • Fundamental terminology
            • Key components
            
            ## Implementation
            • Basic usage patterns
            • Common applications
            • Best practices
            
            ## Technical Details
            • Important considerations
            • Limitations
            • Basic optimization
            """,
            'examples': f"""1. Basic Example
            Here's a simple example of {topic} in practice...
            
            2. Advanced Example
            Here's a more complex implementation...""",
            'question': f"Based on what we've covered, explain the key concepts of {topic} in your own words."
        }

    def parse_topics(self, response: str) -> List[str]:
        """Parse topics from API response with error handling."""
        try:
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            topics = []
            
            for line in lines:
                if line[0].isdigit() and '. ' in line:
                    topic_text = line.split('. ')[1].split(' - ')[0].strip()
                    topics.append(topic_text)
            
            return topics if len(topics) == 5 else []
        except Exception:
            return []

    def initialize_session(self, subject: str, level: str, prerequisites: str, topic: str) -> str:
        """Initialize learning session with improved error handling."""
        prompt = f"""As an expert {subject} tutor teaching at {level} level, create a structured learning path for {topic}.
        Student background: {prerequisites}

        Break down {topic} into exactly 5 sequential subtopics that build progressively.
        Each subtopic should be clear and specific.
        Format your response exactly like this:
        1. (Basic Concept) - Brief description
        2. (Fundamental Principle) - Brief description
        3. (Core Mechanism) - Brief description
        4. (Advanced Application) - Brief description
        5. (Integration) - Brief description

        Make the subtopics specific to {topic} following this pattern of progressive complexity."""

        response = self.api_client.generate_with_retry(prompt)
        
        if response:
            topics = self.parse_topics(response)
        else:
            topics = []

        if not topics:
            # Use fallback topics if API fails or parsing fails
            topics = [
                f"Introduction to {topic}",
                f"Core Concepts of {topic}",
                f"Advanced Principles of {topic}",
                f"Practical Applications of {topic}",
                f"Integration and Best Practices of {topic}"
            ]

        self.topics = topics
        self.current_topic_index = 0
        self.current_topic = self.topics[self.current_topic_index]

        return f"""# 📚 Let's learn about {topic}!

We'll explore these topics:

{chr(10).join(f"{i+1}. {t}" for i, t in enumerate(topics))}

Let's start with {self.current_topic}!"""

    def validate_lesson_content(self, content: Dict[str, str]) -> bool:
        """Validate that all required sections are present in lesson content."""
        required_sections = ['lesson', 'examples', 'question']
        return all(
            section in content and content[section].strip() 
            for section in required_sections
        )

    def teach_topic(self) -> Optional[Dict[str, str]]:
        """Generate lesson content with validation and fallback."""
        if not self.validate_session_state():
            st.error("Session state is invalid. Please restart the session.")
            return None

        current_topic = self.current_topic
        prompt = f"""Create a comprehensive tutorial about {current_topic}. Format as follows:

[LESSON]
{current_topic}

1. Core Concepts
   • [Provide thorough explanation of fundamental principles]
   • [Include detailed technical information]
   • [Explain key terminology]
   • [Describe relationships between concepts]

2. Implementation Details
   • [Explain how these concepts are used in practice]
   • [Discuss common patterns and applications]
   • [Include best practices and guidelines]
   • [Address common challenges and solutions]

3. Technical Considerations
   • [Cover advanced details]
   • [Explain implications]
   • [Discuss limitations]
   • [Include optimization strategies]

[EXAMPLES]
1. Basic Example
[Provide and explain a basic example]

2. Advanced Example
[Provide and explain a more complex example]

[PRACTICE]
Question:
[Ask a specific question that tests understanding of the core concepts]

Consider in your answer:
1. [Key point to address]
2. [Key point to address]
3. [Key point to address]

Explain your reasoning thoroughly."""

        response = self.api_client.generate_with_retry(prompt)
        
        if not response:
            return self.get_fallback_content(current_topic)

        try:
            sections = response.split('[')
            lesson = {}

            for section in sections:
                if 'LESSON]' in section:
                    lesson['lesson'] = section.split(']')[1].strip()
                elif 'EXAMPLES]' in section:
                    lesson['examples'] = section.split(']')[1].strip()
                elif 'PRACTICE]' in section:
                    lesson['question'] = section.split(']')[1].strip()

            if self.validate_lesson_content(lesson):
                return lesson
            
            return self.get_fallback_content(current_topic)

        except Exception as e:
            st.error(f"Error in lesson generation: {str(e)}")
            return self.get_fallback_content(current_topic)

    def evaluate_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Evaluate student answer with improved error handling."""
        prompt = f"""You are an expert tutor. Evaluate this answer:

Question: {question}
Student's answer: {answer}

Provide evaluation in this format:

[CORRECT]
yes/no/partial

[UNDERSTANDING]
• List concepts understood correctly
• Identify any misconceptions
• Note valuable insights

[FEEDBACK]
• Provide detailed, constructive feedback
• Explain any corrections needed
• Give specific examples
• Add relevant context

[IMPROVEMENT]
• Suggest specific study areas
• Recommend practice exercises
• Provide additional resources

[MOVE]
yes/no (Should we move to next topic?)

[FOLLOWUP]
If not moving on, provide a specific follow-up question"""

        response = self.api_client.generate_with_retry(prompt)
        
        if not response:
            return {
                'evaluation': 'partial',
                'understanding': 'Unable to fully evaluate your answer.',
                'feedback': 'Please try again or rephrase your answer.',
                'improvement': 'Consider reviewing the topic material again.',
                'move_on': False,
                'followup': 'Could you elaborate on your answer?'
            }

        try:
            parts = response.split('[')
            evaluation = {}
            
            for part in parts:
                if 'CORRECT]' in part:
                    correct_text = part.split(']')[1].lower().strip()
                    evaluation['evaluation'] = 'correct' if correct_text == 'yes' else 'incorrect' if correct_text == 'no' else 'partial'
                elif 'UNDERSTANDING]' in part:
                    evaluation['understanding'] = part.split(']')[1].strip()
                elif 'FEEDBACK]' in part:
                    evaluation['feedback'] = part.split(']')[1].strip()
                elif 'IMPROVEMENT]' in part:
                    evaluation['improvement'] = part.split(']')[1].strip()
                elif 'MOVE]' in part:
                    evaluation['move_on'] = 'yes' in part.split(']')[1].lower()
                elif 'FOLLOWUP]' in part:
                    evaluation['followup'] = part.split(']')[1].strip()
            
            # Ensure all required fields are present
            required_fields = ['evaluation', 'understanding', 'feedback', 'improvement', 'move_on', 'followup']
            for field in required_fields:
                if field not in evaluation:
                    evaluation[field] = ''
            
            return evaluation
            
        except Exception as e:
            st.error(f"Error in evaluation: {str(e)}")
            return {
                'evaluation': 'partial',
                'feedback': "I couldn't properly evaluate your answer. Please try again.",
                'move_on': False,
                'followup': "Could you rephrase your answer?"
            }

    def move_to_next_topic(self) -> bool:
        """Safely move to the next topic."""
        if not self.validate_session_state():
            return False
            
        self.current_topic_index += 1
        if self.current_topic_index < len(self.topics):
            self.current_topic = self.topics[self.current_topic_index]
            return True
        return False

def init_session_state():
    """Initialize or reset session state."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'teaching_state' not in st.session_state:
        st.session_state.teaching_state = 'initialize'
    if 'tutor' not in st.session_state:
        st.session_state.tutor = AITutor()
    if 'last_question' not in st.session_state:
        st.session_state.last_question = None
    if 'retry_count' not in st.session_state:
        st.session_state.retry_count = 0
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0

def safe_rerun():
    """Safely rerun the app with error tracking."""
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
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.teaching_state = 'teach_topic'
                    safe_rerun()

        elif st.session_state.teaching_state == 'teach_topic':
            with st.spinner("Preparing your lesson..."):
                content = st.session_state.tutor.teach_topic()
                if content:
                    message = f"""# {st.session_state.tutor.current_topic}
                
                {content['lesson']}
                
                ## Examples
                {content['examples']}
                
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
                        st.session_state.last_question, prompt
                    )
                    
                    feedback_class = (
                        'feedback-positive' if evaluation['evaluation'] == 'correct'
                        else 'feedback-partial' if evaluation['evaluation'] == 'partial'
                        else 'feedback-negative'
                    )

                    feedback = f"""<div class='feedback-box {feedback_class}'>

### Understanding Review
{evaluation.get('understanding', 'No understanding analysis available.')}

### Feedback
{evaluation.get('feedback', 'No specific feedback available.')}

### Areas for Improvement
{evaluation.get('improvement', 'No improvement suggestions available.')}"""

                    if not evaluation['move_on']:
                        feedback += f"""

### Follow-up Question
{evaluation.get('followup', 'Would you like to try again with a different approach?')}"""

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
        
        # Log error for debugging
        print(f"Error in main(): {str(e)}")
        
        # Increment error count
        st.session_state.error_count = st.session_state.get('error_count', 0) + 1
        
        # If too many errors occur, suggest refresh
        if st.session_state.error_count > 3:
            st.warning("Multiple errors detected. Please refresh the page to start fresh.")
            st.stop()

def handle_error(error: Exception, context: str = ""):
    """Central error handling function"""
    error_message = f"Error in {context}: {str(error)}"
    print(error_message)  # For logging
    st.error(error_message)
    
    # Increment error count
    st.session_state.error_count = st.session_state.get('error_count', 0) + 1
    
    if st.session_state.error_count > 3:
        st.warning("Too many errors occurred. Please refresh the page.")
        st.stop()
    return None

if __name__ == "__main__":
    try:
        init_session_state()
        main()
    except Exception as e:
        handle_error(e, "application startup")

