"""
auto_update_pipeline.py

Automated pipeline that combines regulation fetching, incremental processing, and vector database updates.
This system automatically:
1. Fetches new regulations from Federal Register
2. Downloads XML files
3. Processes new files into chunks
4. Updates FAISS index with new embeddings
"""
import os
import json
import logging
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Import components
from incremental_pipeline import IncrementalPipeline
from data_fetcher.fetch_regulations import (
    get_latest_documents, 
    get_single_document, 
    detect_program_type, 
    download_xml, 
    is_valid_xml,
    extract_year_from_title,
    generate_filename
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoUpdatePipeline:
    """
    Automated pipeline for regulation updates.
    
    This class orchestrates the complete automated update process:
    1. Fetch new regulations from Federal Register
    2. Download XML files to appropriate directories
    3. Process new files through incremental pipeline
    4. Update FAISS index with new embeddings
    """
    
    def __init__(self, days_back: int = 365, model: str = None):
        """
        Initialize AutoUpdatePipeline.
        
        Args:
            days_back: Number of days to look back for new regulations
            model: Embedding model to use. If None, uses default from config.
                   Available models are defined in config files.
        """
        self.days_back = days_back
        self.model = model if model else config.default_embedding_model
        self.data_dir = Path(config.docs_data_path)
        self.incremental_pipeline = IncrementalPipeline(model=model)
        
        logger.info(f"🚀 Initialized AutoUpdatePipeline (looking back {days_back} days)")
        logger.info(f"💰 Using model: {self.model}")

    def fetch_new_regulations(self) -> List[Dict]:
        """
        Fetch new regulations from Federal Register.
        
        Returns:
            List of regulation documents that need processing
        """
        logger.info(f"🔍 Fetching regulations from the past {self.days_back} days...")
        
        try:
            # Get latest documents
            all_docs = get_latest_documents(self.days_back)
            logger.info(f"📄 Found {len(all_docs)} total documents")
            
            # Filter for relevant documents
            relevant_docs = []
            for doc in all_docs:
                doc_number = doc.get("document_number", "")
                doc_type = doc.get("type", "")
                title = doc.get("title", "")
                publication_date = doc.get("publication_date", "")
                
                # Skip correction documents
                if doc_number.startswith("C"):
                    logger.debug(f"⏭️ Skipping correction document: {doc_number}")
                    continue
                
                # Skip future-dated documents
                if publication_date and datetime.strptime(publication_date, "%Y-%m-%d") > datetime.now():
                    logger.debug(f"⏭️ Skipping future-dated document: {doc_number}")
                    continue
                
                # Skip non-rule documents
                if doc_type not in ["Rule", "Proposed Rule"]:
                    logger.debug(f"⏭️ Skipping non-rule document: {doc_number} ({doc_type})")
                    continue
                
                # Detect program type
                has_program, program_type = detect_program_type(doc)
                if not has_program:
                    logger.debug(f"⏭️ Skipping unrecognized program type: {doc_number} - {title}")
                    continue
                
                relevant_docs.append(doc)
                logger.info(f"✅ Found relevant document: {doc_number} ({program_type}) - {title}")
            
            logger.info(f"📊 Found {len(relevant_docs)} relevant documents")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"❌ Error fetching regulations: {e}")
            return []

    def download_new_files(self, regulations: List[Dict]) -> List[Path]:
        """
        Download XML files for new regulations.
        
        Args:
            regulations: List of regulation documents
            
        Returns:
            List of downloaded file paths
        """
        if not regulations:
            logger.info("📭 No new regulations to download")
            return []
        
        downloaded_files = []
        
        for doc in regulations:
            try:
                doc_number = doc.get("document_number", "")
                publication_date = doc.get("publication_date", "")
                doc_type = doc.get("type", "")
                
                # Get program type
                has_program, program_type = detect_program_type(doc)
                if not has_program:
                    continue
                
                # Create program directory
                program_dir = self.data_dir / program_type
                program_dir.mkdir(parents=True, exist_ok=True)
                
                # Check if file already exists (using unified filename generation)
                filename = generate_filename(doc, program_type)
                if not filename:
                    logger.error(f"Could not generate filename for document {doc_number}")
                    continue
                
                filepath = program_dir / filename
                
                if filepath.exists() and is_valid_xml(filepath):
                    logger.info(f"📁 File already exists: {filepath}")
                    downloaded_files.append(filepath)
                    continue
                
                # Download file
                logger.info(f"⬇️ Downloading: {filename}")
                success = download_xml(doc, self.data_dir, logger=logger)
                
                if success:
                    downloaded_files.append(filepath)
                else:
                    logger.error(f"❌ Failed to download: {filename}")
                    continue
                
                # Add delay between downloads
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"❌ Error downloading {doc.get('document_number', '')}: {e}")
                continue
        
        logger.info(f"📦 Downloaded {len(downloaded_files)} files")
        return downloaded_files

    def process_new_files(self, downloaded_files: List[Path]) -> List[Dict]:
        """
        Process newly downloaded files through incremental pipeline.
        
        Args:
            downloaded_files: List of downloaded file paths
            
        Returns:
            List of processing results
        """
        if not downloaded_files:
            logger.info("📭 No new files to process")
            return []
        
        logger.info(f"🔄 Processing {len(downloaded_files)} new files...")
        
        results = []
        for file_path in downloaded_files:
            try:
                # Convert to relative path for incremental processing
                relative_path = file_path.relative_to(self.data_dir)
                logger.info(f"📄 Processing: {relative_path}")
                
                # Process through incremental pipeline
                result = self.incremental_pipeline.process_single_file(str(relative_path))
                results.append(result)
                
                cost_display = "skipped" if result.get('estimated_cost', 0) == -1 else f"${result.get('estimated_cost', 0)}"
                logger.info(f"✅ Processed {relative_path}: {result['chunks_created']} chunks, {cost_display}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                continue
        
        return results

    def run_full_update(self) -> Dict:
        """
        Run the complete automated update process.
        
        Returns:
            Dictionary with update statistics
        """
        logger.info("🚀 Starting automated regulation update...")
        
        start_time = time.time()
        
        # Step 1: Fetch new regulations
        regulations = self.fetch_new_regulations()
        
        # Step 2: Download new files
        downloaded_files = self.download_new_files(regulations)
        
        # Step 3: Process new files
        processing_results = self.process_new_files(downloaded_files)
        
        # Calculate statistics
        total_chunks = sum(r.get("chunks_created", 0) for r in processing_results)
        total_embeddings = sum(r.get("embeddings_added", 0) for r in processing_results)
        total_cost = sum(r.get("estimated_cost", 0) for r in processing_results if r.get("estimated_cost", 0) >= 0)
        successful_files = len([r for r in processing_results if r.get("status") == "success"])
        
        end_time = time.time()
        duration = end_time - start_time
        
        stats = {
            "regulations": regulations,
            "regulations_found": len(regulations),
            "downloaded_files": downloaded_files,
            "files_downloaded": len(downloaded_files),
            "files_processed": len(processing_results),
            "files_successful": successful_files,
            "total_chunks_created": total_chunks,
            "total_embeddings_added": total_embeddings,
            "total_cost": round(total_cost, 4),
            "duration_seconds": round(duration, 2),
            "processing_results": processing_results
        }
        
        # Log summary
        logger.info("🎉 Automated update completed!")
        logger.info(f"   - Regulations found: {stats['regulations_found']}")
        logger.info(f"   - Files downloaded: {stats['files_downloaded']}")
        logger.info(f"   - Files processed: {stats['files_processed']}")
        logger.info(f"   - Successful: {stats['files_successful']}")
        logger.info(f"   - Total chunks: {stats['total_chunks_created']}")
        logger.info(f"   - Total embeddings: {stats['total_embeddings_added']}")
        logger.info(f"   - Total cost: ${stats['total_cost']}")
        logger.info(f"   - Duration: {stats['duration_seconds']}s")
        
        return stats

    def check_for_updates(self) -> bool:
        """
        Check if there are any new regulations available.
        
        Returns:
            True if updates are available, False otherwise
        """
        logger.info("🔍 Checking for new regulations...")
        
        regulations = self.fetch_new_regulations()
        
        if not regulations:
            logger.info("✅ No new regulations found")
            return False
        
        # Check if any of these regulations need downloading
        for doc in regulations:
            doc_number = doc.get("document_number", "")
            publication_date = doc.get("publication_date", "")
            doc_type = doc.get("type", "")
            
            has_program, program_type = detect_program_type(doc)
            if not has_program:
                continue
            
            # Check if file exists (using unified filename generation)
            filename = generate_filename(doc, program_type)
            if not filename:
                continue
            
            filepath = self.data_dir / program_type / filename
            
            if not filepath.exists():
                logger.info(f"🆕 New regulation found: {doc_number} ({program_type})")
                return True
        
        logger.info("✅ All regulations are up to date")
        return False

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        # Get incremental pipeline status
        incremental_status = self.incremental_pipeline.get_system_status()
        
        # Check for updates
        updates_available = self.check_for_updates()
        
        return {
            **incremental_status,
            "updates_available": updates_available,
            "days_back": self.days_back,
            "last_check": datetime.now().isoformat()
        }


# -------- MAIN AUTO UPDATE RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated regulation update pipeline")
    parser.add_argument("--days", "-d", type=int, default=365, 
                      help="Number of days to look back for new regulations")
    parser.add_argument("--model", "-m", 
                      type=str,
                      help="Embedding model to use (defaults to config default)")
    parser.add_argument("--force", "-f", action="store_true",
                      help="Force processing even if files exist")
    parser.add_argument("--check", "-c", action="store_true",
                      help="Only check for new regulations, don't download or process")
    parser.add_argument("--status", "-s", action="store_true",
                      help="Show system status")
    
    args = parser.parse_args()
    
    # Initialize pipeline with specified model
    pipeline = AutoUpdatePipeline(days_back=args.days, model=args.model)
    
    if args.status:
        status = pipeline.incremental_pipeline.get_system_status()
        print("\n=== System Status ===")
        print(f"Model: {pipeline.model}")
        print(f"Processed files: {status['processed_files_count']}")
        print(f"Total chunks: {status['total_chunks']}")
        print(f"FAISS index size: {status['faiss_index_size']}")
        print(f"New files: {len(status['new_files'])}")
        print(f"Deleted files: {len(status['deleted_files'])}")
        
        if status['new_files']:
            print(f"\nNew files: {status['new_files']}")
        if status['deleted_files']:
            print(f"\nDeleted files: {status['deleted_files']}")
    
    elif args.check:
        has_updates = pipeline.check_for_updates()
        if has_updates:
            print("🆕 Updates available!")
        else:
            print("✅ System is up to date")
    
    else:
        result = pipeline.run_full_update()
        print(f"\n=== Auto Update Results ===")
        print(f"Model: {pipeline.model}")
        print(f"Regulations found: {result['regulations_found']}")
        print(f"Files downloaded: {result['files_downloaded']}")
        print(f"Processing results: {len(result['processing_results'])}")
        
        if result['processing_results']:
            total_cost = sum(r['estimated_cost'] for r in result['processing_results'] if r.get('estimated_cost', 0) >= 0)
            skipped_files = [r for r in result['processing_results'] if r.get('estimated_cost', 0) == -1]
            successful_files = [r for r in result['processing_results'] if r.get('status') == 'success']
            print(f"Files processed successfully: {len(successful_files)}")
            print(f"Files skipped (already exist): {len(skipped_files)}")
            print(f"Total cost: ${total_cost:.4f}") 