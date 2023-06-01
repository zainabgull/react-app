from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import spacy
import en_core_web_sm
from spacy.matcher import Matcher
import PyPDF2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

nlp = en_core_web_sm.load()

# initialize matcher with a vocab
matcher = Matcher(nlp.vocab)

def extract_name_from_resume(text):
    nlp_text = nlp(text)

    # First name and Last name are always Proper Nouns
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]

    matcher.add('None', [pattern])

    matches = matcher(nlp_text)

    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text

def extract_text_from_image(file):
    with Image.open(file) as image:
        text = pytesseract.image_to_string(image)
        return text

@app.route('/api/parse', methods=['GET','POST'])
def parse_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected!'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected!'})
    
    if file and file.filename.lower().endswith(('.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg')):
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        if file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            # extract text from PDF or Word document
            with open(filepath, 'rb') as f:
                if file.filename.lower().endswith('.pdf'):
                    pdf_reader = PyPDF2.PdfFileReader(f)
                    text = ''
                    for page in range(pdf_reader.getNumPages()):
                        text += pdf_reader.getPage(page).extractText()
                else:
                    text = ''
                    for line in f:
                        text += line.decode('utf-8', errors='ignore')
            name = extract_name_from_resume(text)
            return jsonify({'name': name})
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # extract text from image using OCR
            text = extract_text_from_image(filepath)
            name = extract_name_from_resume(text)
            return jsonify({'name': name})
    else:
        return jsonify({'error': 'Invalid file format!'})

if __name__ == '__main__':
    app.run(debug=True)



