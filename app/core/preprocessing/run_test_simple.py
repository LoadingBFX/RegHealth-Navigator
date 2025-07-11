#!/usr/bin/env python3
"""
Simple Test Runner - Direct Execution

Runs incremental update tests with direct imports.
"""

import os
import sys
import json
import random
import shutil
import logging
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

# Add paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Quick environment test."""
    logger.info("🔍 Testing environment...")
    
    try:
        # Test imports
        from config_loader import ConfigLoader
        from pipeline import ProcessingPipeline, AutoUpdatePipeline
        from utils import DataPersistence
        import faiss
        import numpy as np
        logger.info("✅ All imports successful")
        
        # Test config
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        logger.info(f"✅ Config loaded: {processing_config['model']}")
        
        # Test API key
        if processing_config.get('api_key'):
            logger.info("✅ API key available")
        else:
            logger.warning("⚠️ API key not found")
        
        # Test data
        data_dir = Path(processing_config['data_dir'])
        if data_dir.exists():
            xml_count = len(list(data_dir.rglob('*.xml')))
            logger.info(f"✅ Found {xml_count} XML files")
        else:
            logger.warning(f"⚠️ Data directory not found: {data_dir}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Environment test failed: {e}")
        return False

def simple_chunk_modification_test():
    """Simplified chunk modification test."""
    logger.info("\n🧪 === Simple Chunk Modification Test ===")
    
    try:
        from config_loader import ConfigLoader
        from pipeline import ProcessingPipeline
        from utils import DataPersistence
        
        # Load config and create pipeline
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        pipeline = ProcessingPipeline(**processing_config)
        
        # Get system status
        logger.info("📊 Getting system status...")
        status = pipeline.get_system_status()
        
        logger.info(f"System Status:")
        logger.info(f"  Healthy: {status['healthy']}")
        logger.info(f"  Model: {status['model']}")
        logger.info(f"  Total chunks: {status['statistics']['total_chunks']}")
        logger.info(f"  Index size: {status['statistics']['index_size']}")
        logger.info(f"  Total cost: ${status['statistics']['total_cost']:.4f}")
        logger.info(f"  Pending changes: {status['statistics']['pending_changes']}")
        
        # Cost estimate
        logger.info("💰 Getting cost estimate...")
        estimate = pipeline.estimate_update_cost()
        
        logger.info(f"Cost Estimate:")
        logger.info(f"  Files to process: {estimate['estimated_files']}")
        logger.info(f"  Estimated chunks: {estimate['estimated_chunks']}")
        logger.info(f"  Estimated cost: ${estimate['total_estimated_cost']:.4f}")
        
        if estimate['total_estimated_cost'] > 1.0:
            logger.warning("⚠️ High cost estimate, skipping actual update")
            return True
        
        # Run incremental update
        logger.info("🔄 Running incremental update...")
        result = pipeline.run_incremental_update()
        
        logger.info(f"Update Result:")
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Files processed: {result.get('files_processed', 0)}")
        logger.info(f"  Files removed: {result.get('files_removed', 0)}")
        logger.info(f"  Total cost: ${result.get('total_cost', 0):.4f}")
        
        return result['status'] == 'success'
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def simple_data_validation_test():
    """Simple data validation test."""
    logger.info("\n🧪 === Simple Data Validation Test ===")
    
    try:
        from config_loader import ConfigLoader
        from utils import DataPersistence
        
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        output_dir = Path(processing_config['output_dir'])
        
        # Check chunks file
        chunks_file = output_dir / 'chunks.json'
        if chunks_file.exists():
            logger.info(f"✅ Chunks file exists: {chunks_file.stat().st_size:,} bytes")
            
            # Load and validate chunks
            chunks_result = DataPersistence.load_json(chunks_file)
            if chunks_result['status'] == 'success':
                chunks = chunks_result['data']
                logger.info(f"✅ Loaded {len(chunks)} chunks")
                
                # Sample a few chunks for validation
                sample_chunks = list(chunks.items())[:5]
                for chunk_id, chunk in sample_chunks:
                    text_length = len(chunk.get('text', ''))
                    source_file = chunk.get('metadata', {}).get('source_file', 'unknown')
                    logger.info(f"  Chunk {chunk_id}: {text_length} chars from {source_file}")
            else:
                logger.error(f"❌ Failed to load chunks: {chunks_result.get('error')}")
                return False
        else:
            logger.error(f"❌ Chunks file not found: {chunks_file}")
            return False
        
        # Check FAISS index
        index_file = output_dir / 'faiss.index'
        if index_file.exists():
            logger.info(f"✅ FAISS index exists: {index_file.stat().st_size:,} bytes")
            
            try:
                import faiss
                index = faiss.read_index(str(index_file))
                logger.info(f"✅ FAISS index loaded: {index.ntotal} vectors, dimension {index.d}")
            except Exception as e:
                logger.error(f"❌ Failed to load FAISS index: {e}")
                return False
        else:
            logger.error(f"❌ FAISS index not found: {index_file}")
            return False
        
        # Check metadata
        metadata_file = output_dir / 'faiss_metadata.json'
        if metadata_file.exists():
            logger.info(f"✅ Metadata file exists: {metadata_file.stat().st_size:,} bytes")
            
            metadata_result = DataPersistence.load_json(metadata_file)
            if metadata_result['status'] == 'success':
                metadata = metadata_result['data']
                logger.info(f"✅ Loaded metadata for {len(metadata)} entries")
            else:
                logger.error(f"❌ Failed to load metadata: {metadata_result.get('error')}")
                return False
        else:
            logger.error(f"❌ Metadata file not found: {metadata_file}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data validation test failed: {e}")
        return False

