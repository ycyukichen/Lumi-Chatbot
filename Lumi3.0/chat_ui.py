import streamlit as st
import datetime
import pytz
from utils import get_image_base64

def render_chat(messages, user_timezone, image_path="Lumi.webp"):
    local_tz = pytz.timezone(user_timezone)
    for msg in messages:
        role = msg["role"]
        text = msg["content"]
        timestamp = msg.get("timestamp", datetime.datetime.now(pytz.utc))
        formatted_time = timestamp.astimezone(local_tz).strftime("%H:%M") if isinstance(timestamp, datetime.datetime) else ""
        if role == "user":
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                <div style="max-width: 80%; text-align: right;">
                    <div style="background-color: #dcf8c6; padding: 12px 16px; border-radius: 18px 18px 0 18px; display: inline-block; word-wrap: break-word; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);">
                        {text}
                    </div>
                    <div style="font-size: 0.7em; color: #888888; margin-top: 4px;">{formatted_time}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                <div style="margin-right: 8px;">
                    <img src="data:image/webp;base64,{get_image_base64(image_path)}" alt="Lumi" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover;">
                </div>
                <div style="max-width: 70%; text-align: left;">
                    <div style="background-color: #f5f5f5; padding: 12px 16px; border-radius: 18px 18px 18px 0; display: inline-block; word-wrap: break-word;">
                        {text}
                    </div>
                    <div style="font-size: 0.7em; color: #888888; margin-top: 4px;">{formatted_time}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
