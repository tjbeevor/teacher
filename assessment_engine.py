import google.generativeai as genai
from typing import Dict, Any, Optional
import streamlit as st
import time

class AssessmentEngine:
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

    def generate_question(self, topic: str, level: str, question_type: str) -> str:
        """Generate a question based on the topic and difficulty level."""
        prompt = f"""Create a thought-provoking {question_type} question about {topic} appropriate for {level} level students.

The question should:
1. Test deep understanding rather than memorization
2. Connect to real-world applications
3. Require critical thinking
4. Allow for multiple valid approaches
5. Build on fundamental concepts

Format as:
[SCENARIO]
A brief, engaging real-world scenario

[QUESTION]
The specific question to answer

[POINTS TO CONSIDER]
• Key point 1 to address
• Key point 2 to address
• Key point 3 to address

Make the scenario engaging and relevant while ensuring it tests true understanding of {topic}."""

        response = self.generate_with_retry(prompt)
        return response if response else f"Explain a key concept of {topic} and provide an example."

    def evaluate_response(self, question: str, answer: str, topic: str, level: str) -> Dict[str, Any]:
        """Evaluate student response with detailed feedback."""
        prompt = f"""Evaluate this {level}-level response about {topic}.

Question: {question}
Student's Answer: {answer}

Provide a detailed evaluation following this structure:

[CONCEPTUAL UNDERSTANDING]
• List specific concepts the student understood correctly
• Identify any misunderstandings or gaps
• Note any innovative thinking or unique insights
• Evaluate the depth of understanding shown

[CRITICAL THINKING]
• Assess the logical flow of ideas
• Evaluate the use of evidence/examples
• Note any connections made to other concepts
• Comment on the sophistication of analysis

[SPECIFIC FEEDBACK]
• Point out strong aspects of the response
• Identify areas needing improvement
• Suggest specific ways to strengthen the answer
• Provide concrete examples for improvement

[GROWTH AREAS]
• Recommend specific topics to review
• Suggest additional practice areas
• Provide resources for further learning
• Identify skills to develop

[FOLLOW-UP]
• Create a specific follow-up question that:
  - Builds on demonstrated knowledge
  - Addresses identified gaps
  - Pushes thinking to next level
  - Connects to wider concepts

[MASTERY]
Rate each area 1-5 (5 being highest):
• Conceptual Understanding: [1-5]
• Application of Knowledge: [1-5]
• Critical Thinking: [1-5]
• Communication: [1-5]

[MOVE ON]
yes/no (Based on overall understanding)"""

        response = self.generate_with_retry(prompt)
        if not response:
            return self.get_fallback_evaluation()

        try:
            evaluation = self.parse_evaluation(response)
            return self.format_evaluation(evaluation)
        except Exception as e:
            st.error(f"Error parsing evaluation: {str(e)}")
            return self.get_fallback_evaluation()

    def parse_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse the evaluation response into structured feedback."""
        sections = response.split('[')
        evaluation = {}
        
        for section in sections:
            if ':' not in section:
                continue
                
            title = section.split(']')[0].lower()
            content = section.split(']')[1].strip()
            
            if title == 'mastery':
                scores = {}
                for line in content.split('\n'):
                    if ':' in line:
                        category, score = line.split(':')
                        try:
                            scores[category.strip()] = int(score.strip())
                        except ValueError:
                            scores[category.strip()] = 3
                evaluation['mastery'] = scores
            elif title == 'move on':
                evaluation['move_on'] = 'yes' in content.lower()
            else:
                evaluation[title] = content

        return evaluation

    def format_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Format the evaluation into user-friendly feedback."""
        mastery = evaluation.get('mastery', {})
        average_score = sum(mastery.values()) / len(mastery) if mastery else 3
        
        evaluation_level = 'correct' if average_score >= 4 else 'partial' if average_score >= 3 else 'incorrect'
        
        return {
            'evaluation': evaluation_level,
            'understanding': evaluation.get('conceptual understanding', ''),
            'feedback': evaluation.get('specific feedback', ''),
            'improvement': evaluation.get('growth areas', ''),
            'challenge': evaluation.get('follow-up', ''),
            'move_on': evaluation.get('move_on', False)
        }

    def get_fallback_evaluation(self) -> Dict[str, Any]:
        """Provide fallback evaluation when API fails."""
        return {
            'evaluation': 'partial',
            'understanding': 'Your answer shows some understanding of the concepts.',
            'feedback': 'Consider providing more specific examples and explaining your reasoning.',
            'improvement': 'Review the core concepts and try to connect them to real-world applications.',
            'challenge': 'Can you expand on your answer and provide a concrete example?',
            'move_on': False
        }

    def generate_adaptive_question(self, topic: str, previous_performance: float) -> str:
        """Generate a question adapted to the student's performance level."""
        difficulty = "challenging" if previous_performance > 0.8 else \
                    "moderate" if previous_performance > 0.5 else \
                    "foundational"
        
        return self.generate_question(
            topic,
            difficulty,
            "application" if previous_performance > 0.7 else "conceptual"
        )
