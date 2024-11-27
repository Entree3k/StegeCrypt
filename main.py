import sys
import os
from pathlib import Path
import argparse
import logging
from datetime import datetime
from core.plugin_system.plugin_manager import PluginManager
from core.plugin_system.plugin_base import HookPoint
from core.aes_crypt import init_crypto_manager
from core.steganography import init_stego_manager
from core.utils import init_utils_manager

def cleanup_logs(log_dir: Path, max_logs: int = 2) -> None:
    """
    Clean up old log files, keeping only the specified number of most recent logs.
    
    Args:
        log_dir: Path object pointing to the logs directory
        max_logs: Maximum number of log files to keep (default: 3)
    """
    try:
        # Get all log files and their creation times
        log_files = []
        for log_file in log_dir.glob("stegecrypt_*.log"):
            try:
                creation_time = os.path.getctime(log_file)
                log_files.append((creation_time, log_file))
            except OSError:
                continue

        # Sort by creation time (newest first)
        log_files.sort(reverse=True)

        # Remove excess log files
        for _, log_file in log_files[max_logs:]:
            try:
                log_file.unlink()
            except OSError:
                continue
    except Exception as e:
        logging.error(f"Error during log cleanup: {str(e)}")

def setup_logging():
    """Configure logging for the application."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Clean up old logs before creating new one
    cleanup_logs(log_dir)
    
    log_file = log_dir / f"stegecrypt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def setup_environment():
    """Ensure required directories exist."""
    # Create required directories
    for dir_name in ["logs", "plugins", "plugins/themes"]:
        Path(dir_name).mkdir(exist_ok=True)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="StegeCrypt - Secure File Encryption & Steganography"
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in command-line interface mode'
    )
    return parser.parse_args()

def init_managers(plugin_manager):
    """Initialize all core managers."""
    init_crypto_manager(plugin_manager)
    init_stego_manager(plugin_manager)
    init_utils_manager(plugin_manager)

def main():
    """Main entry point for the application."""
    try:
        # Setup environment
        setup_environment()
        setup_logging()
        
        # Initialize plugin manager
        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        
        # Initialize core managers
        init_managers(plugin_manager)
        
        # Execute startup hooks
        plugin_manager.execute_hook(HookPoint.STARTUP.value)
        
        # Parse arguments
        args = parse_arguments()
        
        try:
            if args.cli:
                # Import and run CLI interface
                from cli_interface import main as cli_main
                cli_main(plugin_manager)
            else:
                # Import and run GUI interface
                from gui.app import StegeCryptGUI
                app = StegeCryptGUI(plugin_manager)
                app.run()
                
        finally:
            # Execute shutdown hooks
            plugin_manager.execute_hook(HookPoint.SHUTDOWN.value)
            plugin_manager.cleanup()
            
    except KeyboardInterrupt:
        logging.info("Application terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()