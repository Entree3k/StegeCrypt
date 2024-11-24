import tkinter as tk
from tkinter import ttk
from ..utils.progress_manager import ProgressManager
from typing import Optional

class StatusBar:
    """Status bar component with progress information and time estimation."""
    def __init__(self, parent: tk.Widget):
        # Create main frame
        self.frame = ttk.Frame(parent, style='Status.TFrame')
        self.frame.pack(fill='x', side='bottom', padx=5, pady=5)
        
        # Status label (left-aligned)
        self.status_label = ttk.Label(
            self.frame, 
            text="Ready", 
            style='Status.TLabel'
        )
        self.status_label.pack(side='left', padx=5)
        
        # Time remaining label (right-aligned)
        self.time_label = ttk.Label(
            self.frame, 
            text="", 
            style='Status.TLabel'
        )
        self.time_label.pack(side='right', padx=5)
        
        # Detailed progress label (right-aligned)
        self.progress_detail = ttk.Label(
            self.frame,
            text="",
            style='Status.TLabel'
        )
        self.progress_detail.pack(side='right', padx=5)
        
        # Initialize progress manager
        self.progress_manager = None

    def initialize_progress(self, progress_var: tk.DoubleVar, progress_label: ttk.Label):
        """Initialize progress manager with variables."""
        self.progress_manager = ProgressManager(
            progress_var=progress_var,
            progress_label=progress_label,
            status_label=self.status_label,
            time_label=self.time_label,
            progress_detail=self.progress_detail
        )

    def update_status(self, text: str):
        """Update the status message."""
        self.status_label.config(text=text)

    def update_progress(self, completed: int, total: int, status: Optional[str] = None):
        """Update progress information."""
        if self.progress_manager:
            self.progress_manager.update(completed, total, status)

    def start_progress(self):
        """Start progress tracking."""
        if self.progress_manager:
            self.progress_manager.start()

    def reset(self):
        """Reset the status bar."""
        if self.progress_manager:
            self.progress_manager.reset()
        else:
            self.status_label.config(text="Ready")
            self.time_label.config(text="")
            self.progress_detail.config(text="")

    def get_progress_manager(self) -> Optional[ProgressManager]:
        """Get the progress manager instance."""
        return self.progress_manager

    def set_error(self, message: str):
        """Display an error message."""
        self.status_label.config(text=f"Error: {message}")

    def set_warning(self, message: str):
        """Display a warning message."""
        self.status_label.config(text=f"Warning: {message}")

    def set_success(self, message: str):
        """Display a success message."""
        self.status_label.config(text=f"Success: {message}")