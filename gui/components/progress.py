import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..utils.progress_manager import ProgressManager

class ProgressBar:
    """A reusable progress bar component with percentage display."""
    def __init__(self, parent: ttk.Frame):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.pack(fill='x', padx=20, pady=5)
        
        # Progress variable
        self.progress_var = tk.DoubleVar()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.frame,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill='x', side='left', expand=True)
        
        # Percentage label
        self.progress_label = ttk.Label(
            self.frame,
            text="0%",
            style='Progress.TLabel'
        )
        self.progress_label.pack(side='right', padx=5)
    
    def set_progress(self, value: float):
        """Set the progress value (0-100)."""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value:.1f}%")
    
    def reset(self):
        """Reset the progress bar."""
        self.progress_var.set(0)
        self.progress_label.config(text="0%")

class StatusBar:
    """A reusable status bar component with progress details."""
    def __init__(self, parent: ttk.Frame):
        self.frame = ttk.Frame(parent, style='Status.TFrame')
        self.frame.pack(fill='x', side='bottom', padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(
            self.frame,
            text="Ready",
            style='Status.TLabel'
        )
        self.status_label.pack(side='left', padx=5)
        
        # Time remaining label
        self.time_label = ttk.Label(
            self.frame,
            text="",
            style='Status.TLabel'
        )
        self.time_label.pack(side='right', padx=5)
        
        # Detailed progress label
        self.progress_detail = ttk.Label(
            self.frame,
            text="",
            style='Status.TLabel'
        )
        self.progress_detail.pack(side='right', padx=5)
        
        # Create progress manager
        self.progress_manager = ProgressManager(
            self.status_label,
            self.time_label,
            self.progress_detail
        )
    
    def update_status(self, text: str):
        """Update the status text."""
        self.status_label.config(text=text)
    
    def reset(self):
        """Reset all status indicators."""
        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")