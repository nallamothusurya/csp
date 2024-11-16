from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from markdown import markdown
import os

# Hardcode the Generative AI API key directly in the code
API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"

# Configure the Generative AI model using the hardcoded API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')
chat_model = model.start_chat(history=[])

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# Text-to-text chat functionality
@app.route("/chat", methods=['POST'])
def chat():
    if request.method == 'POST':
        query = request.json.get('query', '').strip()  # Fetch the query from JSON body
        if not query:
            return jsonify({"response": "Please enter something!"})

        try:
            # Send query to the generative model
            gemini_response = chat_model.send_message(query).text
            # Convert the response to markdown and send it back
            return jsonify({"response": markdown(gemini_response)})
        except Exception as e:
            return jsonify({"response": f"Something went wrong: {str(e)}"})
    return jsonify({"response": "Invalid request."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
