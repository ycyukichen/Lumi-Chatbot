# 🚀 Import Libraries
import streamlit as st
import requests

# ✅ API URL
API_URL = "https://Yuki-Chen-emochatbot.hf.space/dialogflow"  

# 🎨 Streamlit UI
st.set_page_config(page_title="Lumi - I'm here for you", layout="centered")

# 🏆 Title & Description
st.title("✨ Meet Lumi - Your Companion 💙")
st.markdown("💬 *You're not alone. Lumi is here to listen and support you.*")

# 📌 User Input
user_input = st.text_area("📝 Talk to Lumi:", placeholder="Tell Lumi how you're feeling today...")

# 🎯 Function to call FastAPI
def get_emotion(text):
    payload = {
        "queryResult": {"queryText": text},
        "session": "test_session_123"
    }
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        return response.json().get("fulfillmentText", "Lumi is here for you. Take your time. 💙")
    else:
        return "⚠️ API Error: Something went wrong. But Lumi is still here for you."

# 🟢 Detect Emotions Button
if st.button("💡 Share with Lumi"):
    if user_input:
        result = get_emotion(user_input)
        st.success(result)
    else:
        st.warning("💬 Go ahead, share your thoughts with Lumi. Lumi is listening. 💙")

# 🎨 Footer
st.markdown("---")
st.markdown("✨ **Lumi is always here whenever you need someone to talk to.** 💙")
