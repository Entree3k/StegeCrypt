import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..utils.progress_manager import ProgressManager

class ProgressBar:
    """A reusable progress bar component with percentage display."""
    def __init__(self, parent: ttk.Frame, plugin_manager=None):
        self.plugin_manager = plugin_manager
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.grid_columnconfigure(0, weight=1)  # Progress bar gets extra space
        
        # Progress variable
        self.progress_var = tk.DoubleVar()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.frame,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        # Percentage label
        self.progress_label = ttk.Label(
            self.frame,
            text="0%",
            style='Progress.TLabel'
        )
        self.progress_label.grid(row=0, column=1, padx=(0, 5))
    
    def set_progress(self, value: float):
        """Set progress with plugin hooks."""
        if self.plugin_manager:
            results = self.plugin_manager.execute_hook(
                HookPoint.PROGRESS_UPDATE.value,
                value=value,
                component=self
            )
            if results and isinstance(results[0], float):
                value = results[0]

        self.progress_var.set(value)
        self.progress_label.config(text=f"{value:.1f}%")
        
    def add_custom_indicator(self, **kwargs) -> ttk.Label:
        """Allow plugins to add custom progress indicators."""
        label = ttk.Label(
            self.frame,
            style='Progress.TLabel',
            **kwargs
        )
        label.pack(side='right', padx=5)
        return label
    
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