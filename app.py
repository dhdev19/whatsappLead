from flask import Flask, request, jsonify
import os
import requests
import pymysql
from dotenv import load_dotenv

# Load env variables
load_dotenv()

app = Flask(__name__)

# WhatsApp Config
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

# Database Config
db_config = {
    'host': os.getenv('HOST'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'database': os.getenv('DATABASE'),
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route("/send-whatsapp", methods=["POST"])
def send_whatsapp():
    # Accept both form-urlencoded and JSON
    if request.is_json:
        form_data = request.get_json()
    else:
        form_data = request.form.to_dict()

    if not form_data:
        return jsonify({"error": "No form data received"}), 400

    user_id = form_data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT whatsapp_number FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Build WhatsApp message
    message_lines = ["📩 New Form Submission:"]
    for key, value in form_data.items():
        if key != "user_id":
            message_lines.append(f"{key.capitalize()}: {value}")
    message_lines.append(f"IP: {request.remote_addr}")
    message_text = "\n".join(message_lines)

    # WhatsApp API payload
    payload = {
        "messaging_product": "whatsapp",
        "to": user["whatsapp_number"],
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
        return jsonify({
            "error": "Failed to send WhatsApp message",
            "response": response.json()
        }), 500

    return jsonify({"message": "WhatsApp message sent successfully"}), 200

if __name__ == "__main__":
    app.run(debug=bool(os.getenv("DEBUG", False)))
