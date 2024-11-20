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
    
    def generate_lesson_content(self, topic: str, all_topics: List[str], current_index: int) -> Optional[Dict[str, str]]:
        """Generate comprehensive lesson content."""
        prompt = f"""Create an engaging lesson about {topic} (Topic {current_index + 1} of {len(all_topics)}).

[LEARNING OBJECTIVES]
Start with 3-4 clear, measurable learning objectives using Bloom's Taxonomy verbs (explain, analyze, evaluate, etc.).
Format as bullet points.

[HOOK]
Create an engaging hook that:
• Poses an intriguing question or scenario
• Connects to real-world experiences
• Sparks curiosity about {topic}

[CORE CONCEPTS]
Break down {topic} into 3 main ideas:
1. [Foundation Concept]
   • Clear explanation using analogies
   • Common examples
   • Key terminology explained simply
   
2. [Main Principle]
   • Detailed explanation with visuals
   • Step-by-step breakdown
   • Connections to previous knowledge
   
3. [Advanced Application]
   • Complex examples
   • Real-world applications
   • Common challenges and solutions

[MISCONCEPTIONS]
List 2-3 common misconceptions about {topic}:
• State the misconception
• Explain why it's incorrect
• Provide the correct understanding

[INTERACTIVE ELEMENTS]
Create 3 engaging activities:
1. "Think About It" question for individual reflection
2. Real-world scenario for analysis
3. "What if" scenario for deeper thinking

[REAL-WORLD APPLICATIONS]
Provide compelling examples of {topic} in:
• Current technology or research
• Industry applications
• Everyday life

[PRACTICE QUESTION]
Create a thought-provoking question that:
• Requires understanding of multiple concepts
• Connects to real-world scenarios
• Prompts critical thinking
• Has multiple valid approaches

Format all content in clear, engaging language appropriate for {current_index + 1}/{len(all_topics)} progression.
"""

        response = self.generate_with_retry(prompt)
        if not response:
            return None

        try:
            sections = response.split('[')
            content = {}
            
            current_section = None
            section_content = []
            
            for line in response.split('\n'):
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    if current_section and section_content:
                        content[current_section.lower()] = '\n'.join(section_content)
                        section_content = []
                    current_section = line.strip()[1:-1]
                elif line.strip() and current_section:
                    section_content.append(line.strip())
            
            if current_section and section_content:
                content[current_section.lower()] = '\n'.join(section_content)

            # Format the content into a lesson structure
            lesson = f"""## Learning Objectives
{content.get('learning objectives', 'Learning objectives not available.')}

## Introduction
{content.get('hook', 'Hook not available.')}

## Core Concepts
{content.get('core concepts', 'Core concepts not available.')}

## Common Misconceptions
{content.get('misconceptions', 'Misconceptions not available.')}"""

            return {
                'lesson': lesson,
                'interactive': content.get('interactive elements', 'Interactive elements not available.'),
                'applications': content.get('real-world applications', 'Applications not available.'),
                'question': content.get('practice question', 'Practice question not available.')
            }

        except Exception as e:
            st.error(f"Error parsing lesson content: {str(e)}")
            return None

    def get_fallback_content(self, topic: str) -> Dict[str, str]:
        """Provide fallback content when API fails."""
        return {
            'lesson': f"""## Learning Objectives
• Understand the basic principles of {topic}
• Identify key components and relationships
• Apply concepts to simple scenarios

## Introduction
Let's explore {topic} and its importance in our world.

## Core Concepts
1. Basic Principles
2. Key Components
3. Fundamental Relationships

## Common Misconceptions
• Common misunderstanding #1
• Common misunderstanding #2""",
            'interactive': "Let's think about how this applies to everyday life...",
            'applications': f"Here are some ways {topic} is used in the real world...",
            'question': f"Explain how {topic} works and why it's important."
        }
