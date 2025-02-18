import streamlit as st
import requests
import pandas as pd
import datetime
import time
import os
from PIL import Image
import base64
import pymongo
from dotenv import load_dotenv
from functools import lru_cache
import random

# API URL
API_URL = "https://Yuki-Chen-emochatbot.hf.space/dialogflow"

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "lumi_chatbot"
COLLECTION_NAME = "chat_history"

# MongoDB connection
try:
    if MONGO_URI is not None:
        client = pymongo.MongoClient(MONGO_URI, maxPoolSize=50)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
    else:
        client = None
        db = None
        collection = None
except Exception as e:
    st.error(f"MongoDB connection error: {str(e)}")
    client = None
    db = None
    collection = None

# Streamlit UI Configuration
st.set_page_config(
    page_title="Lumi - I'm here for you", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Optimize image loading with caching
@lru_cache(maxsize=1)
def get_image_base64(image_path):
    if os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# Cache the CSS to avoid recomputation
@lru_cache(maxsize=1)
def get_custom_css():
    return """
        <style>
            .main {
                background-color: #f5f8fa;
            }
            .chat-title {
                text-align: center;
                padding-bottom: 10px;
            }
            .chat-container {
                max-width: 600px;
                margin: auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 5px;
                margin-bottom: 50px;
            }
            .message-row {
                display: flex;
                margin: 10px 0;
                clear: both;
            }
            .user-row {
                justify-content: flex-end;
            }
            .lumi-row {
                justify-content: flex-start;
            }
            .avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background-color: #ccc;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 8px;
                margin-top: 6px;
            }
            .user-avatar {
                background-color: #dcf8c6;
                margin-left: 8px;
                margin-right: 0;
            }
            .message-content {
                max-width: calc(75% - 40px);
            }
            .user-bubble {
                background-color: #dcf8c6;
                padding: 12px 16px;
                border-radius: 18px 18px 0 18px;
                display: inline-block;
                word-wrap: break-word;
            }
            .lumi-bubble {
                background-color: #f5f5f5;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 0;
                display: inline-block;
                border: 1px solid #e6e6e6;
                word-wrap: break-word;
            }
            .chat-input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background-color: white;
                padding: 15px;
                border-top: 1px solid #e6e6e6;
                z-index: 1000;
            }
            .stTextInput > div > div > input {
                border-radius: 20px;
                padding-left: 15px;
            }
            .timestamp {
                font-size: 0.7em;
                color: #888888;
                margin-top: 4px;
            }
            .user-timestamp {
                text-align: right;
            }
            .lumi-timestamp {
                text-align: left;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .avatar-img {
                width: 100%;
                height: 100%;
                border-radius: 50%;
                object-fit: cover;
            }
            .user-initial {
                color: #fff;
                font-weight: bold;
            }
        </style>
    """

# Check if logo exists
logo_path = "Lumi.webp"
logo_exists = os.path.isfile(logo_path)

# Apply cached CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
    
# Optimize database operations with error handling
def save_message_to_mongo(role, text):
    if collection is not None:  # Changed from 'if collection:'
        try:
            message = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "role": role,
                "text": text
            }
            collection.insert_one(message)
        except Exception as e:
            st.error(f"Failed to save message: {str(e)}")

# Optimize API calls with caching and error handling
@lru_cache(maxsize=100)

def get_emotion(text):
    try:
        payload = {"queryResult": {"queryText": text}, "session": "test_session_123"}
        response = requests.post(API_URL, json=payload, timeout=15)
             
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("fulfillmentText", "Lumi is here for you. Take your time.")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return "I'm having trouble connecting, but I'm still here for you."
    
    except requests.exceptions.ReadTimeout:
        return "Lumi is taking a little longer to respond. Please try again."

    except requests.exceptions.ConnectionError:
        return "I'm unable to connect to my system right now, but I'm here for you."

    except requests.exceptions.RequestException:
        fallback_responses = [
            "It seems Lumi is having some trouble responding right now.",
            "I'm still here for you, even if I can't reply at the moment.",
            "Let's try again in a bit. I'm always here to listen."
        ]
        return random.choice(fallback_responses)

# Display title and description above chat box
st.markdown("""
    <div class="chat-title">
        <h1 style='font-size: 24px;'>Lumi</h1>
        <p style='font-size: 14px;'>💬 You are not alone. Lumi is here to listen and support you.</p>
    </div>
""", unsafe_allow_html=True)

# Chat container with white background
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Add first message if chat is empty
if not st.session_state.messages:
    greeting_time = datetime.datetime.now()
    greeting = "Hi there! I'm Lumi. How are you feeling today?"
    st.session_state.messages.append(("assistant", greeting, greeting_time))
    st.session_state.chat_history.append({
        "timestamp": greeting_time.strftime("%Y-%m-%d %H:%M:%S"),
        "user_input": "",
        "lumi_response": greeting
    })

