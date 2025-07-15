#!/usr/bin/env python3
"""
Comprehensive Incremental Update Test Script

Tests:
1. Chunk content modification and embedding update detection
2. File deletion and automatic re-download functionality
3. Data consistency and cost verification
4. Key information preservation validation

Usage:
    python test_incremental_update.py
"""

import os
import sys
import json
import random
import shutil
import hashlib
import logging
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import preprocessing components
from config_loader import ConfigLoader
from pipeline import ProcessingPipeline, AutoUpdatePipeline
from utils import DataPersistence
import faiss
import numpy as np


class IncrementalUpdateTester:
    """Comprehensive tester for incremental update functionality."""
    
    def __init__(self):
        """Initialize tester with configuration."""
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        
        # Test directories
        self.data_dir = Path(self.processing_config['data_dir'])
        self.output_dir = Path(self.processing_config['output_dir'])
        
        # Backup directory for restoration
        self.backup_dir = self.output_dir / 'test_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Test results storage
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        logger.info(f"🧪 Initialized IncrementalUpdateTester")
        logger.info(f"📁 Data dir: {self.data_dir}")
        logger.info(f"📁 Output dir: {self.output_dir}")
    
    def backup_current_state(self) -> Dict[str, Any]:
        """Backup current chunks and FAISS data."""
        logger.info("📦 Backing up current state...")
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'files_backed_up': []
        }
        
        # Files to backup
        files_to_backup = [
            'chunks.json',
            'faiss.index', 
            'faiss_metadata.json',
            'file_tracking.json'
        ]
        
        for filename in files_to_backup:
            source = self.output_dir / filename
            if source.exists():
                backup_path = self.backup_dir / f"{filename}.backup"
                shutil.copy2(source, backup_path)
                backup_info['files_backed_up'].append(filename)
                logger.info(f"✅ Backed up: {filename}")
        
        return backup_info
    
    def restore_from_backup(self) -> None:
        """Restore data from backup."""
        logger.info("🔄 Restoring from backup...")
        
        backup_files = list(self.backup_dir.glob("*.backup"))
        for backup_file in backup_files:
            original_name = backup_file.name.replace('.backup', '')
            restore_path = self.output_dir / original_name
            shutil.copy2(backup_file, restore_path)
            logger.info(f"✅ Restored: {original_name}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state for comparison."""
        logger.info("📊 Getting current system state...")
        
        state = {
            'chunks': {},
            'faiss_metadata': {},
            'file_tracking': {},
            'faiss_index_size': 0
        }
        
        # Load chunks
        chunks_file = self.output_dir / 'chunks.json'
        if chunks_file.exists():
            chunks_data = DataPersistence.load_json(chunks_file)
            if chunks_data['status'] == 'success':
                state['chunks'] = chunks_data['data']
        
        # Load FAISS metadata
        metadata_file = self.output_dir / 'faiss_metadata.json'
        if metadata_file.exists():
            metadata_result = DataPersistence.load_json(metadata_file)
            if metadata_result['status'] == 'success':
                state['faiss_metadata'] = metadata_result['data']
        
        # Load file tracking
        tracking_file = self.output_dir / 'file_tracking.json'
        if tracking_file.exists():
            tracking_result = DataPersistence.load_json(tracking_file)
            if tracking_result['status'] == 'success':
                state['file_tracking'] = tracking_result['data']
        
        # Get FAISS index size
        index_file = self.output_dir / 'faiss.index'
        if index_file.exists():
            try:
                index = faiss.read_index(str(index_file))
                state['faiss_index_size'] = index.ntotal
            except Exception as e:
                logger.warning(f"Could not read FAISS index: {e}")
        
        logger.info(f"📊 Current state: {len(state['chunks'])} chunks, {state['faiss_index_size']} embeddings")
        
        return state
    
    def test_chunk_modification_update(self) -> Dict[str, Any]:
        """
        Test 1: Modify chunk content and verify embedding update detection.
        """
        logger.info("\n🧪 === TEST 1: Chunk Modification Update ===")
        
        test_result = {
            'test_name': 'chunk_modification_update',
            'success': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Get initial state
            initial_state = self.get_current_state()
            initial_chunks = initial_state['chunks']
            
            if not initial_chunks:
                raise Exception("No chunks found for testing")
            
            # Select random chunk for modification
            chunk_ids = list(initial_chunks.keys())
            selected_chunk_id = random.choice(chunk_ids)
            selected_chunk = initial_chunks[selected_chunk_id]
            
            logger.info(f"🎯 Selected chunk for modification: {selected_chunk_id}")
            logger.info(f"📄 Source file: {selected_chunk.get('metadata', {}).get('source_file', 'unknown')}")
            
            # Create temporary modified chunks file
            modified_chunks = initial_chunks.copy()
            original_text = selected_chunk['text']
            
            # Modify chunk content (add timestamp to make it unique)
            modification_marker = f"[MODIFIED_{datetime.now().strftime('%Y%m%d_%H%M%S')}]"
            modified_text = f"{original_text} {modification_marker}"
            modified_chunks[selected_chunk_id]['text'] = modified_text
            
            # Save modified chunks
            chunks_file = self.output_dir / 'chunks.json'
            save_result = DataPersistence.save_json(modified_chunks, chunks_file)
            if save_result['status'] != 'success':
                raise Exception(f"Failed to save modified chunks: {save_result.get('error')}")
            
            logger.info(f"✅ Modified chunk content with marker: {modification_marker}")
            
            # Create pipeline and run incremental update
            pipeline = ProcessingPipeline(**self.processing_config)
            
            # Get cost estimate first
            estimate = pipeline.estimate_update_cost()
            logger.info(f"💰 Cost estimate: ${estimate['total_estimated_cost']:.4f}")
            
            # Run incremental update
            update_result = pipeline.run_incremental_update()
            
            # Verify update was successful
            if update_result['status'] != 'success':
                raise Exception(f"Incremental update failed: {update_result.get('error')}")
            
            # Get updated state
            updated_state = self.get_current_state()
            
            # Verify embedding was updated
            updated_chunks = updated_state['chunks']
            if selected_chunk_id not in updated_chunks:
                raise Exception(f"Modified chunk {selected_chunk_id} not found after update")
            
            updated_chunk = updated_chunks[selected_chunk_id]
            
            # Check if modification is preserved or if chunk was reprocessed
            chunk_hash_changed = (
                updated_chunk.get('content_hash') != selected_chunk.get('content_hash')
            )
            
            # Record test details
            test_result['details'] = {
                'selected_chunk_id': selected_chunk_id,
                'source_file': selected_chunk.get('metadata', {}).get('source_file'),
                'modification_marker': modification_marker,
                'original_text_length': len(original_text),
                'modified_text_length': len(modified_text),
                'chunk_hash_changed': chunk_hash_changed,
                'initial_chunk_count': len(initial_chunks),
                'updated_chunk_count': len(updated_chunks),
                'initial_faiss_size': initial_state['faiss_index_size'],
                'updated_faiss_size': updated_state['faiss_index_size'],
                'cost_estimate': estimate['total_estimated_cost'],
                'actual_cost': update_result.get('total_cost', 0),
                'files_processed': update_result.get('files_processed', 0),
                'processing_time': update_result.get('duration_seconds', 0)
            }
            
            # Verification checks
            checks = {
                'chunk_count_consistent': len(updated_chunks) >= len(initial_chunks),
                'faiss_size_consistent': updated_state['faiss_index_size'] >= initial_state['faiss_index_size'],
                'update_detected': update_result.get('files_processed', 0) > 0,
                'cost_reasonable': update_result.get('total_cost', 0) > 0
            }
            
            test_result['details']['verification_checks'] = checks
            
            # Test passes if all checks pass
            test_result['success'] = all(checks.values())
            
            if test_result['success']:
                logger.info("✅ TEST 1 PASSED: Chunk modification update working correctly")
            else:
                logger.error("❌ TEST 1 FAILED: Issues detected in chunk modification update")
                
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"❌ TEST 1 ERROR: {e}")
        
        return test_result
    
    def test_file_deletion_and_redownload(self) -> Dict[str, Any]:
        """
        Test 2: Delete files and test automatic re-download functionality.
        """
        logger.info("\n🧪 === TEST 2: File Deletion and Re-download ===")
        
        test_result = {
            'test_name': 'file_deletion_and_redownload',
            'success': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Get initial state
            initial_state = self.get_current_state()
            
            # Find XML files in each directory
            program_dirs = ['MPFS', 'SNF', 'HOSPICE']
            files_to_delete = []
            backup_files = {}
            
            for program_dir in program_dirs:
                program_path = self.data_dir / program_dir
                if program_path.exists():
                    xml_files = list(program_path.glob('*.xml'))
                    if xml_files:
                        # Select random file from this program
                        selected_file = random.choice(xml_files)
                        files_to_delete.append(selected_file)
                        
                        # Backup file content
                        backup_files[str(selected_file)] = selected_file.read_text(encoding='utf-8')
                        
                        logger.info(f"🎯 Selected for deletion: {selected_file}")
            
            if not files_to_delete:
                raise Exception("No XML files found for deletion testing")
            
            # Delete selected files
            deleted_files_info = []
            for file_path in files_to_delete:
                if file_path.exists():
                    # Record file info before deletion
                    file_stat = file_path.stat()
                    file_info = {
                        'path': str(file_path),
                        'size': file_stat.st_size,
                        'mtime': file_stat.st_mtime,
                        'relative_path': str(file_path.relative_to(self.data_dir))
                    }
                    deleted_files_info.append(file_info)
                    
                    # Delete file
                    file_path.unlink()
                    logger.info(f"🗑️ Deleted: {file_path}")
            
            # Create AutoUpdatePipeline with extended days_back to ensure coverage
            extended_config = self.processing_config.copy()
            extended_config['days_back'] = 3 * 365  # 3 years back
            
            auto_pipeline = AutoUpdatePipeline(**extended_config)
            
            # Run full auto update (check, download, process)
            logger.info("🔄 Running full auto update with extended time range...")
            auto_update_result = auto_pipeline.run_full_auto_update()
            
            if auto_update_result['status'] != 'success':
                raise Exception(f"Auto update failed: {auto_update_result.get('error')}")
            
            # Get final state
            final_state = self.get_current_state()
            
            # Verify files were re-downloaded
            redownloaded_files = []
            for file_info in deleted_files_info:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    redownloaded_files.append(file_info['relative_path'])
                    logger.info(f"✅ Re-downloaded: {file_path}")
                else:
                    logger.warning(f"⚠️ Not re-downloaded: {file_path}")
            
            # Analyze chunks and embeddings recovery
            chunks_before = len(initial_state['chunks'])
            chunks_after = len(final_state['chunks'])
            faiss_before = initial_state['faiss_index_size']
            faiss_after = final_state['faiss_index_size']
            
            # Record test details
            test_result['details'] = {
                'files_deleted': [info['relative_path'] for info in deleted_files_info],
                'files_redownloaded': redownloaded_files,
                'chunks_before_deletion': chunks_before,
                'chunks_after_recovery': chunks_after,
                'faiss_before_deletion': faiss_before,
                'faiss_after_recovery': faiss_after,
                'auto_update_duration': auto_update_result.get('duration_seconds', 0),
                'files_downloaded': auto_update_result.get('files_downloaded', 0),
                'files_processed': auto_update_result.get('files_processed', 0),
                'total_cost': auto_update_result.get('total_cost', 0),
                'download_cost': auto_update_result.get('download_cost', 0),
                'processing_cost': auto_update_result.get('processing_cost', 0)
            }
            
            # Verification checks
            checks = {
                'files_redownloaded': len(redownloaded_files) >= len(deleted_files_info) * 0.8,  # 80% success rate
                'chunks_recovered': chunks_after >= chunks_before * 0.9,  # Allow 10% variance
                'faiss_recovered': faiss_after >= faiss_before * 0.9,  # Allow 10% variance
                'cost_incurred': auto_update_result.get('total_cost', 0) > 0,
                'processing_occurred': auto_update_result.get('files_processed', 0) > 0
            }
            
            test_result['details']['verification_checks'] = checks
            test_result['success'] = all(checks.values())
            
            # Restore deleted files if they weren't re-downloaded
            for file_path_str, content in backup_files.items():
                file_path = Path(file_path_str)
                if not file_path.exists():
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                    logger.info(f"🔄 Restored from backup: {file_path}")
            
            if test_result['success']:
                logger.info("✅ TEST 2 PASSED: File deletion and re-download working correctly")
            else:
                logger.error("❌ TEST 2 FAILED: Issues detected in file deletion/re-download")
                
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"❌ TEST 2 ERROR: {e}")
        
        return test_result
    
    def test_key_information_preservation(self) -> Dict[str, Any]:
        """
        Test 3: Verify key information preservation in chunks and FAISS.
        """
        logger.info("\n🧪 === TEST 3: Key Information Preservation ===")
        
        test_result = {
            'test_name': 'key_information_preservation',
            'success': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Get current state
            current_state = self.get_current_state()
            chunks = current_state['chunks']
            
            if not chunks:
                raise Exception("No chunks found for key information testing")
            
            # Sample random XML files for testing
            xml_files = []
            for program_dir in ['MPFS', 'SNF', 'HOSPICE']:
                program_path = self.data_dir / program_dir
                if program_path.exists():
                    xml_files.extend(list(program_path.glob('*.xml'))[:2])  # Max 2 per directory
            
            if not xml_files:
                raise Exception("No XML files found for testing")
            
            # Extract key information from XML files
            key_info_tests = []
            for xml_file in xml_files[:3]:  # Test max 3 files
                try:
                    key_info = self.extract_key_information_from_xml(xml_file)
                    if key_info:
                        key_info_tests.append({
                            'file': str(xml_file.relative_to(self.data_dir)),
                            'key_info': key_info
                        })
                except Exception as e:
                    logger.warning(f"Could not extract key info from {xml_file}: {e}")
            
            # Check if key information is preserved in chunks
            preservation_results = []
            for test_info in key_info_tests:
                file_path = test_info['file']
                key_info = test_info['key_info']
                
                # Find chunks from this file
                file_chunks = {
                    chunk_id: chunk for chunk_id, chunk in chunks.items()
                    if chunk.get('metadata', {}).get('source_file', '').endswith(file_path.replace('\\\\', '/'))
                }
                
                if not file_chunks:
                    logger.warning(f"No chunks found for file: {file_path}")
                    continue
                
                # Check preservation of each key piece of information
                info_preservation = {}
                for info_type, values in key_info.items():
                    found_count = 0
                    total_count = len(values)
                    
                    # Search in chunk texts
                    for value in values:
                        found_in_chunk = False
                        for chunk in file_chunks.values():
                            chunk_text = chunk.get('text', '').lower()
                            if str(value).lower() in chunk_text:
                                found_in_chunk = True
                                break
                        if found_in_chunk:
                            found_count += 1
                    
                    preservation_rate = found_count / total_count if total_count > 0 else 0
                    info_preservation[info_type] = {
                        'found': found_count,
                        'total': total_count,
                        'rate': preservation_rate
                    }
                
                preservation_results.append({
                    'file': file_path,
                    'chunk_count': len(file_chunks),
                    'info_preservation': info_preservation
                })
            
            # Calculate overall preservation statistics
            overall_stats = {
                'files_tested': len(preservation_results),
                'average_preservation_rate': 0,
                'min_preservation_rate': 1.0,
                'max_preservation_rate': 0.0
            }
            
            if preservation_results:
                total_rate = 0
                rate_count = 0
                
                for result in preservation_results:
                    for info_type, preservation in result['info_preservation'].items():
                        rate = preservation['rate']
                        total_rate += rate
                        rate_count += 1
                        overall_stats['min_preservation_rate'] = min(overall_stats['min_preservation_rate'], rate)
                        overall_stats['max_preservation_rate'] = max(overall_stats['max_preservation_rate'], rate)
                
                if rate_count > 0:
                    overall_stats['average_preservation_rate'] = total_rate / rate_count
            
            # Record test details
            test_result['details'] = {
                'key_info_tests': key_info_tests,
                'preservation_results': preservation_results,
                'overall_stats': overall_stats,
                'total_chunks_analyzed': sum(len({chunk_id: chunk for chunk_id, chunk in chunks.items() if chunk.get('metadata', {}).get('source_file', '').endswith(result['file'].replace('\\\\', '/'))}) for result in preservation_results)
            }
            
            # Verification checks
            checks = {
                'files_tested': len(preservation_results) > 0,
                'high_preservation_rate': overall_stats['average_preservation_rate'] >= 0.8,  # 80% preservation
                'no_critical_loss': overall_stats['min_preservation_rate'] >= 0.5,  # No category below 50%
                'chunks_found': overall_stats.get('total_chunks_analyzed', 0) > 0
            }
            
            test_result['details']['verification_checks'] = checks
            test_result['success'] = all(checks.values())
            
            if test_result['success']:
                logger.info("✅ TEST 3 PASSED: Key information preservation verified")
                logger.info(f"📊 Average preservation rate: {overall_stats['average_preservation_rate']:.2%}")
            else:
                logger.error("❌ TEST 3 FAILED: Key information preservation issues detected")
                
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"❌ TEST 3 ERROR: {e}")
        
        return test_result
    
    def extract_key_information_from_xml(self, xml_file: Path) -> Dict[str, List]:
        """Extract key information from XML file for preservation testing."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            key_info = {
                'monetary_values': [],
                'percentages': [],
                'dates': [],
                'section_numbers': [],
                'important_terms': []
            }
            
            # Extract text content
            text_content = ET.tostring(root, method='text', encoding='unicode')
            
            # Find monetary values (dollars)
            import re
            monetary_pattern = r'\$[\d,]+(?:\.\d{2})?'
            key_info['monetary_values'] = re.findall(monetary_pattern, text_content)[:10]  # Max 10
            
            # Find percentages
            percentage_pattern = r'\d+(?:\.\d+)?%'
            key_info['percentages'] = re.findall(percentage_pattern, text_content)[:10]  # Max 10
            
            # Find years
            year_pattern = r'\\b(?:19|20)\\d{2}\\b'
            key_info['dates'] = re.findall(year_pattern, text_content)[:10]  # Max 10
            
            # Find section numbers
            section_pattern = r'§\\s*\\d+(?:\\.\\d+)*'
            key_info['section_numbers'] = re.findall(section_pattern, text_content)[:10]  # Max 10
            
            # Find specific important terms common in regulations
            important_terms = [
                'Medicare', 'Medicaid', 'CMS', 'physician', 'hospital', 'payment',
                'reimbursement', 'billing', 'compliance', 'requirement'
            ]
            
            for term in important_terms:
                if term.lower() in text_content.lower():
                    key_info['important_terms'].append(term)
            
            # Remove duplicates and empty values
            for category in key_info:
                key_info[category] = list(set(filter(None, key_info[category])))
            
            return key_info
            
        except Exception as e:
            logger.warning(f"Error extracting key info from {xml_file}: {e}")
            return {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all incremental update tests."""
        logger.info("\n🚀 === STARTING COMPREHENSIVE INCREMENTAL UPDATE TESTS ===")
        
        # Backup current state
        backup_info = self.backup_current_state()
        
        try:
            # Run tests
            test1_result = self.test_chunk_modification_update()
            self.test_results['tests']['chunk_modification'] = test1_result
            
            # Restore state before next test
            self.restore_from_backup()
            
            test2_result = self.test_file_deletion_and_redownload()
            self.test_results['tests']['file_deletion_redownload'] = test2_result
            
            test3_result = self.test_key_information_preservation()
            self.test_results['tests']['key_information_preservation'] = test3_result
            
            # Calculate overall success
            all_tests_passed = all(
                test_result['success'] 
                for test_result in self.test_results['tests'].values()
            )
            
            self.test_results['overall_success'] = all_tests_passed
            self.test_results['tests_passed'] = sum(
                1 for test_result in self.test_results['tests'].values() 
                if test_result['success']
            )
            self.test_results['total_tests'] = len(self.test_results['tests'])
            
            # Save test results
            results_file = self.output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_result = DataPersistence.save_json(self.test_results, results_file)
            if save_result['status'] == 'success':
                logger.info(f"📊 Test results saved to: {results_file}")
            
            # Print summary
            self.print_test_summary()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            self.test_results['execution_error'] = str(e)
            return self.test_results
        
        finally:
            # Always restore from backup
            self.restore_from_backup()
    
    def print_test_summary(self) -> None:
        """Print comprehensive test summary."""
        logger.info("\n" + "="*60)
        logger.info("📊 INCREMENTAL UPDATE TEST SUMMARY")
        logger.info("="*60)
        
        overall_success = self.test_results.get('overall_success', False)
        tests_passed = self.test_results.get('tests_passed', 0)
        total_tests = self.test_results.get('total_tests', 0)
        
        logger.info(f"Overall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        logger.info(f"Tests Passed: {tests_passed}/{total_tests}")
        logger.info("")
        
        for test_name, test_result in self.test_results['tests'].items():
            status = "✅ PASSED" if test_result['success'] else "❌ FAILED"
            logger.info(f"{status} - {test_result['test_name']}")
            
            if test_result.get('errors'):
                for error in test_result['errors']:
                    logger.info(f"    ❌ Error: {error}")
            
            # Print key metrics
            details = test_result.get('details', {})
            if 'verification_checks' in details:
                checks = details['verification_checks']
                failed_checks = [check for check, passed in checks.items() if not passed]
                if failed_checks:
                    logger.info(f"    ⚠️  Failed checks: {', '.join(failed_checks)}")
            
            logger.info("")
        
        logger.info("="*60)


def main():
    """Main test execution function."""
    try:
        # Initialize tester
        tester = IncrementalUpdateTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            logger.info("🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()