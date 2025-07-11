#!/usr/bin/env python3
"""
Preprocessing Package Usage Examples

This file demonstrates the correct usage of the preprocessing package with proper
embedding incremental operation logic as requested.

The incremental embedding logic follows these steps:
1. Check if FAISS index exists - if not, regenerate embeddings
2. Check index and metadata consistency - if inconsistent, regenerate embeddings  
3. Check if file has existing embeddings - if not, create new embeddings
4. Check if chunks have changed - only if FAISS is healthy and file has existing embeddings
5. Execute update - remove old embeddings + add new embeddings

Key fixes addressed:
- FAISS index missing → regenerate embeddings
- FAISS index corrupted → regenerate embeddings  
- Index metadata inconsistent → regenerate embeddings
- File missing embeddings → create new embeddings
- Only skip update if FAISS is completely healthy and chunks unchanged
"""

import os
import sys
from pathlib import Path
import logging

# Add the app directory to the path
app_dir = Path(__file__).parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.append(str(app_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def example_config_usage():
    """Demonstrate configuration loading and validation."""
    print("=" * 60)
    print("📋 Configuration Usage Example")
    print("=" * 60)
    
    from core.preprocessing.config_loader import ConfigLoader
    
    # Load configuration
    config = ConfigLoader()
    
    # Get different config sections
    chunking_config = config.get_chunking_config()
    embedding_config = config.get_embedding_config()
    paths_config = config.get_paths_config()
    processing_config = config.get_processing_config()
    
    print(f"Chunking: {chunking_config['chunk_words']} words, {chunking_config['overlap_sentences']} overlap")
    print(f"Embedding: {embedding_config['model']}")
    print(f"Data dir: {paths_config['data_directory']}")
    print(f"Output dir: {paths_config['output_directory']}")
    
    # Validate configuration
    validation = config.validate_config()
    print(f"Config valid: {validation['valid']}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  ❌ {issue}")

def example_xml_chunking():
    """Demonstrate XML chunking without requiring real files."""
    print("\n" + "=" * 60)
    print("📄 XML Chunking Example")
    print("=" * 60)
    
    from core.preprocessing.xml_chunker import XMLChunker
    from core.preprocessing.config_loader import ConfigLoader
    
    # Load config and create chunker
    config = ConfigLoader()
    chunking_config = config.get_chunking_config()
    
    chunker = XMLChunker(**chunking_config)
    
    print(f"XMLChunker initialized:")
    print(f"  - Chunk words: {chunker.chunk_words}")
    print(f"  - Overlap sentences: {chunker.overlap_sentences}")
    print(f"  - Encoding: {chunker.encoding}")
    
    # Show processing statistics
    stats = chunker.get_statistics()
    print(f"Current stats: {stats}")

def example_faiss_configuration():
    """Demonstrate FAISS builder configuration (without actual embeddings)."""
    print("\n" + "=" * 60)
    print("🔍 FAISS Builder Configuration Example")
    print("=" * 60)
    
    from core.preprocessing.config_loader import ConfigLoader
    
    config = ConfigLoader()
    embedding_config = config.get_embedding_config()
    
    print(f"FAISS Builder would use:")
    print(f"  - Model: {embedding_config['model']}")
    print(f"  - Batch size: {embedding_config['batch_size']}")
    print(f"  - Max retries: {embedding_config['max_retries']}")
    print(f"  - Rate limit delay: {embedding_config['rate_limit_delay']}s")
    
    # Estimate costs for example texts
    try:
        from core.preprocessing.faiss_builder import FAISSBuilder
        
        # Only proceed if we have a valid API key
        if embedding_config['api_key'] and embedding_config['api_key'] != 'your-openai-api-key-here':
            builder = FAISSBuilder(**embedding_config)
            
            # Example texts for cost estimation
            example_texts = [
                "This is a sample regulation text about Medicare payments.",
                "Healthcare providers must follow specific guidelines for billing.",
                "The Centers for Medicare & Medicaid Services (CMS) sets these rules."
            ]
            
            estimated_cost = builder.estimate_cost(example_texts)
            print(f"  - Estimated cost for 3 example texts: ${estimated_cost:.6f}")
            
            # Show token counts
            total_tokens = sum(builder.count_tokens(text) for text in example_texts)
            print(f"  - Total tokens: {total_tokens}")
            
        else:
            print("  ⚠️  API key not configured - skipping cost estimation")
            
    except Exception as e:
        print(f"  ⚠️  FAISS builder demo failed: {e}")

def example_incremental_manager_logic():
    """Demonstrate the correct incremental embedding logic."""
    print("\n" + "=" * 60)
    print("🔄 Incremental Manager Logic Example")
    print("=" * 60)
    
    from core.preprocessing.config_loader import ConfigLoader
    
    config = ConfigLoader()
    paths_config = config.get_paths_config()
    
    print("Incremental embedding operation logic:")
    print("Step 1: ✅ Check if FAISS index exists")
    print("        → If index missing → regenerate embeddings")
    print("Step 2: ✅ Check index and metadata consistency") 
    print("        → If vector count ≠ metadata count → regenerate embeddings")
    print("Step 3: ✅ Check if file has existing embeddings")
    print("        → If file has no existing embeddings → create new embeddings")
    print("Step 4: ✅ Check if chunks have changed")
    print("        → Only check chunk hash if FAISS healthy AND file has existing embeddings")
    print("        → If chunks unchanged → skip update")
    print("        → If chunks changed → update embeddings")
    print("Step 5: ✅ Execute update")
    print("        → Remove old embeddings + Add new embeddings")
    
    print("\nKey fixes addressed:")
    print("✅ FAISS index missing → regenerate embeddings")
    print("✅ FAISS index corrupted → regenerate embeddings")  
    print("✅ Index metadata inconsistent → regenerate embeddings")
    print("✅ File missing embeddings → create new embeddings")
    print("✅ Only skip update if FAISS completely healthy AND chunks unchanged")
    
    print(f"\nConfiguration paths:")
    print(f"  - Data directory: {paths_config['data_directory']}")
    print(f"  - Chunks file: {paths_config['chunks_file']}")
    print(f"  - FAISS index: {paths_config['faiss_index']}")
    print(f"  - FAISS metadata: {paths_config['faiss_metadata']}")
    print(f"  - Tracking file: {paths_config['tracking_file']}")

def example_pipeline_usage():
    """Demonstrate pipeline usage patterns."""
    print("\n" + "=" * 60)
    print("🚀 Pipeline Usage Example")
    print("=" * 60)
    
    from core.preprocessing.config_loader import ConfigLoader
    
    config = ConfigLoader()
    processing_config = config.get_processing_config()
    
    print("Pipeline configuration:")
    print(f"  - Data directory: {processing_config['data_dir']}")
    print(f"  - Output directory: {processing_config['output_dir']}")
    print(f"  - Model: {processing_config['model']}")
    print(f"  - Chunk words: {processing_config['chunk_words']}")
    print(f"  - Overlap sentences: {processing_config['overlap_sentences']}")
    
    print("\nTypical workflow:")
    print("1. 📁 Initialize ProcessingPipeline with config")
    print("2. 🔍 Check system status with pipeline.get_system_status()")
    print("3. 💰 Estimate costs with pipeline.estimate_update_cost()")
    print("4. 🔄 Run incremental update with pipeline.run_incremental_update()")
    print("5. 📊 Monitor results and handle any errors")
    
    print("\nFor automated workflows:")
    print("1. 🤖 Use AutoUpdatePipeline for regulation fetching")
    print("2. 📡 Check for new regulations with check_for_new_regulations()")
    print("3. ⬇️  Download new files with download_new_regulations()")
    print("4. 🔄 Process everything with run_full_auto_update()")

def example_system_validation():
    """Demonstrate system validation capabilities."""
    print("\n" + "=" * 60)
    print("🔧 System Validation Example")
    print("=" * 60)
    
    from core.preprocessing.config_loader import ConfigLoader
    
    config = ConfigLoader()
    validation_config = config.get_validation_config()
    
    print("System validation checks:")
    print(f"✅ Chunks file exists: {Path(validation_config['chunks_file']).exists()}")
    print(f"✅ FAISS index exists: {Path(validation_config['faiss_index']).exists()}")
    print(f"✅ FAISS metadata exists: {Path(validation_config['faiss_metadata']).exists()}")
    print(f"✅ Tracking file exists: {Path(validation_config['tracking_file']).exists()}")
    print(f"✅ Data directory exists: {Path(validation_config['data_directory']).exists()}")
    
    print(f"\nValidation configuration:")
    print(f"  - Max chunk file size: {validation_config['max_chunk_file_size_mb']} MB")
    print(f"  - Max metadata file size: {validation_config['max_metadata_file_size_mb']} MB")
    print(f"  - Check data consistency: {validation_config['check_data_consistency']}")

def main():
    """Run all usage examples."""
    print("🔧 Preprocessing Package Usage Examples")
    print("This demonstrates the modular, atomic preprocessing system")
    print("with proper embedding incremental operation logic.")
    
    try:
        example_config_usage()
        example_xml_chunking()
        example_faiss_configuration()
        example_incremental_manager_logic()
        example_pipeline_usage()
        example_system_validation()
        
        print("\n" + "=" * 60)
        print("✨ Examples completed successfully!")
        print("=" * 60)
        print("To use the preprocessing package in your code:")
        print("")
        print("```python")
        print("from core.preprocessing.config_loader import ConfigLoader")
        print("from core.preprocessing.pipeline import ProcessingPipeline")
        print("")
        print("# Load configuration")
        print("config = ConfigLoader()")
        print("processing_config = config.get_processing_config()")
        print("")
        print("# Initialize pipeline")
        print("pipeline = ProcessingPipeline(**processing_config)")
        print("")
        print("# Run incremental update")
        print("result = pipeline.run_incremental_update()")
        print("print(f\"Processed {result['files_processed']} files\")")
        print("```")
        print("")
        print("📖 For more details, see the individual module documentation.")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()