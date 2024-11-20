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
.main-content p {
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
.stButton button {
    background-color: #1E88E5;
    color: white;
}
.sidebar-content {
    padding: 1rem;
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
        current_topic = self.current_topic
        
        prompt = f"""Create a comprehensive tutorial about {current_topic}. Format as follows:

[LESSON]
{current_topic}

1. Core Concepts
   • [Provide a thorough explanation of the fundamental principles]
   • [Include detailed technical information]
   • [Explain key terminology]
   • [Describe relationships between concepts]

2. Implementation Details
   • [Explain how these concepts are used in practice]
   • [Discuss common implementation patterns]
   • [Include best practices and guidelines]
   • [Address common challenges and solutions]

3. Technical Considerations
   • [Cover advanced technical details]
   • [Explain performance implications]
   • [Discuss limitations and constraints]
   • [Include optimization strategies]

[EXAMPLES]
1. Basic Implementation
```python
[Provide basic code example]
# Include detailed comments explaining each line
```
- Explanation: [Thorough explanation of what the code does]
- Key Points: [List important concepts demonstrated]
- Output: [Show expected output]

2. Practical Application
```python
[Provide real-world application example]
# Include comprehensive comments
```
- Use Case: [Explain when to use this pattern]
- Implementation Notes: [Detail important considerations]
- Common Pitfalls: [Explain what to watch out for]

[PRACTICE]
Real-World Scenario:
[Present a practical problem that tests understanding]

Considerations:
1. [List key points to consider]
2. [Include technical requirements]
3. [Mention constraints or limitations]

Approach:
- [Guide on how to think about the solution]
- [Mention different possible approaches]
- [Include evaluation criteria]
"""
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

    # Main content area
    with st.container():
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
