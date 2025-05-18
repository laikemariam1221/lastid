def extract_fan_phone_nationality(pdf_path): 
    import fitz  # PyMuPDF
    import re

    doc = fitz.open(pdf_path)
    fan_number = None
    phone_number = None
    nationality_amharic = None
    nationality_english = None
    address_lines = [None]*6  # list to hold 6 address lines
    full_text = ""

    # Regex for FAN and phone
    fan_patterns = [
        r'FAN\s*Number[:\-]?\s*(\d{10,20})',
        r'FAN[:\-]?\s*(\d{10,20})',
        r'Fan\s*No[:\-]?\s*(\d{10,20})',
        r'fan\s*number[:\-]?\s*(\d{10,20})',
        r'(\d{4}\s\d{4}\s\d{4}\s\d{4})'
    ]
    phone_pattern = r'\(?\d{2,4}\)?[-\s]?\d{3}[-\s]?\d{4}'

    for page in doc:
        text = page.get_text("text")
        full_text += text + "\n"

        # Extract FAN number
        for pattern in fan_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fan_number = re.sub(r'\s+', '', match.group(1))
                break

        # Extract phone number
        match_phone = re.search(phone_pattern, text)
        if match_phone:
            phone_number = match_phone.group(0)

    doc.close()

    # Print full extracted text for debugging
    print("========== Full Extracted Text from PDF ==========")
    print(full_text)
    print("===============================================")

    if phone_number and full_text:
        lines = full_text.splitlines()

        phone_line_index = None
        for i, line in enumerate(lines):
            if phone_number in line:
                phone_line_index = i
                break

        # Extract nationality lines above phone number (same as before)
        if phone_line_index is not None and phone_line_index >= 2:
            nationality_amharic = lines[phone_line_index - 2].strip()
            nationality_english = lines[phone_line_index - 1].strip()

        # Extract six address lines BELOW phone number
        if phone_line_index is not None:
            for j in range(6):
                idx = phone_line_index + 1 + j
                if idx < len(lines):
                    address_lines[j] = lines[idx].strip()

    print("Extracted FAN Number:", fan_number)
    print("Extracted Phone Number:", phone_number)
    print("Extracted Nationality (Amharic):", nationality_amharic)
    print("Extracted Nationality (English):", nationality_english)
    for i, addr in enumerate(address_lines, 1):
        print(f"Extracted Address {i}:", addr)

    return (fan_number, phone_number, nationality_amharic, nationality_english, 
            *address_lines)
