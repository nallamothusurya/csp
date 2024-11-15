from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import fitz  # PyMuPDF
import os
import textwrap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from multiprocessing import Pool

# Configuration
GOOGLE_API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Generative AI Chat Model
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

# Path to the folder containing PDF files
PDF_FOLDER_PATH = "data"  # Folder containing PDF files

# Flask app
app = Flask(__name__)

# Global storage for preprocessed PDF text
PDF_TEXT_CHUNKS = []

# Extract text from a single PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return " ".join([page.get_text("text") for page in doc])
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

# Parallelized extraction of text from all PDFs in a folder
def extract_text_parallel(folder_path):
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.pdf')]
    with Pool() as pool:
        results = pool.map(extract_text_from_pdf, files)
    return "\n\n".join(results)

# Deduplicate text based on cosine similarity
def deduplicate_text(texts):
    vectorizer = TfidfVectorizer().fit_transform(texts)
    cosine_sim = cosine_similarity(vectorizer)
    keep = [True] * len(texts)
    for i in range(len(texts)):
        if keep[i]:
            for j in range(i + 1, len(texts)):
                if cosine_sim[i, j] > 0.9:
                    keep[j] = False
    return [text for text, flag in zip(texts, keep) if flag]

# Preprocess and chunk text into smaller parts
def preprocess_and_chunk_text(text, max_chunk_size=1000):
    text = text.strip().replace("\n", " ")
    return textwrap.wrap(text, max_chunk_size)

# Find the most relevant text chunk for a query
def find_relevant_pdf_text(user_query, pdf_text_chunks):
    vectorizer = TfidfVectorizer(max_features=5000)  # Limit features for optimization
    all_texts = [user_query] + pdf_text_chunks
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    relevant_chunks = sorted(
        zip(pdf_text_chunks, cosine_sim[0]),
        key=lambda x: x[1],
        reverse=True
    )
    return relevant_chunks[0][0]

# Cache AI responses
@lru_cache(maxsize=100)
def cached_ai_response(context):
    return chat.send_message(context).text

# Preprocess PDFs once during app startup
@app.before_first_request
def initialize_pdf_text():
    global PDF_TEXT_CHUNKS
    print("Initializing PDF text...")
    pdf_text = extract_text_parallel(PDF_FOLDER_PATH)
    pdf_chunks = preprocess_and_chunk_text(pdf_text)
    PDF_TEXT_CHUNKS = deduplicate_text(pdf_chunks)
    print("PDF text initialization complete.")

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_response():
    """Handle chat requests."""
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Find the most relevant chunk of text
        relevant_text = find_relevant_pdf_text(user_input, PDF_TEXT_CHUNKS)

        # Combine relevant PDF content with the user's query as context for Gemini AI
        context = relevant_text + "\nUser's question: " + user_input
        response_raw = cached_ai_response(context)
        response_text = format_response(response_raw)

        return jsonify({"response": response_text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def format_response(text):
    return text.replace('\n', '<br>').replace("**", " ").replace("*", "• ")

if __name__ == '__main__':
    app.run(debug=True)
