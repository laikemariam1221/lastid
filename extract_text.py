import os
from flask import Flask, request, jsonify
import easyocr
import re

app = Flask(__name__)
reader = easyocr.Reader(['en'])  # You can add other languages too, like ['en', 'am']

# Directory where images are stored
IMAGE_DIR = 'output'

@app.route('/extract-expiry', methods=['GET'])
def extract_expiry_date():
    image_name = 'page1_img3.jpeg'  # You can make this dynamic if needed
    image_path = os.path.join(IMAGE_DIR, image_name)

    if not os.path.exists(image_path):
        return jsonify({'error': f'{image_name} not found in {IMAGE_DIR}'}), 404

    # OCR: extract text from image
    print(f"🔍 Extracting text from: {image_path}")
    result = reader.readtext(image_path, detail=0)
    extracted_text = "\n".join(result)
    print("📄 Full Extracted Text:")
    print(extracted_text)

    # Search for expiry date using regex
    pattern = r'(\d{2,4})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{1,2})'
    matches = re.findall(pattern, extracted_text)

    expiry_dates = []
    for match in matches:
        date = "/".join(match)
        expiry_dates.append(date)

    if expiry_dates:
        print("✅ Found possible expiry dates:")
        for date in expiry_dates:
            print(date)
    else:
        print("❌ No expiry date found.")

    return jsonify({
        'image': image_name,
        'extracted_text': extracted_text,
        'possible_expiry_dates': expiry_dates
    })

if __name__ == '__main__':
    app.run(debug=True)
