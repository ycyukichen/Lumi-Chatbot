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

# API URL
API_URL = "https://Yuki-Chen-emochatbot.hf.space/dialogflow"

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "lumi_chatbot"
COLLECTION_NAME = "chat_history"

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI) if MONGO_URI else None
db = client[DB_NAME] if client else None
collection = db[COLLECTION_NAME] if db else None

# Streamlit UI Configuration
st.set_page_config(
    page_title="Lumi - I'm here for you", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Function to convert image to base64
def get_image_base64(image_path):
    if os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# Check if logo exists
logo_path = "Lumi.webp"
logo_exists = os.path.isfile(logo_path)

# Custom CSS for chat-like experience
st.markdown("""
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
""", unsafe_allow_html=True)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
    
# Function to save a message to MongoDB
def save_message_to_mongo(role, text):
    if collection:
        message = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "text": text
        }
        collection.insert_one(message)

# Function to Call FastAPI
def get_emotion(text):
    payload = {
        "queryResult": {"queryText": text},
        "session": "test_session_123"
    }
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        return response.json().get("fulfillmentText", "Lumi is here for you. Take your time.")
    else:
        return "API Error: Something went wrong. But Lumi is still here for you."

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

# Callback function to process input
def process_input():
    if st.session_state.user_input and not st.session_state.submitted:
        user_text = st.session_state.user_input
        current_time = datetime.datetime.now()
        
        st.session_state.submitted = True
        st.session_state.user_input = ""
        
        st.session_state.messages.append(("user", user_text, current_time))
        
        response = get_emotion(user_text)
        response_time = datetime.datetime.now()
        
        st.session_state.messages.append(("assistant", response, response_time))
        
        st.session_state.chat_history.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_text,
            "lumi_response": response
        })

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