# Display Chat History
for message in st.session_state.messages:
    role, text, timestamp = message
    
    if role == "user":
        st.markdown(f'''
        <div class="message-row user-row">
            <div class="message-content">
                <div class="user-bubble">{text}</div>
                <div class="timestamp user-timestamp">{timestamp.strftime("%H:%M")}</div>
            </div>
            <div class="avatar user-avatar">
                <span class="user-initial">U</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        avatar_html = f'<img src="data:image/webp;base64,{get_image_base64(logo_path)}" class="avatar-img" alt="Lumi">' if logo_exists else '<span>L</span>'
        
        st.markdown(f'''
        <div class="message-row lumi-row">
            <div class="avatar">
                {avatar_html}
            </div>
            <div class="message-content">
                <div class="lumi-bubble">{text}</div>
                <div class="timestamp lumi-timestamp">{timestamp.strftime("%H:%M")}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# Close chat container
st.markdown('</div>', unsafe_allow_html=True)

# Optimize input processing
def process_input():
    if st.session_state.user_input and not st.session_state.submitted:
        user_text = st.session_state.user_input.strip().lower()  # Normalize text
        current_time = datetime.datetime.now()

        st.session_state.submitted = True
        st.session_state.user_input = ""

        st.session_state.messages.append(("user", user_text, current_time))

        # Expanded greetings list
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "what's up", "howdy", "hiya", "yo", "greetings", "sup", "morning",
            "evening", "good day", "how do you do", "how are you", "how are you doing",
            "how’s everything", "how’s it going", "how have you been", "what’s new"
        ]

        # Common responses where the user asks "and you?"
        user_feeling_questions = [
            "i'm good and you", "i am good and you", "i'm fine and you", "i am fine and you",
            "i'm okay and you", "i am okay and you", "i'm doing well and you",
            "i'm alright and you", "i'm great and you", "i'm not bad and you"
        ]

        # Detect positive mood responses
        positive_responses = [
            "i'm good", "i am good", "i'm fine", "i am fine", "i'm okay", "i am okay",
            "i'm doing well", "i'm great", "i'm fantastic", "i'm amazing",
            "i'm wonderful", "i'm happy", "feeling good", "feeling great", "i am feeling well"
        ]

        # Expanded farewell list
        farewells = [
            "bye", "goodbye", "see you", "take care", "later", "farewell",
            "see you soon", "talk to you later", "peace", "so long"
        ]

        # Check for greeting messages
        if any(greet in user_text for greet in greetings):
            greeting_responses = [
                "Hello! 😊 How are you feeling today?",
                "Hey there! I'm Lumi. How's your day going?",
                "Hi! 👋 What’s on your mind today?",
                "Hey! I’m here for you. How can I support you?",
                "Good to see you! How are you feeling?",
                "Howdy! 😊 What's up?",
                "Hey! Hope you're doing okay. Want to chat?",
                "Yo! How’s everything going?",
                "Greetings! Tell me how you’re feeling today.",
                "What's up? 😊 I’m here to listen.",
                "How do you do? Hope you’re having a good day!",
                "How are you? I’m always here if you need to talk."
            ]
            response = random.choice(greeting_responses)

        # Check for "I'm good, and you?" type responses
        elif any(feeling in user_text for feeling in user_feeling_questions):
            lumi_feeling_responses = [
                "I'm just a bot, but I'm happy to chat with you! 😊",
                "I'm here for you! 💙 Tell me more about your day.",
                "I'm doing great because I'm talking to you!",
                "I’m always here, ready to listen. How can I help today?",
                "That’s wonderful! What’s been making you feel good?",
                "That’s great to hear! What’s something positive that happened today?"
            ]
            response = random.choice(lumi_feeling_responses)

        # Handle positive mood responses without calling API
        elif any(positive in user_text for positive in positive_responses):
            positive_replies = [
                "That's awesome! 😊 What's been making you feel good?",
                "I'm so glad to hear that! 🎉 Want to share what made your day great?",
                "That’s great! I love hearing positive things. 💙",
                "Good vibes only! 🌟 Keep up the positivity.",
                "Amazing! What's been making you smile today?",
                "Glad to hear you're doing well! Anything exciting happening?"
            ]
            response = random.choice(positive_replies)

        # Check for farewell messages
        elif any(kw in user_text for kw in farewells):
            farewell_responses = [
                "Goodbye! 😊 Take care and reach out anytime you need me.",
                "See you soon! I'm always here when you need me. 💙",
                "Bye for now! Stay safe and take care. 🌸",
                "Farewell! Hope to chat with you again soon. 😊",
                "Take care! Remember, I'm always here for you. 💙",
                "Talk to you later! Stay strong and be kind to yourself. 💕",
                "So long! I’ll be here whenever you need a chat. 🌼"
            ]
            response = random.choice(farewell_responses)

        else:
            response = get_emotion(user_text)  # Call API for other messages

        response_time = datetime.datetime.now()
        st.session_state.messages.append(("assistant", response, response_time))

        st.session_state.chat_history.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_text,
            "lumi_response": response
        })

        # Save messages to MongoDB
        save_message_to_mongo("user", user_text)
        save_message_to_mongo("assistant", response)

# User Input
st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
st.text_input(
    "",
    placeholder="Tell Lumi how you're feeling today...",
    key="user_input",
    on_change=process_input
)
st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.user_input:
    st.session_state.submitted = False