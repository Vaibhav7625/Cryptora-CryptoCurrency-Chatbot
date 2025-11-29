from flask import Flask, render_template, request, jsonify, redirect, url_for
from gemini_core import process_user_input

app = Flask(__name__)

# -------------------------------
# ROUTES
# -------------------------------

@app.route("/")
def index():
    return redirect(url_for("splash"))

@app.route("/splash")
def splash():
    return render_template("splash.html")

@app.route("/chat")
def chat():
    return render_template("index.html")


# -------------------------------
# MAIN CHAT RESPONSE
# -------------------------------

@app.route("/get-response", methods=["POST"])
def get_response():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "⚠️ No message received."})

    try:
        reply = process_user_input(user_message)

        # ------------------------------------------
        # CASE 1: NEWS RESULT (dict type)
        # Your original formatting style preserved
        # ------------------------------------------
        if isinstance(reply, dict):
            title = reply.get("title", "")
            date = reply.get("date", "")
            sentiment = reply.get("sentiment", "")
            source = reply.get("source", "")
            description = reply.get("description", "")
            link = reply.get("link", "#")

            formatted_reply = f"""
                <div class='response-box'>
                    <p>📰 <strong>{title}</strong></p>
                    <p>📅 <strong>Date:</strong> {date}</p>
                    <p>😐 <strong>Sentiment:</strong> {sentiment}</p>
                    <p>🌐 <strong>Source:</strong> {source}</p>
                    <p>📝 {description}</p>
                    <p>🔗 <a href='{link}' target='_blank'>{link}</a></p>
                </div>
            """

        # ------------------------------------------
        # CASE 2: TEXT RESULT (ALL PRICE, OHLC, TREND, LIST OUTPUTS)
        # EXACT line breaks preserved without altering formatting
        # ------------------------------------------
        else:
            safe_text = reply.replace("\n", "<br>")
            formatted_reply = f"""
                <div class='response-box'>
                    <p style='margin:0; line-height:1.5;'>{safe_text}</p>
                </div>
            """

    except Exception as e:
        formatted_reply = f"""
            <div class='response-box' style='border-left:4px solid red;'>
                <p>❌ Error: {str(e)}</p>
            </div>
        """

    return jsonify({"response": formatted_reply})


# -------------------------------
# APP ENTRY
# -------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
