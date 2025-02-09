from flask import Flask, request, jsonify, render_template
import os
import pdfplumber
import re
import json
from pymongo import MongoClient, errors

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MongoDB configuration
MONGO_URI = " "

def get_mongo_client(uri):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info() 
        return client
    except errors.ServerSelectionTimeoutError as err:
        print(f"Could not connect to MongoDB: {err}")
        return None

client = get_mongo_client(MONGO_URI)
db = client["Marks_Storage"] if client else None
collection = db['Marks'] if db is not None else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/sgpa')
def sgpa():
    return render_template('sgpa.html')

@app.route('/cgpa')
def cgpa():
    return render_template('cgpa.html')

@app.route('/get_subjects', methods=['GET'])
def get_subjects():
    if collection is None:
        return jsonify({"error": "Cannot connect to MongoDB"}), 500

    scheme = request.args.get('scheme')
    semester = request.args.get('semester')
    branch = request.args.get('branch')
    try:
        scheme = int(scheme)
    except ValueError:
        return jsonify({"error": "Invalid scheme value, must be an integer"}), 400

    query = {
        'Scheme': scheme,
        'Sem': str(semester),
        'Branch': branch
    }

    print(f"Querying with: {query}")

    try:
        subjects = collection.find(query)
        subject_list = []
        for subject in subjects:
            print(f"Found subject: {subject}")
            subject_list.append({
                'SubjectCode': subject.get('Subject Code'),
                'SubjectCredits': subject.get('Subject Credits')
            })

        if not subject_list:
            print("No matching subjects found.")
            print(f"All documents: {list(collection.find())}")

        print("Final subject list: ", subject_list)  
        return jsonify(subject_list)
    except Exception as e:
        print(f"Error occurred: {str(e)}")  
        return jsonify({"error": str(e)}), 500


def extract_subject_data(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    print("Extracted text:", text)
    subject_pattern = r'(\b[A-Z]{2,5}\d{2,3}[A-Z]?\d?[A-Z]?\b)[^\d]+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s+([PF])'
    matches = re.findall(subject_pattern, text)
    
    print("Matches found:", matches)  
    
    subject_data = [{"code": match[0], "total_marks": int(match[3]), "status": match[4]} for match in matches]

    json_result = json.dumps(subject_data, indent=2)
    print("Resultant JSON:", json_result)

    return subject_data


@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        subject_data = extract_subject_data(file_path)
        print("Extracted marks data:", subject_data)  
        return jsonify(subject_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
