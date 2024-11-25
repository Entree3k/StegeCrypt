import sys
import atexit
import shutil
import logging
from pathlib import Path
import os

def cleanup_temp_directory():
    """Clean up temporary directory on program exit."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = Path(script_dir) / 'temp'
        if temp_dir.exists():
            try:
                shutil.rmtree(str(temp_dir))
                print("Cleaned up temporary directory")
            except Exception as e:
                print(f"Error cleaning temporary directory: {e}")
    except Exception as e:
        print(f"Error in cleanup: {e}")

def main():
    from gui.components import GalleryViewer
    from core.plugin_manager import PluginManager
    
    # Register cleanup function
    atexit.register(cleanup_temp_directory)
    
    try:
        # Initialize and load plugins first
        logging.info("Initializing plugin manager...")
        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        logging.info("Plugins loaded successfully")
        
        # Create application with plugin manager
        logging.info("Creating application...")
        app = GalleryViewer(plugin_manager)  # Pass plugin_manager to constructor
        
        # Start application
        logging.info("Starting application...")
        app.mainloop()
        
    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
    finally:
        cleanup_temp_directory()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()