from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from extract_photo import extract_profile_photo_with_face_detection
from extract_text_data import extract_text_data
from extract_fan_number import extract_fan_number_from_text  # FAN number extractor

app = Flask(__name__)

# Enabling CORS for all origins (only for development purposes, refine for production)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    pdf_file = request.files['pdf']
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(pdf_path)

    # Extract profile photo
    output_image_path = os.path.join(OUTPUT_FOLDER, 'profile_photo')
    success, image_filename = extract_profile_photo_with_face_detection(pdf_path, output_image_path)

    # Extract text data
    text_data = extract_text_data(pdf_path)

    # Extract FAN number
    fan_number = extract_fan_number_from_text(pdf_path)  # FAN number extraction

    response_data = {
        'image_url': f"{OUTPUT_FOLDER}/{image_filename}" if success else None,
        'text_data': text_data,
        'fan_number': fan_number  # Include FAN number in response
    }

    return jsonify(response_data)

@app.route('/output/<path:filename>')
def get_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
