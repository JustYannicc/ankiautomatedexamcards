import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from fuzzywuzzy import fuzz
import PyPDF2
from pdf2image import convert_from_path

def extract_questions_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        # Initialize PDF reader
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        
        # Extract text from all pages of the PDF
        text = ''
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        
        # Search for questions using regular expressions
        start_pattern = r'\b(\d+)\b(?=\sFind)'
        end_pattern = r'Total for Question (\d+) is (\d+) marks'
        
        questions = []
        for start_match, end_match in zip(re.finditer(start_pattern, text), re.finditer(end_pattern, text)):
            question_text = text[start_match.start():end_match.end()]
            questions.append(question_text)
        
        return questions


def get_text_coordinates(pdf_path, search_text, threshold=90):
    for page_layout in extract_pages(pdf_path, laparams=LAParams()):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                current_text = element.get_text().strip()
                lines = current_text.split("\n")
                for line in lines:
                    # Using fuzz partial ratio to get a score for the match
                    if fuzz.partial_ratio(line, search_text) > threshold:
                        return (element.x0, element.y0, element.x1, element.y1)
    return None

def extract_question_from_pdf(pdf_path, coords, output_image_path):
    """
    Extracts a section of the PDF using the provided coordinates and saves it as an image.

    Parameters:
    - pdf_path (str): Path to the PDF file.
    - coords (tuple): Bounding box coordinates in the format (x0, y0, x1, y1).
    - output_image_path (str): Path to save the extracted image.
    """

    # Convert the PDF page to an image
    dpi_val = 300
    images = convert_from_path(pdf_path, dpi=dpi_val)
    page_image = images[0]

    # Compute the scaling factor
    pdf_width_points = 595.0  # typical width for A4 in points
    pdf_height_points = 842.0  # typical height for A4 in points
    scale_x = page_image.width / pdf_width_points
    scale_y = page_image.height / pdf_height_points

    # Adjust the coordinates using the scaling factor
    x0, y0, x1, y1 = coords
    x0_scaled, x1_scaled = x0 * scale_x, x1 * scale_x
    y0_scaled, y1_scaled = y0 * scale_y, y1 * scale_y

    # Crop the image using the adjusted coordinates
    cropped_image = page_image.crop((x0_scaled, y0_scaled, x1_scaled, y1_scaled))

    # Save the cropped image
    cropped_image.save(output_image_path, "PNG")

# Example usage:
pdf_path = "exampaper.pdf"
coords = (70.87010000000001, 723.8829999999999, 374.31409999999994, 736.135)  # Example coordinates
output_image_path = "question_image.png"
extract_question_from_pdf(pdf_path, coords, output_image_path)