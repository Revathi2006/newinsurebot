from flask import Flask, request, jsonify
from flask_cors import CORS
from chat_handler import ChatHandler
import os

app = Flask(__name__)
CORS(app)

handler = ChatHandler()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    msg = data.get("message", "")
    return jsonify({"reply": handler.handle(msg)})

# Entry point for both local and Render deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns a dynamic port
    app.run(host='0.0.0.0', port=port, debug=False)