from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from markdown import markdown
from bs4 import BeautifulSoup
import requests

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
    
    lines = gemini_response.split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith("heading") or line.lower().startswith("title"):
            formatted_response += f"## **{line}**\n\n"
        elif line.lower().startswith("point") or line.lower().startswith("•") or line.startswith("-"):
            formatted_response += f"- {line.lstrip('-•').strip()}\n"
        elif line:
            formatted_response += f"{line}\n\n"
    
    return formatted_response

def get_top_image(query):
    """
    Function to scrape the top image URL from Bing for a given query.
    """
    search_url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    image_tag = soup.find("img", class_="mimg")
    if image_tag and image_tag.get("src"):
        return image_tag["src"]
    return None

@app.route("/")
def home():
    return render_template("index.html")

# Text-to-text chat functionality
@app.route("/chat", methods=['POST'])
def chat():
    if request.method == 'POST':
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({"response": "Please enter something!"})

        try:
            if "image" in query.lower():
                # Extract the top image from Bing
                image_url = get_top_image(query)
                if image_url:
                    return jsonify({"response": f"<img src='{image_url}' alt='Top image for {query}' />"})
                else:
                    return jsonify({"response": "Could not fetch image. Try another query."})
            else:
                # Send query to the generative model
                gemini_response = chat_model.send_message(query).text
                
                # Format the response
                formatted_response = format_response(gemini_response)
                
                # Convert to markdown
                return jsonify({"response": f"<div class='markdown-body'>{markdown(formatted_response)}</div>"})
        except Exception as e:
            return jsonify({"response": f"Something went wrong: {str(e)}"})
    
    return jsonify({"response": "Invalid request."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
