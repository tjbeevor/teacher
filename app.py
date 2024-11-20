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
        Create a comprehensive, university-level lesson about {self.current_topic}
        
        Follow this detailed template:
        
        [KEY CONCEPT]
        1. Start with a clear, engaging introduction that explains the concept's importance in programming
        2. Provide detailed explanations of all key components and their relationships
        3. Include real-world applications and use cases
        4. Explain advantages, limitations, and best practices
        5. Compare with related concepts and alternatives
        6. Include important implementation considerations
        Break this into clearly formatted sections with bullet points and subsections.
        
        [EXAMPLES]
        Provide 4-5 detailed, real-world examples that:
        1. Start with simple cases and progress to complex scenarios
        2. Show practical implementations
        3. Include code samples with detailed explanations
        4. Demonstrate common patterns and best practices
        5. Include expected output and behavior
        6. Point out potential pitfalls and how to avoid them
        
        [PRACTICE]
        Create an engaging discussion question that:
        1. Tests deep understanding of the concepts
        2. Requires analytical thinking
        3. Relates to real-world scenarios
        4. Has multiple valid approaches to discuss
        5. Encourages creative problem-solving
        """
        try:
            response = self.api_client.generate_content(prompt)
            if not response:
                raise ValueError("No response generated")
            
            # Provide rich default content for Advanced Data Structures
            return {
                'lesson': """# Understanding Advanced Data Structures in Python

## Introduction
Advanced data structures are fundamental building blocks that enable efficient data organization and manipulation in complex programs. They provide specialized ways to store and access data, each optimized for specific use cases.

## Key Concepts

### 1. Lists and Array-Based Structures
* **Dynamic Arrays (Lists)**
  - Automatic resizing and memory management
  - O(1) access time for individual elements
  - Contiguous memory allocation for efficient iteration
  - Best for: Sequential access, random access, and frequent modifications
  
* **Tuples**
  - Immutable sequences
  - Memory efficient
  - Useful for data integrity and as dictionary keys
  - Performance benefits in certain operations

### 2. Dictionary-Based Structures
* **Hash Tables (Dictionaries)**
  - Key-value pair storage
  - O(1) average case for insertions and lookups
  - Hash function implementation
  - Collision resolution strategies
  
* **Sets**
  - Unique elements only
  - Optimized for membership testing
  - Mathematical set operations
  - Hash table implementation internally

### 3. Queue-Based Structures
* **FIFO Queues**
  - First-In-First-Out principle
  - Implementation using collections.deque
  - Thread-safe alternatives
  - Common use cases in task scheduling
  
* **Priority Queues**
  - Heap implementation
  - O(log n) insertion and deletion
  - Applications in scheduling and optimization
  - Custom priority definitions

### 4. Stack-Based Structures
* **LIFO Stacks**
  - Last-In-First-Out principle
  - Implementation options
  - Memory management considerations
  - Applications in program flow control

### 5. Advanced Implementations
* **Linked Lists**
  - Singly and doubly linked
  - Dynamic memory allocation
  - Insertion and deletion efficiency
  - Use cases and limitations
  
* **Trees and Graphs**
  - Hierarchical data representation
  - Traversal algorithms
  - Balancing techniques
  - Real-world applications

## Best Practices
1. Choose structures based on:
   - Access patterns
   - Memory constraints
   - Performance requirements
   - Thread safety needs
   
2. Consider:
   - Space-time tradeoffs
   - Implementation complexity
   - Maintenance overhead
   - Team familiarity""",

            'examples': """# Practical Implementations

## 1. Basic Queue Implementation
```python
from collections import deque

class CustomerServiceQueue:
    def __init__(self):
        self.queue = deque()
        
    def add_customer(self, customer_id):
        self.queue.append(customer_id)
        return f"Customer {customer_id} added to queue. Position: {len(self.queue)}"
        
    def serve_next_customer(self):
        if self.queue:
            return f"Now serving customer {self.queue.popleft()}"
        return "Queue is empty"
        
    def queue_size(self):
        return len(self.queue)

# Usage Example
service_queue = CustomerServiceQueue()
print(service_queue.add_customer("A123"))  # Customer A123 added to queue. Position: 1
print(service_queue.add_customer("B456"))  # Customer B456 added to queue. Position: 2
print(service_queue.serve_next_customer()) # Now serving customer A123
```

