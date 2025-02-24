import os
import torch
import streamlit as st
import requests
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoModelForCausalLM
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

device = "cuda" if torch.cuda.is_available() else "cpu"
BERT_MODEL_NAME = "Yuki-Chen/fine_tuned_BERT_goemotions_1"
hf_token = os.getenv("HUGGINGFACE_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@st.cache_data
def load_emotion_model():
    try:
        tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(BERT_MODEL_NAME).to(device)
        return tokenizer, model
    except Exception as e:
        st.error(f"Error loading emotion model: {e}")
        return None, None

@st.cache_resource
def load_llama_model():
    if not GROQ_API_KEY:
        st.error("Missing Groq API key. Please set GROQ_API_KEY in environment variables.")
        return None

    output_parser = StrOutputParser()
    
    def call_groq_llama3(prompt, max_tokens=512, temperature=0.7):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            raw_output = response.json()["choices"][0]["message"]["content"].strip()
            cleaned_output = output_parser.parse(raw_output)  
            return cleaned_output
        else:
            return f"Error: {response.status_code}, {response.text}"

    return call_groq_llama3 
