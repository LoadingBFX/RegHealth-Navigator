"""
XML Document Chunker

Provides structure-aware chunking of XML documents with configurable
chunk sizes, overlap strategies, and metadata extraction capabilities.

The chunker is designed specifically for regulatory documents and maintains
document structure while creating semantically meaningful chunks.

Example:
    # Initialize chunker with custom settings
    chunker = XMLChunker(chunk_words=500, overlap_sentences=2)
    
    # Process single file
    result = chunker.process_file('document.xml')
    chunks = result['chunks'] if result['status'] == 'success' else []
    
    # Process multiple files with batch processing
    result = chunker.process_files(['doc1.xml', 'doc2.xml'])
    
    # Save chunks to file
    save_result = chunker.save_chunks(chunks, 'output/chunks.json')
"""

import os
import re
import json
import xml.etree.ElementTree as ET
import html
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime

# Import utilities
from .utils import handle_operation, ProcessingError, DataPersistence

logger = logging.getLogger(__name__)


class XMLChunker:
    """
    Advanced XML document chunker with structure-aware processing.
    
    This class provides intelligent chunking of XML documents while preserving
    document structure and extracting relevant metadata. It's optimized for
    regulatory documents with specific handling for various XML elements.
    """
    
    # XML element categories for processing
    STRUCTURAL_TAGS = {'SECTION', 'SUBPART', 'APPENDIX', 'CONTENTS', 'SUPLINF', 'PREAMB', 'REGTEXT'}
    CONTENT_TAGS = {'P', 'E', 'NOTE', 'HD', 'SUBJECT', 'SECTNO'}
    IGNORED_TAGS = {'PRTPAGE', 'GPH', 'GID', 'BILCOD', 'FRDOC', 'STARS'}
    
    def __init__(
        self, 
        chunk_words: int = 500,
        overlap_sentences: int = 1,
        encoding: str = 'utf-8'
    ):
        """
        Initialize XMLChunker with configuration.
        
        Args:
            chunk_words: Target number of words per chunk
            overlap_sentences: Number of sentences to overlap between chunks
            encoding: Text encoding for file operations
            
        Example:
            chunker = XMLChunker(chunk_words=300, overlap_sentences=2)
        """
        self.chunk_words = chunk_words
        self.overlap_sentences = overlap_sentences
        self.encoding = encoding
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'total_chunks': 0,
            'processing_errors': 0
        }
        
        logger.info(f"XMLChunker initialized: words={chunk_words}, overlap={overlap_sentences}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and normalized text
            
        Example:
            clean = chunker.clean_text("  HTML&nbsp;encoded text  ")
            # Returns: "HTML encoded text"
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize whitespace
        text = re.sub(r'\\s+', ' ', text.strip())
        
        return text
    
    def process_special_elements(self, elem: ET.Element) -> Optional[str]:
        """
        Handle special XML elements with custom processing rules.
        
        Args:
            elem: XML element to process
            
        Returns:
            Processed text or None if element should be skipped
            
        Example:
            # For <SU>1</SU> element
            text = chunker.process_special_elements(su_element)
            # Returns: "[1]"
        """
        tag = elem.tag
        
        if tag == "SU":
            # Superscript references
            return f"[{elem.text}]" if elem.text else ""
        
        elif tag == "FTREF":
            # Footnote reference markers
            return "[footnote_ref]"
        
        elif tag in self.IGNORED_TAGS:
            # Remove page numbers, graphics placeholders, etc.
            return ""
        
        elif tag == "GPH":
            # Graphics/table placeholders with ID if available
            gid = elem.find("GID")
            if gid is not None and gid.text:
                return f"[graphic/table: {gid.text}]"
            return "[graphic/table]"
        
        elif tag == "FTNT":
            # Footnote content - extract text safely
            text_parts = []
            if elem.text:
                text_parts.append(elem.text.strip())
            
            for child in elem:
                if child.text:
                    text_parts.append(child.text.strip())
                if child.tail:
                    text_parts.append(child.tail.strip())
            
            return ' '.join(part for part in text_parts if part)
        
        return None
    
    def extract_text_from_element(self, elem: ET.Element) -> str:
        """
        Extract all text content from an XML element and its children.
        
        Args:
            elem: XML element to extract text from
            
        Returns:
            Extracted and cleaned text content
            
        Example:
            text = chunker.extract_text_from_element(paragraph_element)
        """
        # Check for special element handling first
        special_text = self.process_special_elements(elem)
        if special_text is not None:
            return special_text
        
        # Extract all text using itertext for safety
        text_parts = []
        for text in elem.itertext():
            cleaned = self.clean_text(text)
            if cleaned:
                text_parts.append(cleaned)
        
        return " ".join(text_parts)
    
    def merge_footnotes(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract footnotes and create a mapping of reference numbers to content.
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary mapping footnote references to content
            
        Example:
            footnotes = chunker.merge_footnotes(root_element)
            # Returns: {'1': 'Footnote content...', '2': 'Another footnote...'}
        """
        footnotes = {}
        
        for ftnt in root.findall(".//FTNT"):
            # Find reference number in footnote
            for su in ftnt.findall(".//SU"):
                ref_num = su.text
                if ref_num:
                    # Extract footnote text (excluding reference number)
                    footnote_text = self.extract_text_from_element(ftnt)
                    # Clean up reference number from beginning
                    footnote_text = re.sub(r'^\\[\\d+\\]\\s*', '', footnote_text)
                    footnotes[ref_num] = footnote_text.strip()
        
        return footnotes
    
    def replace_footnote_references(self, root: ET.Element, footnotes: Dict[str, str]) -> None:
        """
        Replace footnote references with actual footnote content.
        
        Args:
            root: Root XML element
            footnotes: Dictionary of footnote content
            
        Example:
            chunker.replace_footnote_references(root, footnotes)
            # Modifies the XML tree in place
        """
        for p in root.findall(".//P"):
            for su in p.findall(".//SU"):
                ref_num = su.text
                if ref_num and ref_num in footnotes:
                    footnote_content = footnotes[ref_num]
                    if footnote_content:
                        # Replace superscript with footnote content in parentheses
                        su.text = f" ({footnote_content})"
    
    def preprocess_xml(self, root: ET.Element) -> None:
        """
        Preprocess XML document by merging footnotes and cleaning elements.
        
        Args:
            root: Root XML element to preprocess
            
        Example:
            chunker.preprocess_xml(document_root)
        """
        # Merge footnotes into main text
        footnotes = self.merge_footnotes(root)
        self.replace_footnote_references(root, footnotes)
        
        logger.debug(f"Preprocessed XML: merged {len(footnotes)} footnotes")
    
    def extract_document_context(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract document-level context information for building section headers.
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary with document context information
            
        Example:
            context = chunker.extract_document_context(root)
            # Returns: {'title': '...', 'part': '...', 'document_subject': '...'}
        """
        context = {}
        
        # Extract REGTEXT information
        regtext = root.find('.//REGTEXT')
        if regtext is not None:
            context['title'] = regtext.get('TITLE', '')
            context['part'] = regtext.get('PART', '')
        
        # Extract PREAMB SUBJECT
        preamb_subject = root.find('.//PREAMB/SUBJECT')
        if preamb_subject is not None:
            context['document_subject'] = self.extract_text_from_element(preamb_subject)
        
        return context
    
    def build_section_header(
        self, 
        header_parts: List[str], 
        doc_context: Dict[str, str], 
        block_type: str
    ) -> str:
        """
        Build comprehensive section header with document context.
        
        Args:
            header_parts: List of header components
            doc_context: Document context information
            block_type: Type of the structural block
            
        Returns:
            Formatted section header string
            
        Example:
            header = chunker.build_section_header(
                ['§ 123.45', 'Payment Rules'],
                {'title': 'Medicare', 'part': '123'},
                'SECTION'
            )
            # Returns: "Medicare CFR Part 123 > § 123.45 Payment Rules"
        """
        header_components = []
        
        # Add document-level context
        if doc_context.get('title') and doc_context.get('part'):
            header_components.append(f"{doc_context['title']} CFR Part {doc_context['part']}")
        
        # Add block-specific header
        if header_parts:
            if block_type == 'SECTION' and len(header_parts) >= 2:
                # Format: § sectno subject
                header_components.append(f"§ {header_parts[0]} {header_parts[1]}")
            else:
                header_components.extend(header_parts)
        
        return ' > '.join(header_components) if header_components else block_type
    
    def process_structural_element(self, elem: ET.Element, doc_context: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Process a structural XML element and extract its content block.
        
        Args:
            elem: Structural XML element
            doc_context: Document context information
            
        Returns:
            Dictionary with processed block information or None if empty
            
        Example:
            block = chunker.process_structural_element(section_element, context)
            # Returns: {
            #     'header': 'Section header',
            #     'text': 'Content text...',
            #     'type': 'SECTION',
            #     'word_count': 150
            # }
        """
        block_type = elem.tag
        header_parts = []
        content_paragraphs = []
        
        # Process different structural element types
        if block_type == 'SECTION':
            # Extract section number and subject
            sectno = elem.find('./SECTNO')
            subject = elem.find('./SUBJECT')
            
            if sectno is not None:
                header_parts.append(self.extract_text_from_element(sectno))
            if subject is not None:
                header_parts.append(self.extract_text_from_element(subject))
            
            # Extract all paragraphs
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
        
        elif block_type == 'SUBPART':
            # Extract header
            hd = elem.find('./HD')
            if hd is not None:
                header_parts.append(self.extract_text_from_element(hd))
            
            # Extract content from all child elements except header
            for child in elem:
                if child.tag != 'HD':
                    text = self.extract_text_from_element(child)
                    if text:
                        content_paragraphs.append(text)
        
        elif block_type == 'APPENDIX':
            # Extract appendix header
            hd = elem.find('./HD')
            if hd is not None:
                header_parts.append(self.extract_text_from_element(hd))
            
            # Extract all paragraphs
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
        
        elif block_type == 'CONTENTS':
            # Table of contents
            header_parts.append('Contents')
            
            # Extract content structure elements
            for child in elem.iter():
                if child.tag in {'SECTNO', 'SUBJECT', 'HD'}:
                    text = self.extract_text_from_element(child)
                    if text:
                        content_paragraphs.append(text)
        
        elif block_type in {'SUPLINF', 'PREAMB', 'REGTEXT'}:
            # Standard processing for these types
            type_names = {
                'SUPLINF': 'Supplementary Information',
                'PREAMB': 'Preamble', 
                'REGTEXT': 'Regulatory Text'
            }
            header_parts.append(type_names[block_type])
            
            # Extract all paragraphs
            for p in elem.findall('.//P'):
                para_text = self.extract_text_from_element(p)
                if para_text:
                    content_paragraphs.append(para_text)
        
        # Build section header and combine content
        section_header = self.build_section_header(header_parts, doc_context, block_type)
        full_text = ' '.join(content_paragraphs)
        
        if not full_text.strip():
            return None
        
        return {
            'header': section_header,
            'text': full_text,
            'type': block_type,
            'word_count': len(full_text.split())
        }
    
    def extract_logical_blocks(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract logical content blocks from XML document structure.
        
        Args:
            root: Root XML element
            
        Returns:
            List of logical block dictionaries
            
        Example:
            blocks = chunker.extract_logical_blocks(document_root)
            # Returns list of block dictionaries with header, text, type, etc.
        """
        logical_blocks = []
        
        # Extract document context for headers
        doc_context = self.extract_document_context(root)
        
        # Find and process all structural elements
        for elem in root.iter():
            if elem.tag in self.STRUCTURAL_TAGS:
                block = self.process_structural_element(elem, doc_context)
                if block:
                    logical_blocks.append(block)
        
        logger.debug(f"Extracted {len(logical_blocks)} logical blocks")
        return logical_blocks
    
    def split_into_chunks_with_overlap(
        self, 
        text: str, 
        max_words: int, 
        overlap_sentences: int
    ) -> List[str]:
        """
        Split text into chunks with sentence-level overlap.
        
        Args:
            text: Text to split
            max_words: Maximum words per chunk
            overlap_sentences: Number of sentences to overlap
            
        Returns:
            List of text chunks with overlap
            
        Example:
            chunks = chunker.split_into_chunks_with_overlap(
                "Sentence one. Sentence two. Sentence three.",
                10, 1
            )
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_words = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence exceeds limit
            if current_words + sentence_words > max_words and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - overlap_sentences)
                current_chunk = current_chunk[overlap_start:] + [sentence]
                current_words = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_words += sentence_words
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @handle_operation("document chunking", success_fields={'chunks_created': 0})
    def chunk_document(self, root: ET.Element, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chunk an XML document into semantic blocks with metadata.
        
        Args:
            root: Root XML element
            metadata: Base metadata for chunks
            
        Returns:
            Result dictionary with created chunks
            
        Example:
            result = chunker.chunk_document(xml_root, {'source_file': 'doc.xml'})
            chunks = result['chunks'] if result['status'] == 'success' else []
        """
        # Preprocess XML
        self.preprocess_xml(root)
        
        # Extract logical blocks
        logical_blocks = self.extract_logical_blocks(root)
        
        chunks = []
        chunk_index = 0
        
        for block in logical_blocks:
            section_header = block['header']
            text = block['text']
            word_count = block['word_count']
            
            if word_count <= self.chunk_words:
                # Block fits in single chunk
                chunks.append({
                    'text': text,
                    'section_header': section_header,
                    'metadata': {
                        **metadata,
                        'chunk_id': chunk_index,
                        'block_type': block['type'],
                        'word_count': word_count,
                        'is_sub_chunk': False
                    }
                })
                chunk_index += 1
            else:
                # Split large block into multiple chunks
                sub_chunks = self.split_into_chunks_with_overlap(
                    text, self.chunk_words, self.overlap_sentences
                )
                
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub_chunk,
                        'section_header': section_header,
                        'metadata': {
                            **metadata,
                            'chunk_id': chunk_index,
                            'sub_chunk_index': i,
                            'total_sub_chunks': len(sub_chunks),
                            'block_type': block['type'],
                            'word_count': len(sub_chunk.split()),
                            'is_sub_chunk': True
                        }
                    })
                    chunk_index += 1
        
        self.stats['total_chunks'] += len(chunks)
        
        return {
            'chunks': chunks,
            'chunks_created': len(chunks),
            'logical_blocks': len(logical_blocks),
            'processing_stats': {
                'total_words': sum(len(chunk['text'].split()) for chunk in chunks),
                'average_chunk_size': sum(len(chunk['text'].split()) for chunk in chunks) / len(chunks) if chunks else 0
            }
        }
    
    def extract_file_metadata(self, file_path: Union[str, Path], root: ET.Element) -> Dict[str, Any]:
        """
        Extract metadata from XML file and its content.
        
        Args:
            file_path: Path to the XML file
            root: Root XML element
            
        Returns:
            Dictionary with extracted metadata
            
        Example:
            metadata = chunker.extract_file_metadata('doc.xml', root_element)
        """
        file_path = Path(file_path)
        
        # Base metadata from file
        metadata = {
            'source_file': file_path.name,
            'file_type': 'xml',
            'processing_version': '3.0',
            'processed_at': datetime.now().isoformat()
        }
        
        # Extract XML metadata
        agency = root.find(".//AGENCY")
        if agency is not None and agency.text:
            metadata['agency'] = agency.text.strip()
        
        subject = root.find(".//SUBJECT")
        if subject is not None and subject.text:
            metadata['subject'] = subject.text.strip()
        
        # Extract date information
        dates = root.find(".//DATES")
        if dates is not None and dates.text:
            metadata['dates'] = dates.text.strip()
        
        # Extract CFR information
        cfr = root.find(".//CFR")
        if cfr is not None and cfr.text:
            metadata['cfr'] = cfr.text.strip()
        
        # Infer additional metadata from filename
        filename_lower = file_path.name.lower()
        
        # Extract year
        year_match = re.search(r'(20\\d{2})', filename_lower)
        if year_match:
            metadata['year'] = int(year_match.group(1))
        
        # Determine rule type
        if 'proposed' in filename_lower:
            metadata['rule_type'] = 'Proposed'
        elif 'final' in filename_lower:
            metadata['rule_type'] = 'Final'
        else:
            metadata['rule_type'] = 'Unknown'
        
        # Determine program type
        if 'hospice' in filename_lower:
            metadata['program'] = 'Hospice'
        elif 'snf' in filename_lower:
            metadata['program'] = 'SNF'
        elif 'mpfs' in filename_lower:
            metadata['program'] = 'MPFS'
        else:
            metadata['program'] = 'Unknown'
        
        return metadata
    
    @handle_operation("XML file processing", success_fields={'chunks_created': 0})
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a single XML file and extract chunks.
        
        Args:
            file_path: Path to XML file to process
            
        Returns:
            Result dictionary with processing outcome and chunks
            
        Example:
            result = chunker.process_file('document.xml')
            if result['status'] == 'success':
                chunks = result['chunks']
                print(f"Created {result['chunks_created']} chunks")
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ProcessingError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.xml':
            raise ProcessingError(f"File is not XML: {file_path}")
        
        try:
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract metadata
            metadata = self.extract_file_metadata(file_path, root)
            
            # Chunk document
            chunk_result = self.chunk_document(root, metadata)
            
            # Update statistics
            self.stats['files_processed'] += 1
            
            logger.info(f"Processed {file_path.name}: {chunk_result['chunks_created']} chunks")
            
            return {
                'file_path': str(file_path),
                'chunks': chunk_result['chunks'],
                'chunks_created': chunk_result['chunks_created'],
                'metadata': metadata,
                'processing_stats': chunk_result['processing_stats']
            }
            
        except ET.ParseError as e:
            self.stats['processing_errors'] += 1
            raise ProcessingError(f"XML parsing error in {file_path}: {e}")
        
        except Exception as e:
            self.stats['processing_errors'] += 1
            raise ProcessingError(f"Processing error in {file_path}: {e}")
    
    @handle_operation("batch file processing", success_fields={'files_processed': 0, 'total_chunks': 0})
    def process_files(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Process multiple XML files in batch.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Result dictionary with batch processing outcome
            
        Example:
            result = chunker.process_files(['doc1.xml', 'doc2.xml'])
            if result['status'] == 'success':
                all_chunks = result['all_chunks']
        """
        if not file_paths:
            return {
                'files_processed': 0,
                'total_chunks': 0,
                'all_chunks': [],
                'processing_errors': [],
                'file_results': []
            }
        
        all_chunks = []
        processing_errors = []
        file_results = []
        successful_files = 0
        
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                if result['status'] == 'success':
                    all_chunks.extend(result['chunks'])
                    successful_files += 1
                    file_results.append({
                        'file_path': str(file_path),
                        'status': 'success',
                        'chunks_created': result['chunks_created']
                    })
                else:
                    processing_errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
                    file_results.append({
                        'file_path': str(file_path),
                        'status': 'error',
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                processing_errors.append(error_msg)
                file_results.append({
                    'file_path': str(file_path),
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Batch processing completed: {successful_files}/{len(file_paths)} files successful")
        
        return {
            'files_processed': successful_files,
            'total_files': len(file_paths),
            'total_chunks': len(all_chunks),
            'all_chunks': all_chunks,
            'processing_errors': processing_errors,
            'file_results': file_results,
            'success_rate': successful_files / len(file_paths) if file_paths else 0
        }
    
    def save_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        output_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Save chunks to JSON file using standardized format.
        
        Args:
            chunks: List of chunk dictionaries to save
            output_path: Output file path
            
        Returns:
            Result dictionary with save operation outcome
            
        Example:
            result = chunker.save_chunks(chunks, 'output/chunks.json')
            if result['status'] == 'success':
                print(f"Saved {len(chunks)} chunks")
        """
        return DataPersistence.save_chunks(chunks, output_path, create_backup=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with current processing statistics
            
        Example:
            stats = chunker.get_statistics()
            print(f"Processed {stats['files_processed']} files")
        """
        return {
            **self.stats,
            'success_rate': (
                (self.stats['files_processed'] - self.stats['processing_errors']) / 
                max(self.stats['files_processed'], 1)
            )
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics to zero."""
        self.stats = {
            'files_processed': 0,
            'total_chunks': 0,
            'processing_errors': 0
        }
        logger.info("Processing statistics reset")