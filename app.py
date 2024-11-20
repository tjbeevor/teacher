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
        current_topic = self.current_topic
        
        prompt = f"""Create a comprehensive programming tutorial about {current_topic}. Format your response exactly as follows:
    
    [CONCEPT]
    # {current_topic}
    
    ## Introduction
    Write a thorough introduction explaining what {current_topic} is, why it's important, and how it fits into Python programming.
    
    ## Core Concepts
    Break down all the essential components of {current_topic}, explaining:
    - Each concept in detail
    - How they work
    - When to use them
    - Common pitfalls to avoid
    - Best practices
    
    ## Technical Details
    Provide in-depth technical information about:
    - Syntax rules and conventions
    - Implementation details
    - Performance considerations
    - Memory management (if applicable)
    - Common errors and how to avoid them
    
    ## Best Practices
    List and explain:
    - Recommended approaches
    - Code style guidelines
    - Optimization tips
    - Debugging strategies
    - Common mistakes to avoid
    
    [EXAMPLES]
    Provide multiple practical examples, starting with basic concepts and progressing to more complex implementations. Include:
    
    ## Basic Examples
    ```python
    # Include 2-3 basic examples with detailed explanations
    ```
    
    ## Intermediate Examples
    ```python
    # Include 2-3 intermediate examples showing more complex usage
    ```
    
    ## Advanced Examples
    ```python
    # Include 1-2 advanced examples demonstrating real-world applications
    ```
    
    For each example:
    1. Explain what the code does
    2. Break down key components
    3. Show expected output
    4. Discuss potential variations
    5. Highlight important concepts demonstrated
    
    [QUESTION]
    Create an engaging scenario-based question that:
    1. Tests understanding of multiple concepts covered
    2. Relates to real-world application
    3. Requires critical thinking
    4. Has multiple valid approaches
    5. Encourages discussion of trade-offs and best practices
    
    Present it in a conversational style, asking the student to explain their reasoning and approach."""
    
        try:
            response = self.api_client.generate_content(prompt)
            if not response:
                raise ValueError("No response generated")
    
            text = response.text
            sections = text.split('[')
            lesson = {}
    
            for section in sections:
                if section.startswith('CONCEPT]'):
                    lesson['lesson'] = section.split(']')[1].strip()
                elif section.startswith('EXAMPLES]'):
                    lesson['examples'] = section.split(']')[1].strip()
                elif section.startswith('QUESTION]'):
                    lesson['question'] = section.split(']')[1].strip()
    
            # Default content for Basic Syntax and Data Types
            if 'Basic Syntax' in current_topic or 'Data Types' in current_topic:
                default_lesson = """# Basic Syntax and Data Types in Python
    
    ## Introduction
    Python's syntax and data types form the foundation of the language. Understanding these fundamentals is crucial for writing effective, maintainable code. Python's design philosophy emphasizes readability and simplicity, making it an excellent language for beginners while remaining powerful for advanced applications.
    
    ## Core Concepts
    
    ### Python Syntax Basics
    * **Indentation**: Unlike other languages that use braces {}, Python uses indentation to define code blocks
    * **Line Structure**: Each statement typically occupies one line
    * **Comments**: Use '#' for single-line comments and ''' or \"\"\" for multi-line comments
    * **Case Sensitivity**: Python is case-sensitive ('name' and 'Name' are different variables)
    
    ### Fundamental Data Types
    1. **Numeric Types**
       * `int`: Whole numbers (e.g., -1, 0, 42)
       * `float`: Decimal numbers (e.g., 3.14, -0.001)
       * `complex`: Complex numbers (e.g., 3+4j)
    
    2. **Text Type**
       * `str`: Strings of characters
       * Immutable sequences of Unicode characters
       * Supports multiple operations like slicing and concatenation
    
    3. **Boolean Type**
       * `bool`: True or False values
       * Used in logical operations and control flow
    
    4. **Sequence Types**
       * `list`: Ordered, mutable sequences
       * `tuple`: Ordered, immutable sequences
       * `range`: Represents an immutable sequence of numbers
    
    5. **Mapping Type**
       * `dict`: Key-value pairs
       * Unordered collection of data
    
    6. **Set Types**
       * `set`: Unordered collection of unique elements
       * `frozenset`: Immutable version of set
    
    ## Technical Details
    * Variables are dynamically typed
    * Memory management is handled automatically
    * Type conversion functions: int(), float(), str(), etc.
    * Objects are reference counted for garbage collection
    * Everything in Python is an object
    
    ## Best Practices
    1. Use meaningful variable names
    2. Follow PEP 8 style guidelines
    3. Initialize variables before use
    4. Use type hints for better code documentation
    5. Consider memory usage for large programs"""
    
                default_examples = """## Basic Examples
    ```python
    # 1. Variable Assignment and Basic Types
    name = "Alice"          # String
    age = 25               # Integer
    height = 1.75          # Float
    is_student = True      # Boolean
    
    print(f"Name: {name}, Type: {type(name)}")
    print(f"Age: {age}, Type: {type(age)}")
    print(f"Height: {height}, Type: {type(height)}")
    print(f"Is Student: {is_student}, Type: {type(is_student)}")
    ```
    
    ## Intermediate Examples
    ```python
    # 2. Working with Multiple Types
    # List of student records
    students = [
        {"name": "Bob", "age": 20, "grades": [85, 90, 88]},
        {"name": "Carol", "age": 22, "grades": [92, 95, 89]}
    ]
    
    # Calculate average grade for each student
    for student in students:
        average = sum(student["grades"]) / len(student["grades"])
        print(f"{student['name']}'s average grade: {average:.2f}")
    ```
    
    ## Advanced Examples
    ```python
    # 3. Complex Data Manipulation
    from decimal import Decimal
    from typing import Dict, List, Union
    
    def process_transaction(
        transaction: Dict[str, Union[str, Decimal, List[Dict]]]
    ) -> Dict[str, Union[Decimal, str]]:
        \"\"\"Process a financial transaction with precise decimal calculations.\"\"\"
        
        # Initialize transaction details
        items = transaction['items']
        tax_rate = Decimal('0.08')
        
        # Calculate subtotal with precise decimal arithmetic
        subtotal = sum(Decimal(item['price']) * item['quantity'] 
                      for item in items)
        
        # Calculate tax and total
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        return {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'tax': tax.quantize(Decimal('0.01')),
            'total': total.quantize(Decimal('0.01')),
            'status': 'processed'
        }
    
    # Example usage
    transaction = {
        'items': [
            {'name': 'Widget', 'price': '19.99', 'quantity': 2},
            {'name': 'Gadget', 'price': '9.99', 'quantity': 3}
        ]
    }
    
    result = process_transaction(transaction)
    for key, value in result.items():
        print(f"{key}: {value}")
    ```"""
    
                default_question = """Let's tackle a real-world programming challenge!
    
    Imagine you're building an e-commerce system that needs to handle various types of product data:
    
    1. Product information (name, description, category)
    2. Pricing (regular price, discount price, bulk prices)
    3. Inventory tracking (current stock, minimum stock level)
    4. Customer reviews (rating, comment, date)
    
    Questions to consider:
    1. What data types would you choose for each piece of information and why?
    2. How would you structure this data to make it efficient and maintainable?
    3. What potential issues might you encounter with different data types?
    4. How would you handle currency calculations to ensure accuracy?
    
    Share your thoughts on how you would approach this design, considering both functionality and performance implications."""
    
                return {
                    'lesson': default_lesson,
                    'examples': default_examples,
                    'question': default_question
                }
    
            if all(key in lesson for key in ['lesson', 'examples', 'question']):
                return lesson
    
            raise ValueError("Missing sections in generated content")
    
        except Exception as e:
            st.error(f"Error generating lesson: {str(e)}")
            return None

    def _generate_introduction(self, topic):
        """Generate a topic-specific introduction."""
        # Example mapping of topics to introductions
        intro_templates = {
            'data types': """Python's data types are fundamental building blocks that determine how data is stored and manipulated. Understanding these types is crucial for writing efficient and error-free code.""",
            'functions': """Functions are reusable blocks of code that help organize and modularize programs. They are essential for writing maintainable and scalable Python applications.""",
            'loops': """Loops are control structures that allow repetitive execution of code blocks. They are fundamental for automating repetitive tasks and processing collections of data.""",
            # Add more mappings as needed
        }
        
        # Default introduction if no specific match
        default_intro = f"""Understanding {topic} is a crucial part of mastering Python programming. This concept provides essential functionality that you'll use in virtually every Python program you write."""
        
        # Search for keywords in the topic and return appropriate introduction
        for key, intro in intro_templates.items():
            if key in topic.lower():
                return intro
        return default_intro

    def _generate_core_concepts(self, topic):
        """Generate topic-specific core concepts."""
        concepts = []
        topic_lower = topic.lower()
        
        if 'data' in topic_lower and 'type' in topic_lower:
            concepts = [
                "### Numeric Types",
                "* Integers (int)",
                "* Floating-point numbers (float)",
                "* Complex numbers",
                "\n### Text Type",
                "* Strings (str)",
                "\n### Boolean Type",
                "* True/False values",
                "\n### Sequence Types",
                "* Lists",
                "* Tuples",
                "* Range objects"
            ]
        elif 'function' in topic_lower:
            concepts = [
                "### Function Definition",
                "* Function syntax",
                "* Parameters and arguments",
                "* Return values",
                "\n### Function Types",
                "* Built-in functions",
                "* User-defined functions",
                "* Lambda functions",
                "\n### Function Scope",
                "* Local variables",
                "* Global variables",
                "* Nonlocal variables"
            ]
        # Add more topic-specific concepts
        
        return "\n".join(concepts) if concepts else f"### Understanding {topic}\n* Core principles\n* Key components\n* Common use cases"

    def _generate_examples(self, topic):
        """Generate topic-specific examples."""
        topic_lower = topic.lower()
        
        # Base structure for examples
        example_structure = """## Example 1: Basic Usage
```python
{basic_example}
```

## Example 2: Intermediate Implementation
```python
{intermediate_example}
```

## Example 3: Advanced Application
```python
{advanced_example}
```"""
        
        # Topic-specific examples
        if 'data' in topic_lower and 'type' in topic_lower:
            return example_structure.format(
                basic_example="""# Basic data types
x = 42              # Integer
y = 3.14           # Float
name = "Python"     # String
is_valid = True    # Boolean

print(type(x), x)
print(type(y), y)
print(type(name), name)
print(type(is_valid), is_valid)""",
                
                intermediate_example="""# Type conversion
price = "19.99"
quantity = 3

# Convert string to float and calculate total
total = float(price) * quantity

print(f"Total cost: ${total:.2f}")""",
                
                advanced_example="""# Complex data type operations
from decimal import Decimal

# Using Decimal for precise financial calculations
prices = ['19.99', '9.99', '29.99']
quantities = [2, 3, 1]

# Calculate total with precision
total = sum(Decimal(price) * qty 
           for price, qty in zip(prices, quantities))

print(f"Total: ${total:.2f}")"""
            )
        # Add more topic-specific examples
        
        return example_structure.format(
            basic_example=f"# Basic {topic} example\n# Code here",
            intermediate_example=f"# Intermediate {topic} example\n# Code here",
            advanced_example=f"# Advanced {topic} example\n# Code here"
        )

    def _generate_practice_question(self, topic):
        """Generate a topic-specific practice question."""
        topic_lower = topic.lower()
        
        if 'data' in topic_lower and 'type' in topic_lower:
            return """Let's solve a real-world problem!

You're building a financial application that needs to handle various types of data:
- Customer names and IDs
- Account balances
- Transaction dates
- Interest rates

How would you:
1. Choose appropriate data types for each piece of information?
2. Handle currency calculations to ensure precision?
3. Convert between different data types as needed?
4. Validate input data to prevent errors?

Share your approach to handling these requirements while ensuring data accuracy and program efficiency."""
        
        # Default question format
        return f"""Let's apply what we've learned about {topic}!

Consider a real-world scenario where you need to implement this concept:
1. What key considerations would you keep in mind?
2. How would you handle edge cases?
3. How would you optimize for performance?
4. What best practices would you follow?

Share your thoughts on how you would approach this challenge."""

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
            ["Python Programming", "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
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

    if st.session_state.teaching_state == 'initialize':
        if topic and st.button("Start Learning"):
            with st.spinner("Preparing your learning path..."):
                response = st.session_state.tutor.initialize_session(
                    subject, level, prerequisites, topic
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.teaching_state = 'teach_topic'
                st.rerun()

    elif st.session_state.teaching_state == 'teach_topic':
        try:
            with st.spinner("Preparing your lesson..."):
                content = st.session_state.tutor.teach_topic()
                if not content:
                    raise ValueError("Failed to generate lesson content")
                
                message = f"""# {st.session_state.tutor.current_topic}

## 🔑 Key Concepts
{content['lesson']}

## 📝 Examples
{content['examples']}

## ❓ Practice Question
{content['question']}
"""
                st.session_state.messages.append({"role": "assistant", "content": message})
                st.session_state.last_question = content['question']
                st.session_state.teaching_state = 'wait_for_answer'
                st.rerun()

        except Exception as e:
            st.error(f"An error occurred while preparing the lesson: {str(e)}")
            # Reset to initial state if there's an error
            st.session_state.teaching_state = 'initialize'
            st.rerun()

    elif st.session_state.teaching_state == 'wait_for_answer':
        if prompt := st.chat_input("Share your thoughts..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Analyzing your response..."):
                evaluation = st.session_state.tutor.evaluate_answer(
                    st.session_state.last_question, prompt
                )
                
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

    elif st.session_state.teaching_state == 'finished':
        st.success("🎉 Congratulations! You've completed all topics!")
        if st.button("Start New Topic"):
            st.session_state.teaching_state = 'initialize'
            st.session_state.messages = []
            st.rerun()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'teaching_state' not in st.session_state:
    st.session_state.teaching_state = 'initialize'
if 'tutor' not in st.session_state:
    st.session_state.tutor = AITutor()
if 'last_question' not in st.session_state:
    st.session_state.last_question = None






if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
