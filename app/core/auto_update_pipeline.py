"""
auto_update_pipeline.py

Complete automated pipeline for regulation updates.
Integrates regulation fetching, XML downloading, incremental processing, and embedding updates.
Provides simple, unified entry points with comprehensive error handling and rollback capabilities.

Functionality:
- Automated regulation discovery and downloading from Federal Register
- Incremental processing of new/changed XML files
- FAISS index updates with new embeddings
- Summary generation for new documents
- System validation and cost estimation

Process Flow:
1. Check for new regulations using Federal Register API
2. Download XML files for new regulations
3. Process files through incremental pipeline (chunking + embedding)
4. Update FAISS index with new embeddings
5. Generate summaries for new documents
6. Validate system consistency

Author: Fanxing Bu
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
# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Import pipeline components
from incremental_pipeline import IncrementalPipeline

# Import data fetcher components
try:
    from data_fetcher.fetch_regulations import (
        get_latest_documents, 
        get_single_document, 
        detect_program_type, 
        download_xml, 
        is_valid_xml,
        extract_year_from_title,
        generate_filename
    )
    DATA_FETCHER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Data fetcher not available: {e}")
    DATA_FETCHER_AVAILABLE = False

# Import incremental summary component
try:
    from incremental_summary import IncrementalSummary
    SUMMARY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Incremental summary not available: {e}")
    SUMMARY_AVAILABLE = False

class AutoUpdatePipeline:
    """
    Complete automated regulation update pipeline.
    
    Provides simple entry points for:
    - Full automated updates (fetch + download + process)
    - Incremental updates (process existing files)
    - Manual file processing
    - System monitoring and validation
    
    All operations include proper error handling, cost estimation, and rollback capabilities.
    """
    
    def __init__(self, model: str = None, days_back: int = None):
        """
        Initialize AutoUpdatePipeline.
        
        Args:
            model: Embedding model to use (from config if None)
            days_back: Days to look back for new regulations (from config if None)
        """
        self.model = model if model else config.default_embedding_model
        self.days_back = days_back if days_back else getattr(config, 'regulation_fetch_days_back', 365)
        
        # Initialize core pipeline
        self.pipeline = IncrementalPipeline(model=self.model)
        
        # Initialize incremental summary if available
        self.summary_manager = None
        if SUMMARY_AVAILABLE:
            self.summary_manager = IncrementalSummary()
        
        # Paths
        self.data_dir = Path(config.docs_data_path)
        
        logger.info(f"🚀 Initialized AutoUpdatePipeline")
        logger.info(f"💰 Model: {self.model}")
        logger.info(f"🗓️ Days back: {self.days_back}")
        logger.info(f"📁 Data directory: {self.data_dir}")
        logger.info(f"🌐 Data fetcher available: {DATA_FETCHER_AVAILABLE}")
        logger.info(f"📄 Incremental summary available: {SUMMARY_AVAILABLE}")

    def check_for_new_regulations(self) -> Dict:
        """
        Check for new regulations without downloading.
        
        Returns:
            Dictionary with check results
        """
        logger.info("🔍 Checking for new regulations...")
        
        if not DATA_FETCHER_AVAILABLE:
            return {
                'available': False,
                'error': 'Data fetcher not available',
                'new_regulations': [],
                'status': 'error'
            }
        
        try:
            # Get latest documents from Federal Register
            all_docs = get_latest_documents(self.days_back)
            logger.info(f"📄 Found {len(all_docs)} total documents")
            
            # Filter for relevant documents
            relevant_docs = []
            for doc in all_docs:
                doc_number = doc.get("document_number", "")
                doc_type = doc.get("type", "")
                publication_date = doc.get("publication_date", "")
                
                # Skip correction documents
                if doc_number.startswith("C"):
                    continue
                
                # Skip future-dated documents
                if publication_date and datetime.strptime(publication_date, "%Y-%m-%d") > datetime.now():
                    continue
                
                # Skip non-rule documents
                if doc_type not in ["Rule", "Proposed Rule"]:
                    continue
                
                # Check program type
                has_program, program_type = detect_program_type(doc)
                if not has_program:
                    continue
                
                # Check if file already exists
                filename = generate_filename(doc, program_type)
                if filename:
                    filepath = self.data_dir / program_type / filename
                    if not filepath.exists():
                        relevant_docs.append({
                            'document': doc,
                            'program_type': program_type,
                            'filename': filename,
                            'filepath': str(filepath)
                        })
            
            logger.info(f"📊 Found {len(relevant_docs)} new regulations")
            
            return {
                'available': len(relevant_docs) > 0,
                'new_regulations': relevant_docs,
                'total_found': len(all_docs),
                'relevant_found': len(relevant_docs),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking for regulations: {e}")
            return {
                'available': False,
                'error': str(e),
                'new_regulations': [],
                'status': 'error'
            }

    def download_new_regulations(self, regulations: List[Dict] = None) -> Dict:
        """
        Download new regulations from Federal Register.
        
        Args:
            regulations: List of regulations to download (checks automatically if None)
            
        Returns:
            Dictionary with download results
        """
        if regulations is None:
            check_result = self.check_for_new_regulations()
            if check_result['status'] != 'success':
                return {
                    'downloaded_files': [],
                    'failed_downloads': [],
                    'status': 'error',
                    'error': check_result.get('error', 'Unknown error checking regulations')
                }
            regulations = check_result['new_regulations']
        
        if not regulations:
            logger.info("📭 No new regulations to download")
            return {
                'downloaded_files': [],
                'failed_downloads': [],
                'status': 'success'
            }
        
        logger.info(f"⬇️ Downloading {len(regulations)} regulations...")
        
        downloaded_files = []
        failed_downloads = []
        
        for reg_info in regulations:
            try:
                doc = reg_info['document']
                program_type = reg_info['program_type']
                filename = reg_info['filename']
                
                # Create program directory
                program_dir = self.data_dir / program_type
                program_dir.mkdir(parents=True, exist_ok=True)
                
                # Download file
                logger.info(f"⬇️ Downloading: {filename}")
                success = download_xml(doc, self.data_dir, logger=logger)
                
                if success:
                    filepath = program_dir / filename
                    if filepath.exists() and is_valid_xml(filepath):
                        downloaded_files.append(str(filepath))
                        logger.info(f"✅ Downloaded: {filename}")
                    else:
                        failed_downloads.append({
                            'filename': filename,
                            'error': 'File not found after download or invalid XML'
                        })
                else:
                    failed_downloads.append({
                        'filename': filename,
                        'error': 'Download failed'
                    })
                
                # Add delay between downloads
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"❌ Error downloading {reg_info.get('filename', 'unknown')}: {e}")
                failed_downloads.append({
                    'filename': reg_info.get('filename', 'unknown'),
                    'error': str(e)
                })
        
        logger.info(f"📦 Download completed: {len(downloaded_files)} successful, {len(failed_downloads)} failed")
        
        return {
            'downloaded_files': downloaded_files,
            'failed_downloads': failed_downloads,
            'status': 'success' if not failed_downloads else 'partial_success'
        }

    def run_full_auto_update(self) -> Dict:
        """
        Run complete automated update: check + download + process regulations.
        This is the main entry point for automated updates.
        
        Returns:
            Dictionary with complete update results
        """
        logger.info("🚀 Starting full automated update...")
        start_time = time.time()
        
        try:
            # Step 1: Check for new regulations
            check_result = self.check_for_new_regulations()
            if check_result['status'] != 'success':
                raise Exception(f"Failed to check regulations: {check_result.get('error', 'Unknown')}")
            
            if not check_result['available']:
                logger.info("✅ No new regulations found")
                
                # Still run incremental update on existing files
                incremental_result = self.pipeline.full_incremental_update()
                
                end_time = time.time()
                return {
                    'regulations_check': check_result,
                    'download_result': {'downloaded_files': [], 'failed_downloads': []},
                    'incremental_result': incremental_result,
                    'total_cost': incremental_result['total_cost'],
                    'duration_seconds': round(end_time - start_time, 2),
                    'status': 'success'
                }
            
            # Step 2: Download new regulations
            download_result = self.download_new_regulations(check_result['new_regulations'])
            if download_result['status'] == 'error':
                raise Exception("Failed to download regulations")
            
            # Step 3: Run full incremental update (includes new downloads)
            incremental_result = self.pipeline.full_incremental_update()
            
            # Step 4: Run incremental summary update
            summary_result = None
            if self.summary_manager:
                logger.info("📄 Running incremental summary update...")
                summary_result = self.summary_manager.run_incremental_summary_update()
                logger.info(f"📄 Summary update completed: {summary_result['status']}")
            else:
                logger.info("📄 Skipping summary update (not available)")
            
            # Calculate totals
            total_cost = incremental_result['total_cost']
            end_time = time.time()
            
            logger.info("🎉 Full automated update completed!")
            logger.info(f"   - New regulations found: {check_result['relevant_found']}")
            logger.info(f"   - Files downloaded: {len(download_result['downloaded_files'])}")
            logger.info(f"   - Files processed: {len(incremental_result['process_result']['processed_files'])}")
            logger.info(f"   - Total cost: ${total_cost:.4f}")
            logger.info(f"   - Duration: {round(end_time - start_time, 2)}s")
            
            return {
                'regulations_check': check_result,
                'download_result': download_result,
                'incremental_result': incremental_result,
                'summary_result': summary_result,
                'total_cost': total_cost,
                'duration_seconds': round(end_time - start_time, 2),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Full auto update failed: {e}")
            end_time = time.time()
            return {
                'error': str(e),
                'duration_seconds': round(end_time - start_time, 2),
                'status': 'error'
            }

    def run_incremental_update(self) -> Dict:
        """
        Run incremental update on existing files only (no downloading).
        This is useful for processing files that were downloaded separately.
        
        Returns:
            Dictionary with incremental update results
        """
        logger.info("🔄 Starting incremental update...")
        
        try:
            result = self.pipeline.full_incremental_update()
            
            # Run incremental summary update
            summary_result = None
            if self.summary_manager:
                logger.info("📄 Running incremental summary update...")
                summary_result = self.summary_manager.run_incremental_summary_update()
                logger.info(f"📄 Summary update completed: {summary_result['status']}")
            else:
                logger.info("📄 Skipping summary update (not available)")
            
            logger.info("✅ Incremental update completed!")
            logger.info(f"   - Files deleted: {len(result['cleanup_result']['deleted_files'])}")
            logger.info(f"   - Files processed: {len(result['process_result']['processed_files'])}")
            logger.info(f"   - Total cost: ${result['total_cost']:.4f}")
            
            return {
                **result,
                'summary_result': summary_result
            }
            
        except Exception as e:
            logger.error(f"❌ Incremental update failed: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }

    def process_specific_files(self, file_paths: List[str]) -> Dict:
        """
        Process specific XML files.
        
        Args:
            file_paths: List of file paths (relative to data directory) or filenames
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"📄 Processing {len(file_paths)} specific files...")
        
        # Resolve file paths to full relative paths
        resolved_paths = []
        for file_path in file_paths:
            resolved_path = self._resolve_file_path(file_path)
            if resolved_path:
                resolved_paths.append(resolved_path)
                logger.info(f"   Resolved: {file_path} -> {resolved_path}")
            else:
                logger.warning(f"   Could not resolve: {file_path}")
        
        if not resolved_paths:
            logger.error("❌ No valid files found to process")
            return {
                'processed_files': [],
                'failed_files': [f"Could not resolve: {path}" for path in file_paths],
                'total_cost': 0.0,
                'status': 'error'
            }
        
        results = []
        total_cost = 0.0
        errors = []
        
        for file_path in resolved_paths:
            try:
                result = self.pipeline.process_single_file(file_path)
                results.append(result)
                
                if result['status'] == 'success':
                    total_cost += result['total_cost']
                else:
                    errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                errors.append(f"{file_path}: {str(e)}")
        
        successful_files = [r['file_path'] for r in results if r['status'] == 'success']
        
        # Generate summaries for processed files
        summary_result = None
        if self.summary_manager and successful_files:
            logger.info("📄 Generating summaries for processed files...")
            summary_result = self.summary_manager.generate_summary_for_specific_files(successful_files)
            logger.info(f"📄 Summary generation completed: {summary_result['status']}")
        
        logger.info(f"✅ Specific file processing completed:")
        logger.info(f"   - Files processed: {len(successful_files)}/{len(resolved_paths)}")
        logger.info(f"   - Total cost: ${total_cost:.4f}")
        
        if errors:
            logger.warning(f"⚠️ {len(errors)} files failed to process")
        
        return {
            'processed_files': successful_files,
            'failed_files': errors,
            'summary_result': summary_result,
            'total_cost': total_cost,
            'status': 'success' if not errors else 'partial_success'
        }

    def _resolve_file_path(self, file_path: str) -> Optional[str]:
        """
        Resolve a file path or filename to the full relative path.
        
        Args:
            file_path: File path or filename to resolve
            
        Returns:
            Full relative path if found, None otherwise
        """
        # If it's already a relative path with subdirectory, check if it exists
        if '/' in file_path or '\\' in file_path:
            full_path = self.data_dir / file_path
            if full_path.exists():
                return file_path
        
        # If it's just a filename, search for it in subdirectories
        filename = Path(file_path).name
        for subdir in self.data_dir.iterdir():
            if subdir.is_dir():
                potential_path = subdir / filename
                if potential_path.exists():
                    return str(potential_path.relative_to(self.data_dir))
        
        return None

    def remove_specific_files(self, file_paths: List[str]) -> Dict:
        """
        Remove specific files and their associated data.
        
        Args:
            file_paths: List of file paths (relative to data directory) or filenames
            
        Returns:
            Dictionary with removal results
        """
        logger.info(f"🗑️ Removing {len(file_paths)} specific files...")
        
        # Resolve file paths to full relative paths
        resolved_paths = []
        for file_path in file_paths:
            resolved_path = self._resolve_file_path(file_path)
            if resolved_path:
                resolved_paths.append(resolved_path)
                logger.info(f"   Resolved: {file_path} -> {resolved_path}")
            else:
                logger.warning(f"   Could not resolve: {file_path}")
        
        if not resolved_paths:
            logger.error("❌ No valid files found to remove")
            return {
                'removed_files': [],
                'failed_removals': [f"Could not resolve: {path}" for path in file_paths],
                'total_chunks_removed': 0,
                'total_embeddings_removed': 0,
                'total_rebuild_cost': 0.0,
                'status': 'error'
            }
        
        results = []
        total_rebuild_cost = 0.0
        errors = []
        
        for file_path in resolved_paths:
            try:
                result = self.pipeline.remove_file(file_path)
                results.append(result)
                
                if result['status'] == 'success':
                    total_rebuild_cost += result['rebuild_cost']
                else:
                    errors.append(f"{file_path}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error removing {file_path}: {e}")
                errors.append(f"{file_path}: {str(e)}")
        
        successful_removals = [r['file_path'] for r in results if r['status'] == 'success']
        total_chunks_removed = sum(r.get('chunks_removed', 0) for r in results if r['status'] == 'success')
        total_embeddings_removed = sum(r.get('embeddings_removed', 0) for r in results if r['status'] == 'success')
        
        logger.info(f"✅ File removal completed:")
        logger.info(f"   - Files removed: {len(successful_removals)}/{len(resolved_paths)}")
        logger.info(f"   - Chunks removed: {total_chunks_removed}")
        logger.info(f"   - Embeddings removed: {total_embeddings_removed}")
        logger.info(f"   - Rebuild cost: ${total_rebuild_cost:.4f}")
        
        if errors:
            logger.warning(f"⚠️ {len(errors)} files failed to remove")
        
        return {
            'removed_files': successful_removals,
            'failed_removals': errors,
            'total_chunks_removed': total_chunks_removed,
            'total_embeddings_removed': total_embeddings_removed,
            'total_rebuild_cost': total_rebuild_cost,
            'status': 'success' if not errors else 'partial_success'
        }

    def get_system_status(self) -> Dict:
        """Get comprehensive system status including regulation availability."""
        pipeline_status = self.pipeline.get_system_status()
        
        # Check for available regulations
        regulation_check = self.check_for_new_regulations()
        
        return {
            'model': self.model,
            'days_back': self.days_back,
            'data_fetcher_available': DATA_FETCHER_AVAILABLE,
            'pipeline_status': pipeline_status,
            'regulation_availability': regulation_check,
            'last_check': datetime.now().isoformat()
        }

    def validate_system(self) -> Dict:
        """Validate complete system health."""
        issues = []
        warnings = []
        
        # Check data directory
        if not self.data_dir.exists():
            issues.append(f"Data directory not found: {self.data_dir}")
        
        # Check data fetcher
        if not DATA_FETCHER_AVAILABLE:
            warnings.append("Data fetcher not available - cannot download new regulations")
        
        # Check pipeline
        pipeline_validation = self.pipeline.validate_system()
        issues.extend(pipeline_validation['issues'])
        warnings.extend(pipeline_validation['warnings'])
        
        # Check for available regulations
        if DATA_FETCHER_AVAILABLE:
            regulation_check = self.check_for_new_regulations()
            if regulation_check['status'] == 'success' and regulation_check['available']:
                warnings.append(f"{regulation_check['relevant_found']} new regulations available")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'pipeline_validation': pipeline_validation,
            'system_ready': len(issues) == 0 and DATA_FETCHER_AVAILABLE
        }

    def estimate_full_update_cost(self) -> Dict:
        """Estimate cost of running full auto update."""
        try:
            # Check for new regulations
            check_result = self.check_for_new_regulations()
            
            # Estimate incremental update cost
            incremental_estimate = self.pipeline.estimate_processing_cost()
            
            # If new regulations are available, add them to estimate
            new_reg_estimate = {
                'estimated_files': 0,
                'estimated_chunks': 0,
                'estimated_cost': 0.0
            }
            
            if check_result['status'] == 'success' and check_result['available']:
                # Rough estimate for new regulations (can't chunk without downloading)
                new_regulations = len(check_result['new_regulations'])
                estimated_chunks_per_file = 50  # Conservative estimate
                estimated_chunks = new_regulations * estimated_chunks_per_file
                
                dummy_chunks = [{'text': 'dummy text'} for _ in range(estimated_chunks)]
                estimated_cost = self.pipeline.faiss_manager.estimate_cost(dummy_chunks)
                
                new_reg_estimate = {
                    'estimated_files': new_regulations,
                    'estimated_chunks': estimated_chunks,
                    'estimated_cost': estimated_cost
                }
            
            total_estimated_cost = incremental_estimate['estimated_cost'] + new_reg_estimate['estimated_cost']
            
            return {
                'incremental_estimate': incremental_estimate,
                'new_regulations_estimate': new_reg_estimate,
                'total_estimated_cost': total_estimated_cost,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error estimating cost: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }


