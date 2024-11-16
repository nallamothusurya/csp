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

def format_response(gemini_response):
    """
    Function to format the generative AI response for better readability.
    This function adds markdown formatting like headings, bullet points, etc.
    """
    formatted_response = ""
    
    # Split the response by lines and process each one
    lines = gemini_response.split('\n')
    
    for line in lines:
        line = line.strip()  # Remove extra spaces at the beginning and end of each line
        
        if line.lower().startswith("heading") or line.lower().startswith("title"):
            # Bold and center headings
            formatted_response += f"## **{line}**\n\n"
        elif line.lower().startswith("point") or line.lower().startswith("•") or line.startswith("-"):
            # Convert lines that are bullet points into proper markdown list items
            formatted_response += f"- {line.lstrip('-•').strip()}\n"
        elif line:
            # Regular text, just add it
            formatted_response += f"{line}\n\n"
    
    return formatted_response

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
            
            # Format the response for better readability
            formatted_response = format_response(gemini_response)

            # Convert the formatted response to markdown
            # Wrap the markdown in a div with a specific class for styling
            return jsonify({"response": f"<div class='markdown-body'>{markdown(formatted_response)}</div>"})
        except Exception as e:
            return jsonify({"response": f"Something went wrong: {str(e)}"})
    
    return jsonify({"response": "Invalid request."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
