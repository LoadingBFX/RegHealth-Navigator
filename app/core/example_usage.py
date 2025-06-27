#!/usr/bin/env python3
"""
example_usage.py

Example usage of the automated regulation update system.
This script demonstrates how to use the various components.
"""
import sys
import os

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def example_manual_processing():
    """Example of manual processing workflow."""
    print("=== Manual Processing Example ===")
    
    from incremental_pipeline import IncrementalPipeline
    
    # Initialize pipeline
    pipeline = IncrementalPipeline()
    
    # Check system status
    status = pipeline.get_system_status()
    print(f"System has {status['processed_files_count']} processed files")
    print(f"Total chunks: {status['total_chunks']}")
    print(f"FAISS index size: {status['faiss_index_size']}")
    
    # Check for new files
    new_files = pipeline.chunker.find_new_files()
    if new_files:
        print(f"Found {len(new_files)} new/modified files:")
        for file_path in new_files:
            print(f"  - {file_path.relative_to(pipeline.chunker.input_dir)}")
    else:
        print("No new files found")

def example_automated_update():
    """Example of automated update workflow."""
    print("\n=== Automated Update Example ===")
    
    from auto_update_pipeline import AutoUpdatePipeline
    
    # Initialize auto update pipeline
    pipeline = AutoUpdatePipeline(days_back=30)
    
    # Check for updates
    has_updates = pipeline.check_for_updates()
    if has_updates:
        print("🆕 Updates available!")
        
        # Run full update (commented out to avoid actual processing)
        # stats = pipeline.run_full_update()
        # print(f"Update completed: {stats}")
    else:
        print("✅ System is up to date")

def example_scheduled_update():
    """Example of scheduled update workflow."""
    print("\n=== Scheduled Update Example ===")
    
    from scheduled_updater import run_scheduled_update, get_update_history
    
    # Run scheduled update (commented out to avoid actual processing)
    # result = run_scheduled_update(days_back=30)
    # print(f"Scheduled update result: {result}")
    
    # Show update history
    history = get_update_history(limit=5)
    if history:
        print(f"Recent update history ({len(history)} entries):")
        for entry in history:
            timestamp = entry["timestamp"]
            status = entry.get("status", "unknown")
            print(f"  {timestamp}: {status}")
    else:
        print("No update history found")

def example_single_file_processing():
    """Example of processing a single file."""
    print("\n=== Single File Processing Example ===")
    
    from incremental_pipeline import IncrementalPipeline
    
    pipeline = IncrementalPipeline()
    
    # Example: process a specific file (if it exists)
    # This is just an example - the file might not exist
    example_file = "SNF/2024_SNF_final_2024-16907.xml"
    
    # Check if file exists
    file_path = pipeline.chunker.input_dir / example_file
    if file_path.exists():
        print(f"Processing example file: {example_file}")
        # result = pipeline.process_single_file(example_file)
        # print(f"Processing result: {result}")
    else:
        print(f"Example file not found: {example_file}")

def main():
    """Run all examples."""
    print("RegHealth-Navigator Automated Update System Examples")
    print("=" * 60)
    
    try:
        example_manual_processing()
        example_automated_update()
        example_scheduled_update()
        example_single_file_processing()
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("\nTo run actual updates:")
        print("  python auto_update_pipeline.py --check")
        print("  python auto_update_pipeline.py")
        print("  python scheduled_updater.py")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have:")
        print("  1. Run initial processing (xml_chunker.py + build_faiss.py)")
        print("  2. Set up OPENAI_API_KEY environment variable")
        print("  3. Installed all required dependencies")

if __name__ == "__main__":
    main() 