#!/usr/bin/env python3
"""
Analyze Chunks Structure

Analyze the actual structure of chunks to understand how source files are referenced.
"""

import os
import sys
import json
import logging
from pathlib import Path
from collections import defaultdict

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_chunks_structure():
    """Analyze the structure of chunks and their source file references."""
    logger.info("🔍 Analyzing chunks structure...")
    
    from app.core.preprocessing.config_loader import ConfigLoader
    from app.core.preprocessing.utils.data_persistence import DataPersistence
    
    config = ConfigLoader()
    processing_config = config.get_processing_config()
    output_dir = Path(processing_config['output_dir'])
    data_dir = Path(processing_config['data_dir'])
    
    # Load chunks
    chunks_file = output_dir / 'chunks.json'
    chunks_result = DataPersistence.load_json(chunks_file)
    
    if chunks_result['status'] != 'success':
        logger.error(f"Failed to load chunks: {chunks_result.get('error')}")
        return
    
    chunks = chunks_result['data']
    logger.info(f"📊 Loaded {len(chunks)} chunks")
    
    # Analyze structure
    source_files = defaultdict(int)
    sample_chunks = []
    chunk_fields = set()
    
    if isinstance(chunks, list):
        logger.info("📋 Chunks are stored as a list")
        
        for i, chunk in enumerate(chunks[:10]):  # Sample first 10
            if isinstance(chunk, dict):
                chunk_fields.update(chunk.keys())
                # Check both locations for source_file
                source_file_direct = chunk.get('source_file', 'NO_DIRECT_SOURCE')
                source_file_metadata = chunk.get('metadata', {}).get('source_file', 'NO_METADATA_SOURCE')
                
                # Use metadata source_file as primary
                source_file = source_file_metadata if source_file_metadata != 'NO_METADATA_SOURCE' else source_file_direct
                source_files[source_file] += 1
                
                sample_chunks.append({
                    'index': i,
                    'source_file_direct': source_file_direct,
                    'source_file_metadata': source_file_metadata,
                    'source_file_used': source_file,
                    'text_length': len(chunk.get('text', '')),
                    'fields': list(chunk.keys())
                })
    else:
        logger.info("📋 Chunks are stored as a dictionary")
        
        chunk_ids = list(chunks.keys())[:10]  # Sample first 10
        for chunk_id in chunk_ids:
            chunk = chunks[chunk_id]
            if isinstance(chunk, dict):
                chunk_fields.update(chunk.keys())
                # Check both locations for source_file
                source_file_direct = chunk.get('source_file', 'NO_DIRECT_SOURCE')
                source_file_metadata = chunk.get('metadata', {}).get('source_file', 'NO_METADATA_SOURCE')
                
                # Use metadata source_file as primary
                source_file = source_file_metadata if source_file_metadata != 'NO_METADATA_SOURCE' else source_file_direct
                source_files[source_file] += 1
                
                sample_chunks.append({
                    'chunk_id': chunk_id,
                    'source_file_direct': source_file_direct,
                    'source_file_metadata': source_file_metadata,
                    'source_file_used': source_file,
                    'text_length': len(chunk.get('text', '')),
                    'fields': list(chunk.keys())
                })
    
    # Print analysis
    logger.info(f"\n📋 Chunk Structure Analysis:")
    logger.info(f"  Data type: {'list' if isinstance(chunks, list) else 'dict'}")
    logger.info(f"  Total chunks: {len(chunks)}")
    logger.info(f"  Unique fields: {sorted(chunk_fields)}")
    
    logger.info(f"\n📁 Source File Distribution:")
    sorted_sources = sorted(source_files.items(), key=lambda x: x[1], reverse=True)
    
    for source_file, count in sorted_sources[:20]:  # Top 20
        logger.info(f"  {source_file}: {count} chunks")
    
    logger.info(f"\n🔍 Sample Chunks:")
    for i, sample in enumerate(sample_chunks[:5]):
        logger.info(f"  Sample {i+1}:")
        for key, value in sample.items():
            if key == 'fields':
                logger.info(f"    {key}: {value}")
            else:
                logger.info(f"    {key}: {value}")
        logger.info("")
    
    # Check available XML files
    logger.info(f"📁 Available XML Files:")
    xml_files = []
    for program_dir in ['MPFS', 'SNF', 'HOSPICE']:
        program_path = data_dir / program_dir
        if program_path.exists():
            files = list(program_path.glob('*.xml'))
            xml_files.extend(files)
            logger.info(f"  {program_dir}: {len(files)} files")
            for xml_file in files[:3]:  # Sample first 3
                relative_path = str(xml_file.relative_to(data_dir))
                logger.info(f"    {relative_path}")
    
    # Find chunks that match actual XML files
    logger.info(f"\n🔍 Matching Chunks to XML Files:")
    xml_filenames = [f.name for f in xml_files]
    xml_relative_paths = [str(f.relative_to(data_dir)) for f in xml_files]
    
    matching_files = {}
    for source_file, count in source_files.items():
        if source_file == 'NO_SOURCE':
            continue
        
        # Check various matching patterns
        matches = []
        
        # Direct filename match
        for xml_name in xml_filenames:
            if xml_name in source_file:
                matches.append(f"filename:{xml_name}")
        
        # Relative path match
        for rel_path in xml_relative_paths:
            if rel_path in source_file or source_file.endswith(rel_path):
                matches.append(f"relative:{rel_path}")
        
        if matches:
            matching_files[source_file] = {
                'chunk_count': count,
                'matches': matches
            }
    
    logger.info(f"🎯 Files with Chunks (good candidates for deletion testing):")
    for source_file, info in sorted(matching_files.items(), key=lambda x: x[1]['chunk_count'], reverse=True)[:10]:
        logger.info(f"  {source_file} ({info['chunk_count']} chunks)")
        for match in info['matches'][:2]:  # Show first 2 matches
            logger.info(f"    → {match}")
    
    return {
        'total_chunks': len(chunks),
        'chunk_type': 'list' if isinstance(chunks, list) else 'dict',
        'source_files': dict(source_files),
        'matching_files': matching_files,
        'xml_files': xml_relative_paths
    }

if __name__ == "__main__":
    try:
        result = analyze_chunks_structure()
        print(f"\n✅ Analysis completed. Found {result['total_chunks']} chunks with {len(result['source_files'])} unique source files.")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        sys.exit(1)