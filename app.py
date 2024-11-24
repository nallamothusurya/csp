from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from markdown import markdown
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import re

API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')
chat_model = model.start_chat(history=[])

app = Flask(__name__, static_folder='static')
CORS(app)

DISALLOWED_WORDS = [
    "adult", "sex", "porn", "nude", "xxx", "bikini", "lust",
    "ullu", "xhamster", "boobs", "rape", "fuck", "boob"
]

def contains_prohibited_content(text):
    text_lower = text.lower()
    for word in DISALLOWED_WORDS:
        if word in text_lower:
            return True
    return False

def format_response(gemini_response):
    formatted_response = ""
    lines = gemini_response.split('\n')
    in_code_block = False  # Track if we are inside a code block
    
    for line in lines:
        line = line.strip()
        if line.startswith("```"):  # Start or end of a code block
            in_code_block = not in_code_block
            if in_code_block:
                # Start of the code block with a "Copy" button
                formatted_response += """
<div style='position: relative; background-color: #1e1e1e; padding: 45px; border-radius: 12px; margin-bottom: 20px;'>
  <button onclick="copyCode(this)" style="position: absolute; top: 10px; right: 10px; background: #007BFF; color: #fff; border: none; padding: 5px 10px; border-radius: 12px; cursor: pointer;">Copy</button>
  <pre style='color: #f8f8f2; font-family: "Courier New", Courier, monospace; font-size: 1rem; white-space: pre-wrap; word-wrap: break-word;' class='code-content'>
"""
            else:
                formatted_response += "</pre></div>"
        elif in_code_block:
            formatted_line = apply_syntax_highlighting(line)
            formatted_response += f"{formatted_line}\n"
        elif line.lower().startswith("heading") or line.lower().startswith("title"):
            formatted_response += f"## **{line}**\n\n"
        elif line.lower().startswith("point") or line.lower().startswith("•") or line.startswith("-"):
            formatted_response += f"- {line.lstrip('-•').strip()}\n"
        elif line:
            formatted_response += f"{line}\n\n"
    return formatted_response

def apply_syntax_highlighting(code):
    # Define general patterns for multiple languages
    keywords = r'\b(def|class|if|else|elif|for|while|import|from|try|except|return|break|continue|function|var|let|const|print|echo|public|private|protected|static|void|new|extends|implements|print)\b'
    strings = r'(\"[^\"]*\"|\'[^\']*\')'  # Match both double and single-quoted strings
    comments = r'(#.*|\/\/.*|\/\*[\s\S]*?\*\/)'  # Match Python, JavaScript, and C-style comments

    # Apply syntax highlighting
    code = re.sub(keywords, r'<span style="color: red;">\g<0></span>', code)
    code = re.sub(strings, r'<span style="color: red;">\g<0></span>', code)
    code = re.sub(comments, r'<span style="color: green;">\g<0></span>', code)
    return code

def get_top_image(query):
    search_url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    image_tag = soup.find("img", class_="mimg")
    if image_tag and image_tag.get("src"):
        image_url = image_tag["src"]
        if not image_url.startswith("http"):
            image_url = "https://www.bing.com" + image_url
        return image_url
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=['POST'])
def chat():
    if request.method == 'POST':
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({"response": "Please enter something!"})
        if contains_prohibited_content(query):
            return jsonify({"response": "Your query contains inappropriate content. Please try again with appropriate language."})
        try:
            if any(word in query.lower() for word in ["image", "photo", "logo"]):
                image_url = get_top_image(query)
                if image_url:
                    download_link = f"<a href='{image_url}' download='image.png' target='_blank' style='display: block; margin-top: 10px; text-align: center; text-decoration: none; color: #007BFF;'>View Image</a>"
                    return jsonify({
                        "response": f"<div style='text-align: center;'><img src='{image_url}' alt='{query}' style='max-width: 800px; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);' /><br>{download_link}</div>"
                    })
                else:
                    return jsonify({"response": "Could not fetch image. Try another query."})
            else:
                gemini_response = chat_model.send_message(query).text
                formatted_response = format_response(gemini_response)
                return jsonify({"response": f"<div class='markdown-body'>{markdown(formatted_response)}</div>"})
        except Exception as e:
            return jsonify({"response": f"Something went wrong: {str(e)}"})
    return jsonify({"response": "Invalid request."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
