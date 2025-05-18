import fitz  # PyMuPDF
import cv2
import numpy as np
import os

def detect_face(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    return len(faces) > 0, img_np

def extract_profile_photo_with_face_detection(pdf_path, output_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        for i, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]

            has_face, img_np = detect_face(image_bytes)
            if has_face:
                filename = f"profile_photo.{ext}"
                full_path = f"{output_path}.{ext}"
                cv2.imwrite(full_path, img_np)
                return True, filename

    return False, None
