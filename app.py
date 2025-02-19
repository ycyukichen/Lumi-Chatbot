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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
    
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

# **Define Local Greetings, Farewells, and Fallback Responses**
greetings = {
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "what’s up", "howdy", "hiya", "yo", "greetings", "sup", "morning",
    "evening", "good day", "how do you do", "how are you", "how are you doing",
    "how is everything", "how is it going", "how have you been", "what is new"
}

farewells = {
    "bye", "goodbye", "see you", "take care", "later", "farewell",
    "see you soon", "talk to you later", "peace", "so long"
}

fallback_responses = [
    "I'm here to listen! Could you tell me more about how you're feeling? 💙",
    "I'd love to understand better. Could you share more about what's on your mind? 💭",
    "I'm all ears. Would you like to elaborate a bit more? 💙",
    "I'm here for you. Would you like to share what's happening? 🤗",
    "I'm interested in hearing more. What's been going on? 💙"
]

# **Process User Input**
def process_input():
    if st.session_state.user_input:
        user_text = st.session_state.user_input.strip()
        st.session_state.user_input = ""
        st.session_state.submitted = True

        # Get current local time
        local_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(local_tz)

        # Add user message to chat history
        st.session_state.messages.append(("user", user_text, local_time))

        # **Handle Greetings Locally**
        if user_text.lower() in greetings:
            response = random.choice([
                "Hello! 😊 How are you feeling today?",
                "Hey there! I'm Lumi. How's your day going?",
                "Hi! 👋 What’s on your mind today?",
                "Hey! I’m here for you. How can I support you?",
                "Good to see you! How are you feeling?"
            ])
        
        # **Handle Farewells Locally**
        elif user_text.lower() in farewells:
            response = random.choice([
                "Goodbye! 😊 Take care and reach out anytime you need me.",
                "See you soon! I'm always here when you need me. 💙",
                "Bye for now! Stay safe and take care. 🌸",
                "Farewell! Hope to chat with you again soon. 😊",
                "Take care! Remember, I'm always here for you. 💙"
            ])

        # **Handle Fallbacks Locally (Short or Unclear Inputs)**
        elif len(user_text.split()) < 3:
            response = random.choice(fallback_responses)

        # **Call API for Emotion-Based Responses**
        else:
            response = get_emotion(user_text)

        # Save assistant's response
        response_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(local_tz)
        st.session_state.messages.append(("assistant", response, response_time))

        # Save messages to MongoDB
        save_message("user", user_text)
        save_message("assistant", response)

# **Display Chat History**
for role, text, timestamp in st.session_state.messages:
    local_time = timestamp.astimezone(local_tz)  
    formatted_time = local_time.strftime("%H:%M")  

    if role == "user":
        st.markdown(f'''
        <div style="text-align: right; background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin: 5px 0;">
            {text} <br><span style="font-size: 0.7em; color: #888;">{formatted_time}</span>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div style="text-align: left; background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;">
            {text} <br><span style="font-size: 0.7em; color: #888;">{formatted_time}</span>
        </div>
        ''', unsafe_allow_html=True)

# **User Input Field**
st.text_input(
    "Tell Lumi how you're feeling today...",
    key="user_input",
    on_change=process_input
)
st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.user_input:
    st.session_state.submitted = False
    