from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from markdown import markdown
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
from PIL import Image
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Hardcoded API Key (not recommended for production)
API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')
chat_model = model.start_chat(history=[])

app = Flask(__name__, static_folder='static')
CORS(app)

DISALLOWED_WORDS = [ "sex", "porn", "nude", "xxx", "bikini", "lust",
    "ullu", "xhamster", "boobs", "rape", "fuck", "boob","boobs"
]

def contains_prohibited_content(text):
    """Check if the text contains any disallowed words."""
    text_lower = text.lower()
    for word in DISALLOWED_WORDS:
        if word in text_lower:
            return True
    return False

def format_response(gemini_response):
    """Format the response from the generative model into Markdown."""
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

def get_top_images(query):
    """Fetch top image URLs for the given query."""
    search_url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    image_tags = soup.find_all("img", class_="mimg", limit=3)
    
    image_urls = []
    for image_tag in image_tags:
        img_url = image_tag.get("src")
        if img_url and not img_url.startswith("http"):
            img_url = "https://www.bing.com" + img_url
        if img_url:
            image_urls.append(img_url)
    
    return image_urls

def get_image_dimensions(url):
    """Get the dimensions of the image from the URL."""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img.size
    except Exception as e:
        app.logger.error(f"Error getting image dimensions for {url}: {str(e)}")
        return (0, 0)

def get_best_image(query):
    """Get the best image URL based on dimensions."""
    image_urls = get_top_images(query)
    if not image_urls:
        return None

    best_image_url = None
    max_width, max_height = 0, 0
    
    for url in image_urls:
        width, height = get_image_dimensions(url)
        if width * height > max_width * max_height:
            max_width, max_height = width, height
            best_image_url = url
    
    return best_image_url

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("index.html")

@app.route("/chat", methods=['POST'])
def chat():
    """Handle chat request and respond with a message or image."""
    if request.method == 'POST':
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({"response": "Please enter something!"})
        if contains_prohibited_content(query):
            return jsonify({"response": "Your query contains inappropriate content. Please try again with appropriate language."})
        
        try:
            # Check if the query asks for images
            if any(word in query.lower() for word in ["image", "photo", "logo","pic","pics"]):
                best_image_url = get_best_image(query)
                if best_image_url:
                    return jsonify({
                        "response": f"<div class='chat-image'><img src='{best_image_url}' alt='{query}'  /></div>"
                    })
                else:
                    return jsonify({"response": "Could Generate image. Try another query."})
            else:
                # Get the model's text response
                gemini_response = chat_model.send_message(query).text
                formatted_response = format_response(gemini_response)
                # Send the response formatted in Markdown (which will be converted to HTML on the frontend)
                return jsonify({
                    "response": f"<div class='chat-text'>{markdown(formatted_response)}</div>"
                })
        except Exception as e:
            app.logger.error(f"Error during chat processing: {str(e)}")
            return jsonify({"response": f"Something went wrong: {str(e)}"})
    return jsonify({"response": "Invalid request."})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
