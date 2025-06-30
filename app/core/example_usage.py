#!/usr/bin/env python3
"""
Example usage of the incremental processing system.

This script demonstrates various ways to use the incremental processing system
for adding new XML files to the RAG database.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from incremental_pipeline import IncrementalPipeline
from auto_update_pipeline import AutoUpdatePipeline
from scheduled_updater import run_scheduled_update

def demonstrate_model_comparison():
    """Demonstrate cost comparison between different models."""
    print("=== Model Cost Comparison ===")
    
    # Sample data: 1000 chunks with average 1000 tokens each
    sample_tokens = 1000000  # 1M tokens
    
    # Get models from config
    models = config.embedding_models
    
    print(f"Cost comparison for {sample_tokens:,} tokens:")
    print("-" * 60)
    print(f"{'Model':<25} | {'Price/1K':<10} | {'Cost':<10} | {'Savings vs ada-002':<20}")
    print("-" * 60)
    
    ada_002_price = config.get_embedding_model_price("text-embedding-ada-002")
    
    for model_name, model_config in models.items():
        price = model_config['price_per_1k_tokens']
        cost = sample_tokens / 1000 * price
        savings_vs_ada = (ada_002_price - price) / ada_002_price * 100
        print(f"{model_name:<25} | ${price:<9.5f} | ${cost:<9.4f} | {savings_vs_ada:>5.1f}%")
    
    print("-" * 60)
    print(f"💡 Recommendation: Use {config.default_embedding_model} for best cost-effectiveness")
    print()

def demonstrate_single_file_processing():
    """Demonstrate processing a single file with different models."""
    print("=== Single File Processing ===")
    
    # Example file path (adjust as needed)
    example_file = "MPFS/2024_MPFS_proposed_2024-14828.xml"
    
    # Test with default model and ada-002 for comparison
    models_to_test = [config.default_embedding_model, "text-embedding-ada-002"]
    
    for model in models_to_test:
        print(f"\n🔄 Processing with model: {model}")
        try:
            pipeline = IncrementalPipeline(model=model)
            result = pipeline.process_single_file(example_file)
            
            print(f"✅ Result:")
            print(f"   - File: {result['file']}")
            print(f"   - Status: {result['status']}")
            print(f"   - Chunks: {result['chunks_created']}")
            print(f"   - Embeddings: {result['embeddings_added']}")
            print(f"   - Cost: ${result['estimated_cost']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()

def demonstrate_batch_processing():
    """Demonstrate batch processing of new files."""
    print("=== Batch Processing ===")
    
    try:
        # Use the default model from config
        pipeline = IncrementalPipeline()
        
        print("🔄 Processing all new/modified files...")
        results = pipeline.process_new_files()
        
        if results:
            print(f"✅ Processed {len(results)} files:")
            total_cost = sum(r['estimated_cost'] for r in results)
            total_chunks = sum(r['chunks_created'] for r in results)
            
            for result in results:
                print(f"   - {result['file']}: {result['chunks_created']} chunks, ${result['estimated_cost']}")
            
            print(f"\n📊 Summary:")
            print(f"   - Total files: {len(results)}")
            print(f"   - Total chunks: {total_chunks}")
            print(f"   - Total cost: ${total_cost:.4f}")
        else:
            print("✅ No new files to process")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demonstrate_cleanup_and_processing():
    """Demonstrate cleanup and processing workflow."""
    print("=== Cleanup and Processing ===")
    
    try:
        pipeline = IncrementalPipeline()
        
        print("🔄 Running cleanup and processing...")
        result = pipeline.cleanup_and_process()
        
        print(f"✅ Results:")
        print(f"   - Deleted files: {len(result['deleted_files'])}")
        print(f"   - New files: {len(result['new_files'])}")
        print(f"   - Processing results: {len(result['processing_results'])}")
        
        if result['processing_results']:
            total_cost = sum(r['estimated_cost'] for r in result['processing_results'])
            total_chunks = sum(r['chunks_created'] for r in result['processing_results'])
            print(f"   - Total chunks: {total_chunks}")
            print(f"   - Total cost: ${total_cost:.4f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demonstrate_auto_update():
    """Demonstrate automated update pipeline."""
    print("=== Automated Update Pipeline ===")
    
    try:
        # Use the default model from config
        pipeline = AutoUpdatePipeline(days_back=30)
        
        print("🔄 Running automated update...")
        result = pipeline.run_full_update()
        
        print(f"✅ Update completed:")
        print(f"   - Regulations found: {len(result['regulations'])}")
        print(f"   - Files downloaded: {len(result['downloaded_files'])}")
        print(f"   - Processing results: {len(result['processing_results'])}")
        
        if result['processing_results']:
            total_cost = sum(r['estimated_cost'] for r in result['processing_results'])
            print(f"   - Total cost: ${total_cost:.4f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demonstrate_scheduled_updates():
    """Demonstrate scheduled update functionality."""
    print("=== Scheduled Updates ===")
    
    try:
        print("🔄 Running scheduled update...")
        result = run_scheduled_update(days_back=30)
        
        print(f"✅ Scheduled update completed:")
        print(f"   - Status: {result['status']}")
        print(f"   - Timestamp: {result['timestamp']}")
        
        if result.get('stats'):
            stats = result['stats']
            print(f"   - Regulations found: {len(stats.get('regulations', []))}")
            print(f"   - Files processed: {len(stats.get('processing_results', []))}")
            
            if stats.get('processing_results'):
                total_cost = sum(r.get('estimated_cost', 0) for r in stats['processing_results'])
                print(f"   - Total cost: ${total_cost:.4f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def demonstrate_system_status():
    """Demonstrate system status checking."""
    print("=== System Status ===")
    
    try:
        pipeline = IncrementalPipeline()
        
        print("🔄 Checking system status...")
        status = pipeline.get_system_status()
        
        print(f"✅ System Status:")
        print(f"   - Model: {pipeline.model}")
        print(f"   - Processed files: {status['processed_files_count']}")
        print(f"   - Total chunks: {status['total_chunks']}")
        print(f"   - FAISS index size: {status['faiss_index_size']}")
        print(f"   - FAISS dimension: {status['faiss_index_dimension']}")
        print(f"   - New files: {len(status['new_files'])}")
        print(f"   - Deleted files: {len(status['deleted_files'])}")
        
        if status['new_files']:
            print(f"   - New files: {status['new_files']}")
        if status['deleted_files']:
            print(f"   - Deleted files: {status['deleted_files']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def main():
    """Run all demonstrations."""
    print("🚀 Incremental Processing System - Example Usage")
    print("=" * 60)
    
    # Model comparison
    demonstrate_model_comparison()
    
    # System status
    demonstrate_system_status()
    
    # Single file processing
    demonstrate_single_file_processing()
    
    # Batch processing
    demonstrate_batch_processing()
    
    # Cleanup and processing
    demonstrate_cleanup_and_processing()
    
    # Auto update
    demonstrate_auto_update()
    
    # Scheduled updates
    demonstrate_scheduled_updates()
    
    print("🎉 All demonstrations completed!")
    print("\n💡 Tips:")
    print(f"   - Default model: {config.default_embedding_model}")
    print("   - Use --cleanup flag to handle deleted files")
    print("   - Use --model flag to specify different models")
    print("   - Monitor costs with the detailed logging")
    print("   - Model configuration is in config files")

if __name__ == "__main__":
    main() 