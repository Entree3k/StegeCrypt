import tkinter as tk
from tkinter import ttk, Menu
import logging
from core.plugin_system.plugin_base import HookPoint
from .plugin_manager_gui import PluginManagerGUI

from .styles.theme import configure_app_style
from .styles.material import MaterialColors
from .components.status_bar import StatusBar
from .tabs.encrypt_tab import EncryptTab
from .tabs.decrypt_tab import DecryptTab
from .tabs.embed_tab import EmbedTab
from .tabs.extract_tab import ExtractTab

class StegeCryptGUI:
    """Main GUI application class for StegeCrypt."""
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        
        # Create main window
        self.window = tk.Tk()
        self.window.title("StegeCrypt")
        self.window.geometry("1024x800")  # Increased height
        self.window.minsize(1024, 800)    # Increased minimum size
        self.window.maxsize(1920, 1080)   # Maximum size (Full HD)
        self.window.configure(bg=MaterialColors.BG_COLOR)
        
        # Configure styles
        configure_app_style()
        
        # Execute GUI initialization hook
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.GUI_INIT.value,
                window=self.window
            )
        
        # Create outer frame to handle window resizing
        self.outer_frame = ttk.Frame(self.window)
        self.outer_frame.pack(fill='both', expand=True)
        
        # Create main container
        self.main_container = ttk.Frame(self.outer_frame, style='Main.TFrame')
        self.main_container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Configure grid weights for resizing
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)  # Notebook row
        
        # Setup UI components
        self.setup_header()
        self.setup_menu()
        self.setup_notebook()
        self.setup_status_bar()
        self.setup_tooltips()
        
        # Set up window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
    
    def setup_header(self):
        """Setup the application header."""
        header = ttk.Frame(self.main_container, style='Header.TFrame')
        header.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        title_label = ttk.Label(
            header,
            text="StegeCrypt",
            style='Header.TLabel'
        )
        title_label.pack(fill='x', expand=True)
        
        subtitle_label = ttk.Label(
            header,
            text="Secure File Encryption & Steganography",
            style='SubHeader.TLabel'
        )
        subtitle_label.pack(fill='x', expand=True)
    
    def setup_menu(self):
        """Setup the application menu bar."""
        menubar = Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Plugins menu
        plugins_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plugins", menu=plugins_menu)
        plugins_menu.add_command(
            label="Plugin Manager",
            command=lambda: PluginManagerGUI(self.window, self.plugin_manager)
        )
        
        # Let plugins add their menu items
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.MENU_INIT.value,
                menubar=menubar,
                plugins_menu=plugins_menu,
                main_window=self.window
            )
    
    def setup_notebook(self):
        """Setup the main notebook with tabs."""
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        
        # Create tabs with plugin manager
        self.encrypt_tab = EncryptTab(self.notebook, plugin_manager=self.plugin_manager)
        self.decrypt_tab = DecryptTab(self.notebook, plugin_manager=self.plugin_manager)
        self.embed_tab = EmbedTab(self.notebook, plugin_manager=self.plugin_manager)
        self.extract_tab = ExtractTab(self.notebook, plugin_manager=self.plugin_manager)
        
        # Add tabs to notebook
        self.notebook.add(self.encrypt_tab.frame, text="  Encrypt  ")
        self.notebook.add(self.decrypt_tab.frame, text="  Decrypt  ")
        self.notebook.add(self.embed_tab.frame, text="  Embed Data  ")
        self.notebook.add(self.extract_tab.frame, text="  Extract Data  ")
        
        # Let plugins add their own tabs
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.GUI_TAB_INIT.value,
                notebook=self.notebook
            )
    
    def setup_status_bar(self):
        """Setup the global status bar."""
        self.status_bar = StatusBar(self.main_container, self.plugin_manager)
        self.status_bar.frame.grid(row=3, column=0, sticky='ew', pady=(5, 0))
    
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
        try:
            self.window.mainloop()
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            raise
    
    def quit(self):
        """Clean up and quit the application."""
        try:
            # Execute shutdown hooks
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.SHUTDOWN.value,
                    window=self.window
                )
                
            # Cleanup components
            if hasattr(self, 'status_bar'):
                self.status_bar.cleanup()
                
            # Cleanup tabs
            for tab in [self.encrypt_tab, self.decrypt_tab, self.embed_tab, self.extract_tab]:
                if hasattr(tab, 'cleanup'):
                    try:
                        tab.cleanup()
                    except Exception as e:
                        print(f"Error cleaning up tab: {str(e)}")
            
            # Destroy window
            self.window.quit()
            
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            self.window.quit()