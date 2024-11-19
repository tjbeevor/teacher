import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Enhanced page configuration
st.set_page_config(
    page_title="AI Tutor | Interactive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
    <style>
        /* Main page styling */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Header styling */
        .main-header {
            font-family: 'Helvetica Neue', sans-serif;
            color: #1E3A8A;
            padding: 1rem 0;
            text-align: center;
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f1f5f9;
            padding: 2rem 1rem;
            border-right: 1px solid #e2e8f0;
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            background-color: #1E3A8A;
            color: white;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #2563EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Chat container styling */
        .chat-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        
        /* Message styling */
        .stChat {
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Input box styling */
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        
        /* Progress section styling */
        .progress-section {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Quiz styling */
        .quiz-container {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Success message styling */
        .success-message {
            padding: 1rem;
            border-radius: 8px;
            background-color: #dcfce7;
            color: #166534;
            margin: 1rem 0;
        }
        
        /* Error message styling */
        .error-message {
            padding: 1rem;
            border-radius: 8px;
            background-color: #fee2e2;
            color: #991b1b;
            margin: 1rem 0;
        }
        
        /* Selectbox styling */
        .stSelectbox {
            margin-bottom: 1rem;
        }
        
        /* Radio button styling */
        .stRadio > label {
            background-color: #f8fafc;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Apply custom header
st.markdown("""
    <div class="main-header">
        <h1>🎓 Interactive AI Tutor</h1>
        <p style='color: #475569; font-size: 1.1em;'>Personalized Learning Experience</p>
    </div>
""", unsafe_allow_html=True)

[previous class definitions remain the same...]

def main():
    # Check API key first
    if not check_api_key():
        st.stop()
    
    # Initialize session states
    if 'tutor' not in st.session_state:
        try:
            st.session_state.tutor = AITutor()
        except Exception as e:
            st.error(f"Failed to initialize tutor: {str(e)}")
            st.stop()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding-bottom: 1rem;'>
                <h3 style='color: #1E3A8A;'>Session Configuration</h3>
            </div>
        """, unsafe_allow_html=True)
        
        user_name = st.text_input("👤 Your Name", key="user_name")
        
        subjects = [
            "Python Programming",
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "History",
            "Literature",
            "Economics"
        ]
        subject = st.selectbox("📚 Select Subject", subjects)
        
        levels = ["Beginner", "Intermediate", "Advanced"]
        level = st.selectbox("📊 Select Level", levels)
        
        topic = st.text_input("🎯 Specific Topic")
        
        prerequisites = st.text_area("🔍 Your Background/Prerequisites")
        
        st.markdown("---")
        
        if st.button("🚀 Start New Session"):
            if not topic or not prerequisites:
                st.error("⚠️ Please fill in both Topic and Prerequisites")
            else:
                with st.spinner("🔄 Initializing your personalized session..."):
                    response = st.session_state.tutor.initialize_session(
                        subject, level, prerequisites, topic
                    )
                    st.session_state.messages = []
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.quiz_active = False
                st.success("✨ Session started successfully!")
    
    # Main content area with enhanced styling
    chat_col, viz_col = st.columns([2, 1])
    
    with chat_col:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>💬 Learning Conversation</h3>
            </div>
        """, unsafe_allow_html=True)
        
        message_container = st.container()
        
        with message_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        if prompt := st.chat_input("💭 Type your response here..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.tutor.send_message(prompt)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    with viz_col:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                <h3 style='color: #1E3A8A; margin-bottom: 1rem;'>📈 Learning Progress</h3>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📝 Take Quiz"):
            if not topic:
                st.error("⚠️ Please start a session first")
            else:
                st.session_state.quiz_active = True
                with st.spinner("⚙️ Generating quiz..."):
                    quiz_data = st.session_state.tutor.quiz_generator.generate_quiz(
                        subject,
                        topic,
                        level
                    )
                if quiz_data:
                    st.session_state.current_quiz = quiz_data
                    st.session_state.quiz_score = 0
                    st.session_state.current_question = 0
        
        if st.session_state.quiz_active and hasattr(st.session_state, 'current_quiz'):
            st.markdown("""
                <div class='quiz-container'>
                    <h4 style='color: #1E3A8A;'>Quiz Progress</h4>
                </div>
            """, unsafe_allow_html=True)
            
            question = st.session_state.current_quiz['questions'][st.session_state.current_question]
            
            st.subheader(f"Question {st.session_state.current_question + 1}")
            st.write(question['question'])
            
            answer = st.radio("Select your answer:", question['options'], key=f"q_{st.session_state.current_question}")
            
            if st.button("Submit Answer"):
                if answer == question['correct_answer']:
                    st.session_state.quiz_score += 1
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. {question['explanation']}")
                
                if st.session_state.current_question < len(st.session_state.current_quiz['questions']) - 1:
                    st.session_state.current_question += 1
                else:
                    final_score = (st.session_state.quiz_score / len(st.session_state.current_quiz['questions'])) * 100
                    st.session_state.tutor.progress_tracker.save_progress(
                        user_name,
                        subject,
                        topic,
                        final_score
                    )
                    st.session_state.quiz_active = False
                    st.success(f"🎉 Quiz completed! Score: {final_score}%")
        
        # Enhanced progress visualization
        progress_data = st.session_state.tutor.progress_tracker.load_history()
        if progress_data:
            st.markdown("""
                <div style='margin-top: 2rem;'>
                    <h4 style='color: #1E3A8A;'>Learning Journey</h4>
                </div>
            """, unsafe_allow_html=True)
            
            df = pd.DataFrame(progress_data)
            fig = px.line(df, x='timestamp', y='score', color='subject',
                         title='Performance Over Time',
                         template='seaborn')
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font={'color': '#1E3A8A'},
                title={'font': {'size': 20}},
                xaxis={'gridcolor': '#E2E8F0'},
                yaxis={'gridcolor': '#E2E8F0'}
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
