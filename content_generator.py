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
        prompt = f"""Create a comprehensive lesson about {topic} for {level} level students.
        
        You must format your response with exactly these sections and markers:
    
        [OBJECTIVES]
        List exactly three learning objectives:
        • First objective using Bloom's taxonomy
        • Second objective using Bloom's taxonomy
        • Third objective using Bloom's taxonomy
    
        [INTRODUCTION]
        Write 2-3 paragraphs introducing {topic}, including:
        • Why it's important
        • Real-world applications
        • Connection to previous knowledge
    
        [CORE_CONCEPTS]
        1. First Main Concept
           • Detailed explanation
           • Key terms
           • Examples
           • Common mistakes
    
        2. Second Main Concept
           • Detailed explanation
           • Key terms
           • Examples
           • Common mistakes
    
        3. Third Main Concept
           • Detailed explanation
           • Key terms
           • Examples
           • Common mistakes
    
        [EXAMPLES]
        Basic Example:
        • Step-by-step walkthrough
        • Expected output
        • Why it works
    
        Advanced Example:
        • Real-world scenario
        • Complete implementation
        • Best practices
    
        [PRACTICE]
        Create a question that tests understanding of {topic}.
        • Specific requirements
        • Success criteria
        • Key points to address
        """
    
        try:
            response = self.generate_with_retry(prompt)
            if not response:
                return self.get_default_lesson(topic)
    
            # Debug print
            print(f"Raw API response: {response}")
    
            sections = {}
            current_section = None
            current_content = []
    
            for line in response.split('\n'):
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    if current_section and current_content:
                        content = '\n'.join(current_content)
                        sections[current_section.lower()] = content
                    current_section = line.strip()[1:-1]
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line.strip())
    
            if current_section and current_content:
                sections[current_section.lower()] = '\n'.join(current_content)
    
            # Debug print
            print(f"Parsed sections: {sections}")
    
            result = {
                'objectives': sections.get('objectives', 'No objectives specified.'),
                'introduction': sections.get('introduction', 'No introduction available.'),
                'core_concepts': sections.get('core_concepts', 'No core concepts available.'),
                'examples': sections.get('examples', 'No examples available.'),
                'practice': sections.get('practice', 'No practice question available.')
            }
    
            # Format each section with proper markdown
            formatted_result = {
                'objectives': f"## Learning Objectives\n{result['objectives']}",
                'introduction': f"## Introduction\n{result['introduction']}",
                'core_concepts': f"## Core Concepts\n{result['core_concepts']}",
                'examples': f"## Examples\n{result['examples']}",
                'practice': f"## Practice\n{result['practice']}"
            }
    
            # Debug print
            print(f"Formatted result: {formatted_result}")
    
            return formatted_result
    
        except Exception as e:
            print(f"Error in generate_lesson: {str(e)}")
            return self.get_default_lesson(topic)
