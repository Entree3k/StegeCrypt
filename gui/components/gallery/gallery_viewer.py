import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import logging

from ...material_colors import MaterialColors
from .secure_storage import SecureTempStorage
from .temp_manager import TempManager
from .file_manager import FileManager
from .thumbnail_manager import ThumbnailManager
from .ui_components import UIComponents
from .event_handlers import EventHandlers

class GalleryViewer(tk.Tk):
    """Main application window for StegeCrypt Gallery."""
    def __init__(self, plugin_manager=None):
        """Initialize the application.
        
        Args:
            plugin_manager: Optional plugin manager instance
        """
        super().__init__()
        
        # Store plugin manager
        self.plugin_manager = plugin_manager
        
        # Configure main window
        self.title("StegeCrypt Gallery Viewer")
        self.geometry("1200x800")
        self.configure(bg=MaterialColors.BACKGROUND)
        
        # Configure logging
        self.setup_logging()
        
        try:
            # Initialize secure storage first
            logging.info("Initializing SecureTempStorage...")
            self.secure_storage = SecureTempStorage()
            logging.info("SecureTempStorage initialized successfully")
            
            # Initialize managers with secure storage
            logging.info("Initializing managers...")
            self.temp_manager = TempManager(self.secure_storage)
            self.file_manager = FileManager(self.temp_manager)
            self.thumbnail_manager = ThumbnailManager(self)
            self.ui = UIComponents(self)
            self.event_handlers = EventHandlers(self)
            logging.info("Managers initialized successfully")
            
            # Initialize state variables
            self.current_directory = None
            self.key_file = None
            self.encrypted_files = []
            
            # Track window state
            self.is_closing = False
            
            # Setup UI
            self.setup_styles()
            self.create_layout()
            
            # Bind events
            self.bind_events()
            
            # Initialize plugins if plugin manager exists
            if self.plugin_manager:
                logging.info("Running plugin initialization hooks...")
                self.plugin_manager.run_hook('init', self)
            
            logging.info("GalleryViewer initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize GalleryViewer: {e}")
            messagebox.showerror(
                "Initialization Error",
                "Failed to initialize the application. Please check the logs for details."
            )
            self.quit()
    
    def setup_logging(self):
        """Configure application logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('stegecrypt_gallery.log')
            ]
        )
    
    def setup_styles(self):
        """Configure ttk styles for the application."""
        try:
            self.ui.setup_styles()
        except Exception as e:
            logging.error(f"Failed to setup styles: {e}")
            messagebox.showwarning(
                "Style Error",
                "Failed to load some UI styles. The application may not look as intended."
            )
    
    def create_layout(self):
        """Create the main application layout."""
        try:
            # Create base layout
            self.ui.create_layout()
            
            # Run layout modification hooks if plugin manager exists
            if self.plugin_manager:
                logging.info("Running layout modification hooks...")
                self.plugin_manager.run_hook('modify_layout', self)
                
        except Exception as e:
            logging.error(f"Failed to create layout: {e}")
            messagebox.showerror(
                "Layout Error",
                "Failed to create application layout. The application may not function correctly."
            )
    
    def bind_events(self):
        """Bind application-wide events."""
        # Window events
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Keyboard shortcuts
        self.bind('<Control-o>', lambda e: self.event_handlers.select_directory())
        self.bind('<Control-k>', lambda e: self.event_handlers.select_key())
        self.bind('<Control-q>', lambda e: self.on_closing())
        
        # Handle window state changes
        self.bind('<FocusIn>', self.on_window_focus)
        self.bind('<Configure>', self.on_window_configure)
    
    def on_window_focus(self, event):
        """Handle window focus events."""
        if not self.is_closing:
            # Check temp directory integrity
            self.verify_temp_storage()
    
    def on_window_configure(self, event):
        """Handle window configuration changes."""
        if event.widget == self and not self.is_closing:
            # Update UI layout if needed
            self.ui.update_layout()
    
    def verify_temp_storage(self):
        """Verify secure temporary storage integrity."""
        try:
            if not self.secure_storage.verify_integrity():
                logging.warning("Secure storage integrity check failed")
                self.handle_storage_error()
        except Exception as e:
            logging.error(f"Failed to verify secure storage: {e}")
    
    def handle_storage_error(self):
        """Handle secure storage errors."""
        try:
            # Attempt to recreate secure storage
            self.secure_storage.cleanup()
            self.secure_storage = SecureTempStorage()
            
            # Clear cached data
            self.file_manager.clear_cache()
            self.thumbnail_manager.clear_cache()
            
            # Reload current directory if any
            if self.current_directory:
                self.event_handlers.scan_directory()
                
        except Exception as e:
            logging.error(f"Failed to recover from storage error: {e}")
            messagebox.showerror(
                "Storage Error",
                "Critical storage error occurred. Please restart the application."
            )
            self.quit()
    
    def save_session_state(self):
        """Save current session state."""
        try:
            state = {
                'current_directory': self.current_directory,
                'key_file': self.key_file,
                'window_geometry': self.geometry()
            }
            
            # Save state securely
            self.secure_storage.save_session_state(state)
            logging.info("Session state saved successfully")
            
        except Exception as e:
            logging.error(f"Failed to save session state: {e}")
    
    def load_session_state(self):
        """Load previous session state."""
        try:
            state = self.secure_storage.load_session_state()
            if state:
                # Restore window geometry
                if 'window_geometry' in state:
                    self.geometry(state['window_geometry'])
                
                # Restore directory and key file
                if 'current_directory' in state and os.path.exists(state['current_directory']):
                    self.current_directory = state['current_directory']
                    self.event_handlers.scan_directory()
                
                if 'key_file' in state and os.path.exists(state['key_file']):
                    self.key_file = state['key_file']
                    self.event_handlers.decrypt_files()
                
                logging.info("Session state restored successfully")
                
        except Exception as e:
            logging.error(f"Failed to load session state: {e}")
    
    def cleanup(self):
        """Perform cleanup operations."""
        try:
            # Save session state
            self.save_session_state()
            
            # Clean up managers
            self.file_manager.clear_cache()
            self.thumbnail_manager.clear_cache()
            self.temp_manager.clean_temp_files()
            
            # Clean up secure storage
            self.secure_storage.cleanup()
            
            logging.info("Cleanup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    
    def on_closing(self, event=None):
        """Handle application closing."""
        try:
            if not self.is_closing:
                self.is_closing = True
                
                # Run plugin shutdown hooks if plugin manager exists
                if self.plugin_manager:
                    self.plugin_manager.run_hook('shutdown', self)
                
                # Perform cleanup
                self.cleanup()
                
                # Destroy all child windows
                for child in self.winfo_children():
                    if isinstance(child, tk.Toplevel):
                        child.destroy()
                
                logging.info("Application closed successfully")
                
                # Quit application
                self.quit()
                
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
            self.quit()
    
    def show_about_dialog(self):
        """Show about dialog."""
        about_text = """
        StegeCrypt Gallery Viewer
        Version 1.0.0
        
        A secure viewer for StegeCrypt encrypted files.
        
        Features:
        - Secure temporary storage
        - Image and video support
        - Encrypted thumbnail caching
        - Session state persistence
        """
        
        messagebox.showinfo("About StegeCrypt Gallery", about_text)
    
    def show_error_dialog(self, title, message, exception=None):
        """Show error dialog with optional technical details."""
        if exception:
            details = f"\n\nTechnical Details:\n{str(exception)}"
            message += details
        
        messagebox.showerror(title, message)
    
    def __repr__(self):
        """Return string representation of the viewer."""
        return f"GalleryViewer(directory='{self.current_directory}', files={len(self.encrypted_files)})"