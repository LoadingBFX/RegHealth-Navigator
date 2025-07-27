"""
mpfs_summary_generator.py

Specialized summary generator for MPFS (Medicare Physician Fee Schedule) documents only.
Provides targeted summary generation for MPFS regulations with program-specific filtering.

Functionality:
- Filter and process only MPFS documents
- Generate summaries for MPFS files only
- Support for specific MPFS file processing
- Incremental MPFS summary updates
- MPFS-specific validation and error handling

Author: Fanxing Bu
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
from incremental_summary import IncrementalSummary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MpfssummaryGenerator(IncrementalSummary):
    """
    Specialized summary generator for MPFS documents only.
    Extends IncrementalSummary with MPFS-specific filtering.
    """
    
    def __init__(self):
        """Initialize MPFS Summary Generator."""
        super().__init__()
        logger.info(f"🚀 Initialized MPFS Summary Generator")
        logger.info(f"📁 MPFS data directory: {self.data_dir / 'MPFS'}")
    
    def find_mpfs_files(self) -> List[Path]:
        """Find all MPFS XML files in data directory."""
        mpfs_dir = self.data_dir / "MPFS"
        if not mpfs_dir.exists():
            logger.warning(f"⚠️ MPFS directory not found: {mpfs_dir}")
            return []
        
        xml_files = list(mpfs_dir.glob("*.xml"))
        logger.info(f"📄 Found {len(xml_files)} MPFS XML files")
        return sorted(xml_files)
    
    def find_mpfs_files_without_summaries(self) -> List[Path]:
        """Find MPFS files that don't have summaries yet."""
        mpfs_files = self.find_mpfs_files()
        files_without_summaries = []
        
        for xml_file in mpfs_files:
            if not self.has_existing_summary(xml_file):
                files_without_summaries.append(xml_file)
        
        logger.info(f"📄 Found {len(files_without_summaries)} MPFS files without summaries")
        return files_without_summaries
    
    def generate_summary_for_mpfs_files(self, file_paths: List[str] = None, force_regenerate: bool = False) -> Dict:
        """
        Generate summaries for MPFS files.
        
        Args:
            file_paths: List of MPFS file paths or filenames (optional, if None, process all MPFS files)
            force_regenerate: If True, regenerate summary even if it exists
            
        Returns:
            Dictionary with processing results
        """
        if file_paths:
            # Process specific MPFS files
            logger.info(f"📄 Generating summaries for {len(file_paths)} specific MPFS files...")
            
            # Filter to ensure only MPFS files
            mpfs_files = []
            for file_path in file_paths:
                if self._is_mpfs_file(file_path):
                    mpfs_files.append(file_path)
                else:
                    logger.warning(f"⚠️ Skipping non-MPFS file: {file_path}")
            
            if not mpfs_files:
                logger.error("❌ No valid MPFS files found to process")
                return {
                    'processed': [],
                    'skipped': [],
                    'failed': [f"Not MPFS files: {file_paths}"],
                    'status': 'error'
                }
            
            return self.generate_summary_for_specific_files(mpfs_files, force_regenerate)
        else:
            # Process all MPFS files
            logger.info("📄 Generating summaries for all MPFS files...")
            
            if force_regenerate:
                mpfs_files = self.find_mpfs_files()
            else:
                mpfs_files = self.find_mpfs_files_without_summaries()
            
            if not mpfs_files:
                logger.info("✅ All MPFS files already have summaries")
                return {
                    'processed': [],
                    'skipped': [],
                    'failed': [],
                    'status': 'success',
                    'total_files': 0
                }
            
            # Convert Path objects to strings for processing
            file_paths = [str(f.relative_to(self.data_dir)) for f in mpfs_files]
            return self.generate_summary_for_specific_files(file_paths, force_regenerate)
    
    def run_mpfs_incremental_summary_update(self, force_regenerate: bool = False) -> Dict:
        """
        Run incremental summary update for MPFS files only.
        
        Args:
            force_regenerate: If True, regenerate all MPFS summaries
            
        Returns:
            Dictionary with processing results
        """
        logger.info("📄 Starting MPFS incremental summary update...")
        
        try:
            # Find MPFS files
            if force_regenerate:
                mpfs_files = self.find_mpfs_files()
            else:
                mpfs_files = self.find_mpfs_files_without_summaries()
            
            logger.info(f"📊 Found {len(mpfs_files)} MPFS files to process")
            
            if not mpfs_files:
                logger.info("✅ All MPFS files already have summaries")
                return {
                    'status': 'success',
                    'processed': [],
                    'skipped': [],
                    'failed': [],
                    'total_files': 0
                }
            
            # Process files
            processed = []
            skipped = []
            failed = []
            
            for xml_file in mpfs_files:
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
            
            logger.info(f"📄 MPFS incremental summary update completed:")
            logger.info(f"   - Processed: {len(processed)}")
            logger.info(f"   - Skipped: {len(skipped)}")
            logger.info(f"   - Failed: {len(failed)}")
            
            return {
                'status': 'success',
                'processed': processed,
                'skipped': skipped,
                'failed': failed,
                'total_files': len(mpfs_files)
            }
            
        except Exception as e:
            logger.error(f"❌ MPFS incremental summary update failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _is_mpfs_file(self, file_path: str) -> bool:
        """Check if a file path corresponds to an MPFS file."""
        # Check if path contains MPFS
        if 'MPFS' in file_path.upper():
            return True
        
        # Check if it's a filename that matches MPFS pattern
        filename = Path(file_path).name
        if filename.upper().startswith(('MPFS', '20') and 'MPFS' in filename.upper()):
            return True
        
        return False
    
    def get_mpfs_summary_status(self) -> Dict:
        """Get status of MPFS summary generation."""
        mpfs_files = self.find_mpfs_files()
        files_with_summaries = []
        files_without_summaries = []
        
        for xml_file in mpfs_files:
            if self.has_existing_summary(xml_file):
                files_with_summaries.append(xml_file.name)
            else:
                files_without_summaries.append(xml_file.name)
        
        return {
            'total_mpfs_files': len(mpfs_files),
            'files_with_summaries': files_with_summaries,
            'files_without_summaries': files_without_summaries,
            'summary_coverage': f"{len(files_with_summaries)}/{len(mpfs_files)} ({len(files_with_summaries)/len(mpfs_files)*100:.1f}%)" if mpfs_files else "0/0 (0%)"
        }


# -------- MAIN ENTRY POINT --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MPFS-specific summary generation for regulatory documents")
    parser.add_argument("--files", "-f", nargs="+",
                      help="Generate summaries for specific MPFS files (relative paths or filenames)")
    parser.add_argument("--force", action="store_true",
                      help="Force regenerate summaries even if they exist")
    parser.add_argument("--incremental", "-i", action="store_true",
                      help="Run incremental update on all MPFS files (default)")
    parser.add_argument("--status", "-s", action="store_true",
                      help="Show MPFS summary status")
    
    args = parser.parse_args()
    
    # Initialize MPFS summary generator
    mpfs_generator = MpfssummaryGenerator()
    
    if args.status:
        status = mpfs_generator.get_mpfs_summary_status()
        print(f"\n=== MPFS Summary Status ===")
        print(f"Total MPFS files: {status['total_mpfs_files']}")
        print(f"Summary coverage: {status['summary_coverage']}")
        
        if status['files_with_summaries']:
            print(f"\nFiles with summaries ({len(status['files_with_summaries'])}):")
            for file in status['files_with_summaries']:
                print(f"  ✅ {file}")
        
        if status['files_without_summaries']:
            print(f"\nFiles without summaries ({len(status['files_without_summaries'])}):")
            for file in status['files_without_summaries']:
                print(f"  ❌ {file}")
    
    elif args.files:
        # Generate summaries for specific MPFS files
        result = mpfs_generator.generate_summary_for_mpfs_files(args.files, args.force)
        print(f"\n=== MPFS Specific File Summary Results ===")
    else:
        # Run incremental update (default behavior)
        result = mpfs_generator.run_mpfs_incremental_summary_update(args.force)
        print(f"\n=== MPFS Incremental Summary Results ===")
    
    if args.files or not args.status:
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