## 2. Priority Queue for Task Scheduling
```python
import heapq

class TaskScheduler:
    def __init__(self):
        self.tasks = []  # List of (priority, task_name) tuples
        
    def add_task(self, task_name, priority):
        heapq.heappush(self.tasks, (priority, task_name))
        
    def get_next_task(self):
        if self.tasks:
            priority, task = heapq.heappop(self.tasks)
            return f"Running {task} (priority: {priority})"
        return "No tasks remaining"

# Usage Example
scheduler = TaskScheduler()
scheduler.add_task("Emergency backup", 1)
scheduler.add_task("Regular backup", 3)
scheduler.add_task("Critical update", 2)

print(scheduler.get_next_task())  # Running Emergency backup (priority: 1)
print(scheduler.get_next_task())  # Running Critical update (priority: 2)
```

## 3. Custom Dictionary with History
```python
class HistoryDict:
    def __init__(self):
        self.data = {}
        self.history = []
        
    def __setitem__(self, key, value):
        self.history.append((key, self.data.get(key)))
        self.data[key] = value
        
    def __getitem__(self, key):
        return self.data[key]
        
    def undo(self):
        if self.history:
            key, old_value = self.history.pop()
            if old_value is None:
                del self.data[key]
            else:
                self.data[key] = old_value

# Usage Example
hd = HistoryDict()
hd["name"] = "Alice"
hd["name"] = "Bob"
print(hd["name"])  # Bob
hd.undo()
print(hd["name"])  # Alice
```

## 4. Advanced Graph Implementation
```python
from collections import defaultdict

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)
        
    def add_edge(self, start, end):
        self.graph[start].append(end)
        
    def find_path(self, start, end, path=None):
        if path is None:
            path = []
        path = path + [start]
        
        if start == end:
            return path
            
        for vertex in self.graph[start]:
            if vertex not in path:
                new_path = self.find_path(vertex, end, path)
                if new_path:
                    return new_path
        return None

# Usage Example
g = Graph()
g.add_edge("A", "B")
g.add_edge("B", "C")
g.add_edge("C", "D")
print(g.find_path("A", "D"))  # ['A', 'B', 'C', 'D']
```""",

            'question': """Let's dive into a real-world scenario:

Imagine you're designing a system for a busy hospital's Emergency Room. The ER needs to manage patients based on both their arrival time AND the severity of their condition. Some patients need immediate attention, while others can wait.

Questions to consider:
1. Which data structure(s) would you choose to implement this system and why?
2. How would you handle new arrivals vs. updating the condition of existing patients?
3. What would happen if multiple doctors need to access and update the system simultaneously?

Share your thoughts on how you would approach this challenge, considering factors like efficiency, fairness, and practical implementation."""
        }
            
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

    # Main content area
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Initial state - Topic selection
    if st.session_state.teaching_state == 'initialize':
        if topic and st.button("Start Learning"):
            with st.spinner("Preparing your learning path..."):
                response = st.session_state.tutor.initialize_session(
                    subject, level, prerequisites, topic
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.teaching_state = 'teach_topic'
                st.rerun()

    # Teaching state - Present lesson
    elif st.session_state.teaching_state == 'teach_topic':
        try:
            with st.spinner("Preparing your lesson..."):
                content = st.session_state.tutor.teach_topic()
                if content and all(key in content for key in ['lesson', 'examples', 'question']):
                    message = f"""# {st.session_state.tutor.current_topic}

## 🔑 Let's Understand This!
{content['lesson']}

## 📝 See It In Action
{content['examples']}

## ❓ Let's Chat About This
{content['question']}
"""
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.session_state.last_question = content['question']
                    st.session_state.teaching_state = 'wait_for_answer'
                    st.rerun()
                else:
                    st.error("I couldn't generate the lesson properly. Let's try again!")
                    st.session_state.teaching_state = 'initialize'
                    st.rerun()
        except Exception as e:
            st.error(f"An error occurred while preparing the lesson: {str(e)}")
            st.session_state.teaching_state = 'initialize'
            st.rerun()

    # Waiting for answer state
    elif st.session_state.teaching_state == 'wait_for_answer':
        if prompt := st.chat_input("Share your thoughts..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Thinking about your response..."):
                evaluation = st.session_state.tutor.evaluate_answer(
                    st.session_state.last_question, prompt
                )
                
                # Format feedback with appropriate emoji
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

    # Finished state
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
