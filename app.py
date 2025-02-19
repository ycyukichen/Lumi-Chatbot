import streamlit as st
import requests
import pandas as pd
import datetime
import time
import pytz
import os
from PIL import Image
import base64
import pymongo
from dotenv import load_dotenv
from functools import lru_cache
import random
import re
import contractions

# API URL
API_URL = "https://Yuki-Chen-emochatbot.hf.space/dialogflow"

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "lumi_chatbot"
COLLECTION_NAME = "chat_history"

# MongoDB Connection
def get_mongo_collection():
    try:
        if MONGO_URI:
            client = pymongo.MongoClient(MONGO_URI, maxPoolSize=50)
            db = client[DB_NAME]
            return db[COLLECTION_NAME]
    except Exception as e:
        st.error(f"MongoDB connection error: {str(e)}")
    return None

collection = get_mongo_collection()

# Encode image to Base64
@st.cache_data
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return ""

# Streamlit UI Configuration
st.set_page_config(page_title="Lumi - I'm here for you", layout="centered", initial_sidebar_state="collapsed")

# Theme Settings
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

@st.cache_data
def get_custom_css(theme=None):
    css = {
        "dark": """
        .main { background-color: #121212 !important; color: #ffffff !important; }
        .chat-container { background-color: #1e1e1e !important; }
        .user-bubble { background-color: #00a884 !important; color: #ffffff !important; }
        .lumi-bubble { background-color: #252525 !important; color: #ffffff !important; }
        """,
        "light": """
        .main { background-color: #f5f8fa !important; color: #000000 !important; }
        .chat-container { background-color: #ffffff !important; }
        .user-bubble { background-color: #dcf8c6 !important; color: #000000 !important; }
        .lumi-bubble { background-color: #f5f5f5 !important; color: #000000 !important; }
        """
    }
    return f"<style>{css.get(theme, css['light'])}</style>"

st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

# Dark/Light Mode Toggle
if st.button("🌙 Dark Mode" if st.session_state.theme != "dark" else "☀️ Light Mode"):
    st.session_state.theme = "dark" if st.session_state.theme != "dark" else "light"
    st.rerun()

# Load Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Get User Timezone
@st.cache_data
def get_user_timezone():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return data.get("timezone", "UTC")
    except Exception:
        return "UTC"

user_timezone = get_user_timezone()
local_tz = pytz.timezone(user_timezone)

# Display Title & Description
st.markdown("""
    <div style="text-align: center;">
        <h1 style='font-size: 24px;'>Lumi</h1>
        <p>💬 You are not alone. Lumi is here to listen and support you.</p>
    </div>
""", unsafe_allow_html=True)
        
# Check if logo exists
logo_path = "Lumi.webp"
logo_exists = os.path.isfile(logo_path)

# Initialize Chat
if not st.session_state.messages:
    greeting = "Hi there! I'm Lumi. How are you feeling today?"
    st.session_state.messages.append(("assistant", greeting, datetime.datetime.now(pytz.utc)))

# Save Message to MongoDB
def save_message(role, text):
    if collection:
        try:
            collection.insert_one({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "role": role,
                "text": text
            })
        except Exception as e:
            st.error(f"Database error: {e}")

# Optimize API calls with caching and error handling
@lru_cache(maxsize=100)
def get_emotion(text):
    try:
        response = requests.post(API_URL, json={"queryResult": {"queryText": text}, "session": "test_session_123"}, timeout=15)
        if response.status_code == 200:
            return response.json().get("fulfillmentText", "Lumi is here for you. Take your time.")
    except requests.exceptions.RequestException:
        return random.choice([
            "I'm having trouble connecting, but I'm still here for you.",
            "It seems Lumi is having some trouble responding right now.",
            "Let's try again in a bit. I'm always here to listen."
        ])

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

# Clean User Input
def clean_text(text):
    return contractions.fix(re.sub(r"[^\w\s]", "", text)).lower().strip()
