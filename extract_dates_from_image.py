import pytesseract
import cv2
import re
from PIL import Image

def extract_dates_from_image(image_path):
    # Load image using OpenCV
    image = cv2.imread(image_path)

    # Preprocess the image (convert to grayscale)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Optional: Thresholding to improve OCR accuracy
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR extraction
    text = pytesseract.image_to_string(thresh)

    # Debugging print
    print("OCR Output:\n", text)

    # Regex to match different date formats
    date_pattern = r'(\d{4}\s*/\s*\d{1,2}\s*/\s*\d{1,2})|(\d{4}\s*/\s*[a-zA-Z]+\s*/\s*\d{1,2})'
    matches = re.findall(date_pattern, text)

    # Flatten the matches and clean up
    extracted_dates = [m[0] if m[0] else m[1] for m in matches]

    return extracted_dates
