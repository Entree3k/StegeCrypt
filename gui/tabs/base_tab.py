from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List, Any
from datetime import datetime
import os

from ..components.file_input import FileInput, DirectoryInput, FileListInput
from ..components.progress import ProgressBar
from ..components.status_bar import StatusBar
from ..styles.material import MaterialColors
from core.plugin_system.plugin_base import HookPoint

class BaseTab(ABC):
    """Abstract base class for all tabs."""
    
    def __init__(self, parent: ttk.Notebook, title: str, plugin_manager=None):
        """Initialize the base tab structure."""
        # Create main frame for the tab
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)  # Content frame gets extra space
        
        self.title = title
        self.plugin_manager = plugin_manager
        
        # Create header
        header = ttk.Label(
            self.frame,
            text=self.title,
            style='Header.TLabel'
        )
        header.grid(row=0, column=0, sticky='ew', pady=(10, 20))
        
        # Create components container
        self.content_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Progress and status area
        bottom_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        bottom_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ProgressBar(bottom_frame)
        self.progress_bar.frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        
        # Status bar
        self.status_bar = StatusBar(bottom_frame, self.plugin_manager)
        self.status_bar.frame.grid(row=1, column=0, sticky='ew')
        
        # Initialize progress tracking
        self.status_bar.initialize_progress(
            self.progress_bar.progress_var,
            self.progress_bar.progress_label
        )
        
        # Processing state
        self.is_processing = False
        self.files_to_process: List[str] = []
        self.current_file_index = 0
        
        # Execute GUI tab initialization hook
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.GUI_TAB_INIT.value,
                tab=self,
                title=title,
                content_frame=self.content_frame
            )

    def execute_hook(self, hook_point: str, **kwargs) -> List[Any]:
        """Helper method to execute hooks with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                self.show_error(f"Plugin error during {hook_point}: {str(e)}")
                return []
        return []

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
            self.show_error(str(e))
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
    
    def update_status(self, text: str):
        """Update the status message."""
        if self.plugin_manager:
            modified_text = self.execute_hook(
                HookPoint.STATUS_UPDATE.value,
                original_text=text,
                tab=self
            )
            if modified_text and modified_text[0]:
                text = modified_text[0]
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
    
    @abstractmethod
    def setup_ui(self):
        """Set up the tab's user interface."""
        pass
    
    @abstractmethod
    def clear_fields(self):
        """Clear all input fields."""
        pass
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up any resources
            if hasattr(self, 'progress_bar'):
                self.progress_bar.reset()
            
            # Execute cleanup hook if available
            if self.plugin_manager and hasattr(HookPoint, 'TAB_CLEANUP'):
                self.execute_hook(
                    HookPoint.TAB_CLEANUP.value,
                    tab=self
                )
        except Exception as e:
            print(f"Error during tab cleanup: {str(e)}")