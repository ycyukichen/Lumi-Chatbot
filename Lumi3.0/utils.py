import base64
import requests
import pytz

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return ""

def get_user_timezone():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return data.get("timezone", "UTC")
    except Exception:
        return "UTC"
