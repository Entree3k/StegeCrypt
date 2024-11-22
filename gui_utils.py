import tkinter as tk
from tkinter import ttk

class MaterialStyle:
    """Material Design color constants and styles."""
    BG_COLOR = "#f0f0f0"
    PRIMARY_COLOR = "#2196F3"
    SECONDARY_COLOR = "#757575"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FFC107"
    ERROR_COLOR = "#f44336"
    DARK_PRIMARY = "#1976D2"
    LIGHT_PRIMARY = "#BBDEFB"
    WHITE = "#FFFFFF"
    BLACK = "#000000"

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Display the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(
            self.tooltip,
            text=self.text,
            justify='left',
            background="#ffffe0",
            relief='solid',
            borderwidth=1,
            padding=(5, 5)
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ProgressManager:
    """Manage progress updates and time estimation."""
    def __init__(self, progress_var, progress_label, status_label, time_label, progress_detail):
        self.progress_var = progress_var
        self.progress_label = progress_label
        self.status_label = status_label
        self.time_label = time_label
        self.progress_detail = progress_detail
        self.start_time = None
    
    def start(self):
        """Start progress tracking."""
        self.start_time = time.time()
        self.update(0, 0, "Starting...")
    
    def update(self, completed: int, total: int, status: str = None):
        """Update progress and status."""
        if completed > 0 and total > 0:
            progress = (completed / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress:.1f}%")
            
            # Update time remaining
            elapsed = time.time() - self.start_time
            avg_time = elapsed / completed
            remaining = (total - completed) * avg_time
            
            if remaining < 60:
                time_text = f"{remaining:.0f} seconds remaining"
            else:
                minutes = remaining // 60
                seconds = remaining % 60
                time_text = f"{minutes:.0f}m {seconds:.0f}s remaining"
                
            self.time_label.config(text=time_text)
            self.progress_detail.config(text=f"File {completed}/{total}")
        
        if status:
            self.status_label.config(text=status)
    
    def reset(self):
        """Reset progress tracking."""
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")