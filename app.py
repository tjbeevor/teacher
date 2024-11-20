import streamlit as st
import google.generativeai as genai
from datetime import datetime

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
.main-content h1 {
    font-size: 1.8rem;
    margin-bottom: 1rem;
}
.main-content h2 {
    font-size: 1.4rem;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
    color: #1E88E5;
}
.main-content h3 {
    font-size: 1.2rem;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    color: #43A047;
}
.main-content p, .stMarkdown p {
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}
.main-content pre {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
}
.main-content code {
    font-size: 0.9rem;
}
.section-divider {
    margin: 2rem 0;
    border-top: 1px solid #e0e0e0;
}
.feedback-box {
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
    background-color: #f8f9fa;
}
.feedback-positive {
    border-left: 4px solid #43A047;
}
.feedback-partial {
    border-left: 4px solid #FB8C00;
}
.feedback-negative {
    border-left: 4px solid #E53935;
}
.stButton button {
    width: 100%;
    background-color: #1E88E5;
    color: white;
}
</style>
""", unsafe_allow_html=True)

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
        self.retry_count = 0
        self.max_retries = 3

    def initialize_session(self, subject, level, prerequisites, topic):
        prompt = f"""
        As a tutor teaching {subject} at {level} level, create a well-structured learning path.
        Student background: {prerequisites}
        Topic: {topic}

        Provide exactly 5 key subtopics that progressively build understanding.
        Format as:
        1. [Basic concept/foundation]
        2. [Core principles]
        3. [Advanced concepts]
        4. [Practical applications]
        5. [Integration and synthesis]
        """
        try:
            response = self.api_client.generate_content(prompt)
            if response:
                topics = [line.split('. ')[1].strip() 
                         for line in response.split('\n') 
                         if line.strip() and line[0].isdigit()]
                if len(topics) == 5:
                    self.topics = topics
                    self.current_topic_index = 0
                    self.current_topic = self.topics[self.current_topic_index]
                    return f"""# Let's study {topic}!

Below is your learning path:

1. {topics[0]}
2. {topics[1]}
3. {topics[2]}
4. {topics[3]}
5. {topics[4]}

Let's begin with {self.current_topic}!"""
            return "I'm sorry, but I couldn't generate topics. Please try again."
        except Exception as e:
            st.error(f"Error initializing session: {str(e)}")
            return "I'm sorry, but I encountered an error. Please try again."

    def teach_topic(self):
        current_topic = self.current_topic
        
        prompt = f"""Create a comprehensive tutorial about {current_topic}.
        Format as follows:

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

        try:
            response = self.api_client.generate_content(prompt)
            if not response:
                return None

            content = response
            sections = content.split('[')
            lesson = {}

            for section in sections:
                if 'LESSON]' in section:
                    lesson['lesson'] = section.split(']')[1].strip()
                elif 'EXAMPLES]' in section:
                    lesson['examples'] = section.split(']')[1].strip()
                elif 'PRACTICE]' in section:
                    lesson['question'] = section.split(']')[1].strip()

            if all(key in lesson for key in ['lesson', 'examples', 'question']):
                return lesson

            raise ValueError("Missing sections in generated content")

        except Exception as e:
            st.error(f"Error in lesson generation: {str(e)}")
            return None

    def evaluate_answer(self, question, answer):
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

        try:
            response = self.api_client.generate_content(prompt)
            if response:
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

def init_session_state():
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

init_session_state()

def main():
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

{content['lesson']}

## Examples
{content['examples']}

## Practice
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
            
            # Create formatted feedback
            feedback_class = (
                'feedback-positive' if evaluation['evaluation'] == 'correct'
                else 'feedback-partial' if evaluation['evaluation'] == 'partial'
                else 'feedback-negative'
            )

            feedback = f"""<div class='feedback-box {feedback_class}'>

### Understanding Review
{evaluation.get('understanding', '')}

### Feedback
{evaluation.get('feedback', '')}

### Areas for Improvement
{evaluation.get('improvement', '')}"""

            if not evaluation['move_on']:
                feedback += f"""

### Follow-up Question
{evaluation.get('followup', '')}"""

            feedback += "</div>"
            
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
