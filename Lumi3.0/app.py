import streamlit as st
import datetime
import pytz
import random
import re
from transformers import pipeline

from utils import get_user_timezone
from model_loader import load_emotion_model, load_llama_model
from chat_ui import render_chat

# Page Configuration
st.set_page_config(page_title="Lumi - Your AI Friend", layout="centered")
st.markdown("<h1 style='text-align: center;'>Lumi</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>💬 I'm here to listen, support, and chat with you.</p>", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hi there! I'm Lumi. How are you feeling today?",
        "timestamp": datetime.datetime.now(pytz.utc)
    }]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Timezone Setup
user_timezone = get_user_timezone()

# Model Loading
bert_tokenizer, bert_model = load_emotion_model()
emotion_classifier = (
    pipeline("text-classification", model=bert_model, tokenizer=bert_tokenizer, device=0)
    if bert_model else None
)
llama_tokenizer, llama_model = load_llama_model()
llama_pipe = pipeline("text-generation", model=llama_model, tokenizer=llama_tokenizer)

# Helper Functions
def detect_keyword_category(text):
    GREETING_KEYWORDS = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening",
                           "what’s up", "howdy", "hiya", "yo", "greetings", "sup", "morning",
                           "evening", "good day", "how do you do", "how are you", "how are you doing",
                           "how's everything", "how's it going", "how have you been", "what's new"}
    FAREWELL_KEYWORDS = {"bye", "goodbye", "see you", "take care", "later", "farewell",
                         "see you soon", "talk to you later", "peace", "so long"}
    IDENTITY_PATTERNS = [r"\bwho are you\b", r"\bwho is lumi\b", r"\bwhat is lumi\b", r"\btell me about lumi\b"]

    text_lower = text.lower().strip()
    text_lower = re.sub(r"[^\w\s]", "", text_lower)
    if any(re.search(pattern, text_lower) for pattern in IDENTITY_PATTERNS):
        return "identity"
    if any(re.search(rf"\b{re.escape(greet)}\b", text_lower) for greet in GREETING_KEYWORDS):
        return "greeting"
    if any(re.search(rf"\b{re.escape(fare)}\b", text_lower) for fare in FAREWELL_KEYWORDS):
        return "farewell"
    return None

def get_direct_response(category):
    if category == "greeting":
        return random.choice([
            "Hello! 😊 How are you feeling today?",
            "Hey there! I'm Lumi. How's your day going?",
            "Hi! 👋 What’s on your mind today?",
            "Hey! I’m here for you. How can I help you?",
            "Good to see you! How are you feeling?"
        ])
    elif category == "farewell":
        return random.choice([
            "Goodbye! 😊 Take care and reach out anytime you need me.",
            "See you soon! I'm always here when you need me. 💙",
            "Bye for now! Stay safe and take care. 🌸",
            "Farewell! Hope to chat with you again soon. 😊",
            "Take care! Remember, I'm always here for you. 💙"
        ])
    elif category == "identity":
        return (
            "🌟 Hi! I'm Lumi, your AI friend. 🌟\n"
            "I'm here to listen, support, and chat with you. Whether you're feeling happy, sad, "
            "or just want to talk, I'm always here to provide friendly and empathetic conversations.\n"
            "You can share your thoughts, ask for advice, or just chat about anything! 💙"
        )
    return None

def classify_emotion(text, topk=1):
    if not emotion_classifier:
        return [{"label": "neutral", "score": 1.0}]
    try:
        result = emotion_classifier(text, top_k=topk)
        return result
    except Exception:
        return [{"label": "neutral", "score": 1.0}]

emotion_prompts = {
    "admiration": "The user is expressing admiration. Respond with enthusiasm and engage positively.",
    "amusement": "The user is amused. Keep the conversation light and playful.",
    "anger": "The user is angry. Validate their feelings and help them process their emotions calmly.",
    "annoyance": "The user is annoyed. Acknowledge their frustration and provide helpful suggestions.",
    "approval": "The user is approving of something. Engage and continue the positive discussion.",
    "caring": "The user is expressing care. Respond with warmth and kindness.",
    "confusion": "The user is confused. Provide clear, step-by-step guidance to help them understand.",
    "curiosity": "The user is curious. Encourage their exploration and provide insightful answers.",
    "desire": "The user is expressing desire. Respond supportively and engage in discussion.",
    "disappointment": "The user is disappointed. Show empathy and offer encouragement.",
    "disapproval": "The user disapproves of something. Respect their viewpoint and discuss constructively.",
    "disgust": "The user is disgusted. Understand their perspective and respond appropriately.",
    "embarrassment": "The user is embarrassed. Reassure them and make them feel at ease.",
    "excitement": "The user is excited. Engage with enthusiasm and encourage their energy.",
    "fear": "The user is afraid. Offer reassurance and support.",
    "gratitude": "The user is expressing gratitude. Acknowledge their appreciation and respond warmly.",
    "grief": "The user is grieving. Offer support, sympathy, and patience.",
    "joy": "The user is joyful. Celebrate their happiness and encourage positivity.",
    "love": "The user is expressing love. Respond warmly and supportively.",
    "nervousness": "The user is nervous. Help them feel reassured and offer calming advice.",
    "optimism": "The user is optimistic. Encourage their positivity and enthusiasm.",
    "pride": "The user is proud. Celebrate their achievements with them.",
    "realization": "The user has had a realization. Encourage their insights and discussion.",
    "relief": "The user feels relieved. Acknowledge their feelings and continue the conversation naturally.",
    "remorse": "The user feels remorse. Offer support and encourage self-forgiveness.",
    "sadness": "The user is sad. Respond with empathy and emotional support.",
    "surprise": "The user is surprised. Engage with curiosity and discuss the surprise.",
    "neutral": "The user is neutral. Respond naturally based on the conversation flow."
}

def generate_response(user_input):
    emotions = classify_emotion(user_input, topk=3)
    dominant_emotion = emotions[0]["label"]
    
    st.session_state.chat_history.append(f"User ({dominant_emotion}): {user_input}")
    st.session_state.chat_history = st.session_state.chat_history[-10:]

    emotion_instruction = emotion_prompts.get(dominant_emotion, "Respond naturally.")
    prompt = (
        "You are an emotionally intelligent chatbot that provides warm and empathetic responses.\n"
        "Always acknowledge the user's feelings and offer thoughtful, caring advice.\n\n"
        f"Emotion-Specific Instruction: {emotion_instruction}\n\n"
        "Conversation History:\n" +
        "\n".join(st.session_state.chat_history) + "\n\n"
        "Chatbot:"
    )

    with st.spinner("Generating response..."):
        chatbot_response = load_llama_model(prompt, max_tokens=200, temperature=0.7)

    st.session_state.chat_history.append(f"Chatbot: {chatbot_response}")
    st.session_state.chat_history = st.session_state.chat_history[-10:]
    return chatbot_response

# Render the chat
render_chat(st.session_state.messages, user_timezone)

# User input
user_input = st.chat_input("Tell me what's on your mind...")
if user_input is not None:
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.datetime.now(pytz.utc)
    }
    st.session_state.messages.append(user_message)

    category = detect_keyword_category(user_input)
    direct_reply = get_direct_response(category)
    if direct_reply:
        ai_response = direct_reply
    else:
        ai_response = generate_response(user_input)

    assistant_message = {
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.datetime.now(pytz.utc)
    }
    st.session_state.messages.append(assistant_message)
    st.rerun()
    render_chat()
