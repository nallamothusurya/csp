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

# List of common medical-related terms
MEDICAL_TERMS = [
    "medicine", "health", "disease", "surgery", "doctor", "patient","tablet", "pill", "prescription","tablets", "pills", "prescriptions",
    "medical", "healthcare", "hospital", "clinic", "nurse", "pharmacy", "medication", "treatment", "therapy", "diagnosis", "symptoms",
    "medicines", "diseases", "surgeries", "doctors", "patients", 
    "medication", "therapy", "hospital", "paracetamol", "aspirin", "cancer", 
    "treatment", "symptom", "prescription", "diagnosis", "infection", 
    "vaccine", "antibiotics", "flu", "heart disease", "mental health", "injury", "cure","cures","fever", 
     "abrasion", "amputation", "ankle sprain", "back strain", "bee sting", "black eye", 
    "blood clot", "bone fracture", "bruise", "burn", "car accident", "chickenpox", "cold", 
    "concussion", "corneal abrasion", "cut", "dental abscess", "diarrhea", "dislocated joint", 
    "dog bite", "earache", "eczema", "electric shock", "eye infection", "fainting", "fever", 
    "flu", "food poisoning", "gallstones", "gastroenteritis", "gout", "hand, foot, and mouth disease", 
    "hangover", "headache", "heart attack", "heat stroke", "hepatitis", "herpes", "hives", 
    "insect bite", "kidney stones", "laceration", "lyme disease", "malaria", "measles", 
    "meningitis", "migraine", "mononucleosis", "motion sickness", "multiple sclerosis", 
    "muscle strain", "nosebleed", "poison ivy", "poison oak", "poison sumac", "rabies", 
    "diabetes", "hypertension", "arthritis", "asthma", "stroke", "cyst", "tumor", "radiation",
    "rash", "respiratory infection", "ringworm", "rocky mountain spotted fever", "salmonella", 
    "scarlet fever", "sepsis", "shingles", "sinus infection", "skin cancer", "snakebite", 
    "sore throat", "spider bite", "sprain", "stroke", "sunburn", "tetanus", "tick bite", 
    "toothache", "tonsillitis", "traumatic brain injury", "tuberculosis", "urinary tract infection", 
    "vertigo", "viral infection", "vomiting", "whooping cough",
    
    # Specialized terms
    "cancer", "paracetamol", "aspirin", "heart disease", "diabetes", "hypertension", "arthritis", 
    "asthma", "stroke", "cyst", "tumor", "radiation", "chemotherapy", "neurosurgery", 
    "psychology", "psychiatry", "antidepressant", "anxiety", "depression", "PTSD", "Alzheimer's", 
    "Parkinson's", "insulin", "colitis", "bronchitis", "pneumonia", "fibromyalgia", 
    "lupus", "osteoporosis", "biopsy", "stem cell therapy", "gene therapy", "anesthesia",
    
    # Additional healthcare-related terms
    "pharmacy", "ambulance", "emergency", "ICU", "pediatrics", "geriatrics", "obstetrics", 
    "gynecology", "orthopedics", "oncology", "cardiology", "neurology", "dermatology", 
    "radiology", "dental care", "dialysis", "prosthesis", "rehabilitation", "clinical trial", 
    "public health", "epidemic", "pandemic", "contagion", "healthcare system", 
    "hospitalization", "vaccination", "childbirth", "prenatal care", "postpartum care",
    'Abilify', 'Abilify Asimtufii', 'Abilify Maintena', 'Abiraterone', 'Acetaminophen', 'Acetylcysteine', 'Actemra', 'Acyclovir', 'Adalimumab', 'Adderall', 'Advair Diskus', 'Advil', 'Afinitor', 'Agamree', 'Aimovig', 'Ajovy', 'Albuterol', 'Aldactone', 'Alecensa', 'Alendronate', 'Aleve', 'Alfuzosin', 'Allopurinol', 'Alprazolam', 'Alprolix', 'Alunbrig', 'Amantadine', 'Ambien', 'Ambroxol', 'Aminocaproic acid', 'Amiodarone', 'Amitriptyline', 'Amlodipine', 'Amoxicillin', 'Amoxicillin and Clavulanate', 'Ampicillin', 'Anastrozole', 'AndroGel', 'Annovera', 'Apalutamide', 'Apixaban', 'Apokyn', 'Apriso', 'Aptiom', 'Aricept', 'Arikayce', 'Arimidex', 'Aripiprazole', 'Aristada', 'Aromasin', 'Ascorbic acid', 'Aspirin', 'Atenolol', 'Ativan', 'Atogepant', 'Atomoxetine', 'Atorvastatin', 'Aubagio', 'Augmentin', 'Austedo', 'Auvelity', 'Avonex', 'Avsola', 'Azathioprine', 'Azelastine', 'Azilect', 'Azithromycin', 'Azulfidine', 'A/B Otic', 'Abacavir', 'Abacavir and lamivudine', 'Abacavir and Lamivudine Tablets', 'Abacavir Oral Solution', 'Abacavir Sulfate Tablets', 'Abacavir, dolutegravir, and lamivudine', 'Abacavir, Lamivudine and Zidovudine Tablets', 'Abacavir, lamivudine, and zidovudine', 'Abaloparatide', 'Abametapir', 'Abatacept', 'Abatuss DMX', 'Abavite', 'Abbokinase', 'Abciximab', 'Abecma', 'Abelcet', 'Abemaciclib', 'Abilify', 'Abilify (Aripiprazole Intramuscular)', 'Abilify Asimtufii', 'Abilify Asimtufii injection', 'Abilify Discmelt', 'Abilify Maintena', 'Abilify Maintena Prefilled Syringe injection', 'Abilify Mycite', 'Abilify MyCite Maintenance Kit oral with sensor', 'Abilify MyCite Starter Kit oral with sensor', 'Abiraterone', 'Abiraterone Acetate', 'Abiraterone and niraparib', 'Abiraterone, micronized', 'Ablavar', 'Ablysinol', 'AbobotulinumtoxinA', 'Abraxane', 'Abreva', 'Abrilada', 'Abrocitinib', 'Abrysvo', 'Absorbine Athletes Foot', 'Absorbine Jr. Antifungal', 'Absorica', 'Absorica LD', 'Abstral', 'Abstral Sublingual Tablet', 'A-Caro-25', 'Acacia Gum', 'Acai', 'Acalabrutinib', 'ACAM2000', 'Acamprosate', 'Acanya', 'Acarbose', 'Accelerated Covid-19 Test Kit', 'AccessPak for HIV PEP Basic', 'AccessPak for HIV PEP Expanded with Kaletra', 'AccessPak for HIV PEP Expanded with Viracept', 'Acclean', 'Acclean 60 Second Fluoride Treatment', 'Acclean Plus', 'Accolate', 'Accretropin', 'Accrufer', 'Accucaine', 'Accuneb', 'Accupril', 'Accuretic', 'Accutane', 'ACD  A', 'ACD Blood Pack Units', 'Acebutolol', 'Acella Antipyrine and Benzocaine Otic Solution', 'Aceon', 'Acephen', 'Acephen rectal', 'Acerola', 'Acetadote', 'Acetaminophen', 'Acetaminophen (Intravenous)', 'Acetaminophen (Oral, Rectal)', 'Acetaminophen and benzhydrocodone', 'Acetaminophen and butalbital', 'Acetaminophen and caffeine', 'Acetaminophen and chlorpheniramine', 'Acetaminophen and codeine', 'Acetaminophen and Codeine Oral Solution', 'Acetaminophen and dextromethorphan', 'Acetaminophen and diphenhydramine', 'Acetaminophen and ibuprofen', 'Acetaminophen and Oxycodone', 'Acetaminophen and phenylephrine', 'Acetaminophen and phenyltoloxamine', 'Acetaminophen and pseudoephedrine', 'Acetaminophen and tramadol', 'Acetaminophen Congestion and Pain', 'Acetaminophen injection', 'Acetaminophen rectal', 'Acetaminophen, aspirin, and caffeine', 'Acetaminophen, butalbital, and caffeine', 'Acetaminophen, butalbital, caffeine, and codeine', 'Acetaminophen, caffeine, and dihydrocodeine', 'Acetaminophen, caffeine, and magnesium salicylate', 'Acetaminophen, chlorpheniramine, and dextromethorphan', 'Acetaminophen, chlorpheniramine, and phenylephrine', 'Acetaminophen, chlorpheniramine, dextromethorphan, and pseudoephedrine', 'Acetaminophen, dextromethorphan, and diphenhydramine', 'Acetaminophen, dextromethorphan, and doxylamine', 'Acetaminophen, dextromethorphan, and phenylephrine', 'Acetaminophen, dextromethorphan, and triprolidine', 'Acetaminophen, dextromethorphan, doxylamine, and phenylephrine', 'Acetaminophen, dextromethorphan, doxylamine, and pseudoephedrine', 'Acetaminophen, dextromethorphan, guaifenesin, and phenylephrine', 'Acetaminophen, dextromethorphan, guaifenesin, and pseudoephedrine', 'Acetaminophen, dextromethorphan, phenylephrine, and triprolidine', 'Acetaminophen, diphenhydramine, and phenylephrine', 'Acetaminophen, magnesium salicylate, and pamabrom', 'Acetaminophen, pheniramine, and phenylephrine', 'Acetasol HC', 'Acetasol HC otic', 'Acetazolamide', 'Acetazolamide (Intravenous)', 'Acetazolamide Capsules', 'Acetazolamide Tablets', 'AcetaZOLAMIDE, acetaZOLAMIDE Sodium', 'Acetic Acid', 'Acetic acid and hydrocortisone otic', 'Acetic acid irrigant', 'Acetic Acid Irrigation', 'Acetic acid otic', 'Acetic acid vaginal', 'Acetohydroxamic acid', 'Acetone, isopropyl alcohol, and polysorbate', 'Acetylcholine', 'Acetylcysteine', 'Acetylcysteine (Intravenous)', 'Acetylcysteine (Oral)', 'Acetylcysteine inhalation', 'Acetylcysteine Injection', 'Acetylcysteine Solution', 'Acetylcysteine, Acetylcysteine Lysine(Local, Systemic)', 'Achromycin V', 'Aci-Jel vaginal', 'Acid Controller Original Strength', 'Acid Gone', 'Acid Gone Extra Strength', 'Acid Jelly vaginal', 'Acidic Vaginal Jelly vaginal', 'Acidophilus', 'Acidophilus Extra Strength', 'Acidophilus Probiotic Blend', 'Acidophilus with Pectin', 'Aciphex', 'AcipHex Sprinkle', 'Acitretin', 'Acitretin Capsules', 'Ackee', 'Aclasta', 'Aclidinium', 'Aclidinium and formoterol', 'Aclovate', 'Acne', 'Acne 10 Gel', 'Acne Foaming Cream Face Cleanser', 'Acne Wash', 'Acne-Clear', 'Acnevir', 'Acomplia', 'Aconite', 'Acrivastine and pseudoephedrine', 'ACT COVID-19 Antibody Test', 'ACT Fluoride Rinse', 'Actamin', 'Actamin Maximum Strength', 'Actemra', 'Acthar Gel', 'Acthar Gel Pre-filled SelfJect Injector', 'Acthar Gel, H.P.', 'ActHIB', 'Acthrel', 'Acticin', 'Acticlate', 'Actidose', 'Actidose-Aqua', 'Actifed', 'Actifed Cold and Allergy', 'Actigall', 'Actimmune', 'Actiq', 'Actisite', 'Activase', 'Activated charcoal', 'Activella', 'ActivICE', 'Actonel', 'Actonel with Calcium', 'Actoplus Met', 'Actoplus Met XR', 'Actos', 'Acuflex', 'Acular', 'Acular LS', 'Acular PF', 'Acunistat-30 Injection System', 'Acunistat-60 Injection System', 'Acunivive 15 Injection System', 'Acunivive 30 Injection System', 'Acunivive 60 Injection System', 'Acunivive 90 Injection System', 'Acunol', 'Acuvail', 'Acuvue Theravision with Ketotifen', 'Acyclovir', 'Acyclovir (Buccal mucosa)', 'Acyclovir (Ophthalmic)', 'Acyclovir (Oral, Intravenous)', 'Acyclovir and hydrocortisone', 'Acyclovir and hydrocortisone topical', 'Acyclovir Capsules', 'Acyclovir Cream', 'Acyclovir injection', 'Acyclovir IV Infusion', 'Acyclovir Ointment', 'Acyclovir Oral Suspension', 'Acyclovir Tablets', 'Acyclovir topical', 'Acys-5', 'Aczone'

]

def is_medical_query(query):
    """Check if the query contains any medical-related terms."""
    query_lower = query.lower()
    return any(term in query_lower for term in MEDICAL_TERMS)

# Define DISALLOWED_WORDS list
DISALLOWED_WORDS = ["violation", "harmful", "inappropriate", "dangerous", "offensive", "abuse"]

def contains_prohibited_content(text):
    """Check if the text contains prohibited content."""
    text_lower = text.lower()
    return any(word in text_lower for word in DISALLOWED_WORDS)

def apply_syntax_highlighting(code):
    """Apply syntax highlighting using Pygments."""
    try:
        lexer = guess_lexer(code)
    except Exception:
        lexer = PythonLexer()
    formatter = HtmlFormatter(style="monokai", nowrap=True)
    highlighted_code = highlight(code, lexer, formatter)
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
        
        # Check if the query is medical-related
        if not is_medical_query(query):
            return jsonify({"response": "Hi, I am a medical AI. I only respond to medical-related queries. I am a language model trained on medical data and can provide information on a wide range of medical topics. Please ask me a medical-related question."})

        try:
            if any(word in query.lower() for word in ["image", "photo", "logo"]):
                # If the query contains a medical-related term and requests an image
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