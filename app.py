from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from markdown import markdown
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import re
from html import escape
from pygments import highlight
from pygments.lexers import guess_lexer, PythonLexer
from pygments.formatters import HtmlFormatter

# Google Generative AI API Key
API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')
chat_model = model.start_chat(history=[])

app = Flask(__name__, static_folder='static')
CORS(app)

# List of prohibited words for query filtering
DISALLOWED_WORDS = [
    "adult", "sex", "porn", "nude", "xxx", "bikini", "lust",
    "ullu", "xhamster", "boobs", "rape", "fuck", "boob", "hot"
]

def contains_prohibited_content(text):
    """Check if the text contains prohibited content."""
    text_lower = text.lower()
    for word in DISALLOWED_WORDS:
        if word in text_lower:
            return True
    return False

def apply_syntax_highlighting(code):
    """Apply syntax highlighting using Pygments."""
    try:
        # Guess the language of the code
        lexer = guess_lexer(code)
    except Exception:
        # Fallback to Python lexer if the language cannot be determined
        lexer = PythonLexer()

    # Highlight the code using HTML formatter
    formatter = HtmlFormatter(style="monokai", nowrap=True)  # Use 'monokai' style
    highlighted_code = highlight(code, lexer, formatter)

    # Wrap in a styled container
    return f"""
<div style='position: relative; background-color: #171717; padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
  <button onclick="copyCode(this)" style="position: absolute; top: 10px; right: 10px; background: #007BFF; color: #fff; border: none; padding: 5px 10px; border-radius: 12px; cursor: pointer;">Copy</button>
  <pre style='color: #f8f8f2; font-family: "Consolas", "Courier New", "Courier", monospace;
 font-size: 1rem; white-space: pre-wrap; word-wrap: break-word;' class='code-content'>
{highlighted_code}
  </pre>
</div>
"""

def format_response(gemini_response):
    """Format the Gemini response with code highlighting."""
    formatted_response = ""
    lines = gemini_response.split('\n')
    in_code_block = False
    code_block_content = []

    for line in lines:
        line = line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                # Process the code block content when closing the block
                highlighted_code = apply_syntax_highlighting("\n".join(code_block_content))
                formatted_response += highlighted_code
                code_block_content = []
        elif in_code_block:
            code_block_content.append(line)
        else:
            formatted_response += f"{line}\n\n"
    return formatted_response

def get_top_image(query):
    """Fetch the top image for a query using Bing Image Search."""
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
    """Render the homepage."""
    return render_template("index.html")

@app.route("/chat", methods=['POST'])
def chat():
    """Handle chatbot queries."""
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
