#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import argparse
import logging
from datetime import datetime

def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
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
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

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

def main():
    """Main entry point for the application."""
    try:
        # Setup environment
        setup_environment()
        setup_logging()
        
        # Parse arguments
        args = parse_arguments()
        
        if args.cli:
            # Import and run CLI interface
            from cli_interface import main as cli_main
            cli_main()
        else:
            # Import and run GUI interface
            from gui.app import StegeCryptGUI
            app = StegeCryptGUI()
            app.run()
            
    except KeyboardInterrupt:
        logging.info("Application terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()