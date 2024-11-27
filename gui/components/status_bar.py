import tkinter as tk
from tkinter import ttk
from ..utils.progress_manager import ProgressManager
from typing import Optional
from core.plugin_system.plugin_base import HookPoint

class StatusBar:
    """Status bar component with progress information and time estimation."""
    def __init__(self, parent: tk.Widget, plugin_manager=None):
        self.plugin_manager = plugin_manager
        
        # Create main frame
        self.frame = ttk.Frame(parent, style='Status.TFrame')
        self.frame.grid(row=999, column=0, sticky='ew', padx=5, pady=5)  # Use high row number to ensure it's at bottom
        
        # Configure grid weights
        self.frame.grid_columnconfigure(0, weight=1)  # Status label column
        self.frame.grid_columnconfigure(1, weight=0)  # Progress detail column
        self.frame.grid_columnconfigure(2, weight=0)  # Time label column
        
        # Status label (left-aligned)
        self.status_label = ttk.Label(
            self.frame, 
            text="Ready", 
            style='Status.TLabel'
        )
        self.status_label.grid(row=0, column=0, sticky='w', padx=5)
        
        # Time remaining label (right-aligned)
        self.time_label = ttk.Label(
            self.frame, 
            text="", 
            style='Status.TLabel'
        )
        self.time_label.grid(row=0, column=2, sticky='e', padx=5)
        
        # Detailed progress label (right-aligned before time)
        self.progress_detail = ttk.Label(
            self.frame,
            text="",
            style='Status.TLabel'
        )
        self.progress_detail.grid(row=0, column=1, sticky='e', padx=5)
        
        # Allow plugins to add custom status elements
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.STATUS_BAR_INIT.value,
                status_bar=self,
                frame=self.frame
            )
        
        # Initialize progress manager
        self.progress_manager = None

    def execute_hook(self, hook_point: str, **kwargs) -> list:
        """Execute hook with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                print(f"Plugin error during {hook_point}: {str(e)}")
        return []

    def initialize_progress(self, progress_var: tk.DoubleVar, progress_label: ttk.Label):
        """Initialize progress manager with variables."""
        self.progress_manager = ProgressManager(
            progress_var=progress_var,
            progress_label=progress_label,
            status_label=self.status_label,
            time_label=self.time_label,
            progress_detail=self.progress_detail,
            plugin_manager=self.plugin_manager
        )

    def update_status(self, text: str):
        """Update the status message."""
        # Allow plugins to modify status text
        results = self.execute_hook(
            HookPoint.STATUS_UPDATE.value,
            original_text=text,
            status_bar=self
        )
        
        # Use modified text if provided by plugin
        if results and isinstance(results[0], str):
            text = results[0]
            
        self.status_label.config(text=text)

    def update_progress(self, completed: int, total: int, status: Optional[str] = None):
        """Update progress information."""
        # Allow plugins to modify progress values
        results = self.execute_hook(
            HookPoint.PROGRESS_UPDATE.value,
            completed=completed,
            total=total,
            status=status,
            status_bar=self
        )
        
        # Apply modifications from plugins
        if results:
            for result in results:
                if isinstance(result, dict):
                    completed = result.get('completed', completed)
                    total = result.get('total', total)
                    status = result.get('status', status)
        
        if self.progress_manager:
            self.progress_manager.update(completed, total, status)

    def start_progress(self):
        """Start progress tracking."""
        self.execute_hook(
            HookPoint.PROGRESS_START.value,
            status_bar=self
        )
        
        if self.progress_manager:
            self.progress_manager.start()

    def reset(self):
        """Reset the status bar."""
        self.execute_hook(
            HookPoint.PROGRESS_RESET.value,
            status_bar=self
        )
        
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
        # Allow plugins to modify error messages
        results = self.execute_hook(
            HookPoint.STATUS_ERROR.value,
            message=message,
            status_bar=self
        )
        
        if results and isinstance(results[0], str):
            message = results[0]
            
        self.status_label.config(text=f"Error: {message}")

    def set_warning(self, message: str):
        """Display a warning message."""
        # Allow plugins to modify warning messages
        results = self.execute_hook(
            HookPoint.STATUS_WARNING.value,
            message=message,
            status_bar=self
        )
        
        if results and isinstance(results[0], str):
            message = results[0]
            
        self.status_label.config(text=f"Warning: {message}")

    def set_success(self, message: str):
        """Display a success message."""
        # Allow plugins to modify success messages
        results = self.execute_hook(
            HookPoint.STATUS_SUCCESS.value,
            message=message,
            status_bar=self
        )
        
        if results and isinstance(results[0], str):
            message = results[0]
            
        self.status_label.config(text=f"Success: {message}")

    def add_custom_label(self, text: str, side: str = 'right', **kwargs) -> ttk.Label:
        """Allow plugins to add custom labels to the status bar."""
        label = ttk.Label(
            self.frame,
            text=text,
            style='Status.TLabel',
            **kwargs
        )
        label.pack(side=side, padx=5)
        return label

    def cleanup(self):
        """Clean up status bar resources."""
        if self.plugin_manager:
            self.execute_hook(
                HookPoint.STATUS_CLEANUP.value,
                status_bar=self
            )