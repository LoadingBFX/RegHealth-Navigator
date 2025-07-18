"""
compare.py

Section-by-section rule comparison system for CMS regulations.
Provides detailed analysis of changes between different versions of regulatory rules.

Functionality:
- Section-by-section comparison of CMS regulatory rules
- Semantic similarity matching between rule sections
- Detailed change analysis with impact assessment
- FAISS-based chunk retrieval and similarity search
- OpenAI GPT-4 integration for intelligent comparison
- Token management and context optimization

Process Flow:
1. Parse comparison query to identify target rules
2. Retrieve relevant chunks from FAISS index
3. Organize chunks by section headers
4. Find matching sections using semantic similarity
5. Compare matched sections for changes and impact
6. Analyze unmatched sections for unique content
7. Generate comprehensive comparison report

Author: Dhruv
"""

import openai
import json
import re
import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional
import tiktoken
from dotenv import load_dotenv
import os
from datetime import datetime
from collections import defaultdict

class SectionBySectionRuleComparator:
    def __init__(self, faiss_index_path: str, metadata_path: str, api_key: str):
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        
        # Load FAISS index and metadata
        self.index = faiss.read_index(faiss_index_path)
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        # Token management
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.max_tokens_per_section = 15000  # Conservative limit per section comparison
        self.max_chunk_tokens = 1000  # Max tokens per individual chunk

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.encoding.encode(text))

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoding.decode(tokens[:max_tokens]) + "..."

    def organize_chunks_by_section(self, chunks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Organize chunks by their section headers
        """
        sections = defaultdict(list)
        for chunk in chunks:
            section_header = chunk.get('section_header', 'General')
            # Normalize section headers for better matching
            normalized_header = self.normalize_section_header(section_header)
            sections[normalized_header].append(chunk)
        
        # Sort chunks within each section by similarity score
        for section in sections:
            sections[section].sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return dict(sections)

    def normalize_section_header(self, header: str) -> str:
        """
        Normalize section headers to improve matching between rules
        """
        if not header:
            return "General"
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', header.lower().strip())
        
        # Remove common prefixes/suffixes that might differ between years
        normalized = re.sub(r'^(section|part|chapter)\s+', '', normalized)
        normalized = re.sub(r'\s+(section|part|chapter)$', '', normalized)
        
        # Remove year references that might make sections appear different
        normalized = re.sub(r'\b(20\d{2}|cy\s*20\d{2})\b', '', normalized)
        
        # Remove common Roman numerals and numbers that might differ
        normalized = re.sub(r'\b[ivxlcdm]+\.\s*', '', normalized)
        normalized = re.sub(r'^\d+\.\s*', '', normalized)
        
        return normalized.strip() or "General"

    def find_matching_sections(self, rule1_sections: Dict, rule2_sections: Dict) -> List[Tuple[str, str, float]]:
        """
        Find matching sections between two rules using semantic similarity
        Returns list of (rule1_section, rule2_section, similarity_score)
        """
        matches = []
        
        for section1_name, section1_chunks in rule1_sections.items():
            best_match = None
            best_score = 0
            
            # Create a representative text for this section
            section1_text = self.create_section_summary(section1_chunks)
            section1_embedding = self.embed_query(section1_text)
            
            for section2_name, section2_chunks in rule2_sections.items():
                # Skip if already matched
                if any(match[1] == section2_name for match in matches):
                    continue
                
                section2_text = self.create_section_summary(section2_chunks)
                section2_embedding = self.embed_query(section2_text)
                
                # Calculate semantic similarity
                similarity = np.dot(section1_embedding[0], section2_embedding[0]) / (
                    np.linalg.norm(section1_embedding[0]) * np.linalg.norm(section2_embedding[0])
                )
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = section2_name
            
            if best_match and best_score > 0.3:  # Minimum similarity threshold
                matches.append((section1_name, best_match, best_score))
        
        # Sort by similarity score (highest first)
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches

    def create_section_summary(self, chunks: List[Dict], max_chunks: int = 5) -> str:
        """
        Create a concise summary of a section from its chunks
        """
        if not chunks:
            return ""
        
        # Take top chunks by similarity score
        top_chunks = chunks[:max_chunks]
        
        summary_parts = []
        for chunk in top_chunks:
            # Truncate long chunks
            text = self.truncate_text(chunk['text'], 200)  # Short summary
            summary_parts.append(text)
        
        return " ".join(summary_parts)

    def compare_single_section(self, rule1: Dict, rule2: Dict, 
                              rule1_section: str, rule2_section: str,
                              rule1_chunks: List[Dict], rule2_chunks: List[Dict],
                              section_similarity: float, topic: str) -> Dict:
        """
        Compare a single section between two rules
        """
        # Prepare context for this section
        rule1_context = self.prepare_section_context(rule1_chunks, rule1_section)
        rule2_context = self.prepare_section_context(rule2_chunks, rule2_section)
        
        # Check token count and truncate if needed
        total_tokens = self.count_tokens(rule1_context) + self.count_tokens(rule2_context)
        if total_tokens > self.max_tokens_per_section:
            # Reduce chunk count proportionally
            reduction_factor = self.max_tokens_per_section / total_tokens
            rule1_reduced = int(len(rule1_chunks) * reduction_factor * 0.5)
            rule2_reduced = int(len(rule2_chunks) * reduction_factor * 0.5)
            
            rule1_context = self.prepare_section_context(rule1_chunks[:rule1_reduced], rule1_section)
            rule2_context = self.prepare_section_context(rule2_chunks[:rule2_reduced], rule2_section)

        prompt = f"""Compare this specific section between two CMS rules:

**Focus Topic**: {topic}

**Rule 1**: {rule1['program']} {rule1['year']} {rule1['rule_type']} Rule
**Section**: {rule1_section}
{rule1_context}

**Rule 2**: {rule2['program']} {rule2['year']} {rule2['rule_type']} Rule  
**Section**: {rule2_section}
{rule2_context}

**Section Similarity Score**: {section_similarity:.2f}

Please provide a focused comparison of ONLY this section, including:

1. **Key Changes**: What specifically changed in this section?
2. **Impact**: How do these changes affect healthcare providers?
3. **Details**: Important numbers, dates, or requirements that changed
4. **Significance**: Rate the importance of changes (High/Medium/Low)

Keep the analysis focused and specific to this section only. Be concise but thorough.

Section Comparison:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a healthcare policy expert specializing in detailed section-by-section rule analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            return {
                "rule1_section": rule1_section,
                "rule2_section": rule2_section,
                "similarity_score": section_similarity,
                "comparison": response.choices[0].message.content,
                "chunk_counts": {
                    "rule1": len(rule1_chunks),
                    "rule2": len(rule2_chunks)
                },
                "token_usage": {
                    "rule1_context": self.count_tokens(rule1_context),
                    "rule2_context": self.count_tokens(rule2_context)
                }
            }
            
        except Exception as e:
            return {
                "rule1_section": rule1_section,
                "rule2_section": rule2_section,
                "similarity_score": section_similarity,
                "comparison": f"Error analyzing section: {str(e)}",
                "error": True
            }

    def prepare_section_context(self, chunks: List[Dict], section_name: str) -> str:
        """
        Prepare context string for a specific section
        """
        if not chunks:
            return f"[{section_name}]: No content available"
        
        context = f"[{section_name}]\n"
        for i, chunk in enumerate(chunks):
            # Add chunk with truncation
            truncated_text = self.truncate_text(chunk['text'], self.max_chunk_tokens)
            context += f"\n{i+1}. {truncated_text}\n"
        
        return context

    def identify_unmatched_sections(self, rule1_sections: Dict, rule2_sections: Dict, 
                                   matches: List[Tuple[str, str, float]]) -> Tuple[List[str], List[str]]:
        """
        Identify sections that don't have matches in the other rule
        """
        matched_rule1 = {match[0] for match in matches}
        matched_rule2 = {match[1] for match in matches}
        
        unmatched_rule1 = [section for section in rule1_sections.keys() if section not in matched_rule1]
        unmatched_rule2 = [section for section in rule2_sections.keys() if section not in matched_rule2]
        
        return unmatched_rule1, unmatched_rule2

    def analyze_unmatched_sections(self, rule: Dict, unmatched_sections: List[str], 
                                 sections_dict: Dict, rule_label: str) -> Dict:
        """
        Analyze sections that exist in only one rule
        """
        if not unmatched_sections:
            return {"sections": [], "analysis": "No unique sections found."}
        
        # Limit to top 5 most significant unmatched sections
        sections_analysis = []
        for section_name in unmatched_sections[:5]:
            chunks = sections_dict[section_name]
            summary = self.create_section_summary(chunks, max_chunks=3)
            
            sections_analysis.append({
                "section_name": section_name,
                "chunk_count": len(chunks),
                "summary": summary[:500]  # Limit summary length
            })
        
        prompt = f"""Analyze these sections that appear ONLY in {rule_label} ({rule['program']} {rule['year']} {rule['rule_type']}):

{json.dumps(sections_analysis, indent=2)}

Provide:
1. **New Content**: What new topics/requirements are introduced?
2. **Significance**: Why were these sections added/removed?
3. **Impact**: How does this affect healthcare providers?

Analysis:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a healthcare policy expert analyzing unique rule sections."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            return {
                "sections": sections_analysis,
                "analysis": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "sections": sections_analysis,
                "analysis": f"Error analyzing unique sections: {str(e)}"
            }

    def generate_final_summary(self, section_comparisons: List[Dict], 
                             rule1_unique: Dict, rule2_unique: Dict,
                             rule1: Dict, rule2: Dict, query: str) -> str:
        """
        Generate a comprehensive final summary from all section comparisons
        """
        # Categorize sections by significance
        high_impact = []
        medium_impact = []
        low_impact = []
        
        for comp in section_comparisons:
            if not comp.get('error'):
                analysis = comp['comparison'].lower()
                if 'high' in analysis and 'significance' in analysis:
                    high_impact.append(comp)
                elif 'medium' in analysis and 'significance' in analysis:
                    medium_impact.append(comp)
                else:
                    low_impact.append(comp)
        
        prompt = f"""Based on the following section-by-section analysis, provide a comprehensive summary comparing:

**Query**: {query}
**Rule 1**: {rule1['program']} {rule1['year']} {rule1['rule_type']} Rule
**Rule 2**: {rule2['program']} {rule2['year']} {rule2['rule_type']} Rule

**HIGH IMPACT SECTIONS** ({len(high_impact)} sections):
{self.summarize_section_group(high_impact)}

**MEDIUM IMPACT SECTIONS** ({len(medium_impact)} sections):
{self.summarize_section_group(medium_impact)}

**UNIQUE TO RULE 1**:
{rule1_unique['analysis']}

**UNIQUE TO RULE 2**:
{rule2_unique['analysis']}

Provide a comprehensive executive summary including:

1. **Overview**: What are the main themes of changes?
2. **Critical Changes**: Top 5 most important changes for providers
3. **Financial Impact**: Key financial/payment changes
4. **Implementation Timeline**: When do changes take effect?
5. **Action Items**: What should healthcare providers do?

Executive Summary:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior healthcare policy consultant providing executive summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating final summary: {str(e)}"

    def summarize_section_group(self, section_group: List[Dict]) -> str:
        """
        Create a brief summary of a group of section comparisons
        """
        if not section_group:
            return "No sections in this category."
        
        summaries = []
        for comp in section_group[:3]:  # Limit to top 3
            section_name = comp['rule1_section']
            # Extract first sentence of comparison for brevity
            first_sentence = comp['comparison'].split('.')[0] + "."
            summaries.append(f"• {section_name}: {first_sentence}")
        
        if len(section_group) > 3:
            summaries.append(f"• ... and {len(section_group) - 3} more sections")
        
        return "\n".join(summaries)

    def compare_rules(self, query: str) -> Dict:
        """
        Main method for section-by-section rule comparison
        """
        print(f"Starting section-by-section comparison for: {query}")
        
        # Step 1: Parse the query (reuse existing method)
        rule1, rule2, topic = self.parse_comparison_query(query)
        print(f"Rule 1: {rule1}")
        print(f"Rule 2: {rule2}")
        print(f"Topic: {topic}")
        
        # Step 2: Get all chunks for each rule
        query_embedding = self.embed_query(query)
        rule1_all_chunks = self.filter_chunks_by_rule(rule1)
        rule2_all_chunks = self.filter_chunks_by_rule(rule2)
        
        if not rule1_all_chunks or not rule2_all_chunks:
            return {"error": "Could not find chunks for one or both rules"}
        
        # Step 3: Get relevant chunks (larger set for section analysis)
        rule1_relevant = self.semantic_similarity_search(query_embedding, rule1_all_chunks, k=150)
        rule2_relevant = self.semantic_similarity_search(query_embedding, rule2_all_chunks, k=150)
        
        #print(f"Found {len(rule1_relevant)} relevant chunks in rule 1")
        #print(f"Found {len(rule2_relevant)} relevant chunks in rule 2")
        
        # Step 4: Organize chunks by section
        rule1_sections = self.organize_chunks_by_section(rule1_relevant)
        rule2_sections = self.organize_chunks_by_section(rule2_relevant)
        
        #print(f"Rule 1 sections: {list(rule1_sections.keys())}")
        #print(f"Rule 2 sections: {list(rule2_sections.keys())}")
        
        # Step 5: Find matching sections
        section_matches = self.find_matching_sections(rule1_sections, rule2_sections)
        #print(f"Found {len(section_matches)} matching section pairs")
        
        # Step 6: Compare each matching section
        section_comparisons = []
        for rule1_section, rule2_section, similarity in section_matches:
            #print(f"Comparing: {rule1_section} <-> {rule2_section} (similarity: {similarity:.2f})")
            
            comparison = self.compare_single_section(
                rule1, rule2, rule1_section, rule2_section,
                rule1_sections[rule1_section], rule2_sections[rule2_section],
                similarity, topic
            )
            section_comparisons.append(comparison)
        
        # Step 7: Analyze unmatched sections
        unmatched_rule1, unmatched_rule2 = self.identify_unmatched_sections(
            rule1_sections, rule2_sections, section_matches
        )
        
        rule1_unique = self.analyze_unmatched_sections(
            rule1, unmatched_rule1, rule1_sections, "Rule 1"
        )
        rule2_unique = self.analyze_unmatched_sections(
            rule2, unmatched_rule2, rule2_sections, "Rule 2"
        )
        
        # Step 8: Extract source file information from chunks
        def extract_source_info_from_chunks(chunks):
            """Extract source file info from the first chunk"""
            if not chunks:
                return {}
            
            first_chunk = chunks[0]
            metadata = first_chunk.get("metadata", {})
            source_file = metadata.get("source_file", "")
            
            # Extract document number from source file and call federal register API
            import re
            import requests
            
            doc_match = re.search(r'(\d{4}-\d{5})', source_file)
            if doc_match:
                doc_number = doc_match.group(1)
                try:
                    api_url = f"https://www.federalregister.gov/api/v1/documents/{doc_number}.json"
                    response = requests.get(api_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "source_file": source_file,
                            "pdf_url": data.get("pdf_url", ""),
                            "html_url": data.get("html_url", ""),
                            "document_title": data.get("title", "")
                        }
                except Exception as e:
                    print(f"Failed to fetch document info for {doc_number}: {e}")
            
            return {"source_file": source_file}
        
        rule1_source_info = extract_source_info_from_chunks(rule1_relevant)
        rule2_source_info = extract_source_info_from_chunks(rule2_relevant)

        # Step 9: Generate final comprehensive summary
        final_summary = self.generate_final_summary(
            section_comparisons, rule1_unique, rule2_unique, rule1, rule2, query
        )
        
        result = {
            "rule1": {**rule1, **rule1_source_info},
            "rule2": {**rule2, **rule2_source_info},
            "topic": topic,
            "section_comparisons": section_comparisons,
            "rule1_unique_sections": rule1_unique,
            "rule2_unique_sections": rule2_unique,
            "final_summary": final_summary,
            "stats": {
                "total_sections_compared": len(section_comparisons),
                "rule1_unique_sections": len(unmatched_rule1),
                "rule2_unique_sections": len(unmatched_rule2),
                "rule1_total_chunks": len(rule1_relevant),
                "rule2_total_chunks": len(rule2_relevant)
            }
        }

        response = json.dumps(result, default=self.clean_numpy, indent=2)
        return response

    # Include existing methods from original class
    def parse_comparison_query(self, query: str) -> Tuple[Dict, Dict, str]:
        """Parse user query to extract rules and topic (from original class)"""
        query_lower = query.lower()
        
        # Extract programs
        programs = []
        if "mpfs" in query_lower:
            programs.append("MPFS")
        if "snf" in query_lower:
            programs.append("SNF")
        if "hospice" in query_lower:
            programs.append("Hospice")
        
        # Extract years
        years = re.findall(r'\b(20\d{2})\b', query)
        years = [int(year) for year in years]
        
        # Extract rule types
        rule_types = []
        if "final" in query_lower:
            rule_types.append("Final")
        if "proposed" in query_lower:
            rule_types.append("Proposed")
        
        # Extract topic/focus
        topic = self._extract_topic(query_lower)
        
        # Create rule dictionaries
        rule1, rule2 = self._create_rule_dicts(programs, years, rule_types, topic)
        
        return rule1, rule2, topic

    def _extract_topic(self, query_lower: str) -> str:
        """Extract the main topic from the query"""
        topic_keywords = {
            "fee schedule": "fee schedule",
            "payment": "payment",
            "wage index": "wage index",
            "quality": "quality",
            "reporting": "reporting",
            "cap amount": "cap amount",
            "update": "update"
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in query_lower:
                return topic
        
        return "general comparison"

    def _create_rule_dicts(self, programs: List[str], years: List[int], 
                          rule_types: List[str], topic: str) -> Tuple[Dict, Dict]:
        """Create two rule dictionaries from extracted information"""
        program = programs[0] if programs else "General"
        
        if len(years) == 2 and len(rule_types) == 1:
            rule1 = {"program": program, "year": years[0], "rule_type": rule_types[0], "topic": topic}
            rule2 = {"program": program, "year": years[1], "rule_type": rule_types[0], "topic": topic}
        elif len(years) == 1 and len(rule_types) == 2:
            rule1 = {"program": program, "year": years[0], "rule_type": rule_types[0], "topic": topic}
            rule2 = {"program": program, "year": years[0], "rule_type": rule_types[1], "topic": topic}
        elif len(years) == 2 and len(rule_types) == 2:
            rule1 = {"program": program, "year": years[0], "rule_type": rule_types[0], "topic": topic}
            rule2 = {"program": program, "year": years[1], "rule_type": rule_types[1], "topic": topic}
        else:
            current_date_time = datetime.now()
            rule1 = {"program": program, "year": years[0] if years else current_date_time.year - 1, "rule_type": "Final", "topic": topic}
            rule2 = {"program": program, "year": years[-1] if len(years) > 1 else current_date_time.year, "rule_type": "Final", "topic": topic}
        
        return rule1, rule2

    def embed_query(self, query: str) -> np.ndarray:
        """Create embedding for the user query"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        return np.array([response.data[0].embedding], dtype="float32")

    def filter_chunks_by_rule(self, rule: Dict) -> List[Dict]:
        """Filter metadata chunks by rule dictionary"""
        filtered_chunks = []
        
        for chunk in self.metadata:
            meta = chunk.get("metadata", {})
            
            # Check program match
            if rule["program"].lower() not in meta.get("program", "").lower():
                continue
            
            # Check year match
            if meta.get("year") != rule["year"]:
                continue
                
            # Check rule type match
            if rule["rule_type"].lower() not in meta.get("rule_type", "").lower():
                continue
            
            filtered_chunks.append(chunk)
        
        return filtered_chunks

    def semantic_similarity_search(self, query_embedding: np.ndarray, 
                                 rule_chunks: List[Dict], k: int = 50) -> List[Dict]:
        """Find most relevant chunks from a specific rule using semantic similarity"""
        if not rule_chunks:
            return []
        
        # Search directly in the main FAISS index
        distances, indices = self.index.search(query_embedding, k * 2)
        
        # Create a set of rule chunk texts for fast lookup
        rule_chunk_texts = {chunk["text"] for chunk in rule_chunks}
        
        # Filter results to only include chunks from the specified rule
        relevant_chunks = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                chunk_data = self.metadata[idx]
                if chunk_data["text"] in rule_chunk_texts:
                    chunk = chunk_data.copy()
                    chunk['similarity_score'] = 1 / (1 + dist)
                    relevant_chunks.append(chunk)
                    
                    if len(relevant_chunks) >= k:
                        break
        
        return relevant_chunks

    def clean_numpy(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, (set, tuple)):
            return list(obj)
        return str(obj)

# # Example usage
# if __name__ == "__main__":
#     load_dotenv()
#     import os
#
#     faiss_index_path = "./rag_data/faiss.index"
#     metadata_path = "./rag_data/faiss_metadata.json"
#
#     comparator = SectionBySectionRuleComparator(
#         faiss_index_path=faiss_index_path,
#         metadata_path=metadata_path,
#         api_key=os.getenv("OPENAI_API_KEY")
#     )
#
#     # Test query
#     query = "Compare MPFS fee schedule for 2023 final rule and 2024 final rule"
#
#     print(f"Testing section-by-section comparison: {query}")
#     result = comparator.compare_rules(query)
#     print (result)
#
#     # if "error" in result:
#     #     print(f"Error: {result['error']}")
#     # else:
#     #     # print(f"\n{'='*80}")
#     #     # print("SECTION-BY-SECTION COMPARISON RESULTS")
#     #     # print('='*80)
#
#     #     # print(f"\nRules Compared:")
#     #     # print(f"Rule 1: {result['rule1']['program']} {result['rule1']['year']} {result['rule1']['rule_type']}")
#     #     # print(f"Rule 2: {result['rule2']['program']} {result['rule2']['year']} {result['rule2']['rule_type']}")
#
#     #     # #print(f"\nStats:")
#     #     # stats = result['stats']
#     #     # print(f"- Sections compared: {stats['total_sections_compared']}")
#     #     # print(f"- Rule 1 unique sections: {stats['rule1_unique_sections']}")
#     #     # print(f"- Rule 2 unique sections: {stats['rule2_unique_sections']}")
#
#     #     print(f"\n{'='*60}")
#     #     print("FINAL EXECUTIVE SUMMARY")
#     #     print('='*60)
#     #     print(result['final_summary'])
#
#     #     print(f"\n{'='*60}")
#     #     print("DETAILED SECTION COMPARISONS")
#     #     print('='*60)
#     #     for i, comp in enumerate(result['section_comparisons'][:10], 1):  # Show first 5
#     #         if not comp.get('error'):
#     #             print(f"\n{i}. {comp['rule1_section']} <-> {comp['rule2_section']}")
#     #             #print(f"   Similarity: {comp['similarity_score']:.2f}")
#     #             print(f"   {comp['comparison']}")