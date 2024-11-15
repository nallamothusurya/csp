from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import fitz  # PyMuPDF
import os
import textwrap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
GOOGLE_API_KEY = "AIzaSyAbmkh8cRl9OpBs5MpmB3mGjXsusV-BtUo"
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Generative AI Chat Model
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

# Path to the folder containing PDF files
PDF_FOLDER_PATH = "data"  # Folder containing PDF files

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def extract_text_from_pdfs_in_folder(folder_path):
    combined_text = ""
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            combined_text += extract_text_from_pdf(pdf_path) + "\n\n"  # Adding a space between PDFs
    return combined_text

def deduplicate_text(texts):
    vectorizer = TfidfVectorizer().fit_transform(texts)
    cosine_sim = cosine_similarity(vectorizer)
    keep = [True] * len(texts)
    for i in range(len(texts)):
        if keep[i]:
            for j in range(i + 1, len(texts)):
                if cosine_sim[i, j] > 0.9:  # Consider passages as duplicates if similarity > 90%
                    keep[j] = False
    return [text for text, flag in zip(texts, keep) if flag]

def preprocess_and_chunk_text(text, max_chunk_size=1000):
    text = text.strip().replace("\n", " ")
    return textwrap.wrap(text, max_chunk_size)

def find_relevant_pdf_text(user_query, pdf_text_chunks):
    vectorizer = TfidfVectorizer()
    all_texts = [user_query] + pdf_text_chunks
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    relevant_chunks = sorted(
        zip(pdf_text_chunks, cosine_sim[0]),
        key=lambda x: x[1],
        reverse=True
    )
    return relevant_chunks[0][0]

# Flask routes
app = Flask(__name__)

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
        pdf_text = extract_text_from_pdfs_in_folder(PDF_FOLDER_PATH)
        pdf_chunks = preprocess_and_chunk_text(pdf_text)

        # Deduplicate the PDF text
        pdf_chunks = deduplicate_text(pdf_chunks)

        # Find the most relevant chunk of text based on the user's query
        relevant_text = find_relevant_pdf_text(user_input, pdf_chunks)

        # Combine relevant PDF content with the user's query as context for Gemini AI
        context = relevant_text + "\nUser's question: " + user_input
        response_raw = chat.send_message(context)
        response_text = format_response(response_raw.text)

        return jsonify({"response": response_text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def format_response(text):
    formatted_text = text.replace('\n', '<br>').replace("**", " ").replace("*", "• ")
    return f"<strong></strong><br>{formatted_text}"

if __name__ == '__main__':
    app.run(debug=True)
