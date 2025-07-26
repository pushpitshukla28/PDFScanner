#!/usr/bin/env python3
"""
Simple Document Analyzer - No API Keys Required
Analyzes PDF documents using keyword-based matching
"""

import os
import json
import re
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any
import PyPDF2

class SimpleDocumentAnalyzer:
    def __init__(self):
        # Define persona-specific keywords and their weights
        self.persona_patterns = {
            'investment_analyst': {
                'high_priority': ['revenue', 'profit', 'margin', 'earnings', 'roi', 'growth', 'dividend', 'valuation', 'cash flow', 'ebitda'],
                'medium_priority': ['market', 'competition', 'industry', 'sector', 'trend', 'risk', 'volatility', 'equity', 'debt'],
                'low_priority': ['customer', 'product', 'service', 'technology', 'operations']
            },
            'financial_analyst': {
                'high_priority': ['cost', 'expense', 'budget', 'cash flow', 'balance sheet', 'income statement', 'financial', 'accounting'],
                'medium_priority': ['revenue', 'sales', 'profit', 'margin', 'debt', 'equity', 'assets', 'liabilities'],
                'low_priority': ['market', 'customer', 'product', 'strategy']
            },
            'product_manager': {
                'high_priority': ['feature', 'requirement', 'user', 'customer', 'market fit', 'roadmap', 'product', 'functionality'],
                'medium_priority': ['technical', 'architecture', 'performance', 'scalability', 'integration', 'api'],
                'low_priority': ['cost', 'revenue', 'profit', 'financial']
            },
            'researcher': {
                'high_priority': ['methodology', 'results', 'findings', 'conclusion', 'data', 'analysis', 'study', 'research'],
                'medium_priority': ['hypothesis', 'experiment', 'survey', 'evidence', 'statistics', 'sample'],
                'low_priority': ['market', 'commercial', 'business', 'cost']
            },
            'business_analyst': {
                'high_priority': ['process', 'workflow', 'requirements', 'stakeholder', 'analysis', 'business', 'strategy'],
                'medium_priority': ['performance', 'metrics', 'kpi', 'efficiency', 'optimization', 'improvement'],
                'low_priority': ['technical', 'technology', 'code', 'development']
            },
            'marketing_analyst': {
                'high_priority': ['campaign', 'customer', 'market', 'brand', 'advertising', 'conversion', 'engagement'],
                'medium_priority': ['sales', 'revenue', 'roi', 'metrics', 'analytics', 'demographics'],
                'low_priority': ['technical', 'development', 'architecture', 'infrastructure']
            }
        }
        
        # Common stop words to ignore
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'can', 'may', 'might', 'must', 'shall', 'should', 'would', 'could'
        }

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF with page information"""
        try:
            print(f"  Extracting text from: {os.path.basename(pdf_path)}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():  # Only add pages with content
                            pages.append({
                                'page_number': page_num + 1,
                                'text': text
                            })
                    except Exception as e:
                        print(f"    ⚠️  Warning: Could not extract page {page_num + 1}: {e}")
                        continue
                
                return {
                    'filename': os.path.basename(pdf_path),
                    'total_pages': len(pages),
                    'pages': pages
                }
        except Exception as e:
            print(f"  ❌ Error extracting text from {pdf_path}: {e}")
            return None

    def identify_sections(self, text: str, page_number: int) -> List[Dict]:
        """Identify sections in the text using simple heuristics"""
        lines = text.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a potential header
            if self.is_likely_header(line):
                # Save previous section
                if current_section and current_content:
                    content_text = ' '.join(current_content)
                    if len(content_text.strip()) > 20:  # Only save substantial content
                        sections.append({
                            'title': current_section,
                            'content': content_text,
                            'page_number': page_number,
                            'start_line': line_num - len(current_content),
                            'end_line': line_num - 1
                        })
                
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            content_text = ' '.join(current_content)
            if len(content_text.strip()) > 20:
                sections.append({
                    'title': current_section,
                    'content': content_text,
                    'page_number': page_number,
                    'start_line': len(lines) - len(current_content),
                    'end_line': len(lines) - 1
                })
        
        # If no sections found, treat entire page as one section
        if not sections and text.strip():
            # Try to extract a title from the first few lines
            first_lines = [line.strip() for line in lines[:5] if line.strip()]
            title = first_lines[0] if first_lines else f"Page {page_number} Content"
            
            sections.append({
                'title': title,
                'content': text,
                'page_number': page_number,
                'start_line': 0,
                'end_line': len(lines)
            })
        
        return sections

    def is_likely_header(self, line: str) -> bool:
        """Simple heuristics to identify headers"""
        # Clean the line
        line = line.strip()
        
        # Too short or too long unlikely to be headers
        if len(line) < 3 or len(line) > 150:
            return False
        
        # Skip lines that are mostly numbers or special characters
        if re.match(r'^[\d\s\-\.\,\(\)]+$', line):
            return False
        
        # All uppercase (common for headers) but not too long
        if line.isupper() and len(line.split()) <= 12:
            return True
        
        # Starts with number (1. Introduction, 2.1 Analysis, etc.)
        if re.match(r'^\d+\.?\d*\.?\s+[A-Za-Z]', line):
            return True
        
        # Title case and reasonable length
        if line.istitle() and 3 <= len(line.split()) <= 10:
            return True
        
        # Contains common header patterns
        header_patterns = [
            r'^(CHAPTER|SECTION|PART)\s+\d+',
            r'^(Abstract|Summary|Introduction|Conclusion|Discussion|Results|Methods?|Analysis)',
            r'^(Overview|Background|Methodology|Findings|Recommendations?)',
            r'^\d+\.\s+(Introduction|Background|Analysis|Results|Conclusion)',
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        
        # Ends with colon (often indicates a section start)
        if line.endswith(':') and len(line.split()) <= 8:
            return True
        
        return False

    def calculate_relevance_score(self, text: str, persona: str, job_description: str) -> Dict[str, Any]:
        """Calculate relevance score based on keyword matching"""
        text_lower = text.lower()
        job_lower = job_description.lower()
        
        # Get persona-specific keywords
        persona_key = persona.lower().replace(' ', '_').replace('-', '_')
        patterns = self.persona_patterns.get(persona_key, {})
        
        # If persona not found, try partial matching
        if not patterns:
            for key in self.persona_patterns.keys():
                if any(word in key for word in persona_key.split('_')):
                    patterns = self.persona_patterns[key]
                    break
        
        # Score calculation
        score_breakdown = {
            'high_priority_matches': 0,
            'medium_priority_matches': 0,
            'low_priority_matches': 0,
            'job_keyword_matches': 0,
            'total_score': 0,
            'matched_keywords': []
        }
        
        # Check high priority keywords (weight: 3)
        for keyword in patterns.get('high_priority', []):
            pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                score_breakdown['high_priority_matches'] += matches
                score_breakdown['matched_keywords'].append(f"{keyword} (H:{matches})")
        
        # Check medium priority keywords (weight: 2)
        for keyword in patterns.get('medium_priority', []):
            pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                score_breakdown['medium_priority_matches'] += matches
                score_breakdown['matched_keywords'].append(f"{keyword} (M:{matches})")
        
        # Check low priority keywords (weight: 1)
        for keyword in patterns.get('low_priority', []):
            pattern = r'\b' + keyword.replace(' ', r'\s+') + r'\b'
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                score_breakdown['low_priority_matches'] += matches
                score_breakdown['matched_keywords'].append(f"{keyword} (L:{matches})")
        
        # Check job-specific keywords (weight: 2.5)
        job_words = [word for word in job_lower.split() if len(word) > 3 and word not in self.stop_words]
        for word in job_words:
            pattern = r'\b' + re.escape(word) + r'\b'
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                score_breakdown['job_keyword_matches'] += matches
                score_breakdown['matched_keywords'].append(f"{word} (J:{matches})")
        
        # Calculate total score
        total_score = (
            score_breakdown['high_priority_matches'] * 3 +
            score_breakdown['medium_priority_matches'] * 2 +
            score_breakdown['low_priority_matches'] * 1 +
            score_breakdown['job_keyword_matches'] * 2.5
        )
        
        # Normalize by text length (per 100 words)
        word_count = len(text.split())
        normalized_score = (total_score / max(word_count / 100, 1)) if word_count > 0 else 0
        
        score_breakdown['total_score'] = round(normalized_score, 2)
        score_breakdown['word_count'] = word_count
        score_breakdown['raw_score'] = total_score
        
        return score_breakdown

    def analyze_documents(self, pdf_paths: List[str], persona: str, job_description: str) -> Dict[str, Any]:
        """Main analysis function"""
        print(f"\n Starting analysis...")
        print(f" Persona: {persona}")
        print(f" Job: {job_description}")
        print(f" Documents: {len(pdf_paths)}")
        
        all_results = []
        document_summaries = []
        total_sections = 0
        
        for pdf_path in pdf_paths:
            print(f"\n Processing: {os.path.basename(pdf_path)}")
            
            # Extract text
            doc_data = self.extract_text_from_pdf(pdf_path)
            if not doc_data:
                print(f" Skipping {pdf_path} - could not extract text")
                continue
            
            document_summaries.append({
                'filename': doc_data['filename'],
                'total_pages': doc_data['total_pages']
            })
            
            print(f"  Extracted {doc_data['total_pages']} pages")
            
            # Process each page
            sections_found = 0
            for page_data in doc_data['pages']:
                page_text = page_data['text']
                if not page_text.strip():
                    continue
                
                # Identify sections on this page
                sections = self.identify_sections(page_text, page_data['page_number'])
                sections_found += len(sections)
                
                for section in sections:
                    # Calculate relevance
                    relevance = self.calculate_relevance_score(
                        section['content'], persona, job_description
                    )
                    
                    # Only include sections with meaningful relevance
                    if relevance['total_score'] > 0.3:  # Lower threshold for more results
                        all_results.append({
                            'document': doc_data['filename'],
                            'page_number': section['page_number'],
                            'section_title': section['title'][:100] + ('...' if len(section['title']) > 100 else ''),
                            'importance_rank': min(max(1, int(6 - relevance['total_score'])), 5),
                            'relevance_score': relevance['total_score'],
                            'analysis': {
                                'summary': section['content'][:300] + ('...' if len(section['content']) > 300 else ''),
                                'relevance_to_job': f"Score: {relevance['total_score']} | Keywords: {', '.join(relevance['matched_keywords'][:5])}",
                                'word_count': relevance['word_count'],
                                'keyword_breakdown': {
                                    'high_priority': relevance['high_priority_matches'],
                                    'medium_priority': relevance['medium_priority_matches'],
                                    'low_priority': relevance['low_priority_matches'],
                                    'job_specific': relevance['job_keyword_matches']
                                },
                                'matched_keywords': relevance['matched_keywords'][:10]  # Top 10 matches
                            }
                        })
            
            print(f"  Found {sections_found} sections")
            total_sections += sections_found
        
        # Sort by relevance score (highest first)
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"\n Analysis Summary:")
        print(f"  Total sections analyzed: {total_sections}")
        print(f"  Relevant sections found: {len(all_results)}")
        print(f"  Top sections (showing up to 25): {min(len(all_results), 25)}")
        
        # Prepare final output
        result = {
            'metadata': {
                'input_documents': [doc['filename'] for doc in document_summaries],
                'persona': persona,
                'job_to_be_done': job_description,
                'processing_timestamp': datetime.now().isoformat(),
                'total_sections_analyzed': total_sections,
                'relevant_sections_found': len(all_results),
                'analysis_method': 'Rule-based keyword matching',
                'document_summaries': document_summaries,
                'available_personas': list(self.persona_patterns.keys())
            },
            'extracted_sections': all_results[:25]  # Top 25 most relevant sections
        }
        
        return result

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze PDF documents without API keys',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python document_analyzer.py --documents report1.pdf report2.pdf --persona "Investment Analyst" --job "Analyze revenue trends"
  
  python document_analyzer.py --documents *.pdf --persona "Product Manager" --job "Identify user requirements" --output results.json
  
Available personas:
  - investment_analyst
  - financial_analyst  
  - product_manager
  - researcher
  - business_analyst
  - marketing_analyst
        """
    )
    
    parser.add_argument('--documents', nargs='+', required=True, 
                       help='PDF file paths (supports wildcards)')
    parser.add_argument('--persona', required=True, 
                       help='Analyst persona (e.g., "Investment Analyst")')
    parser.add_argument('--job', required=True, 
                       help='Job to be done description')
    parser.add_argument('--output', default='analysis_result.json', 
                       help='Output JSON file (default: analysis_result.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed progress information')
    
    args = parser.parse_args()
    
    # Expand wildcards and validate files
    import glob
    pdf_files = []
    for pattern in args.documents:
        matches = glob.glob(pattern)
        if matches:
            pdf_files.extend(matches)
        else:
            # Check if it's a direct file path
            if os.path.exists(pattern):
                pdf_files.append(pattern)
            else:
                print(f" Warning: No files found matching: {pattern}")
    
    # Filter for PDF files
    pdf_files = [f for f in pdf_files if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(" Error: No PDF files found!")
        return 1
    
    print(f" Ready to analyze {len(pdf_files)} PDF files")
    
    # Validate files exist
    missing_files = [f for f in pdf_files if not os.path.exists(f)]
    if missing_files:
        print(f" Error: Files not found: {', '.join(missing_files)}")
        return 1
    
    try:
        # Run analysis
        analyzer = SimpleDocumentAnalyzer()
        result = analyzer.analyze_documents(pdf_files, args.persona, args.job)
        
        # Save result
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n Analysis complete!")
        print(f"Results saved to: {args.output}")
        
        # Show quick summary
        if result['extracted_sections']:
            print(f"\n🏆 Top 3 most relevant sections:")
            for i, section in enumerate(result['extracted_sections'][:3], 1):
                print(f"  {i}. {section['document']} (Page {section['page_number']}) - Score: {section['relevance_score']}")
                print(f"     {section['section_title']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())