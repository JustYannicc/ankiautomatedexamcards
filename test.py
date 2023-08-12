import PyPDF2
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import re
import os
import logging
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modify the find_question_boundaries function to not only find boundaries but also return the total number of questions
def find_question_boundaries_and_count(text):
    logging.info("Identifying question boundaries...")
    matches = re.findall(r"\b(\d+)\b(.*?)(\(Total for Question \1 is \d+ marks\))", text, re.DOTALL)
    # Filter out any matches that don't have three elements
    valid_matches = [match for match in matches if len(match) == 3]
    total_questions = len(valid_matches)  # Count of total questions
    return valid_matches, total_questions

def extract_questions_from_pdf(pdf_path, output_dir):
    logging.info("Starting extraction process...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert the entire PDF to images
    logging.info("Converting PDF pages to images...")
    images = convert_from_path(pdf_path)

    next_expected_question_number = 1  # Start with question number 1

    for idx, img in enumerate(images):
        logging.info(f"Processing page {idx + 1}...")
        img_text = pytesseract.image_to_string(img)

        # Limit the search to the leftmost 1/4 of the page
        quarter_width = img.width // 4
        limited_img = img.crop((0, 0, quarter_width, img.height))
        limited_data = pytesseract.image_to_data(limited_img, output_type=pytesseract.Output.DICT)

        # Debugging: Print the detected text from the leftmost 1/4 of the page
        logging.info(f"Detected text in left 1/4: {limited_data['text']}")

        # Extract all question numbers from the leftmost 1/4 of the page
        question_starts = [i for i, text in enumerate(limited_data['text']) if text.strip() == str(next_expected_question_number)]
        
        logging.info(f"Detected starts for questions: {question_starts}")  # Debugging
        
        if not question_starts:  # If the expected question number is not found, move to the next page
            continue

        for i, start_index in enumerate(question_starts):
            x_start, y_start = limited_data['left'][start_index], limited_data['top'][start_index]
            
            # Determine the end y-coordinate based on the next question start or the bottom of the image
            if i < len(question_starts) - 1:
                y_end = limited_data['top'][question_starts[i + 1]]
            else:
                y_end = img.height
            
            # Extract the region for the current question
            x_end = img.width  # Capture till the end of the width
            question_img = img.crop((x_start - 10, y_start - 40, x_end, y_end))
            
            path = os.path.join(output_dir, f"question {next_expected_question_number}.png")
            question_img.save(path)
            logging.info(f"Saved question {next_expected_question_number} to {path}")

            next_expected_question_number += 1  # Prepare for the next question

# Usage:
pdf_path = 'exampaper.pdf'
output_dir = 'images'
extract_questions_from_pdf(pdf_path, output_dir)