import fitz  # PyMuPDF
import re

def split_name(full_name):
    parts = full_name.split()
    return {
        "first_name": parts[0] if len(parts) > 0 else None,
        "middle_name": parts[1] if len(parts) > 1 else None,
        "last_name": parts[2] if len(parts) > 2 else None,
    }

def extract_text_data(pdf_path):
    doc = fitz.open(pdf_path)

    full_name_block = None
    dob_english = None
    sex_value = None
    expiry_date = None  # NEW

    text = ""

    for page in doc:
        text += page.get_text()

        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # sort top to bottom, left to right

        for i, block in enumerate(blocks):
            x0, y0, x1, y1, block_text, *_ = block
            block_text = block_text.strip()

            # Extract full name block
            if "ሙሉ ስም" in block_text or "First, Middle, Surname" in block_text:
                if i + 1 < len(blocks):
                    full_name_block = blocks[i + 1][4].strip()

            # Extract English DOB from blocks
            if "የትውልድ ቀን" in block_text or "Date of Birth" in block_text:
                if i + 2 < len(blocks):
                    dob_english = blocks[i + 2][4].strip()

            # Extract SEX value from block below the label
            if "ፆታ" in block_text or "SEX" in block_text.upper():
                sex_x0, sex_y0 = x0, y0
                for j in range(i + 1, len(blocks)):
                    next_x0, next_y0, _, _, next_text, *_ = blocks[j]
                    if abs(next_x0 - sex_x0) < 50 and 0 < (next_y0 - sex_y0) < 100:
                        possible_sex = next_text.strip()
                        if re.search(r'(ሴት|ወንድ|Female|Male)', possible_sex, re.IGNORECASE):
                            sex_value = possible_sex
                            break

            # Extract Date of Expiry block
            if "Date of Expiry" in block_text or "Date of Expiration" in block_text:
                if i + 1 < len(blocks):
                    expiry_date_candidate = blocks[i + 1][4].strip()
                    # Basic check: looks like a date
                    if re.search(r'\d{2,4}[-/]\d{1,2}[-/]\d{1,4}', expiry_date_candidate):
                        expiry_date = expiry_date_candidate

    doc.close()

    # Fallback from full text (not block) if not found
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    amharic_name_fallback = next((line for line in lines if re.match(r'^[\u1200-\u137F\s]{5,}$', line)), None)
    english_name_fallback = next((line for line in lines if re.match(r'^[A-Za-z\s]{5,}$', line)), None)

    # Extract full names from blocks or fallback
    amharic_name = None
    english_name = None

    if full_name_block:
        parts = full_name_block.split()
        amharic_parts = [p for p in parts if re.match(r'^[\u1200-\u137F]+$', p)]
        english_parts = [p for p in parts if re.match(r'^[A-Za-z]+$', p)]
        amharic_name = " ".join(amharic_parts) if amharic_parts else amharic_name_fallback
        english_name = " ".join(english_parts) if english_parts else english_name_fallback
    else:
        amharic_name = amharic_name_fallback
        english_name = english_name_fallback

    # Split the English DOB into two dates if they exist
    dob_split = None
    if dob_english:
        dob_split = dob_english.split("\n")
        if len(dob_split) == 2:
            dob_english = {
                "date_1": dob_split[0].strip(),
                "date_2": dob_split[1].strip(),
            }

    data = {
        "full_name_amharic": amharic_name,
        "full_name_english": english_name,
        "date_of_birth": dob_english,
        "sex": sex_value,
        "date_of_expiry": expiry_date  # NEW
    }

    # Split names into parts
    if data['full_name_amharic']:
        data.update({f"amharic_{k}": v for k, v in split_name(data['full_name_amharic']).items()})
    if data['full_name_english']:
        data.update({f"english_{k}": v for k, v in split_name(data['full_name_english']).items()})

    return data
