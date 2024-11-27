from tkinter import ttk
import time
from typing import Optional
from core.plugin_system.plugin_base import HookPoint

class ProgressManager:
    """Manage progress updates and time estimation for file operations."""
    def __init__(self, progress_var, progress_label, status_label, time_label, progress_detail, plugin_manager=None):
        self.progress_var = progress_var
        self.progress_label = progress_label
        self.status_label = status_label
        self.time_label = time_label
        self.progress_detail = progress_detail
        self.start_time: Optional[float] = None
        self.plugin_manager = plugin_manager
    
    def execute_hook(self, hook_point: str, **kwargs) -> list:
        """Execute hook with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                print(f"Plugin error during {hook_point}: {str(e)}")
        return []
    
    def start(self):
        """Start progress tracking."""
        self.start_time = time.time()
        self.update(0, 0, "Starting...")
        
        self.execute_hook(
            HookPoint.PROGRESS_START.value,
            manager=self
        )
    
    def update(self, completed: int, total: int, status: str = None):
        """Update progress and status displays."""
        # Allow plugins to modify progress values
        if self.plugin_manager:
            results = self.execute_hook(
                HookPoint.PROGRESS_UPDATE.value,
                completed=completed,
                total=total,
                status=status,
                manager=self
            )
            if results and isinstance(results[0], dict):
                completed = results[0].get('completed', completed)
                total = results[0].get('total', total)
                status = results[0].get('status', status)
        
        if completed > 0 and total > 0:
            progress = (completed / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress:.1f}%")
            
            # Update time remaining estimate
            elapsed = time.time() - self.start_time if self.start_time else 0
            avg_time = elapsed / completed
            remaining = (total - completed) * avg_time
            
            # Allow plugins to modify time estimation
            if self.plugin_manager:
                results = self.execute_hook(
                    HookPoint.PROGRESS_TIME_ESTIMATE.value,
                    elapsed=elapsed,
                    remaining=remaining,
                    completed=completed,
                    total=total
                )
                if results and isinstance(results[0], float):
                    remaining = results[0]
            
            time_text = self._format_time_remaining(remaining)
            self.time_label.config(text=time_text)
            self.progress_detail.config(text=f"File {completed}/{total}")
        
        if status:
            self.status_label.config(text=status)
    
    def reset(self):
        """Reset all progress indicators."""
        self.execute_hook(
            HookPoint.PROGRESS_RESET.value,
            manager=self
        )
        
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")
        self.start_time = None
    
    def _format_time_remaining(self, seconds: float) -> str:
        """Format remaining time as a human-readable string."""
        # Allow plugins to customize time formatting
        if self.plugin_manager:
            results = self.execute_hook(
                HookPoint.PROGRESS_TIME_FORMAT.value,
                seconds=seconds
            )
            if results and isinstance(results[0], str):
                return results[0]
        
        if seconds < 60:
            return f"{seconds:.0f} seconds remaining"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s remaining"