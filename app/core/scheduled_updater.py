"""
scheduled_updater.py

Scheduled updater that can be run periodically to check for and process new regulations.
This script is designed to be run via cron or similar scheduling systems.
"""
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from auto_update_pipeline import AutoUpdatePipeline

# Configure logging
def setup_logging():
    """Setup logging for scheduled updates."""
    log_dir = Path(config.build_faiss_output_folder) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"update_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_scheduled_update(days_back: int = 30, force: bool = False) -> Dict:
    """
    Run a scheduled update.
    
    Args:
        days_back: Number of days to look back for new regulations
        force: Force update even if no new regulations found
        
    Returns:
        Dictionary with update results
    """
    logger = setup_logging()
    logger.info("🕐 Starting scheduled regulation update...")
    
    try:
        pipeline = AutoUpdatePipeline(days_back=days_back)
        
        # Check if updates are needed
        if not force and not pipeline.check_for_updates():
            logger.info("✅ No updates needed")
            return {
                "status": "no_updates",
                "timestamp": datetime.now().isoformat(),
                "message": "No new regulations found"
            }
        
        # Run full update
        stats = pipeline.run_full_update()
        
        # Save update history
        save_update_history(stats)
        
        logger.info("✅ Scheduled update completed successfully")
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Scheduled update failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def save_update_history(stats: Dict):
    """Save update history to a JSON file."""
    history_file = Path(config.build_faiss_output_folder) / "update_history.json"
    
    # Load existing history
    if history_file.exists():
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    # Add new entry
    history.append({
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    })
    
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    
    # Save updated history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def get_update_history(limit: int = 10) -> List[Dict]:
    """Get recent update history."""
    history_file = Path(config.build_faiss_output_folder) / "update_history.json"
    
    if not history_file.exists():
        return []
    
    with open(history_file, "r") as f:
        history = json.load(f)
    
    return history[-limit:]

def main():
    """Main function for scheduled updates."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scheduled regulation updater")
    parser.add_argument("--days", "-d", type=int, default=30,
                      help="Number of days to look back")
    parser.add_argument("--force", "-f", action="store_true",
                      help="Force update even if no new regulations found")
    parser.add_argument("--history", "-H", action="store_true",
                      help="Show recent update history")
    parser.add_argument("--limit", "-l", type=int, default=10,
                      help="Number of history entries to show")
    
    args = parser.parse_args()
    
    if args.history:
        history = get_update_history(args.limit)
        print(f"Recent update history (last {len(history)} entries):")
        for entry in history:
            timestamp = entry["timestamp"]
            status = entry.get("status", "unknown")
            stats = entry.get("stats", {})
            
            print(f"  {timestamp}: {status}")
            if stats:
                print(f"    - Files: {stats.get('files_processed', 0)}")
                print(f"    - Chunks: {stats.get('total_chunks_created', 0)}")
                print(f"    - Cost: ${stats.get('total_cost', 0)}")
    else:
        result = run_scheduled_update(args.days, args.force)
        print(f"Update result: {result}")

if __name__ == "__main__":
    main() 