# Display Chat History
for role, text, timestamp in st.session_state.messages:
    local_time = timestamp.astimezone(local_tz)  
    formatted_time = local_time.strftime("%H:%M")  

    if role == "user":
        st.markdown(f'''
        <div class="message-row user-row" style="display: flex; justify-content: flex-end; align-items: center; margin: 10px 0;">
            <div class="message-content" style="max-width: 80%; text-align: right;">
                <div class="user-bubble" style="background-color: #dcf8c6; padding: 12px 16px; border-radius: 18px 18px 0 18px; display: inline-block; word-wrap: break-word; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);">
                    {text}
                </div>
                <div class="timestamp user-timestamp" style="font-size: 0.7em; color: #888888; margin-top: 4px;">
                    {formatted_time}
                </div>
            </div>
            <div class="avatar user-avatar" style="width: 36px; height: 36px; border-radius: 50%; background-color: #dcf8c6; display: flex; align-items: center; justify-content: center; margin-left: 8px; margin-right: 0;">
                <span class="user-initial" style="color: #fff; font-weight: bold;">U</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="message-row lumi-row" style="display: flex; justify-content: flex-start; align-items: center; margin: 10px 0;">
            <div class="avatar" style="width: 36px; height: 36px; border-radius: 50%; background-color: #ccc; display: flex; align-items: center; justify-content: center; margin-right: 8px;">
                <img src="data:image/webp;base64,{get_image_base64(logo_path)}" class="avatar-img" alt="Lumi" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">
            </div>
            <div class="message-content" style="max-width: 70%; text-align: left;">
                <div class="lumi-bubble" style="background-color: #f5f5f5; padding: 12px 16px; border-radius: 18px 18px 18px 0; display: inline-block; word-wrap: break-word;">
                    {text}
                </div>
                <div class="timestamp lumi-timestamp" style="font-size: 0.7em; color: #888888; margin-top: 4px;">
                    {timestamp.strftime("%H:%M")}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# Close chat container
st.markdown('</div>', unsafe_allow_html=True)

# Clean text
def clean_text(text):
    """Expand contractions and remove punctuation"""
    text = contractions.fix(text)  # Expand contractions ("I'm" → "I am")
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation ("how are you?" → "how are you")
    return text.lower().strip()  # Convert to lowercase

def process_input():
    if st.session_state.user_input and not st.session_state.submitted:
        user_text = st.session_state.user_input.strip()
        user_timezone = get_user_timezone()  # Get user's timezone
        local_tz = pytz.timezone(user_timezone)

        # Get current UTC time and convert to user's local time
        current_utc_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        local_time = current_utc_time.astimezone(local_tz)

        st.session_state.submitted = True
        st.session_state.user_input = ""

        st.session_state.messages.append(("user", user_text, local_time))
        
        sentences = [s.strip() for s in re.split(r'[.!?]', user_text) if s.strip()]

        responses = []

        # Convert lists to sets for faster lookup
        greetings = {
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "what is up", "howdy", "hiya", "yo", "greetings", "sup", "morning",
            "evening", "good day", "how do you do", "how are you", "how are you doing",
            "how is everything", "how is it going", "how have you been", "what is new",
            "hi how do you do", "hi how are you", "hi how are you doing",
            "hi how is everything", "hi how is it going", "hi how have you been", "hi, what is new",
        }

        user_feeling_questions = {
            "i am good and you", "i am fine and you", "i am okay and you",
            "i am doing well and you", "i am alright and you", "i am great and you",
            "i am not bad and you"
        }

        positive_responses = {
            "i am good", "i am fine", "i am okay", "i am doing well", "i am great",
            "i am fantastic", "i am amazing", "i am wonderful", "i am happy",
            "feeling good", "feeling great", "i am feeling well"
        }

        farewells = {
            "bye", "goodbye", "see you", "take care", "later", "farewell",
            "see you soon", "talk to you later", "peace", "so long"
        }

        casual_prompts = {
            "what about you", "you tell", "tell me", "your turn", "you go",
            "what do you think", "what would you say"
        }

        for sentence in sentences:
            # Check for greeting messages
            if sentence in greetings:
                response = random.choice([
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
                ])

            # Check for "I'm good, and you?" type responses
            elif sentence in user_feeling_questions:
                response = random.choice([
                    "I'm just a bot, but I'm happy to chat with you! 😊",
                    "I'm here for you! 💙 Tell me more about your day.",
                    "I'm doing great because I'm talking to you!",
                    "I’m always here, ready to listen. How can I help today?",
                    "That’s wonderful! What’s been making you feel good?",
                    "That’s great to hear! What’s something positive that happened today?"
                ])

            # Handle positive mood responses
            elif sentence in positive_responses:
                response = random.choice([
                    "That's awesome! 😊 What's been making you feel good?",
                    "I'm so glad to hear that! 🎉 Want to share what made your day great?",
                    "That’s great! I love hearing positive things. 💙",
                    "Good vibes only! 🌟 Keep up the positivity.",
                    "Amazing! What's been making you smile today?",
                    "Glad to hear you're doing well! Anything exciting happening?"
                ])

            # Handle casual prompts (e.g., "you tell", "your turn")
            elif sentence in casual_prompts:
                response = random.choice([
                    "Hmm, I’d say I’m feeling... well, as great as a bot can be! 😊",
                    "You know, I’m just here to make your day better! Tell me something fun.",
                    "Good question! If I had feelings, I’d say I’m feeling pretty happy to chat with you!",
                    "My turn? Well, I think you’re awesome! Now, tell me more about you. 😊",
                    "I’d say… I’m here, ready to listen! What’s on your mind?",
                    "I’d love to answer, but I’m more interested in hearing about you!"
                ])

            # Check for farewell messages
            elif sentence in farewells:
                response = random.choice([
                    "Goodbye! 😊 Take care and reach out anytime you need me.",
                    "See you soon! I'm always here when you need me. 💙",
                    "Bye for now! Stay safe and take care. 🌸",
                    "Farewell! Hope to chat with you again soon. 😊",
                    "Take care! Remember, I'm always here for you. 💙",
                    "Talk to you later! Stay strong and be kind to yourself. 💕",
                    "So long! I’ll be here whenever you need a chat. 🌼"
                ])

            else:
                response = get_emotion(user_text)  # Call API for other messages
            
            responses.append(response)
        
        final_response = " ".join(responses)

        response_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(local_tz)
        st.session_state.messages.append(("assistant", final_response, response_time))

        st.session_state.chat_history.append({
            "timestamp": current_utc_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_text,
            "lumi_response": final_response
        })

        # Save messages to MongoDB
        save_message("user", user_text)
        save_message("assistant", final_response)

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
    