#!/usr/bin/env python3
"""
Quick Preprocessing Test

Tests the existing preprocessing functionality without relative imports.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_and_data():
    """Test configuration and data availability."""
    logger.info("🔍 Testing configuration and data...")
    
    try:
        # Import with absolute paths
        from app.core.preprocessing.config_loader import ConfigLoader
        
        # Test config loading
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"  Model: {processing_config['model']}")
        logger.info(f"  Chunk words: {processing_config['chunk_words']}")
        logger.info(f"  Days back: {processing_config['days_back']}")
        logger.info(f"  Data dir: {processing_config['data_dir']}")
        logger.info(f"  Output dir: {processing_config['output_dir']}")
        
        # Test data availability
        data_dir = Path(processing_config['data_dir'])
        output_dir = Path(processing_config['output_dir'])
        
        if data_dir.exists():
            xml_files = list(data_dir.rglob('*.xml'))
            logger.info(f"✅ Found {len(xml_files)} XML files in data directory")
            
            # Show breakdown by program
            for program in ['MPFS', 'SNF', 'HOSPICE']:
                program_files = [f for f in xml_files if f.parent.name == program]
                if program_files:
                    logger.info(f"  {program}: {len(program_files)} files")
        else:
            logger.error(f"❌ Data directory not found: {data_dir}")
            return False
        
        if output_dir.exists():
            # Check existing processed data
            chunks_file = output_dir / 'chunks.json'
            faiss_index = output_dir / 'faiss.index'
            metadata_file = output_dir / 'faiss_metadata.json'
            
            if chunks_file.exists():
                size_mb = chunks_file.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Chunks file: {size_mb:.1f} MB")
            
            if faiss_index.exists():
                size_mb = faiss_index.stat().st_size / (1024 * 1024)
                logger.info(f"✅ FAISS index: {size_mb:.1f} MB")
            
            if metadata_file.exists():
                size_mb = metadata_file.stat().st_size / (1024 * 1024)
                logger.info(f"✅ FAISS metadata: {size_mb:.1f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def test_incremental_manager():
    """Test incremental manager functionality."""
    logger.info("🔍 Testing incremental manager...")
    
    try:
        from app.core.preprocessing.config_loader import ConfigLoader
        from app.core.preprocessing.incremental_manager import IncrementalManager
        
        # Load config
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        
        # Create manager
        manager = IncrementalManager(
            data_directory=processing_config['data_dir'],
            output_directory=processing_config['output_dir'],
            api_key=processing_config.get('api_key'),
            model=processing_config['model'],
            chunk_words=processing_config['chunk_words'],
            overlap_sentences=processing_config['overlap_sentences']
        )
        
        logger.info("✅ IncrementalManager created successfully")
        
        # Get status
        status = manager.get_status()
        logger.info(f"✅ Manager status retrieved")
        logger.info(f"  Data consistency: {status.get('data_consistency', 'unknown')}")
        logger.info(f"  Files exist: {status.get('files_exist', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ IncrementalManager test failed: {e}")
        return False

def test_chunk_analysis():
    """Analyze existing chunks for key information."""
    logger.info("🔍 Testing chunk analysis...")
    
    try:
        from app.core.preprocessing.config_loader import ConfigLoader
        from app.core.preprocessing.utils.data_persistence import DataPersistence
        
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        output_dir = Path(processing_config['output_dir'])
        
        # Load chunks
        chunks_file = output_dir / 'chunks.json'
        if not chunks_file.exists():
            logger.warning("⚠️ No chunks file found for analysis")
            return True
        
        chunks_result = DataPersistence.load_json(chunks_file)
        if chunks_result['status'] != 'success':
            logger.error(f"❌ Failed to load chunks: {chunks_result.get('error')}")
            return False
        
        chunks = chunks_result['data']
        logger.info(f"✅ Loaded {len(chunks)} chunks for analysis")
        
        # Sample analysis
        sample_size = min(10, len(chunks))
        sample_chunks = list(chunks.items())[:sample_size]
        
        # Analyze chunk content
        analysis = {
            'total_chunks': len(chunks),
            'sample_size': sample_size,
            'text_lengths': [],
            'source_files': set(),
            'monetary_values': 0,
            'percentages': 0,
            'dates': 0
        }
        
        import re
        monetary_pattern = r'\$[\d,]+(?:\.\d{2})?'
        percentage_pattern = r'\d+(?:\.\d+)?%'
        year_pattern = r'\b(?:19|20)\d{2}\b'
        
        for chunk_id, chunk in sample_chunks:
            text = chunk.get('text', '')
            analysis['text_lengths'].append(len(text))
            analysis['source_files'].add(chunk.get('metadata', {}).get('source_file', 'unknown'))
            
            # Look for key information
            analysis['monetary_values'] += len(re.findall(monetary_pattern, text))
            analysis['percentages'] += len(re.findall(percentage_pattern, text))
            analysis['dates'] += len(re.findall(year_pattern, text))
        
        # Report analysis
        avg_length = sum(analysis['text_lengths']) / len(analysis['text_lengths']) if analysis['text_lengths'] else 0
        logger.info(f"📊 Chunk Analysis Results:")
        logger.info(f"  Total chunks: {analysis['total_chunks']:,}")
        logger.info(f"  Sample analyzed: {analysis['sample_size']}")
        logger.info(f"  Average text length: {avg_length:.0f} characters")
        logger.info(f"  Source files: {len(analysis['source_files'])}")
        logger.info(f"  Monetary values found: {analysis['monetary_values']}")
        logger.info(f"  Percentages found: {analysis['percentages']}")
        logger.info(f"  Dates found: {analysis['dates']}")
        
        # Show sample source files
        logger.info(f"  Sample source files:")
        for i, source_file in enumerate(list(analysis['source_files'])[:5]):
            logger.info(f"    {i+1}. {source_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Chunk analysis failed: {e}")
        return False

def test_cost_estimation():
    """Test cost estimation functionality."""
    logger.info("🔍 Testing cost estimation...")
    
    try:
        from app.core.preprocessing.config_loader import ConfigLoader
        from app.core.preprocessing.incremental_manager import IncrementalManager
        
        config = ConfigLoader()
        processing_config = config.get_processing_config()
        
        manager = IncrementalManager(
            data_directory=processing_config['data_dir'],
            output_directory=processing_config['output_dir'],
            api_key=processing_config.get('api_key'),
            model=processing_config['model'],
            chunk_words=processing_config['chunk_words'],
            overlap_sentences=processing_config['overlap_sentences']
        )
        
        # Get cost estimate for potential updates
        estimate = manager.estimate_incremental_update_cost()
        
        logger.info("✅ Cost estimation completed")
        logger.info(f"📊 Cost Estimate:")
        logger.info(f"  Files to process: {estimate.get('files_to_process', 0)}")
        logger.info(f"  Estimated chunks: {estimate.get('estimated_new_chunks', 0)}")
        logger.info(f"  Estimated cost: ${estimate.get('estimated_cost', 0):.4f}")
        logger.info(f"  Current total cost: ${estimate.get('current_total_cost', 0):.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cost estimation failed: {e}")
        return False

def main():
    """Run all quick tests."""
    logger.info("🚀 Starting Quick Preprocessing Tests")
    
    tests = [
        ("Configuration and Data", test_config_and_data),
        ("Incremental Manager", test_incremental_manager),
        ("Chunk Analysis", test_chunk_analysis),
        ("Cost Estimation", test_cost_estimation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
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
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 QUICK TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All quick tests passed!")
        logger.info("\n💡 Next steps:")
        logger.info("  1. The preprocessing system is working correctly")
        logger.info("  2. You can now run incremental updates")
        logger.info("  3. The system tracks costs and changes efficiently")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())