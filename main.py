import sys
from gui_interface import StegeCryptGUI
import cli_interface
from pathlib import Path

def setup_environment():
    """Ensure required directories exist."""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

def main():
    # Setup required directories
    setup_environment()
    
    if len(sys.argv) > 1:
        # If arguments provided, run CLI mode
        cli_interface.main()
    else:
        # No arguments, launch GUI
        app = StegeCryptGUI()
        app.window.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)