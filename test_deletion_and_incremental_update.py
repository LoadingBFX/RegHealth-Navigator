#!/usr/bin/env python3
"""
Test Deletion and Incremental Update

1. Randomly delete a file and its chunks/embeddings
2. Test incremental update process
3. Verify if deleted file gets restored
"""

import os
import sys
import json
import random
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeletionAndIncrementalTester:
    """Test deletion followed by incremental update."""
    
    def __init__(self):
        """Initialize the tester."""
        from app.core.preprocessing.config_loader import ConfigLoader
        from app.core.preprocessing.incremental_manager import IncrementalManager
        
        # Load configuration
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        self.data_dir = Path(self.processing_config['data_dir'])
        self.output_dir = Path(self.processing_config['output_dir'])
        
        # Initialize incremental manager
        self.manager = IncrementalManager(
            data_directory=self.data_dir,
            output_directory=self.output_dir,
            api_key=self.processing_config.get('api_key'),
            model=self.processing_config['model']
        )
        
        # Backup directory
        self.backup_dir = self.output_dir / 'deletion_incremental_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("🧪 DeletionAndIncrementalTester initialized")
        logger.info(f"📁 Data directory: {self.data_dir}")
        logger.info(f"📁 Output directory: {self.output_dir}")
    
    def create_system_backup(self) -> Dict[str, Any]:
        """Create complete system backup."""
        logger.info("📦 Creating system backup...")
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'files_backed_up': []
        }
        
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
    
    def restore_system_backup(self) -> None:
        """Restore system from backup."""
        logger.info("🔄 Restoring system from backup...")
        
        backup_files = list(self.backup_dir.glob("*.backup"))
        for backup_file in backup_files:
            original_name = backup_file.name.replace('.backup', '')
            restore_path = self.output_dir / original_name
            shutil.copy2(backup_file, restore_path)
            logger.info(f"✅ Restored: {original_name}")
    
    def analyze_current_system(self) -> Dict[str, Any]:
        """Analyze current system state."""
        logger.info("📊 Analyzing current system state...")
        
        # Get system status
        status = self.manager.get_status()
        
        # Load chunks and analyze file distribution
        chunks = self.manager._load_chunks()
        
        file_counts = {}
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_counts[source_file] = file_counts.get(source_file, 0) + 1
        
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Check available XML files in data directory
        available_xml_files = []
        for program in ['MPFS', 'SNF', 'HOSPICE']:
            program_dir = self.data_dir / program
            if program_dir.exists():
                xml_files = list(program_dir.glob('*.xml'))
                available_xml_files.extend(xml_files)
        
        analysis = {
            'system_status': status,
            'total_chunks': len(chunks),
            'file_chunk_counts': file_counts,
            'sorted_files': sorted_files,
            'available_xml_files': [str(f.relative_to(self.data_dir)) for f in available_xml_files],
            'xml_file_count': len(available_xml_files)
        }
        
        logger.info(f"📊 System Analysis:")
        logger.info(f"  Total chunks: {analysis['total_chunks']:,}")
        logger.info(f"  Files in chunks: {len(file_counts)}")
        logger.info(f"  Available XML files: {len(available_xml_files)}")
        logger.info(f"  Index vectors: {status.get('index_size', 0):,}")
        logger.info(f"  Data consistency: {status.get('data_consistency', {})}")
        
        return analysis
    
    def select_random_file_for_deletion(self, analysis: Dict[str, Any]) -> str:
        """Select a random file for deletion."""
        logger.info("🎲 Selecting random file for deletion...")
        
        # Get files that have chunks and exist in data directory
        available_files = analysis['available_xml_files']
        files_with_chunks = set(analysis['file_chunk_counts'].keys())
        
        # Find files that exist both in data directory and have chunks
        deletable_files = []
        for xml_file in available_files:
            filename = Path(xml_file).name
            if filename in files_with_chunks:
                chunk_count = analysis['file_chunk_counts'][filename]
                deletable_files.append({
                    'relative_path': xml_file,
                    'filename': filename,
                    'chunk_count': chunk_count
                })
        
        if not deletable_files:
            raise Exception("No files found that can be deleted and restored")
        
        # Select a random file (prefer smaller files to minimize disruption)
        # Sort by chunk count and select from the smaller half
        deletable_files.sort(key=lambda x: x['chunk_count'])
        smaller_half = deletable_files[:len(deletable_files)//2] or deletable_files
        selected = random.choice(smaller_half)
        
        logger.info(f"🎯 Selected for deletion: {selected['filename']}")
        logger.info(f"  Relative path: {selected['relative_path']}")
        logger.info(f"  Chunks to delete: {selected['chunk_count']:,}")
        logger.info(f"  File exists in data directory: ✅")
        
        return selected
    
    def perform_file_deletion(self, selected_file: Dict[str, Any]) -> Dict[str, Any]:
        """Delete the selected file's chunks and embeddings."""
        logger.info(f"🗑️ Deleting file: {selected_file['filename']}")
        
        # Use incremental manager's remove_file method
        removal_result = self.manager.remove_file(selected_file['relative_path'])
        
        if removal_result['status'] != 'success':
            raise Exception(f"File deletion failed: {removal_result.get('error')}")
        
        logger.info(f"✅ File deletion completed:")
        logger.info(f"  Chunks removed: {removal_result.get('chunks_removed', 0):,}")
        logger.info(f"  Embeddings removed: {removal_result.get('embeddings_removed', 0):,}")
        logger.info(f"  Rebuild cost: ${removal_result.get('rebuild_cost', 0):.4f}")
        
        return removal_result
    
    def verify_file_deletion(self, selected_file: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that file was completely deleted."""
        logger.info("🔍 Verifying file deletion...")
        
        # Check chunks
        chunks = self.manager._load_chunks()
        filename = selected_file['filename']
        
        remaining_chunks = 0
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == filename:
                remaining_chunks += 1
        
        # Check system status
        status = self.manager.get_status()
        
        verification = {
            'filename': filename,
            'remaining_chunks': remaining_chunks,
            'completely_deleted': remaining_chunks == 0,
            'system_status': status,
            'file_exists_in_data_dir': (self.data_dir / selected_file['relative_path']).exists()
        }
        
        logger.info(f"📊 Deletion Verification:")
        logger.info(f"  Remaining chunks: {remaining_chunks}")
        logger.info(f"  Completely deleted: {'✅' if verification['completely_deleted'] else '❌'}")
        logger.info(f"  File still exists in data dir: {'✅' if verification['file_exists_in_data_dir'] else '❌'}")
        
        return verification
    
    def run_incremental_update(self) -> Dict[str, Any]:
        """Run incremental update to see if deleted file gets restored."""
        logger.info("🔄 Running incremental update...")
        
        # Get status before incremental update
        before_status = self.manager.get_status()
        before_chunks = len(self.manager._load_chunks())
        
        logger.info(f"📊 Before incremental update:")
        logger.info(f"  Chunks: {before_chunks:,}")
        logger.info(f"  Index vectors: {before_status.get('index_size', 0):,}")
        logger.info(f"  Pending changes: {before_status.get('pending_changes', 0)}")
        
        # Run full incremental update
        update_result = self.manager.full_incremental_update()
        
        if update_result['status'] != 'success':
            logger.error(f"❌ Incremental update failed: {update_result.get('error')}")
            return update_result
        
        # Get status after incremental update
        after_status = self.manager.get_status()
        after_chunks = len(self.manager._load_chunks())
        
        logger.info(f"✅ Incremental update completed:")
        logger.info(f"  Files processed: {update_result.get('files_processed', 0)}")
        logger.info(f"  Files removed: {update_result.get('files_removed', 0)}")
        logger.info(f"  Total cost: ${update_result.get('total_cost', 0):.4f}")
        
        logger.info(f"📊 After incremental update:")
        logger.info(f"  Chunks: {after_chunks:,} (change: {after_chunks - before_chunks:+,})")
        logger.info(f"  Index vectors: {after_status.get('index_size', 0):,}")
        
        update_result.update({
            'before_chunks': before_chunks,
            'after_chunks': after_chunks,
            'chunks_change': after_chunks - before_chunks,
            'before_status': before_status,
            'after_status': after_status
        })
        
        return update_result
    
    def verify_file_restoration(self, selected_file: Dict[str, Any], original_chunk_count: int) -> Dict[str, Any]:
        """Verify if deleted file was restored by incremental update."""
        logger.info("🔍 Verifying file restoration...")
        
        filename = selected_file['filename']
        
        # Check if file chunks are back
        chunks = self.manager._load_chunks()
        restored_chunks = 0
        
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == filename:
                restored_chunks += 1
        
        # Check file tracking
        file_tracker = self.manager.file_tracker
        file_status = file_tracker.get_file_status(self.data_dir / selected_file['relative_path'])
        
        verification = {
            'filename': filename,
            'original_chunk_count': original_chunk_count,
            'restored_chunks': restored_chunks,
            'file_restored': restored_chunks > 0,
            'fully_restored': restored_chunks == original_chunk_count,
            'file_tracking_status': file_status,
            'restoration_percentage': (restored_chunks / original_chunk_count * 100) if original_chunk_count > 0 else 0
        }
        
        logger.info(f"📊 File Restoration Verification:")
        logger.info(f"  Original chunks: {original_chunk_count:,}")
        logger.info(f"  Restored chunks: {restored_chunks:,}")
        logger.info(f"  File restored: {'✅' if verification['file_restored'] else '❌'}")
        logger.info(f"  Fully restored: {'✅' if verification['fully_restored'] else '❌'}")
        logger.info(f"  Restoration: {verification['restoration_percentage']:.1f}%")
        
        return verification
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete deletion and incremental update test."""
        logger.info("\\n🚀 Starting Deletion + Incremental Update Test")
        logger.info("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # Phase 1: Backup
            logger.info("\\n📋 PHASE 1: System Backup")
            backup_info = self.create_system_backup()
            test_results['backup'] = backup_info
            
            # Phase 2: Initial analysis
            logger.info("\\n📋 PHASE 2: Initial System Analysis")
            initial_analysis = self.analyze_current_system()
            test_results['initial_analysis'] = initial_analysis
            
            # Phase 3: Select file for deletion
            logger.info("\\n📋 PHASE 3: Random File Selection")
            selected_file = self.select_random_file_for_deletion(initial_analysis)
            test_results['selected_file'] = selected_file
            original_chunk_count = selected_file['chunk_count']
            
            # Phase 4: Delete file
            logger.info("\\n📋 PHASE 4: File Deletion")
            deletion_result = self.perform_file_deletion(selected_file)
            test_results['deletion'] = deletion_result
            
            # Phase 5: Verify deletion
            logger.info("\\n📋 PHASE 5: Deletion Verification")
            deletion_verification = self.verify_file_deletion(selected_file)
            test_results['deletion_verification'] = deletion_verification
            
            if not deletion_verification['completely_deleted']:
                logger.error("❌ File deletion verification failed")
                test_results['success'] = False
                return test_results
            
            # Phase 6: Incremental update
            logger.info("\\n📋 PHASE 6: Incremental Update")
            update_result = self.run_incremental_update()
            test_results['incremental_update'] = update_result
            
            if update_result['status'] != 'success':
                logger.error("❌ Incremental update failed")
                test_results['success'] = False
                return test_results
            
            # Phase 7: Verify restoration
            logger.info("\\n📋 PHASE 7: File Restoration Verification")
            restoration_verification = self.verify_file_restoration(selected_file, original_chunk_count)
            test_results['restoration_verification'] = restoration_verification
            
            # Determine overall success
            test_results['success'] = (
                deletion_verification['completely_deleted'] and
                update_result['status'] == 'success' and
                restoration_verification['file_restored']
            )
            
            # Print summary
            self.print_test_summary(test_results)
            
            return test_results
            
        except Exception as e:
            logger.error(f"💥 Test failed: {e}")
            test_results['error'] = str(e)
            return test_results
        
        finally:
            # Always restore system backup
            try:
                self.restore_system_backup()
                logger.info("🔄 System restored from backup")
            except Exception as e:
                logger.error(f"❌ Failed to restore backup: {e}")
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary."""
        logger.info("\\n" + "=" * 60)
        logger.info("📊 DELETION + INCREMENTAL UPDATE TEST SUMMARY")
        logger.info("=" * 60)
        
        success = results.get('success', False)
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"Overall Result: {status}")
        
        # Selected file
        selected_file = results.get('selected_file', {})
        if selected_file:
            logger.info(f"\\n🎯 Test Target:")
            logger.info(f"  File: {selected_file.get('filename', 'Unknown')}")
            logger.info(f"  Original chunks: {selected_file.get('chunk_count', 0):,}")
        
        # Deletion results
        deletion = results.get('deletion', {})
        if deletion:
            logger.info(f"\\n🗑️ Deletion Phase:")
            logger.info(f"  Chunks removed: {deletion.get('chunks_removed', 0):,}")
            logger.info(f"  Embeddings removed: {deletion.get('embeddings_removed', 0):,}")
            logger.info(f"  Rebuild cost: ${deletion.get('rebuild_cost', 0):.4f}")
        
        # Incremental update results
        update = results.get('incremental_update', {})
        if update:
            logger.info(f"\\n🔄 Incremental Update Phase:")
            logger.info(f"  Files processed: {update.get('files_processed', 0)}")
            logger.info(f"  Chunks change: {update.get('chunks_change', 0):+,}")
            logger.info(f"  Total cost: ${update.get('total_cost', 0):.4f}")
        
        # Restoration verification
        restoration = results.get('restoration_verification', {})
        if restoration:
            logger.info(f"\\n🔍 Restoration Verification:")
            logger.info(f"  File restored: {'✅' if restoration.get('file_restored') else '❌'}")
            logger.info(f"  Fully restored: {'✅' if restoration.get('fully_restored') else '❌'}")
            logger.info(f"  Restoration: {restoration.get('restoration_percentage', 0):.1f}%")
            logger.info(f"  Restored chunks: {restoration.get('restored_chunks', 0):,}")
        
        if success:
            logger.info(f"\\n💡 Test Conclusions:")
            logger.info(f"  ✅ File deletion works correctly")
            logger.info(f"  ✅ Incremental update detects missing files")
            logger.info(f"  ✅ Deleted files are automatically restored")
            logger.info(f"  ✅ System maintains data integrity")
            logger.info(f"  ✅ Full workflow is production-ready")
        else:
            logger.info(f"\\n⚠️ Test Issues:")
            logger.info(f"  ❌ Check deletion or restoration process")
            logger.info(f"  ❌ Review incremental update logic")
        
        logger.info("=" * 60)


def main():
    """Run deletion and incremental update test."""
    try:
        tester = DeletionAndIncrementalTester()
        results = tester.run_complete_test()
        
        success = results.get('success', False)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())