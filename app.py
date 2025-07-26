#!/usr/bin/env python3
"""
Intelligent Document Analyzer for Adobe Hackathon Round 1B
Analyzes PDF documents using a semantic AI model (Sentence-BERT).
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

# For AI-based semantic analysis
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# For robust PDF parsing to identify sections
from pdfminer.high_level import extract_text

class IntelligentDocumentAnalyzer:
    """
    A class that encapsulates the logic for document analysis using an AI model.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initializes the analyzer and loads the AI model."""
        print("Initializing Analyzer for Round 1B...")
        # This model is small, fast, runs completely offline on a CPU,
        # and is excellent at understanding the meaning of text.
        self.model = SentenceTransformer(model_name)
        print("AI model loaded successfully.")

    def segment_text_into_chunks(self, full_text: str) -> List[str]:
        """
        Breaks the full text of a document into meaningful chunks (e.g., paragraphs).
        This is a simple but effective way to create sections for analysis.
        """
        paragraphs = full_text.split('\n\n')
        # Filter out very short paragraphs that are unlikely to contain meaningful content
        return [p.strip() for p in paragraphs if len(p.strip()) > 100]

    def analyze_documents_for_persona(self, pdf_paths: List[str], persona: str, job_description: str) -> Dict[str, Any]:
        """
        Main analysis function for Round 1B using the AI model.
        """
        print("\nStarting AI-powered analysis...")
        print(f"  -> Persona: {persona}")
        print(f"  -> Job: {job_description}")
        
        # The AI query is a combination of the persona and their job for better context
        ai_query = f"As a {persona}, I need to {job_description}"
        all_sections = []

        for pdf_path in pdf_paths:
            print(f"  -> Processing: {os.path.basename(pdf_path)}")
            
            try:
                full_text = extract_text(pdf_path)
                sections = self.segment_text_into_chunks(full_text)
                
                if not sections:
                    print(f"     Warning: No meaningful text sections found in {os.path.basename(pdf_path)}")
                    continue

                # Convert the AI query and all text sections into numerical embeddings
                query_embedding = self.model.encode([ai_query])
                section_embeddings = self.model.encode(sections)
                
                # Calculate the cosine similarity between the query and each section
                similarities = cosine_similarity(query_embedding, section_embeddings)[0]

                for i, section_text in enumerate(sections):
                    relevance_score = float(similarities[i])
                    if relevance_score > 0.25:  # Relevance threshold to filter out noise
                        all_sections.append({
                            'document': os.path.basename(pdf_path),
                            'content': section_text,
                            'relevance_score': relevance_score
                        })
            except Exception as e:
                print(f"     ERROR: Failed to process {os.path.basename(pdf_path)}. Reason: {e}")

        # Sort all found sections from all documents by their relevance score
        all_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Prepare the final output in the hackathon's required JSON format
        result = {
            'metadata': {
                'input_documents': [os.path.basename(p) for p in pdf_paths],
                'persona': persona,
                'job_to_be_done': job_description,
                'processing_timestamp': datetime.now().isoformat()
            },
            'extracted_sections': []
        }

        for rank, section in enumerate(all_sections):
            # Create an "extractive summary" by finding the most relevant sentence in the section
            sentences = [s.strip() for s in section['content'].replace("\n", " ").split('.') if s]
            best_sentence = ""
            if sentences:
                sentence_embeddings = self.model.encode(sentences)
                sentence_similarities = cosine_similarity(self.model.encode([ai_query]), sentence_embeddings)[0]
                best_sentence = sentences[sentence_similarities.argmax()]

            result['extracted_sections'].append({
                'document': section['document'],
                'page_number': "N/A", # Page number is harder to get without layout analysis
                'section_title': f"Relevant Section {rank + 1}",
                'importance_rank': rank + 1,
                'refined_text': best_sentence
            })

        print(f"\nAnalysis complete. Found {len(result['extracted_sections'])} relevant sections.")
        return result

def run_hackathon_1b():
    """Main execution function for the Docker container for Round 1B."""
    input_dir = "/app/input"
    output_dir = "/app/output"

    if not os.path.exists(input_dir):
        print(f"FATAL: Input directory {input_dir} not found!")
        return

    pdf_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    persona_file = os.path.join(input_dir, 'persona.json')

    if not pdf_files:
        print("FATAL: No PDF files found in /app/input.")
        return

    if not os.path.exists(persona_file):
        print("FATAL: persona.json not found in /app/input. Cannot run Round 1B.")
        return
        
    with open(persona_file, 'r', encoding='utf-8') as f:
        persona_info = json.load(f)

    # --- Run Analysis ---
    analyzer = IntelligentDocumentAnalyzer()
    result = analyzer.analyze_documents_for_persona(
        pdf_paths=pdf_files,
        persona=persona_info['persona'],
        job_description=persona_info['job_to_be_done']
    )

    # --- Write Output ---
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'round_1b_result.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Successfully saved Round 1B analysis to {output_path}")

if __name__ == '__main__':
    run_hackathon_1b()
