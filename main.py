import os
import json
import re
import time
import psutil
from functools import wraps
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

# Performance monitoring decorator (REMOVE AFTER TESTING)
def measure_performance(func):
    """Decorator to measure time, memory, and CPU usage"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get process info
        process = psutil.Process(os.getpid())
        
        # Before execution
        start_time = time.perf_counter()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu_percent = process.cpu_percent()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # After execution
        end_time = time.perf_counter()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu_percent = process.cpu_percent()
        
        # Calculate metrics
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"\n{'='*60}")
        print(f"⏱️  PERFORMANCE METRICS FOR {func.__name__.upper()}")
        print(f"{'='*60}")
        print(f"⏰ Execution Time: {execution_time:.4f} seconds")
        print(f"🧠 Memory Usage: {end_memory:.2f} MB (Δ {memory_used:+.2f} MB)")
        print(f"💻 CPU Usage: {end_cpu_percent:.2f}%")
        print(f"📊 Time per page: {execution_time/get_page_count(args[0]) if args else 0:.4f}s")
        
        # Performance assessment
        if execution_time <= 10:
            print(f"✅ PASSED: Execution time within 10s limit")
        else:
            print(f"❌ FAILED: Execution time exceeded 10s limit")
            
        if end_memory <= 200:
            print(f"✅ PASSED: Memory usage within 200MB limit")
        else:
            print(f"❌ FAILED: Memory usage exceeded 200MB limit")
        
        return result
    return wrapper

def get_page_count(pdf_path):
    """Quick page count estimation"""
    try:
        page_count = sum(1 for _ in extract_pages(pdf_path))
        return page_count
    except:
        return 1

# Context manager for timing code sections (REMOVE AFTER TESTING)
class TimeComplexityProfiler:
    """Profile specific code sections"""
    def __init__(self, section_name):
        self.section_name = section_name
        self.start_time = None
        self.process = psutil.Process(os.getpid())
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        print(f"🔍 Starting {self.section_name}...")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        elapsed = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        
        print(f"  ⏱️  {self.section_name}: {elapsed:.4f}s (Δ{memory_delta:+.2f}MB)")

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

@measure_performance  # REMOVE THIS DECORATOR AFTER TESTING
def extract_outline_from_pdf(pdf_path):
    """
    Optimized main function focused on speed and essential functionality.
    Target: <10 seconds for 50-page PDF.
    """
    all_text_elements = []
    
    # Single pass collection with minimal processing
    with TimeComplexityProfiler("PDF Parsing"):  # REMOVE AFTER TESTING
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
    with TimeComplexityProfiler("Font Analysis"):  # REMOVE AFTER TESTING
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
    with TimeComplexityProfiler("Heading Detection"):  # REMOVE AFTER TESTING
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

# TESTING FUNCTIONS (REMOVE AFTER TESTING)
def estimate_complexity(pdf_path):
    """Estimate time complexity based on PDF characteristics"""
    try:
        page_count = 0
        element_count = 0
        char_count = 0
        
        print(f"\n📈 COMPLEXITY ANALYSIS")
        print(f"{'='*40}")
        
        for page_layout in extract_pages(pdf_path):
            page_count += 1
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    element_count += 1
                    char_count += len(element.get_text())
        
        print(f"📄 Pages: {page_count}")
        print(f"📦 Text Elements: {element_count}")
        print(f"🔤 Characters: {char_count}")
        print(f"📊 Elements per Page: {element_count/page_count:.1f}")
        print(f"📊 Characters per Element: {char_count/element_count:.1f}")
        
        # Complexity estimation
        print(f"\n🧮 ESTIMATED COMPLEXITY:")
        print(f"  Time: O(n) where n = {element_count} text elements")
        print(f"  Space: O(k) where k = {element_count} elements stored")
        
        # Performance prediction
        estimated_time = element_count * 0.0001  # Rough estimate
        print(f"  Predicted Time: ~{estimated_time:.2f} seconds")
        
        return {
            'pages': page_count,
            'elements': element_count,
            'characters': char_count,
            'estimated_time': estimated_time
        }
        
    except Exception as e:
        print(f"Error in complexity analysis: {e}")
        return None

def load_test_simulation(pdf_path, iterations=3):
    """Simulate multiple runs to test consistency"""
    print(f"\n🔄 LOAD TEST SIMULATION ({iterations} iterations)")
    print(f"{'='*50}")
    
    times = []
    memories = []
    
    for i in range(iterations):
        process = psutil.Process(os.getpid())
        start_time = time.perf_counter()
        start_memory = process.memory_info().rss / 1024 / 1024
        
        # Run your main function here
        try:
            result = extract_outline_from_pdf(pdf_path)  # Your main function
            
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss / 1024 / 1024
            
            elapsed = end_time - start_time
            memory_used = end_memory
            
            times.append(elapsed)
            memories.append(memory_used)
            
            print(f"  Run {i+1}: {elapsed:.4f}s, {memory_used:.2f}MB")
            
        except Exception as e:
            print(f"  Run {i+1}: FAILED - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_memory = sum(memories) / len(memories)
        
        print(f"\n📊 LOAD TEST RESULTS:")
        print(f"  Average Time: {avg_time:.4f}s")
        print(f"  Min Time: {min_time:.4f}s")
        print(f"  Max Time: {max_time:.4f}s")
        print(f"  Time Variance: {max_time - min_time:.4f}s")
        print(f"  Average Memory: {avg_memory:.2f}MB")
        
        # Consistency check
        variance = max_time - min_time
        if variance < 1.0:  # Less than 1 second variance
            print(f"  ✅ CONSISTENT: Low time variance")
        else:
            print(f"  ⚠️  INCONSISTENT: High time variance")

if __name__ == "__main__":
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

        print(f"\n🧪 TESTING {filename}")  # REMOVE AFTER TESTING
        
        if not os.path.exists(pdf_path):
            print(f"Error: File {pdf_path} does not exist!")
            continue
        
        # TESTING CODE (REMOVE AFTER TESTING)
        estimate_complexity(pdf_path)
            
        try:
            outline_data = extract_outline_from_pdf(pdf_path)

            if outline_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=2, ensure_ascii=False)
                print(f"  ✅ Created '{output_filename}' with {len(outline_data['outline'])} headings")
                
                # OPTIONAL: Load test (REMOVE AFTER TESTING)
                # load_test_simulation(pdf_path, iterations=3)
            else:
                print(f"  ❌ Failed to process '{filename}'")
                
        except Exception as e:
            print(f"  ❌ Error processing '{filename}': {e}")
    
    print("\n🏁 Processing complete!")