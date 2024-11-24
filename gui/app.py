import tkinter as tk
from tkinter import ttk

from .styles.theme import configure_app_style
from .styles.material import MaterialColors
from .components.status_bar import StatusBar
from .tabs.encrypt_tab import EncryptTab
from .tabs.decrypt_tab import DecryptTab
from .tabs.embed_tab import EmbedTab
from .tabs.extract_tab import ExtractTab

class StegeCryptGUI:
    """Main GUI application class for StegeCrypt."""
    
    def __init__(self):
        # Create main window
        self.window = tk.Tk()
        self.window.title("StegeCrypt")
        self.window.geometry("800x800")
        self.window.minsize(800, 800)
        self.window.configure(bg=MaterialColors.BG_COLOR)
        
        # Configure styles
        configure_app_style()
        
        # Create main container
        self.main_container = ttk.Frame(self.window, style='Main.TFrame')
        self.main_container.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Setup UI components
        self.setup_header()
        self.setup_notebook()
        self.setup_status_bar()
        
        # Setup tooltips
        self.setup_tooltips()
    
    def setup_header(self):
        """Setup the application header."""
        header = ttk.Frame(self.main_container, style='Header.TFrame')
        header.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(
            header,
            text="StegeCrypt",
            style='Header.TLabel'
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header,
            text="Secure File Encryption & Steganography",
            style='SubHeader.TLabel'
        )
        subtitle_label.pack()
    
    def setup_notebook(self):
        """Setup the main notebook with tabs."""
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Create tabs
        self.encrypt_tab = EncryptTab(self.notebook)
        self.decrypt_tab = DecryptTab(self.notebook)
        self.embed_tab = EmbedTab(self.notebook)
        self.extract_tab = ExtractTab(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.encrypt_tab.frame, text="  Encrypt  ")
        self.notebook.add(self.decrypt_tab.frame, text="  Decrypt  ")
        self.notebook.add(self.embed_tab.frame, text="  Embed Data  ")
        self.notebook.add(self.extract_tab.frame, text="  Extract Data  ")
    
    def setup_status_bar(self):
        """Setup the global status bar."""
        self.status_bar = StatusBar(self.window)
    
    def setup_tooltips(self):
        """Setup tooltips for various UI elements."""
        from .utils.tooltips import create_tooltip
        
        # Add tooltips to tabs
        create_tooltip(
            self.encrypt_tab.frame,
            "Encrypt files using AES-256 encryption.\nSupports multiple file selection."
        )
        create_tooltip(
            self.decrypt_tab.frame,
            "Decrypt previously encrypted files.\nRequires the original key file."
        )
        create_tooltip(
            self.embed_tab.frame,
            "Hide encrypted data within an image using steganography."
        )
        create_tooltip(
            self.extract_tab.frame,
            "Extract hidden data from an image that contains embedded information."
        )
    
    def run(self):
        """Start the application main loop."""
        self.window.mainloop()
        
    def quit(self):
        """Clean up and quit the application."""
        # Perform any necessary cleanup
        self.window.quit()