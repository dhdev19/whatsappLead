from flask import Flask, request, jsonify
import os
import requests
import pymysql
import logging
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Flask app
app = Flask(__name__)

# Logging config
logging.basicConfig(level=logging.INFO)

# WhatsApp API config
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

# MySQL config
db_config = {
    'host': os.getenv('HOST'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'database': os.getenv('DATABASE'),
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

def format_key(key):
    """Format keys like full_name -> Full Name"""
    return re.sub(r'_', ' ', key).title()

@app.route("/send-whatsapp", methods=["POST"])
def send_whatsapp():
    # Accept JSON or form-urlencoded data
    # form_data = request.get_json() if request.is_json else request.form.to_dict()
    form_data = request.form.to_dict()
    print("Form data:", request.form.to_dict())
    print("Raw data:", request.data)
    print("Headers:", dict(request.headers))

    if not form_data:
        return jsonify({"error": "No form data received"}), 400

    user_id = form_data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_id = int(user_id)
    # Fetch WhatsApp number from DB
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT whatsapp_number FROM leadUsers WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
        conn.close()
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    if not user:
        return jsonify({"error": "User not found"}), 404

    recipient_number = user.get("whatsapp_number")
    if not recipient_number or not recipient_number.isdigit():
        return jsonify({"error": "Invalid or missing WhatsApp number"}), 400

    # Build WhatsApp message
    message_lines = ["📩 New Form Submission:"]
    for key, value in form_data.items():
        if key != "user_id":
            clean_key = format_key(key)
            clean_value = str(value).strip()
            message_lines.append(f"{clean_key}: {clean_value}")
    message_lines.append(f"IP: {request.remote_addr}")
    message_text = "\n".join(message_lines)

    # WhatsApp API payload
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message_text}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        logging.error(f"WhatsApp API error: {response.text}")
        return jsonify({
            "error": "Failed to send WhatsApp message",
            "response": response.json()
        }), 500

    return jsonify({
        "message": "WhatsApp message sent successfully",
        "whatsapp_response": response.json()
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=bool(os.getenv("DEBUG", False)))
