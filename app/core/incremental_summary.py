"""
incremental_summary.py

Simple incremental summary generation similar to incremental_pipeline pattern.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to Python path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Import required components
from summarizer import SummaryGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncrementalSummary:
    """
    Incremental summary generation for regulatory documents.
    Similar pattern to IncrementalPipeline.
    """
    
    def __init__(self):
        """Initialize IncrementalSummary."""
        self.data_dir = Path(config.docs_data_path)
        self.summary_dir = Path(config.summary_output_dir)
        self.chunks_dir = Path(config.build_faiss_output_folder)
        
        # Ensure summary directory exists
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize summarizer
        self.summarizer = SummaryGenerator()
        
        logger.info(f"🚀 Initialized IncrementalSummary")
        logger.info(f"📁 Data directory: {self.data_dir}")
        logger.info(f"📁 Summary directory: {self.summary_dir}")
        logger.info(f"📁 Chunks directory: {self.chunks_dir}")
    
    def find_xml_files(self) -> List[Path]:
        """Find all XML files in data directory."""
        xml_files = []
        for subdir in self.data_dir.iterdir():
            if subdir.is_dir():
                xml_files.extend(subdir.glob("*.xml"))
        return sorted(xml_files)
    
    def has_existing_summary(self, xml_file: Path) -> bool:
        """Check if summary already exists for given XML file."""
        summary_file = self.summary_dir / f"{xml_file.stem}.md"
        return summary_file.exists()
    
    def load_chunks_for_file(self, xml_file: Path) -> List[Dict]:
        """Load chunks for a specific XML file from chunks.json."""
        try:
            chunks_file = self.chunks_dir / "chunks.json"
            if not chunks_file.exists():
                logger.warning(f"📄 Chunks file not found: {chunks_file}")
                return []
            
            import json
            with open(chunks_file, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)
            
            # Filter chunks for this specific file
            filename = xml_file.name
            file_chunks = [chunk for chunk in all_chunks 
                          if chunk.get('metadata', {}).get('source_file') == filename]
            
            logger.info(f"📄 Found {len(file_chunks)} chunks for {filename}")
            return file_chunks
            
        except Exception as e:
            logger.error(f"❌ Error loading chunks for {xml_file.name}: {e}")
            return []
    
    def generate_summary_for_file(self, xml_file: Path) -> Dict:
        """Generate summary for a single XML file."""
        try:
            logger.info(f"📄 Generating summary for: {xml_file.name}")
            
            # Load chunks for this file
            chunks = self.load_chunks_for_file(xml_file)
            
            if not chunks:
                return {
                    'status': 'error',
                    'error': 'No chunks found for file'
                }
            
            # Generate summary using SummaryGenerator
            summary_result = self.summarizer.generate_report(chunks, xml_file.stem)
            
            if summary_result:
                return {
                    'status': 'success',
                    'file': str(xml_file),
                    'summary_length': len(summary_result),
                    'chunks_used': len(chunks)
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Summary generation failed'
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating summary for {xml_file}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_summary_for_specific_files(self, file_paths: List[str], force_regenerate: bool = False) -> Dict:
        """
        Generate summaries for specific files.
        
        Args:
            file_paths: List of file paths (relative to data directory) or filenames
            force_regenerate: If True, regenerate summary even if it exists
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"📄 Generating summaries for {len(file_paths)} specific files...")
        
        # Resolve file paths to full paths
        resolved_files = []
        for file_path in file_paths:
            resolved_file = self._resolve_file_path(file_path)
            if resolved_file:
                resolved_files.append(resolved_file)
                logger.info(f"   Resolved: {file_path} -> {resolved_file}")
            else:
                logger.warning(f"   Could not resolve: {file_path}")
        
        if not resolved_files:
            logger.error("❌ No valid files found to process")
            return {
                'processed': [],
                'failed': [f"Could not resolve: {path}" for path in file_paths],
                'status': 'error'
            }
        
        processed = []
        skipped = []
        failed = []
        
        for xml_file in resolved_files:
            if not force_regenerate and self.has_existing_summary(xml_file):
                logger.info(f"📄 Summary exists for {xml_file.name}, skipping...")
                skipped.append(str(xml_file))
            else:
                result = self.generate_summary_for_file(xml_file)
                if result['status'] == 'success':
                    processed.append(result)
                    logger.info(f"✅ Generated summary for {xml_file.name}")
                else:
                    failed.append({
                        'file': str(xml_file),
                        'error': result['error']
                    })
                    logger.warning(f"❌ Failed to generate summary for {xml_file.name}: {result['error']}")
        
        logger.info(f"📄 Specific file summary generation completed:")
        logger.info(f"   - Processed: {len(processed)}")
        logger.info(f"   - Skipped: {len(skipped)}")
        logger.info(f"   - Failed: {len(failed)}")
        
        return {
            'status': 'success',
            'processed': processed,
            'skipped': skipped,
            'failed': failed,
            'total_files': len(resolved_files)
        }
    
    def _resolve_file_path(self, file_path: str) -> Path:
        """
        Resolve a file path or filename to the full Path object.
        
        Args:
            file_path: File path or filename to resolve
            
        Returns:
            Full Path object if found, None otherwise
        """
        # If it's already a relative path with subdirectory, check if it exists
        if '/' in file_path or '\\' in file_path:
            full_path = self.data_dir / file_path
            if full_path.exists():
                return full_path
        
        # If it's just a filename, search for it in subdirectories
        filename = Path(file_path).name
        for subdir in self.data_dir.iterdir():
            if subdir.is_dir():
                potential_path = subdir / filename
                if potential_path.exists():
                    return potential_path
        
        return None
    
    def run_incremental_summary_update(self) -> Dict:
        """
        Run incremental summary update - main method like pipeline.
        """
        logger.info("📄 Starting incremental summary update...")
        
        try:
            # Find all XML files
            xml_files = self.find_xml_files()
            logger.info(f"📊 Found {len(xml_files)} XML files")
            
            # Process files that don't have summaries
            processed = []
            skipped = []
            failed = []
            
            for xml_file in xml_files:
                if self.has_existing_summary(xml_file):
                    logger.info(f"📄 Summary exists for {xml_file.name}, skipping...")
                    skipped.append(str(xml_file))
                else:
                    result = self.generate_summary_for_file(xml_file)
                    if result['status'] == 'success':
                        processed.append(result)
                        logger.info(f"✅ Generated summary for {xml_file.name}")
                    else:
                        failed.append({
                            'file': str(xml_file),
                            'error': result['error']
                        })
                        logger.warning(f"❌ Failed to generate summary for {xml_file.name}: {result['error']}")
            
            logger.info(f"📄 Incremental summary update completed:")
            logger.info(f"   - Processed: {len(processed)}")
            logger.info(f"   - Skipped: {len(skipped)}")
            logger.info(f"   - Failed: {len(failed)}")
            
            return {
                'status': 'success',
                'processed': processed,
                'skipped': skipped,
                'failed': failed,
                'total_files': len(xml_files)
            }
            
        except Exception as e:
            logger.error(f"❌ Incremental summary update failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# -------- MAIN ENTRY POINT --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental summary generation for regulatory documents")
    parser.add_argument("--files", "-f", nargs="+",
                      help="Generate summaries for specific files (relative paths or filenames)")
    parser.add_argument("--force", action="store_true",
                      help="Force regenerate summaries even if they exist")
    parser.add_argument("--incremental", "-i", action="store_true",
                      help="Run incremental update on all files (default)")
    
    args = parser.parse_args()
    
    # Initialize summary manager
    summary_manager = IncrementalSummary()
    
    if args.files:
        # Generate summaries for specific files
        result = summary_manager.generate_summary_for_specific_files(args.files, args.force)
        print(f"\n=== Specific File Summary Results ===")
    else:
        # Run incremental update (default behavior)
        result = summary_manager.run_incremental_summary_update()
        print(f"\n=== Incremental Summary Results ===")
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Processed: {len(result['processed'])}")
        print(f"Skipped: {len(result['skipped'])}")
        print(f"Failed: {len(result['failed'])}")
        print(f"Total files: {result['total_files']}")
        
        if result['processed']:
            print("\nProcessed files:")
            for item in result['processed']:
                print(f"  ✅ {item['file']} ({item['chunks_used']} chunks, {item['summary_length']} chars)")
        
        if result['failed']:
            print("\nFailed files:")
            for item in result['failed']:
                print(f"  ❌ {item['file']}: {item['error']}")
    else:
        print(f"Error: {result['error']}")