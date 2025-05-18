import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import fitz  # PyMuPDF
import re
import easyocr

# External imports assumed to be defined elsewhere
from extract_photo import extract_profile_photo_with_face_detection
from extract_text_data import extract_text_data
from extract_fan_number import extract_fan_phone_nationality

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])  # Add 'am' for Amharic if needed


def extract_all_images(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    image_filenames = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page{page_index+1}_img{img_index+1}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            image_filenames.append(image_filename)
    return image_filenames


def extract_text_with_easyocr(image_path):
    try:
        result = reader.readtext(image_path, detail=0)
        text = "\n".join(result)
        return text.strip()
    except Exception as e:
        logging.error(f"EasyOCR error on {image_path}: {e}")
        return ""


def extract_expiration_dates(text):
    try:
        date_pattern = r'(\d{4})[\/\-\.]+([A-Za-z]{2,}|\d{1,2})[\/\-\.]+(\d{1,2})'
        if 'date of expiry' in text.lower():
            matches = re.findall(date_pattern, text)
            expiry_dates = [f"{y}/{m}/{d}" for y, m, d in matches]
            return expiry_dates
        return []
    except Exception as e:
        logging.error(f"Error extracting expiry dates: {e}")
        return []

def extract_fin_from_text(text):
    try:
        # Look for pattern like "FIN" followed by digits and optional spaces
        match = re.search(r'FIN\s*([\d\s]+)', text, re.IGNORECASE)
        if match:
            raw_digits = ''.join(match.group(1).split())  # Remove spaces
            if len(raw_digits) >= 12:
                # Only keep the first 12 digits
                fin_cleaned = raw_digits[:12]
                # Format as XXXX XXXX XXXX
                return f"{fin_cleaned[:4]} {fin_cleaned[4:8]} {fin_cleaned[8:12]}"
    except Exception as e:
        logging.error(f"Error extracting FIN: {e}")
    return None

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    pdf_file = request.files['pdf']
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(pdf_path)

    logging.debug(f"Received PDF file: {pdf_file.filename}")
    logging.debug(f"PDF saved at: {pdf_path}")

    # Extract profile photo
    output_image_path = os.path.join(OUTPUT_FOLDER, 'profile_photo')
    success, image_filename = extract_profile_photo_with_face_detection(pdf_path, output_image_path)

    # Extract all images from the PDF
    all_image_filenames = extract_all_images(pdf_path, OUTPUT_FOLDER)

    # Extract text from all images using EasyOCR
    all_extracted_texts = {}
    expiry_dates = []
    fin_number = None

    for image_filename in all_image_filenames:
        image_path = os.path.join(OUTPUT_FOLDER, image_filename)
        text = extract_text_with_easyocr(image_path)
        all_extracted_texts[image_filename] = text
        print(f"📝 Extracted text from {image_filename}:\n{text}\n")

        # Extract FIN number if found (only once)
        if fin_number is None:
            fin_number = extract_fin_from_text(text)

        expiry_dates += extract_expiration_dates(text)

    # Remove duplicates in expiry dates
    expiry_dates = list(set(expiry_dates))

    # Extract text from third image (backward compatibility)
    extracted_text = all_extracted_texts.get(all_image_filenames[2], "") if len(all_image_filenames) >= 3 else ""

    # Other extractions
    text_data = extract_text_data(pdf_path)

    fan_number, phone_number, nationality_amharic, nationality_english, \
    address_1, address_2, address_3, address_4, address_5, address_6 = extract_fan_phone_nationality(pdf_path)

    # Print formatted output in terminal
    if fin_number:
        print("\n===============================================")
        print(f"Extracted FIN Number: {fin_number}")
        print(f"Extracted Phone Number: {phone_number}")
        print(f"Extracted Nationality (Amharic): {nationality_amharic}")
        print(f"Extracted Nationality (English): {nationality_english}")
        print(f"Extracted Address 1: {address_1}")
        print(f"Extracted Address 2: {address_2}")
        print(f"Extracted Address 3: {address_3}")
        print(f"Extracted Address 4: {address_4}")
        print(f"Extracted Address 5: {address_5}")
        print(f"Extracted Address 6: {address_6}")
        print("===============================================\n")

    # Build and return the JSON response
    response_data = {
        'file_name': pdf_file.filename,
        'image_url': f"{OUTPUT_FOLDER}/{image_filename}" if success else None,
        'all_images': [f"{OUTPUT_FOLDER}/{fname}" for fname in all_image_filenames],
        'extracted_text_from_third_image': extracted_text,
        'all_extracted_texts': all_extracted_texts,
        'possible_expiry_dates': expiry_dates,
        'text_data': text_data,
        'fan_number': fan_number,
        'phone_number': phone_number,
        'nationality_amharic': nationality_amharic,
        'nationality_english': nationality_english,
        'address_1': address_1,
        'address_2': address_2,
        'address_3': address_3,
        'address_4': address_4,
        'address_5': address_5,
        'address_6': address_6,
        'fin_number': fin_number,
    }

    return jsonify(response_data)


@app.route('/output/<path:filename>')
def get_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
