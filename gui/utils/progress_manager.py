from tkinter import ttk
import time
from typing import Optional

class ProgressManager:
    """Manage progress updates and time estimation for file operations."""
    def __init__(self, progress_var, progress_label, status_label, time_label, progress_detail):
        self.progress_var = progress_var
        self.progress_label = progress_label
        self.status_label = status_label
        self.time_label = time_label
        self.progress_detail = progress_detail
        self.start_time: Optional[float] = None
    
    def start(self):
        """Start progress tracking."""
        self.start_time = time.time()
        self.update(0, 0, "Starting...")
    
    def update(self, completed: int, total: int, status: str = None):
        """Update progress and status displays."""
        if completed > 0 and total > 0:
            progress = (completed / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress:.1f}%")
            
            # Update time remaining estimate
            elapsed = time.time() - self.start_time if self.start_time else 0
            avg_time = elapsed / completed
            remaining = (total - completed) * avg_time
            
            time_text = self._format_time_remaining(remaining)
            self.time_label.config(text=time_text)
            self.progress_detail.config(text=f"File {completed}/{total}")
        
        if status:
            self.status_label.config(text=status)
    
    def reset(self):
        """Reset all progress indicators."""
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")
        self.start_time = None
    
    def _format_time_remaining(self, seconds: float) -> str:
        """Format remaining time as a human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f} seconds remaining"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s remaining"