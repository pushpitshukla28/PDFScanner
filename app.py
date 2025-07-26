#!/usr/bin/env python3
"""
Polished Intelligent Document Analyzer for Adobe Hackathon
Integrates and outputs separate results for Round 1A and Round 1B.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

# For AI-based semantic analysis
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# For robust PDF parsing
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar

class PolishedAnalyzer:
    """
    A class that integrates structural and semantic analysis for a complete solution.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initializes the analyzer and loads the AI model."""
        print("Initializing Polished Analyzer...")
        self.model = SentenceTransformer(model_name)
        print("AI model loaded successfully.")

    def _get_text_properties(self, text_element: LTTextContainer):
        font_sizes, font_names = [], []
        for text_line in text_element:
            if hasattr(text_line, '_objs'):
                for char in text_line._objs:
                    if isinstance(char, LTChar):
                        font_sizes.append(char.height)
                        if hasattr(char, 'fontname'): font_names.append(char.fontname)
        if not font_sizes: return 0, False
        avg_font_size = sum(font_sizes) / len(font_sizes)
        is_bold = any('bold' in name.lower() for name in font_names)
        return avg_font_size, is_bold

    def extract_outline_data(self, pdf_path: str) -> Dict[str, Any]:
        """
        Performs Round 1A: Extracts title and H1/H2/H3 headings.
        """
        all_text_elements = []
        try:
            for page_layout in extract_pages(pdf_path):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text = element.get_text().strip()
                        if text:
                            avg_font_size, is_bold = self._get_text_properties(element)
                            all_text_elements.append({'text': text, 'font_size': avg_font_size, 'is_bold': is_bold, 'page': page_layout.pageid})
        except Exception as e:
            print(f"  -> WARNING (1A): Could not parse PDF for outline. {e}")
            return {"title": "Parsing Error", "outline": []}
        
        if not all_text_elements: return {"title": "No Text Found", "outline": []}

        page1_elements = [el for el in all_text_elements if el['page'] == 1]
        document_title = max(page1_elements, key=lambda x: x['font_size'])['text'] if page1_elements else "Untitled Document"

        outline = []
        unique_font_sizes = sorted(list(set(el['font_size'] for el in all_text_elements)), reverse=True)
        body_font_size_threshold = (sum(unique_font_sizes) / len(unique_font_sizes)) * 1.1 if unique_font_sizes else 10

        for el in all_text_elements:
            if el['font_size'] > body_font_size_threshold and len(el['text']) < 150 and not el['text'].endswith('.'):
                if el['text'] == document_title: continue
                level = "H3"
                if len(unique_font_sizes) > 1:
                    if el['font_size'] >= unique_font_sizes[0] * 0.9: level = "H1"
                    elif el['font_size'] >= unique_font_sizes[1] * 0.9: level = "H2"
                outline.append({"level": level, "text": el['text'], "page": el['page']})
        
        seen = set()
        unique_outline = [x for x in outline if not (x['text'] in seen or seen.add(x['text']))]
        return {"title": document_title, "outline": sorted(unique_outline, key=lambda x: x['page'])}

    def _create_sections_from_outline(self, full_text: str, outline: List[Dict]) -> List[Dict]:
        if not outline:
            return [{'title': 'Full Document', 'content': full_text, 'page': 1}]
        sections = []
        sorted_outline = sorted(outline, key=lambda x: x['page'])
        for i, heading_info in enumerate(sorted_outline):
            heading_text = heading_info['text']
            start_index = full_text.find(heading_text)
            if start_index == -1: continue
            end_index = len(full_text)
            if i + 1 < len(sorted_outline):
                next_heading_text = sorted_outline[i+1]['text']
                end_index = full_text.find(next_heading_text, start_index)
                if end_index == -1: end_index = len(full_text)
            content = full_text[start_index + len(heading_text):end_index].strip()
            if content:
                sections.append({'title': heading_text, 'content': content, 'page': heading_info['page']})
        return sections

    def _get_refined_summary(self, query: str, content: str, num_sentences: int = 2) -> str:
        sentences = [s.strip() for s in content.replace('\n', ' ').split('.') if len(s.strip()) > 10]
        if not sentences: return content[:250] + "..."
        sentence_embeddings = self.model.encode(sentences)
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, sentence_embeddings)[0]
        top_sentence_indices = similarities.argsort()[-num_sentences:][::-1]
        top_sentence_indices.sort()
        summary = " ".join([sentences[i] for i in top_sentence_indices])
        return summary

    def analyze_for_persona(self, pdf_path: str, outline_data: Dict, persona: str, job_description: str) -> Dict[str, Any]:
        """Performs Round 1B analysis using a pre-computed outline."""
        ai_query = f"As a {persona}, I need to {job_description}"
        full_text = extract_text(pdf_path)
        sections = self._create_sections_from_outline(full_text, outline_data['outline'])
        if not sections: return None

        analyzed_sections = []
        for section in sections:
            if len(section['content']) < 50: continue
            section_embedding = self.model.encode([section['content']])
            query_embedding = self.model.encode([ai_query])
            relevance_score = cosine_similarity(query_embedding, section_embedding)[0][0]
            if relevance_score > 0.2:
                refined_summary = self._get_refined_summary(ai_query, section['content'])
                analyzed_sections.append({
                    'document': os.path.basename(pdf_path),
                    'page_number': section['page'],
                    'section_title': section['title'],
                    'relevance_score': float(relevance_score),
                    'refined_text': refined_summary
                })
        
        analyzed_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        result = {
            'metadata': {'input_documents': [os.path.basename(pdf_path)], 'persona': persona, 'job_to_be_done': job_description, 'processing_timestamp': datetime.now().isoformat()},
            'extracted_sections': []
        }
        for rank, section in enumerate(analyzed_sections):
            result['extracted_sections'].append({
                'document': section['document'], 'page_number': section['page_number'],
                'section_title': section['section_title'], 'importance_rank': rank + 1,
                'refined_text': section['refined_text']
            })
        return result

def run_hackathon_polished():
    """Main execution function for the Docker container."""
    input_dir = "/app/input"
    output_dir = "/app/output"

    if not os.path.exists(input_dir):
        print(f"FATAL: Input directory {input_dir} not found!")
        return

    pdf_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    persona_file = os.path.join(input_dir, 'persona.json')

    if not pdf_files: print("FATAL: No PDF files found."); return
    if not os.path.exists(persona_file): print("FATAL: persona.json not found."); return
        
    with open(persona_file, 'r', encoding='utf-8') as f:
        persona_info = json.load(f)

    analyzer = PolishedAnalyzer()
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for pdf_path in pdf_files:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"\n--- Processing {os.path.basename(pdf_path)} ---")

        # --- Run and Save Round 1A Result ---
        print("  -> Running Round 1A: Outline Extraction...")
        outline_data = analyzer.extract_outline_data(pdf_path)
        if outline_data:
            output_1a_path = os.path.join(output_dir, f'{base_name}_outline.json')
            with open(output_1a_path, 'w', encoding='utf-8') as f:
                json.dump(outline_data, f, indent=2)
            print(f"     ✅ Success! Saved 1A results to {os.path.basename(output_1a_path)}")

        # --- Run and Save Round 1B Result ---
        print("  -> Running Round 1B: Persona Intelligence Analysis...")
        # We pass the outline_data we just generated to the 1B function
        persona_result = analyzer.analyze_for_persona(
            pdf_path=pdf_path,
            outline_data=outline_data,
            persona=persona_info['persona'],
            job_description=persona_info['job_to_be_done']
        )
        if persona_result:
            output_1b_path = os.path.join(output_dir, f'{base_name}_analysis.json')
            with open(output_1b_path, 'w', encoding='utf-8') as f:
                json.dump(persona_result, f, indent=2)
            print(f"     ✅ Success! Saved 1B results to {os.path.basename(output_1b_path)}")

if __name__ == '__main__':
    run_hackathon_polished()
