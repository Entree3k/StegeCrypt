from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List
from datetime import datetime
import os

from ..components.file_input import FileInput, DirectoryInput, FileListInput
from ..components.progress import ProgressBar
from ..components.status_bar import StatusBar
from ..styles.material import MaterialColors

class BaseTab(ABC):
    """Abstract base class for all tabs."""
    
    def __init__(self, parent: ttk.Notebook, title: str):
        """Initialize the base tab structure."""
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.title = title
        
        # Set up header
        self.setup_header()
        
        # Create components container
        self.content_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Progress bar
        self.progress_bar = ProgressBar(self.frame)
        
        # Status bar (local to tab)
        self.status_bar = StatusBar(self.frame)
        self.status_bar.initialize_progress(
            self.progress_bar.progress_var,
            self.progress_bar.progress_label
        )
        
        # Processing state
        self.is_processing = False
        self.files_to_process: List[str] = []
        self.current_file_index = 0
    
    def setup_header(self):
        """Set up the tab header."""
        ttk.Label(
            self.frame,
            text=self.title,
            font=('Helvetica', 14, 'bold'),
            background=MaterialColors.WHITE,
            foreground=MaterialColors.PRIMARY_COLOR
        ).pack(pady=10, padx=20, anchor='w')
    
    def start_processing(self, process_func, validation_func=None):
        """Start processing files in a separate thread."""
        if self.is_processing:
            messagebox.showwarning("Warning", "A process is already running")
            return
            
        if validation_func and not validation_func():
            return
            
        self.is_processing = True
        self.status_bar.start_progress()
        threading.Thread(target=self._process_wrapper, args=(process_func,)).start()
    
    def _process_wrapper(self, process_func):
        """Wrapper for processing function with proper cleanup."""
        try:
            process_func()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.is_processing = False
            self.status_bar.reset()
    
    def _generate_output_filename(
        self, 
        input_path: str, 
        output_dir: str, 
        suffix: str = "",
        keep_extension: bool = True
    ) -> str:
        """Generate an output filename with timestamp."""
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if keep_extension:
            return os.path.join(output_dir, f"{name}_{timestamp}{suffix}{ext}")
        return os.path.join(output_dir, f"{name}_{timestamp}{suffix}")
    
    @abstractmethod
    def setup_ui(self):
        """Set up the tab's user interface."""
        pass
    
    @abstractmethod
    def clear_fields(self):
        """Clear all input fields."""
        pass
    
    def update_status(self, text: str):
        """Update the status message."""
        self.status_bar.update_status(text)
    
    def update_progress(self, completed: int, total: int, status: Optional[str] = None):
        """Update progress information."""
        self.status_bar.update_progress(completed, total, status)
    
    def show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Error", message)
    
    def show_warning(self, message: str):
        """Show warning message."""
        messagebox.showwarning("Warning", message)
    
    def show_success(self, message: str):
        """Show success message."""
        messagebox.showinfo("Success", message)