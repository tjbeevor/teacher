import google.generativeai as genai
from typing import Dict, List, Optional
import streamlit as st
import time

class LessonGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.max_retries = 3
        self.retry_delay = 1

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
            time.sleep(self.retry_delay * (attempt + 1))
        return None

    def generate_curriculum(self, subject: str, level: str, topic: str, prerequisites: str) -> List[str]:
        """Generate a structured curriculum for the topic."""
        prompt = f"""Create exactly 5 sequential subtopics for teaching {topic} in {subject} at {level} level.

        Format your response EXACTLY like this example:
        1. Basic Foundations - Understanding core principles
        2. Key Components - Exploring main elements
        3. Practical Applications - Real-world usage
        4. Advanced Concepts - Deeper insights
        5. Integration & Synthesis - Bringing it all together

        Make sure each subtopic:
        - Builds progressively on previous knowledge
        - Is appropriate for {level} level
        - Relates specifically to {topic}
        - Has clear learning outcomes

        Background context: {prerequisites}"""

        try:
            response = self.generate_with_retry(prompt)
            if not response:
                return self.get_default_curriculum(topic)

            # Parse the response
            topics = []
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            for line in lines:
                if line[0].isdigit() and '. ' in line and ' - ' in line:
                    # Extract just the topic name before the dash
                    topic_name = line.split(' - ')[0].split('. ')[1].strip()
                    topics.append(topic_name)

            # Validate we got exactly 5 topics
            if len(topics) == 5:
                return topics
            else:
                return self.get_default_curriculum(topic)

        except Exception as e:
            st.error(f"Error in curriculum generation: {str(e)}")
            return self.get_default_curriculum(topic)

    def get_default_curriculum(self, topic: str) -> List[str]:
        """Provide default curriculum structure if generation fails."""
        return [
            f"Introduction to {topic}",
            f"Fundamental Concepts of {topic}",
            f"Practical Applications of {topic}",
            f"Advanced Topics in {topic}",
            f"Mastering {topic}"
        ]

    def format_curriculum(self, topics: List[str]) -> str:
        """Format the curriculum for display."""
        formatted_topics = []
        for i, topic in enumerate(topics, 1):
            formatted_topics.append(f"{i}. {topic}")
        return "\n".join(formatted_topics)
    
    def generate_lesson(self, topic: str, level: str) -> Dict[str, str]:
        prompt = f"""Create a detailed, engaging lesson about {topic} for {level} level students.
        
        Structure your response EXACTLY using these section headers, and make sure each section has substantial content:

        [OBJECTIVES]
        • Create 3 specific learning objectives using Bloom's Taxonomy verbs
        • Make them measurable and appropriate for {level} level
        • Focus on practical skills and understanding

        [INTRODUCTION]
        • Start with an engaging hook or real-world example
        • Explain why {topic} is important
        • Connect to previous knowledge
        • Set expectations for what will be learned

        [CORE CONCEPTS]
        1. Fundamental Concept:
           • Detailed explanation in simple terms
           • Key terminology defined
           • Basic examples
           • Common misconceptions addressed

        2. Main Principles:
           • In-depth explanation
           • Step-by-step breakdown
           • Visual or conceptual examples
           • Practical applications

        3. Advanced Ideas:
           • Higher-level concepts
           • Real-world applications
           • Best practices
           • Common pitfalls and solutions

        [EXAMPLES]
        Example 1 (Basic):
        • Provide a simple, clear example
        • Include step-by-step explanation
        • Show expected output or result
        • Explain why it works

        Example 2 (Advanced):
        • Show a more complex, real-world example
        • Break down the implementation
        • Discuss variations and alternatives
        • Include best practices

        [PRACTICE]
        • Create a challenging but appropriate question
        • Include specific requirements
        • Provide context or scenario
        • List key points to address in the answer

        Make all content clear, engaging, and specifically tailored for {level} level students learning {topic}."""

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_default_lesson(topic)

        try:
            sections = {}
            current_section = None
            current_content = []

            lines = response.split('\n')
            for line in lines:
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    if current_section and current_content:
                        sections[current_section.lower()] = '\n'.join(current_content)
                    current_section = line.strip()[1:-1]
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line.strip())

            if current_section and current_content:
                sections[current_section.lower()] = '\n'.join(current_content)

            # Add section headers and formatting
            formatted_sections = {
                'objectives': f"### Learning Objectives\n{sections.get('objectives', 'No objectives specified.')}",
                'introduction': f"### Overview\n{sections.get('introduction', 'No introduction available.')}",
                'core_concepts': f"### Core Concepts\n{sections.get('core concepts', 'No core concepts available.')}",
                'examples': f"### Examples\n{sections.get('examples', 'No examples available.')}",
                'practice': f"### Practice Question\n{sections.get('practice', 'No practice question available.')}"
            }

            return formatted_sections

        except Exception as e:
            print(f"Error in generate_lesson: {str(e)}")
            return self.get_default_lesson(topic)

    def get_default_lesson(self, topic: str) -> Dict[str, str]:
        return {
            'objectives': f"""### Learning Objectives
- Understand the fundamental principles of {topic}
- Apply basic {topic} concepts to solve simple problems
- Analyze and explain how {topic} works in practice""",
            
            'introduction': f"""### Overview
Welcome to {topic}! This fundamental concept is crucial for understanding how to build effective programs. 
We'll explore the basic principles, see how they work in practice, and learn to apply them in real-world scenarios.""",
            
            'core_concepts': f"""### Core Concepts
1. Basic Principles
   • Understanding the fundamentals
   • Key terminology and concepts
   • Basic usage patterns

2. Implementation Details
   • How to apply {topic}
   • Best practices and conventions
   • Common patterns and uses

3. Advanced Considerations
   • Performance implications
   • Error handling
   • Optimization strategies""",
            
            'examples': """### Examples
1. Basic Example
   • Simple implementation
   • Step-by-step explanation
   • Expected outcomes

2. Advanced Example
   • Real-world scenario
   • Complex implementation
   • Best practices demonstrated""",
            
            'practice': f"""### Practice Question
Create a solution that demonstrates your understanding of {topic}. 

Consider:
- Basic implementation
- Error handling
- Best practices
- Real-world applicability"""
        }
