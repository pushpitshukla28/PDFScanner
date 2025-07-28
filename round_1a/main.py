import os
import json
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

def get_text_properties(text_element):
    """
    Efficiently extracts font properties with minimal overhead.
    Optimized for speed over detailed analysis.
    """
    font_sizes = []
    font_names = []
    
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
    
    # Fast bold detection - check first few font names
    is_bold = False
    if font_names:
        # Check only first 3 font names for efficiency
        sample_names = font_names[:3]
        is_bold = any('bold' in name.lower() or 'black' in name.lower() 
                     for name in sample_names)
    
    return avg_font_size, is_bold

def is_potential_heading(text_content, font_size, is_bold, avg_doc_font_size):
    """
    Streamlined heading detection with essential rules only.
    Optimized for speed and accuracy.
    """
    if not text_content or len(text_content.strip()) == 0:
        return False

    # Quick preprocessing
    text_content = text_content.strip()
    
    # Fast exclusion rules
    if len(text_content) > 150:
        return False
        
    if text_content.endswith('.') and len(text_content) > 40:
        return False

    # Core detection rules (optimized for speed)
    
    # Rule 1: Font size based detection
    font_ratio = font_size / avg_doc_font_size if avg_doc_font_size > 0 else 1
    if font_size > 14 or (font_size > 11 and is_bold) or font_ratio > 1.3:
        return True
        
    # Rule 2: All caps (limited check for performance)
    if text_content.isupper() and 5 < len(text_content) < 80:
        return True
        
    # Rule 3: Numbered sections (fast regex)
    if re.match(r'^\s*(\d+(\.\d+)*|[A-Z]\.|[IVXLCDM]+\.)\s+', text_content):
        return True
    
    # Rule 4: Multilingual patterns (essential only)
    # Japanese/Chinese chapter patterns
    if re.match(r'^第[一二三四五六七八九十\d]+[章節条項节条款]', text_content):
        return True
    
    # Rule 5: Bold text with reasonable size
    if is_bold and font_ratio > 1.1 and len(text_content) < 100:
        return True

    return False

def classify_heading_level(font_size, unique_font_sizes):
    """
    Fast heading level classification using simple thresholds.
    """
    if not unique_font_sizes:
        return "H3"

    # Simple size-based classification for speed
    largest = unique_font_sizes[0]
    second_largest = unique_font_sizes[1] if len(unique_font_sizes) > 1 else largest
    
    if font_size >= largest * 0.95:
        return "H1"
    elif font_size >= second_largest * 0.9:
        return "H2"
    else:
        return "H3"

def extract_outline_from_pdf(pdf_path):
    """
    Optimized main function focused on speed and essential functionality.
    Target: <10 seconds for 50-page PDF.
    """
    all_text_elements = []
    
    # Single pass collection with minimal processing
    try:
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text_content = element.get_text().strip()
                    if text_content and len(text_content) < 500:  # Pre-filter very long text
                        avg_font_size, is_bold = get_text_properties(element)
                        if avg_font_size > 0:  # Only add elements with valid font size
                            all_text_elements.append({
                                'text': text_content,
                                'font_size': avg_font_size,
                                'is_bold': is_bold,
                                'page_number': page_layout.pageid
                            })
    except Exception as e:
        print(f"Error during PDF parsing: {e}")
        return None

    if not all_text_elements:
        return {"title": "Empty Document", "outline": []}

    # Fast font size analysis
    all_font_sizes = [el['font_size'] for el in all_text_elements]
    avg_doc_font_size = sum(all_font_sizes) / len(all_font_sizes)
    unique_font_sizes = sorted(list(set(all_font_sizes)), reverse=True)
    
    # Quick title detection - first large text on page 1
    document_title = "Untitled Document"
    title_threshold = unique_font_sizes[0] * 0.9 if unique_font_sizes else 16
    
    for item in all_text_elements:
        if (item['page_number'] == 1 and 
            item['font_size'] >= title_threshold and 
            len(item['text']) < 200):
            document_title = item['text']
            break

    # Fast heading detection
    outline = []
    for item in all_text_elements:
        if item['text'] != document_title:  # Don't include title as heading
            if is_potential_heading(item['text'], item['font_size'], 
                                  item['is_bold'], avg_doc_font_size):
                level = classify_heading_level(item['font_size'], unique_font_sizes)
                outline.append({
                    "level": level,
                    "text": item['text'],
                    "page": item['page_number']
                })

    return {
        "title": document_title,
        "outline": outline
    }

if __name__ == "__main__":  # Fixed this line
    input_dir = "/app/input"
    output_dir = "/app/output"

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist!")
        exit(1)
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = os.listdir(input_dir)
    pdf_files = [f for f in input_files if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in input directory!")
        exit(0)

    print(f"Processing {len(pdf_files)} PDF files...")
    
    for filename in pdf_files:
        pdf_path = os.path.join(input_dir, filename)
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing '{filename}'...")
        
        if not os.path.exists(pdf_path):
            print(f"Error: File {pdf_path} does not exist!")
            continue
            
        try:
            outline_data = extract_outline_from_pdf(pdf_path)

            if outline_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=2, ensure_ascii=False)
                print(f"  -> Created '{output_filename}' with {len(outline_data['outline'])} headings")
            else:
                print(f"  -> Failed to process '{filename}'")
                
        except Exception as e:
            print(f"  -> Error processing '{filename}': {e}")
    
    print("Processing complete!")