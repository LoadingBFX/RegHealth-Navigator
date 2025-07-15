#!/usr/bin/env python3
"""
Quick Test Runner for Incremental Update Testing

This script provides a simplified interface to run specific tests or all tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --test chunk       # Run only chunk modification test
    python run_tests.py --test deletion    # Run only file deletion test  
    python run_tests.py --test preservation # Run only key info preservation test
    python run_tests.py --dry-run          # Show what would be tested without executing
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from test_incremental_update import IncrementalUpdateTester


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def run_specific_test(tester: IncrementalUpdateTester, test_name: str):
    """Run a specific test."""
    test_methods = {
        'chunk': tester.test_chunk_modification_update,
        'deletion': tester.test_file_deletion_and_redownload,
        'preservation': tester.test_key_information_preservation
    }
    
    if test_name not in test_methods:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_methods.keys())}")
        return False
    
    print(f"🧪 Running single test: {test_name}")
    
    # Backup current state
    backup_info = tester.backup_current_state()
    
    try:
        # Run the specific test
        test_result = test_methods[test_name]()
        
        # Print results
        if test_result['success']:
            print(f"✅ Test '{test_name}' PASSED")
        else:
            print(f"❌ Test '{test_name}' FAILED")
            if test_result.get('errors'):
                for error in test_result['errors']:
                    print(f"   Error: {error}")
        
        return test_result['success']
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return False
    
    finally:
        # Restore from backup
        tester.restore_from_backup()


def dry_run_tests():
    """Show what tests would be executed without running them."""
    print("🔍 DRY RUN - Tests that would be executed:")
    print("")
    
    tests = [
        {
            'name': 'Chunk Modification Update',
            'description': 'Modifies a random chunk and verifies embedding update detection',
            'checks': [
                'Random chunk selection and modification',
                'Embedding update detection',
                'Data consistency verification',
                'Cost estimation accuracy'
            ]
        },
        {
            'name': 'File Deletion and Re-download',
            'description': 'Deletes XML files and tests automatic re-download',
            'checks': [
                'Random file deletion from MPFS/SNF/HOSPICE',
                'Auto-update with extended time range (3 years)',
                'File re-download verification',
                'Chunk and embedding recovery',
                'Cost and API call tracking'
            ]
        },
        {
            'name': 'Key Information Preservation',
            'description': 'Verifies critical information is preserved in chunks',
            'checks': [
                'Monetary values preservation',
                'Percentages and dates preservation',
                'Section numbers preservation',
                'Important regulatory terms preservation'
            ]
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"{i}. {test['name']}")
        print(f"   Description: {test['description']}")
        print(f"   Checks:")
        for check in test['checks']:
            print(f"     • {check}")
        print("")
    
    print("💡 Use --test <name> to run individual tests:")
    print("   --test chunk       (Chunk Modification Update)")
    print("   --test deletion    (File Deletion and Re-download)")
    print("   --test preservation (Key Information Preservation)")


def main():
    parser = argparse.ArgumentParser(description='Incremental Update Test Runner')
    parser.add_argument(
        '--test', 
        choices=['chunk', 'deletion', 'preservation'],
        help='Run specific test only'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what tests would run without executing'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Handle dry run
    if args.dry_run:
        dry_run_tests()
        return
    
    # Initialize tester
    try:
        tester = IncrementalUpdateTester()
    except Exception as e:
        print(f"💥 Failed to initialize tester: {e}")
        sys.exit(1)
    
    # Run tests
    if args.test:
        # Run specific test
        success = run_specific_test(tester, args.test)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        print("🚀 Running all incremental update tests...")
        results = tester.run_all_tests()
        success = results.get('overall_success', False)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()