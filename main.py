import os
import json
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

def get_text_properties(text_element):
    """
    Extracts the average font size and bold status from a text element.
    This is a heuristic (a rule-based guess).
    """
    font_sizes = []
    font_names = []
    
    # Iterate through each character in the text element to check its properties
    for text_line in text_element:
        if hasattr(text_line, '_objs'):
            for char in text_line._objs:
                if isinstance(char, LTChar):
                    font_sizes.append(char.height)
                    if hasattr(char, 'fontname'):
                        font_names.append(char.fontname)

    if not font_sizes:
        return 0, False

    avg_font_size = sum(font_sizes) / len(font_sizes)
    # A common way to guess if text is bold is by checking the font name
    is_bold = any('bold' in name.lower() for name in font_names)
    
    return avg_font_size, is_bold

def is_potential_heading(text_line, font_size, is_bold, page_width):
    """
    Uses a set of rules to guess if a line of text is a heading.
    **This is the main section you will need to test and refine.**
    """
    text_content = text_line.get_text().strip()
    
    if not text_content:
        return False

    # Rule 1: Too long lines are probably not headings
    if len(text_content) > 150:
        return False
        
    # Rule 2: Lines ending with a period are often body text
    if text_content.endswith('.'):
        return False

    # Rule 3: Font size is a strong indicator
    if font_size > 14 or (font_size > 11 and is_bold):
        return True
        
    # Rule 4: All-caps text is often a heading
    if text_content.isupper() and len(text_content) > 5:
        return True
        
    # Rule 5: Lines with common heading numbering (e.g., "1.2", "A.", "IV.")
    if re.match(r'^\s*(\d+(\.\d+)*|[A-Z]\.|[IVXLCDM]+\.)\s+', text_content):
        return True

    return False

def classify_heading_level(font_size, unique_font_sizes):
    """
    Classifies a heading as H1, H2, or H3 based on its font size
    relative to other font sizes in the document.
    **You may need to adjust these thresholds.**
    """
    if not unique_font_sizes:
        return "H3" # Default if no context

    # The largest font is likely H1
    if font_size >= unique_font_sizes[0] * 0.9:
        return "H1"
    # The next largest is H2
    elif len(unique_font_sizes) > 1 and font_size >= unique_font_sizes[1] * 0.9:
        return "H2"
    # Otherwise, it's likely H3
    else:
        return "H3"

def extract_outline_from_pdf(pdf_path):
    """
    Main function to extract a structured outline from a PDF.
    """
    all_text_elements = []
    
    print(f"Starting PDF processing for: {pdf_path}")
    
    # --- Pass 1: Collect all text elements and their properties ---
    try:
        for page_layout in extract_pages(pdf_path):
            print(f"Processing page {page_layout.pageid}")
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    avg_font_size, is_bold = get_text_properties(element)
                    text_content = element.get_text().strip()
                    if text_content:  # Only add non-empty text
                        all_text_elements.append({
                            'element': element,
                            'page_number': page_layout.pageid,
                            'font_size': avg_font_size,
                            'is_bold': is_bold,
                            'page_width': page_layout.width,
                            'text': text_content
                        })
    except Exception as e:
        print(f"Error during PDF parsing with pdfminer.six: {e}")
        return None

    print(f"Found {len(all_text_elements)} text elements")

    # Get a sorted list of unique font sizes found in the document, largest first
    all_font_sizes = [el['font_size'] for el in all_text_elements if el['font_size'] > 0]
    unique_font_sizes = sorted(list(set(all_font_sizes)), reverse=True)
    
    print(f"Unique font sizes: {unique_font_sizes}")

    document_title = "Untitled Document"
    outline = []
    found_title = False

    # --- Pass 2: Identify and classify the title and headings ---
    for item in all_text_elements:
        text_element = item['element']
        text_content = item['text']

        if not text_content:
            continue
            
        font_size = item['font_size']
        is_bold = item['is_bold']

        # Heuristic for Title: The first, largest piece of text on the first page
        if not found_title and item['page_number'] == 1 and font_size >= (unique_font_sizes[0] if unique_font_sizes else 20):
            document_title = text_content
            found_title = True
            print(f"Found title: {document_title}")
            continue # Don't also classify the title as a heading

        # Use our rules to check if it's a heading
        if is_potential_heading(text_element, font_size, is_bold, item['page_width']):
            level = classify_heading_level(font_size, unique_font_sizes)
            outline.append({
                "level": level,
                "text": text_content,
                "page": item['page_number']
            })
            print(f"Found heading ({level}): {text_content}")

    print(f"Extracted {len(outline)} headings")

    # Final JSON structure
    return {
        "title": document_title,
        "outline": outline
    }

if __name__ == "__main__":
    # These paths are set for the Docker environment as per hackathon rules
    input_dir = "/app/input"
    output_dir = "/app/output"

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Check if directories exist
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist!")
        exit(1)
        
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)

    # List files in input directory
    input_files = os.listdir(input_dir)
    print(f"Files in input directory: {input_files}")
    
    pdf_files = [f for f in input_files if f.lower().endswith(".pdf")]
    print(f"PDF files found: {pdf_files}")
    
    if not pdf_files:
        print("No PDF files found in input directory!")
        exit(0)

    # Process all PDF files found in the input directory
    for filename in pdf_files:
        pdf_path = os.path.join(input_dir, filename)
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(output_dir, output_filename)

        print(f"\nProcessing '{filename}'...")
        print(f"Full path: {pdf_path}")
        
        # Check if file exists and is readable
        if not os.path.exists(pdf_path):
            print(f"Error: File {pdf_path} does not exist!")
            continue
            
        try:
            outline_data = extract_outline_from_pdf(pdf_path)

            if outline_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=4, ensure_ascii=False)
                print(f"  -> Successfully created '{output_filename}'")
                print(f"  -> Output saved to: {output_path}")
            else:
                print(f"  -> Failed to process '{filename}'")
        except Exception as e:
            print(f"  -> Error processing '{filename}': {e}")
    
    print("\nProcessing complete!")