def simple_file_analysis_test():
    """Simple file analysis test."""
    logger.info("\n🧪 === Simple File Analysis Test ===")
    
    try:
        from config_loader import ConfigLoader
        
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        data_dir = Path(processing_config['data_dir'])
        
        if not data_dir.exists():
            logger.error(f"❌ Data directory not found: {data_dir}")
            return False
        
        # Analyze XML files
        program_dirs = ['MPFS', 'SNF', 'HOSPICE']
        total_files = 0
        total_size = 0
        
        for program_dir in program_dirs:
            program_path = data_dir / program_dir
            if program_path.exists():
                xml_files = list(program_path.glob('*.xml'))
                dir_size = sum(f.stat().st_size for f in xml_files)
                total_files += len(xml_files)
                total_size += dir_size
                
                logger.info(f"📁 {program_dir}: {len(xml_files)} files, {dir_size:,} bytes")
                
                # Sample one file for analysis
                if xml_files:
                    sample_file = xml_files[0]
                    try:
                        tree = ET.parse(sample_file)
                        root = tree.getroot()
                        text_content = ET.tostring(root, method='text', encoding='unicode')
                        
                        # Simple analysis
                        word_count = len(text_content.split())
                        char_count = len(text_content)
                        
                        logger.info(f"  Sample analysis ({sample_file.name}):")
                        logger.info(f"    Characters: {char_count:,}")
                        logger.info(f"    Words: {word_count:,}")
                        
                    except Exception as e:
                        logger.warning(f"  Could not analyze {sample_file.name}: {e}")
            else:
                logger.warning(f"⚠️ Directory not found: {program_path}")
        
        logger.info(f"📊 Total: {total_files} XML files, {total_size:,} bytes")
        
        return total_files > 0
        
    except Exception as e:
        logger.error(f"❌ File analysis test failed: {e}")
        return False

def main():
    """Run simplified tests."""
    logger.info("🚀 Starting Simplified Incremental Update Tests")
    
    # Test environment
    if not test_environment():
        logger.error("💥 Environment test failed")
        return 1
    
    # Run tests
    tests = [
        ("Data Validation", simple_data_validation_test),
        ("File Analysis", simple_file_analysis_test),
        ("Chunk Modification", simple_chunk_modification_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} ERROR: {e}")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())