# -------- MAIN AUTO UPDATE PIPELINE RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated regulation update pipeline")
    parser.add_argument("--full-auto", action="store_true", 
                      help="Run full automated update (check + download + process)")
    parser.add_argument("--incremental", "-i", action="store_true", 
                      help="Run incremental update on existing files only")
    parser.add_argument("--check-regulations", "-c", action="store_true",
                      help="Check for new regulations without downloading")
    parser.add_argument("--download", "-d", action="store_true",
                      help="Download new regulations without processing")
    parser.add_argument("--process-files", "-p", nargs="+",
                      help="Process specific files (relative paths)")
    parser.add_argument("--remove-files", "-r", nargs="+", 
                      help="Remove specific files and their data")
    parser.add_argument("--status", "-s", action="store_true",
                      help="Show comprehensive system status")
    parser.add_argument("--validate", "-v", action="store_true",
                      help="Validate system health")
    parser.add_argument("--estimate", "-e", action="store_true",
                      help="Estimate full update cost")
    parser.add_argument("--model", "-m", type=str,
                      help="Embedding model to use")
    parser.add_argument("--days", type=int, 
                      default=4*365,
                      help="Days to look back for regulations (default: 1460)")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AutoUpdatePipeline(model=args.model, days_back=args.days)
    
    if args.status:
        status = pipeline.get_system_status()
        print("\n=== Auto Update Pipeline Status ===")
        print(f"Model: {status['model']}")
        print(f"Days back: {status['days_back']}")
        print(f"Data fetcher available: {status['data_fetcher_available']}")
        print(f"Last check: {status['last_check']}")
        
        if status['regulation_availability']['status'] == 'success':
            print(f"New regulations available: {status['regulation_availability']['available']}")
            if status['regulation_availability']['available']:
                print(f"Count: {status['regulation_availability']['relevant_found']}")
    
    elif args.validate:
        validation = pipeline.validate_system()
        print("\n=== System Validation ===")
        print(f"Valid: {validation['valid']}")
        print(f"System ready: {validation['system_ready']}")
        
        if validation['issues']:
            print("\nIssues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️ {warning}")
    
    elif args.estimate:
        estimate = pipeline.estimate_full_update_cost()
        if estimate['status'] == 'success':
            print("\n=== Cost Estimate ===")
            print(f"Incremental update: ${estimate['incremental_estimate']['estimated_cost']:.4f}")
            print(f"New regulations: ${estimate['new_regulations_estimate']['estimated_cost']:.4f}")
            print(f"Total estimated: ${estimate['total_estimated_cost']:.4f}")
        else:
            print(f"Error estimating cost: {estimate['error']}")
    
    elif args.check_regulations:
        result = pipeline.check_for_new_regulations()
        print(f"\nRegulation check:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"New regulations available: {result['available']}")
            print(f"Total found: {result['total_found']}")
            print(f"Relevant found: {result['relevant_found']}")
        else:
            print(f"Error: {result['error']}")
    
    elif args.download:
        result = pipeline.download_new_regulations()
        print(f"\nDownload result:")
        print(f"Status: {result['status']}")
        print(f"Downloaded: {len(result['downloaded_files'])}")
        print(f"Failed: {len(result['failed_downloads'])}")
    
    elif args.process_files:
        result = pipeline.process_specific_files(args.process_files)
        print(f"\nProcess specific files:")
        print(f"Status: {result['status']}")
        print(f"Processed: {len(result['processed_files'])}")
        print(f"Failed: {len(result['failed_files'])}")
        print(f"Cost: ${result['total_cost']:.4f}")
    
    elif args.remove_files:
        result = pipeline.remove_specific_files(args.remove_files)
        print(f"\nRemove specific files:")
        print(f"Status: {result['status']}")
        print(f"Removed: {len(result['removed_files'])}")
        print(f"Failed: {len(result['failed_removals'])}")
        print(f"Rebuild cost: ${result['total_rebuild_cost']:.4f}")
    
    elif args.incremental:
        result = pipeline.run_incremental_update()
        print(f"\nIncremental update:")
        print(f"Status: {result['status']}")
        print(f"Total cost: ${result['total_cost']:.4f}")
    
    elif args.full_auto:
        result = pipeline.run_full_auto_update()
        print(f"\nFull automated update:")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Duration: {result['duration_seconds']}s")
            print(f"Total cost: ${result['total_cost']:.4f}")
        else:
            print(f"Error: {result['error']}")
    
    else:
        print("Please specify an operation. Use --help for options.")
        parser.print_help()