#!/usr/bin/env python3
"""
Enhanced Intelligent Document Analyzer for Adobe Hackathon Round 1B
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

# For AI-based semantic analysis
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# For robust PDF parsing
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer


class IntelligentDocumentAnalyzer:
    """
    Enhanced document analyzer with better segmentation and relevance scoring.
    """
    def _init_(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initializes the analyzer and loads the AI model."""
        print("Initializing Enhanced Analyzer for Round 1B...")
        self.model = SentenceTransformer(model_name)
        print("AI model loaded successfully.")

    def extract_text_with_pages(self, pdf_path: str) -> List[Dict]:
        """Extract text with accurate page information."""
        pages_content = []
        try:
            for page_num, page_layout in enumerate(extract_pages(pdf_path), 1):
                page_text = ""
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        page_text += element.get_text()
                
                if page_text.strip():
                    pages_content.append({
                        'page_number': page_num,
                        'content': page_text.strip()
                    })
        except Exception as e:
            print(f"Error extracting text with pages from {pdf_path}: {e}")
            # Fallback to simple extraction
            try:
                full_text = extract_text(pdf_path)
                pages_content.append({
                    'page_number': 1,
                    'content': full_text
                })
            except:
                pass
        
        return pages_content

    def advanced_text_segmentation(self, pdf_path: str) -> List[Dict]:
        """Enhanced segmentation with section detection."""
        pages_data = self.extract_text_with_pages(pdf_path)
        
        if not pages_data:
            return []
        
        all_sections = []
        
        # Section detection patterns
        section_patterns = [
            r'\n\s*(\d+\.?\s+[A-Z][^\n]*)\n',  # "1. Introduction"
            r'\n\s*([A-Z][A-Z\s]{5,30})\n',   # "METHODOLOGY"
            r'\n\s*(Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References|Bibliography)[:\s]*\n',
            r'\n\s*(Chapter|Section|Part)\s+\d+[:\s][^\n]\n'
        ]
        
        for page_data in pages_data:
            page_num = page_data['page_number']
            text = page_data['content']
            
            # Try to detect structured sections
            sections_found = []
            lines = text.split('\n')
            current_section = ""
            current_title = f"Section from Page {page_num}"
            
            for line in lines:
                section_detected = False
                for pattern in section_patterns:
                    match = re.search(pattern, f"\n{line}\n", re.IGNORECASE)
                    if match:
                        # Save previous section
                        if current_section.strip() and len(current_section.strip()) > 100:
                            sections_found.append({
                                'title': current_title,
                                'content': current_section.strip(),
                                'page_number': page_num,
                                'document': os.path.basename(pdf_path)
                            })
                        
                        current_title = match.group(1).strip()
                        current_section = ""
                        section_detected = True
                        break
                
                if not section_detected:
                    current_section += line + "\n"
            
            # Add final section
            if current_section.strip() and len(current_section.strip()) > 100:
                sections_found.append({
                    'title': current_title,
                    'content': current_section.strip(),
                    'page_number': page_num,
                    'document': os.path.basename(pdf_path)
                })
            
            # If no structured sections found, fall back to paragraph segmentation
            if not sections_found:
                paragraphs = text.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if len(para.strip()) > 100:
                        all_sections.append({
                            'title': f"Section {i+1} from Page {page_num}",
                            'content': para.strip(),
                            'page_number': page_num,
                            'document': os.path.basename(pdf_path)
                        })
            else:
                all_sections.extend(sections_found)
        
        return all_sections

    def calculate_enhanced_relevance(self, section_text: str, query_embedding, persona: str, job: str) -> float:
        """Enhanced relevance scoring with domain-specific boosts."""
        # Base semantic similarity
        section_embedding = self.model.encode([section_text])
        base_score = float(cosine_similarity(query_embedding, section_embedding)[0][0])
        
        # Domain-specific keyword boosting
        domain_keywords = {
            'researcher': ['methodology', 'results', 'analysis', 'study', 'research', 'experiment', 'data', 'findings'],
            'student': ['definition', 'example', 'concept', 'theory', 'principle', 'explanation', 'summary'],
            'analyst': ['trend', 'performance', 'metric', 'comparison', 'analysis', 'report', 'statistics'],
            'investor': ['revenue', 'profit', 'growth', 'market', 'financial', 'earnings', 'investment'],
            'journalist': ['news', 'event', 'report', 'story', 'update', 'development', 'announcement']
        }
        
        # Job-specific keywords
        job_keywords = {
            'literature review': ['review', 'survey', 'comparison', 'analysis', 'study', 'research'],
            'exam preparation': ['definition', 'concept', 'theory', 'principle', 'example', 'practice'],
            'financial analysis': ['revenue', 'profit', 'cost', 'investment', 'performance', 'growth'],
            'summarize': ['summary', 'overview', 'key points', 'main', 'important', 'conclusion']
        }
        
        keyword_boost = 0
        text_lower = section_text.lower()
        
        # Persona-based boost
        for role, keywords in domain_keywords.items():
            if role.lower() in persona.lower():
                keyword_boost += sum(0.05 for keyword in keywords if keyword in text_lower)
                break
        
        # Job-based boost
        for job_type, keywords in job_keywords.items():
            if job_type.lower() in job.lower():
                keyword_boost += sum(0.05 for keyword in keywords if keyword in text_lower)
                break
        
        return min(base_score + keyword_boost, 1.0)

    def extract_best_subsection(self, section_content: str, query_embedding) -> str:
        """Extract the most relevant sentence/paragraph from a section."""
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', section_content) if len(s.strip()) > 20]
        
        if not sentences:
            return section_content[:200] + "..." if len(section_content) > 200 else section_content
        
        if len(sentences) == 1:
            return sentences[0]
        
        # Find best sentence
        try:
            sentence_embeddings = self.model.encode(sentences)
            similarities = cosine_similarity(query_embedding, sentence_embeddings)[0]
            best_idx = similarities.argmax()
            return sentences[best_idx]
        except:
            return sentences[0]

    def analyze_documents_for_persona(self, pdf_paths: List[str], persona: str, job_description: str) -> Dict[str, Any]:
        """
        Main analysis function with enhanced processing.
        """
        print("\nStarting Enhanced AI-powered analysis...")
        print(f"  -> Persona: {persona}")
        print(f"  -> Job: {job_description}")
        
        # Enhanced AI query
        ai_query = f"As a {persona}, I need to {job_description}"
        query_embedding = self.model.encode([ai_query])
        
        all_sections = []

        for pdf_path in pdf_paths:
            print(f"  -> Processing: {os.path.basename(pdf_path)}")
            
            try:
                sections = self.advanced_text_segmentation(pdf_path)
                
                if not sections:
                    print(f"     Warning: No meaningful sections found in {os.path.basename(pdf_path)}")
                    continue

                for section in sections:
                    relevance_score = self.calculate_enhanced_relevance(
                        section['content'], query_embedding, persona, job_description
                    )
                    
                    if relevance_score > 0.2:  # Relevance threshold
                        section['relevance_score'] = relevance_score
                        all_sections.append(section)
                        
            except Exception as e:
                print(f"     ERROR: Failed to process {os.path.basename(pdf_path)}. Reason: {e}")

        # Sort by relevance
        all_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Prepare output
        result = {
            'metadata': {
                'input_documents': [os.path.basename(p) for p in pdf_paths],
                'persona': persona,
                'job_to_be_done': job_description,
                'processing_timestamp': datetime.now().isoformat(),
                'total_sections_found': len(all_sections)
            },
            'extracted_sections': []
        }

        for rank, section in enumerate(all_sections[:20]):  # Limit to top 20 sections
            refined_text = self.extract_best_subsection(section['content'], query_embedding)
            
            result['extracted_sections'].append({
                'document': section['document'],
                'page_number': section['page_number'],
                'section_title': section['title'],
                'importance_rank': rank + 1,
                'refined_text': refined_text,
                'relevance_score': section['relevance_score']
            })

        print(f"\nAnalysis complete. Found {len(result['extracted_sections'])} relevant sections.")
        return result


def run_hackathon_1b():
    """Main execution function for Round 1B."""
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
        print("FATAL: persona.json not found in /app/input.")
        return
        
    with open(persona_file, 'r', encoding='utf-8') as f:
        persona_info = json.load(f)

    # Run Analysis
    analyzer = IntelligentDocumentAnalyzer()
    result = analyzer.analyze_documents_for_persona(
        pdf_paths=pdf_files,
        persona=persona_info['persona'],
        job_description=persona_info['job_to_be_done']
    )

    # Write Output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'round_1b_result.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully saved Round 1B analysis to {output_path}")


if _name_ == '_main_':
    run_hackathon_1b()