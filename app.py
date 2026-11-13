"""
app.py
------
Flask web server. Serves the chat page and exposes a /chat JSON API.
"""

from flask import Flask, jsonify, render_template, request

from chatbot import FAQChatbot

app = Flask(__name__)

# Build the chatbot once when the server starts (not on every request)
bot = FAQChatbot()


@app.route("/")
def home():
    """Serve the chat interface."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Receive {"message": "..."} and return the chatbot's answer as JSON."""
    try:
        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return jsonify({"status": "error",
                            "answer": "Invalid request. Please send a message."}), 400

        result = bot.get_response(data["message"])
        status_code = 400 if result["status"] == "empty" else 200
        return jsonify(result), status_code

    except Exception as exc:  # last-resort safety net
        app.logger.exception("Unexpected error: %s", exc)
        return jsonify({"status": "error",
                        "answer": "Something went wrong on the server. Please try again."}), 500


if __name__ == "__main__":
    import logging
    from waitress import serve

    logging.basicConfig(level=logging.INFO)

    print("FAQ Chatbot is starting...")

    serve(app, host="127.0.0.1", port=5000)