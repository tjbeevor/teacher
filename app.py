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
        Create a comprehensive lesson about {self.current_topic}
        
        Format your response exactly following this template:
        
        [KEY CONCEPT]
        First, provide a clear, high-level overview (1-2 sentences).
        Then, break down 3-4 main aspects of the topic in detail.
        Include important principles, common use cases, and key points to remember.
        
        [EXAMPLES]
        Provide 3-4 practical examples, starting simple and increasing in complexity.
        Each example should:
        - Show the code
        - Explain what it does
        - Highlight key concepts being demonstrated
        Include any relevant output or results.
        
        [PRACTICE]
        Create a practice question that:
        - Tests understanding of multiple aspects covered
        - Requires practical application
        - Has a clear, specific goal
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
            # Provide rich default content
            return {
                'lesson': """In Python, data types and variables are fundamental building blocks of programming. A variable is a named container that stores data, while a data type defines what kind of data can be stored and what operations can be performed on it.

Key Aspects:

1. Variable Declaration and Assignment
   • Variables are created through assignment using the = operator
   • Names must start with a letter or underscore, followed by letters, numbers, or underscores
   • Python uses dynamic typing - type is determined automatically based on the assigned value
   • Variables are case-sensitive (age and Age are different variables)

2. Basic Data Types
   • Numeric Types:
     - int: Whole numbers (e.g., -1, 0, 42)
     - float: Decimal numbers (e.g., 3.14, -0.001)
     - complex: Complex numbers (e.g., 3+4j)
   • Text Type:
     - str: Strings of characters (e.g., "Hello", 'Python')
   • Boolean Type:
     - bool: True or False values
   • None Type:
     - None: Represents absence of value

3. Type Conversion
   • Implicit conversion: Python automatically converts compatible types
   • Explicit conversion: Using functions like int(), float(), str()
   • Type checking using type() function

4. Variable Scope
   • Local variables: Defined within functions
   • Global variables: Defined outside functions
   • Namespace considerations
""",
                'examples': """1. Basic Variable Assignment and Types
```python
# Simple variable assignments
age = 25                 # Integer
height = 1.75           # Float
name = "Alice"          # String
is_student = True       # Boolean
has_license = None      # None type

# Checking types
print(f"age is type: {type(age)}")        # <class 'int'>
print(f"height is type: {type(height)}")  # <class 'float'>
print(f"name is type: {type(name)}")      # <class 'str'>
```

2. Type Conversion and Operations
```python
# String to number conversion
price_str = "19.99"
price_float = float(price_str)    # Convert string to float
price_int = int(price_float)      # Convert float to int

print(f"String: {price_str}, Float: {price_float}, Int: {price_int}")
# Output: String: 19.99, Float: 19.99, Int: 19

# Numeric operations
total = price_int + 5
print(f"Total: {total}")  # Output: Total: 24
```

3. String Operations and Formatting
```python
# String concatenation and formatting
first_name = "John"
last_name = "Doe"
age = 30

# Using f-strings (recommended)
message = f"{first_name} {last_name} is {age} years old"

# Using .format() method
message2 = "{} {} is {} years old".format(first_name, last_name, age)

# Using + operator
message3 = first_name + " " + last_name + " is " + str(age) + " years old"

print(message)   # John Doe is 30 years old
```

4. Complex Variable Usage
```python
# Working with multiple types and conversions
items = ["apple", "banana", "orange"]  # List
prices = [0.50, 0.75, 0.60]           # List of floats
quantities = [3, 2, 4]                # List of integers

# Calculate total cost
total_cost = sum(price * qty for price, qty in zip(prices, quantities))

# Format as currency string
formatted_cost = f"${total_cost:.2f}"

print(f"Shopping Cart:")
for item, price, qty in zip(items, prices, quantities):
    print(f"  {item}: {qty} x ${price:.2f} = ${price * qty:.2f}")
print(f"Total: {formatted_cost}")

# Output:
# Shopping Cart:
#   apple: 3 x $0.50 = $1.50
#   banana: 2 x $0.75 = $1.50
#   orange: 4 x $0.60 = $2.40
# Total: $5.40
```
""",
                'question': """Create a program that does the following:

1. Create three variables:
   - A string containing your full name
   - A float containing your height in meters
   - An integer containing your age

2. Convert your height to feet (1 meter = 3.28084 feet) and round to 2 decimal places
3. Create an f-string that prints: "My name is [name], I am [age] years old and [height] feet tall."

Show your complete code with all variables and calculations."""
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

    elif st.session_state.teaching_state == 'teach_topic':
        with st.spinner("Preparing your lesson..."):
            content = st.session_state.tutor.teach_topic()
        
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
