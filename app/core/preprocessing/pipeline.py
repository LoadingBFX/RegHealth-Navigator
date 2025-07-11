"""
Processing Pipeline

Provides high-level orchestration for document processing workflows with
automated regulation fetching, batch processing, and scheduled updates.

Example:
    # Basic processing pipeline
    pipeline = ProcessingPipeline(
        data_dir="data/xml",
        output_dir="output",
        api_key="your-openai-key"
    )
    
    # Process all pending files
    result = pipeline.run_incremental_update()
    
    # Auto-update pipeline with regulation fetching
    auto_pipeline = AutoUpdatePipeline(
        data_dir="data/xml",
        output_dir="output",
        api_key="your-openai-key"
    )
    
    # Run complete automated workflow
    result = auto_pipeline.run_full_auto_update()
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime, timedelta

# Import core components
from .incremental_manager import IncrementalManager
from .utils import handle_operation, ProcessingError, combine_results

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    High-level processing pipeline for document workflows.
    
    This class provides simplified interfaces for common processing tasks
    while managing the underlying complexity of the incremental manager.
    """
    
    def __init__(
        self,
        data_dir: Union[str, Path],
        output_dir: Union[str, Path],
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        chunk_words: int = 500,
        overlap_sentences: int = 1
    ):
        """
        Initialize ProcessingPipeline.
        
        Args:
            data_dir: Directory containing XML files
            output_dir: Directory for output files
            api_key: OpenAI API key
            model: Embedding model to use
            chunk_words: Target words per chunk
            overlap_sentences: Sentence overlap
            
        Example:
            pipeline = ProcessingPipeline(
                "data/xml",
                "output",
                model="text-embedding-3-large"
            )
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.model = model
        
        # Initialize incremental manager
        self.manager = IncrementalManager(
            data_directory=data_dir,
            output_directory=output_dir,
            api_key=api_key,
            model=model,
            chunk_words=chunk_words,
            overlap_sentences=overlap_sentences
        )
        
        logger.info(f"ProcessingPipeline initialized")
        logger.info(f"  Data: {self.data_dir}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Model: {self.model}")
    
    @handle_operation("incremental update", success_fields={'files_processed': 0, 'total_cost': 0.0})
    def run_incremental_update(self) -> Dict[str, Any]:
        """
        Run incremental update to process new/modified files and clean up deleted files.
        
        Returns:
            Result dictionary with update statistics
            
        Example:
            result = pipeline.run_incremental_update()
            if result['status'] == 'success':
                print(f"Processed {result['files_processed']} files, cost: ${result['total_cost']:.4f}")
        """
        logger.info("Starting incremental update")
        
        # Run full incremental update
        update_result = self.manager.full_incremental_update()
        
        if update_result['status'] != 'success':
            raise ProcessingError(f"Incremental update failed: {update_result.get('error')}")
        
        files_processed = update_result['files_processed']
        files_removed = update_result['files_removed']
        total_cost = update_result['total_cost']
        errors = update_result.get('errors', [])
        
        # Log summary
        logger.info(f"Incremental update completed:")
        logger.info(f"  Files processed: {files_processed}")
        logger.info(f"  Files removed: {files_removed}")
        logger.info(f"  Total cost: ${total_cost:.4f}")
        
        if errors:
            logger.warning(f"  Errors: {len(errors)}")
            for error in errors[:5]:  # Log first 5 errors
                logger.warning(f"    {error}")
        
        return {
            'files_processed': files_processed,
            'files_removed': files_removed,
            'total_cost': total_cost,
            'errors': errors,
            'summary': update_result.get('summary', {}),
            'operation_details': update_result
        }
    
    @handle_operation("batch processing", success_fields={'files_processed': 0, 'total_cost': 0.0})
    def process_files(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Process specific files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Result dictionary with processing statistics
            
        Example:
            result = pipeline.process_files(["MPFS/doc1.xml", "MPFS/doc2.xml"])
        """
        if not file_paths:
            return {
                'files_processed': 0,
                'total_cost': 0.0,
                'file_results': [],
                'errors': []
            }
        
        logger.info(f"Processing {len(file_paths)} specific files")
        
        # Process files through manager
        batch_result = self.manager.process_multiple_files(file_paths)
        
        if batch_result['status'] != 'success':
            raise ProcessingError(f"Batch processing failed: {batch_result.get('error')}")
        
        files_processed = batch_result['files_processed']
        total_cost = batch_result['total_cost']
        errors = batch_result.get('errors', [])
        
        logger.info(f"Batch processing completed: {files_processed}/{len(file_paths)} files successful")
        
        return {
            'files_processed': files_processed,
            'total_files': len(file_paths),
            'total_cost': total_cost,
            'file_results': batch_result['file_results'],
            'errors': errors,
            'success_rate': batch_result.get('success_rate', 0.0)
        }
    
    @handle_operation("file removal", success_fields={'files_removed': 0, 'rebuild_cost': 0.0})
    def remove_files(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Remove specific files and their data.
        
        Args:
            file_paths: List of file paths to remove
            
        Returns:
            Result dictionary with removal statistics
            
        Example:
            result = pipeline.remove_files(["old_doc1.xml", "old_doc2.xml"])
        """
        if not file_paths:
            return {
                'files_removed': 0,
                'rebuild_cost': 0.0,
                'removal_results': [],
                'errors': []
            }
        
        logger.info(f"Removing {len(file_paths)} files")
        
        removal_results = []
        total_rebuild_cost = 0.0
        successful_removals = 0
        errors = []
        
        for file_path in file_paths:
            try:
                remove_result = self.manager.remove_file(file_path)
                removal_results.append(remove_result)
                
                if remove_result['status'] == 'success':
                    successful_removals += 1
                    total_rebuild_cost += remove_result.get('rebuild_cost', 0.0)
                else:
                    errors.append(f"{file_path}: {remove_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                errors.append(error_msg)
                removal_results.append({
                    'file_path': str(file_path),
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"Error removing {file_path}: {e}")
        
        logger.info(f"File removal completed: {successful_removals}/{len(file_paths)} successful")
        
        return {
            'files_removed': successful_removals,
            'total_files': len(file_paths),
            'rebuild_cost': total_rebuild_cost,
            'removal_results': removal_results,
            'errors': errors,
            'success_rate': successful_removals / len(file_paths) if file_paths else 0
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            System status dictionary
            
        Example:
            status = pipeline.get_system_status()
            print(f"System health: {'✅' if status['healthy'] else '❌'}")
        """
        # Get manager status
        manager_status = self.manager.get_status()
        
        # Get validation results
        validation = self.manager.validate_system()
        
        # Determine overall health
        healthy = validation['valid'] and manager_status['data_consistency']['chunks_vs_metadata']
        
        return {
            'healthy': healthy,
            'model': self.model,
            'data_directory': str(self.data_dir),
            'output_directory': str(self.output_dir),
            'statistics': {
                'total_chunks': manager_status['total_chunks'],
                'index_size': manager_status['index_size'],
                'total_cost': manager_status['total_cost'],
                'files_tracked': manager_status['files_tracked'],
                'pending_changes': manager_status['pending_changes'],
                'pending_deletions': manager_status['pending_deletions']
            },
            'file_status': manager_status['files_exist'],
            'data_consistency': manager_status['data_consistency'],
            'validation': {
                'valid': validation['valid'],
                'issues': validation['issues'],
                'warnings': validation['warnings']
            }
        }
    
    def estimate_update_cost(self) -> Dict[str, Any]:
        """
        Estimate cost of running incremental update.
        
        Returns:
            Cost estimation dictionary
            
        Example:
            estimate = pipeline.estimate_update_cost()
            print(f"Estimated cost: ${estimate['total_estimated_cost']:.4f}")
        """
        return self.manager.estimate_cost()


class AutoUpdatePipeline(ProcessingPipeline):
    """
    Automated update pipeline with regulation fetching capabilities.
    
    Extends ProcessingPipeline to add automatic regulation discovery,
    downloading, and processing workflows.
    """
    
    def __init__(
        self,
        data_dir: Union[str, Path],
        output_dir: Union[str, Path],
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        chunk_words: int = 500,
        overlap_sentences: int = 1,
        days_back: int = 30
    ):
        """
        Initialize AutoUpdatePipeline.
        
        Args:
            data_dir: Directory containing XML files
            output_dir: Directory for output files
            api_key: OpenAI API key
            model: Embedding model to use
            chunk_words: Target words per chunk
            overlap_sentences: Sentence overlap
            days_back: Days to look back for new regulations
            
        Example:
            pipeline = AutoUpdatePipeline(
                "data/xml",
                "output", 
                days_back=7
            )
        """
        super().__init__(data_dir, output_dir, api_key, model, chunk_words, overlap_sentences)
        
        self.days_back = days_back
        
        # Try to import regulation fetcher
        try:
            # Add the parent directory to path for imports
            parent_dir = Path(__file__).parent.parent
            if str(parent_dir) not in sys.path:
                sys.path.append(str(parent_dir))
            
            from data_fetcher.fetch_regulations import (
                get_latest_documents, download_xml, is_valid_xml,
                detect_program_type, generate_filename
            )
            
            self.regulation_fetcher = {
                'get_latest_documents': get_latest_documents,
                'download_xml': download_xml,
                'is_valid_xml': is_valid_xml,
                'detect_program_type': detect_program_type,
                'generate_filename': generate_filename,
                'available': True
            }
            
            logger.info("Regulation fetcher available")
            
        except ImportError as e:
            logger.warning(f"Regulation fetcher not available: {e}")
            self.regulation_fetcher = {'available': False}
    
    @handle_operation("regulation check", success_fields={'new_regulations': 0})
    def check_for_new_regulations(self) -> Dict[str, Any]:
        """
        Check for new regulations without downloading.
        
        Returns:
            Result dictionary with new regulation information
            
        Example:
            result = pipeline.check_for_new_regulations()
            if result['new_regulations'] > 0:
                print(f"Found {result['new_regulations']} new regulations")
        """
        if not self.regulation_fetcher['available']:
            raise ProcessingError("Regulation fetcher not available")
        
        logger.info(f"Checking for new regulations (last {self.days_back} days)")
        
        try:
            # Get latest documents
            all_docs = self.regulation_fetcher['get_latest_documents'](self.days_back)
            logger.info(f"Found {len(all_docs)} total documents")
            
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
                if publication_date:
                    try:
                        pub_date = datetime.strptime(publication_date, "%Y-%m-%d")
                        if pub_date > datetime.now():
                            continue
                    except ValueError:
                        continue
                
                # Skip non-rule documents
                if doc_type not in ["Rule", "Proposed Rule"]:
                    continue
                
                # Check program type
                has_program, program_type = self.regulation_fetcher['detect_program_type'](doc)
                if not has_program:
                    continue
                
                # Check if file already exists
                filename = self.regulation_fetcher['generate_filename'](doc, program_type)
                if filename:
                    filepath = self.data_dir / program_type / filename
                    if not filepath.exists():
                        relevant_docs.append({
                            'document': doc,
                            'program_type': program_type,
                            'filename': filename,
                            'filepath': str(filepath)
                        })
            
            logger.info(f"Found {len(relevant_docs)} new regulations")
            
            return {
                'new_regulations': len(relevant_docs),
                'total_found': len(all_docs),
                'regulation_list': relevant_docs,
                'programs_found': list(set(r['program_type'] for r in relevant_docs))
            }
            
        except Exception as e:
            raise ProcessingError(f"Error checking regulations: {e}")
    
    @handle_operation("regulation download", success_fields={'downloaded_files': 0})
    def download_new_regulations(self, regulations: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Download new regulations from Federal Register.
        
        Args:
            regulations: List of regulations to download (auto-detect if None)
            
        Returns:
            Result dictionary with download statistics
            
        Example:
            result = pipeline.download_new_regulations()
            print(f"Downloaded {result['downloaded_files']} files")
        """
        if not self.regulation_fetcher['available']:
            raise ProcessingError("Regulation fetcher not available")
        
        # Get regulations to download
        if regulations is None:
            check_result = self.check_for_new_regulations()
            if check_result['status'] != 'success':
                raise ProcessingError("Failed to check for new regulations")
            regulations = check_result['regulation_list']
        
        if not regulations:
            logger.info("No new regulations to download")
            return {
                'downloaded_files': 0,
                'failed_downloads': 0,
                'download_results': []
            }
        
        logger.info(f"Downloading {len(regulations)} regulations")
        
        download_results = []
        successful_downloads = 0
        failed_downloads = 0
        
        for reg_info in regulations:
            try:
                doc = reg_info['document']
                program_type = reg_info['program_type']
                filename = reg_info['filename']
                
                # Create program directory
                program_dir = self.data_dir / program_type
                program_dir.mkdir(parents=True, exist_ok=True)
                
                # Download file
                logger.info(f"Downloading: {filename}")
                success = self.regulation_fetcher['download_xml'](
                    doc, self.data_dir, logger=logger
                )
                
                if success:
                    filepath = program_dir / filename
                    if filepath.exists() and self.regulation_fetcher['is_valid_xml'](filepath):
                        successful_downloads += 1
                        download_results.append({
                            'filename': filename,
                            'filepath': str(filepath),
                            'program_type': program_type,
                            'status': 'success'
                        })
                        logger.info(f"✅ Downloaded: {filename}")
                    else:
                        failed_downloads += 1
                        download_results.append({
                            'filename': filename,
                            'status': 'error',
                            'error': 'File not found after download or invalid XML'
                        })
                else:
                    failed_downloads += 1
                    download_results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': 'Download failed'
                    })
                
                # Add delay between downloads
                time.sleep(1 + (0.5 * len(regulations) / 10))  # Adaptive delay
                
            except Exception as e:
                failed_downloads += 1
                download_results.append({
                    'filename': reg_info.get('filename', 'unknown'),
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"Error downloading {reg_info.get('filename', 'unknown')}: {e}")
        
        logger.info(f"Download completed: {successful_downloads} successful, {failed_downloads} failed")
        
        return {
            'downloaded_files': successful_downloads,
            'failed_downloads': failed_downloads,
            'total_attempted': len(regulations),
            'download_results': download_results,
            'success_rate': successful_downloads / len(regulations) if regulations else 0
        }
    
    @handle_operation("full auto update", success_fields={'total_cost': 0.0, 'files_processed': 0})
    def run_full_auto_update(self) -> Dict[str, Any]:
        """
        Run complete automated update workflow: check + download + process.
        
        Returns:
            Result dictionary with complete workflow statistics
            
        Example:
            result = pipeline.run_full_auto_update()
            print(f"Auto-update completed: {result['files_processed']} files, ${result['total_cost']:.4f}")
        """
        logger.info("Starting full automated update")
        start_time = time.time()
        
        try:
            # Step 1: Check for new regulations
            if self.regulation_fetcher['available']:
                check_result = self.check_for_new_regulations()
                new_regulations = check_result.get('regulation_list', [])
                
                # Step 2: Download new regulations
                if new_regulations:
                    download_result = self.download_new_regulations(new_regulations)
                    downloaded_files = download_result['downloaded_files']
                else:
                    download_result = {'downloaded_files': 0, 'failed_downloads': 0}
                    downloaded_files = 0
            else:
                logger.info("Regulation fetcher not available, skipping download phase")
                check_result = {'new_regulations': 0, 'regulation_list': []}
                download_result = {'downloaded_files': 0, 'failed_downloads': 0}
                downloaded_files = 0
            
            # Step 3: Run incremental update (processes both new downloads and existing files)
            update_result = self.run_incremental_update()
            if update_result['status'] != 'success':
                raise ProcessingError(f"Incremental update failed: {update_result.get('error')}")
            
            # Calculate totals
            total_cost = update_result['total_cost']
            files_processed = update_result['files_processed']
            files_removed = update_result['files_removed']
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Log comprehensive summary
            logger.info("🎉 Full automated update completed!")
            logger.info(f"   Duration: {duration:.1f} seconds")
            logger.info(f"   New regulations found: {check_result.get('new_regulations', 0)}")
            logger.info(f"   Files downloaded: {downloaded_files}")
            logger.info(f"   Files processed: {files_processed}")
            logger.info(f"   Files removed: {files_removed}")
            logger.info(f"   Total cost: ${total_cost:.4f}")
            
            return {
                'total_cost': total_cost,
                'files_processed': files_processed,
                'files_removed': files_removed,
                'files_downloaded': downloaded_files,
                'new_regulations_found': check_result.get('new_regulations', 0),
                'duration_seconds': round(duration, 2),
                'phase_results': {
                    'regulation_check': check_result,
                    'download': download_result,
                    'incremental_update': update_result
                },
                'summary': {
                    'regulation_fetcher_available': self.regulation_fetcher['available'],
                    'download_success_rate': download_result.get('success_rate', 0.0),
                    'processing_success': update_result['status'] == 'success',
                    'total_operations': (
                        check_result.get('new_regulations', 0) + 
                        files_processed + 
                        files_removed
                    )
                }
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"❌ Full auto update failed after {duration:.1f}s: {e}")
            raise ProcessingError(f"Auto update failed: {e}")
    
    def schedule_auto_update(
        self, 
        interval_hours: int = 24,
        max_cost_per_run: float = 10.0
    ) -> Dict[str, Any]:
        """
        Schedule periodic auto-updates (for demonstration - actual scheduling would use external tools).
        
        Args:
            interval_hours: Hours between updates
            max_cost_per_run: Maximum cost allowed per update run
            
        Returns:
            Scheduling configuration
            
        Example:
            config = pipeline.schedule_auto_update(interval_hours=12, max_cost_per_run=5.0)
        """
        # This is a conceptual implementation - real scheduling would use cron, systemd, etc.
        
        schedule_config = {
            'interval_hours': interval_hours,
            'max_cost_per_run': max_cost_per_run,
            'next_run': datetime.now() + timedelta(hours=interval_hours),
            'command': f"python -m preprocessing.pipeline --auto-update",
            'cost_limit_enabled': True,
            'pre_run_estimation': True
        }
        
        logger.info(f"Auto-update schedule configured:")
        logger.info(f"  Interval: {interval_hours} hours")
        logger.info(f"  Cost limit: ${max_cost_per_run:.2f}")
        logger.info(f"  Next run: {schedule_config['next_run']}")
        
        # Save schedule configuration
        schedule_file = self.output_dir / "schedule_config.json"
        from .utils import DataPersistence
        save_result = DataPersistence.save_json(schedule_config, schedule_file)
        
        if save_result['status'] == 'success':
            logger.info(f"Schedule saved to: {schedule_file}")
        
        return schedule_config


# CLI interface for running pipelines
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Document Processing Pipeline")
    parser.add_argument("--data-dir", required=True, help="Data directory path")
    parser.add_argument("--output-dir", required=True, help="Output directory path")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--model", default="text-embedding-3-small", help="Embedding model")
    
    # Operation selection
    parser.add_argument("--incremental", action="store_true", help="Run incremental update")
    parser.add_argument("--auto-update", action="store_true", help="Run full auto update")
    parser.add_argument("--check-regulations", action="store_true", help="Check for new regulations")
    parser.add_argument("--download", action="store_true", help="Download new regulations")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--estimate", action="store_true", help="Estimate update cost")
    
    # File operations
    parser.add_argument("--process-files", nargs="+", help="Process specific files")
    parser.add_argument("--remove-files", nargs="+", help="Remove specific files")
    
    # Configuration
    parser.add_argument("--chunk-words", type=int, default=500, help="Words per chunk")
    parser.add_argument("--overlap", type=int, default=1, help="Sentence overlap")
    parser.add_argument("--days-back", type=int, default=30, help="Days to look back for regulations")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load base configuration from config files
        from .config_loader import ConfigLoader
        config_loader = ConfigLoader()
        base_config = config_loader.get_processing_config()
        
        # Override with command line arguments (higher priority)
        config_overrides = {}
        if args.api_key:
            config_overrides['api_key'] = args.api_key
        if args.model and args.model != "text-embedding-3-small":  # Only override if different from default
            config_overrides['model'] = args.model
        if args.chunk_words != 500:  # Only override if different from default
            config_overrides['chunk_words'] = args.chunk_words
        if args.overlap != 1:  # Only override if different from default
            config_overrides['overlap_sentences'] = args.overlap
        if args.days_back != 30:  # Only override if different from default
            config_overrides['days_back'] = args.days_back
        
        # Always override paths if provided
        if args.data_dir:
            config_overrides['data_dir'] = args.data_dir
        if args.output_dir:
            config_overrides['output_dir'] = args.output_dir
        
        # Merge configurations (CLI args override config files)
        final_config = {**base_config, **config_overrides}
        
        # Choose pipeline type
        if args.auto_update or args.check_regulations or args.download:
            pipeline = AutoUpdatePipeline(**final_config)
        else:
            pipeline = ProcessingPipeline(**final_config)
        
        # Execute requested operation
        if args.status:
            status = pipeline.get_system_status()
            print("\\n=== System Status ===")
            print(f"Healthy: {'✅' if status['healthy'] else '❌'}")
            print(f"Model: {status['model']}")
            print(f"Total chunks: {status['statistics']['total_chunks']}")
            print(f"Index size: {status['statistics']['index_size']}")
            print(f"Total cost: ${status['statistics']['total_cost']:.4f}")
            print(f"Pending changes: {status['statistics']['pending_changes']}")
            
        elif args.estimate:
            estimate = pipeline.estimate_update_cost()
            print("\\n=== Cost Estimate ===")
            print(f"Files to process: {estimate['estimated_files']}")
            print(f"Estimated chunks: {estimate['estimated_chunks']}")
            print(f"Estimated cost: ${estimate['total_estimated_cost']:.4f}")
            
        elif args.check_regulations and isinstance(pipeline, AutoUpdatePipeline):
            result = pipeline.check_for_new_regulations()
            print(f"\\nNew regulations found: {result['new_regulations']}")
            print(f"Total documents checked: {result['total_found']}")
            
        elif args.download and isinstance(pipeline, AutoUpdatePipeline):
            result = pipeline.download_new_regulations()
            print(f"\\nDownload results:")
            print(f"Downloaded: {result['downloaded_files']}")
            print(f"Failed: {result['failed_downloads']}")
            
        elif args.process_files:
            result = pipeline.process_files(args.process_files)
            print(f"\\nProcessed {result['files_processed']}/{result['total_files']} files")
            print(f"Total cost: ${result['total_cost']:.4f}")
            
        elif args.remove_files:
            result = pipeline.remove_files(args.remove_files)
            print(f"\\nRemoved {result['files_removed']}/{result['total_files']} files")
            print(f"Rebuild cost: ${result['rebuild_cost']:.4f}")
            
        elif args.incremental:
            result = pipeline.run_incremental_update()
            print(f"\\nIncremental update completed:")
            print(f"Files processed: {result['files_processed']}")
            print(f"Files removed: {result['files_removed']}")
            print(f"Total cost: ${result['total_cost']:.4f}")
            
        elif args.auto_update and isinstance(pipeline, AutoUpdatePipeline):
            result = pipeline.run_full_auto_update()
            print(f"\\nFull auto-update completed:")
            print(f"Duration: {result['duration_seconds']}s")
            print(f"Files downloaded: {result['files_downloaded']}")
            print(f"Files processed: {result['files_processed']}")
            print(f"Total cost: ${result['total_cost']:.4f}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)