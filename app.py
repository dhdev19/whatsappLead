from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
CLIENT_NUMBER = os.getenv("CLIENT_WHATSAPP_NUMBER")

app = Flask(__name__)

@app.route("/send-whatsapp", methods=["POST"])
def send_whatsapp():
    form_data = request.form.to_dict()

    if not form_data:
        return jsonify({"error": "No form data received"}), 400

    # Format WhatsApp message
    message_lines = ["📩 New Form Submission:"]
    for key, value in form_data.items():
        message_lines.append(f"{key.capitalize()}: {value}")
    message_lines.append(f"IP: {request.remote_addr}")

    message_text = "\n".join(message_lines)

    # WhatsApp API payload
    payload = {
        "messaging_product": "whatsapp",
        "to": CLIENT_NUMBER,
        "type": "text",
        "text": {"body": message_text}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Failed to send WhatsApp message", "details": response.json()}), 500

    return jsonify({"message": "WhatsApp message sent successfully"}), 200

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG'))
