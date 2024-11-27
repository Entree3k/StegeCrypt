import tkinter as tk
from tkinter import ttk
from core.plugin_system.plugin_base import HookPoint

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text, plugin_manager=None):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.plugin_manager = plugin_manager
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
    
    def execute_hook(self, hook_point: str, **kwargs) -> list:
        """Execute hook with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                print(f"Plugin error during {hook_point}: {str(e)}")
        return []
    
    def show_tooltip(self, event=None):
        """Display the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Allow plugins to modify tooltip position
        if self.plugin_manager:
            results = self.execute_hook(
                HookPoint.TOOLTIP_POSITION.value,
                x=x,
                y=y,
                widget=self.widget
            )
            if results and isinstance(results[0], dict):
                x = results[0].get('x', x)
                y = results[0].get('y', y)
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Allow plugins to modify tooltip text
        display_text = self.text
        if self.plugin_manager:
            results = self.execute_hook(
                HookPoint.TOOLTIP_TEXT.value,
                original_text=self.text,
                widget=self.widget
            )
            if results and isinstance(results[0], str):
                display_text = results[0]
        
        # Allow plugins to modify tooltip style
        style_kwargs = {
            'justify': 'left',
            'background': "#ffffe0",
            'relief': 'solid',
            'borderwidth': 1,
            'padding': (5, 5)
        }
        
        if self.plugin_manager:
            results = self.execute_hook(
                HookPoint.TOOLTIP_STYLE.value,
                style=style_kwargs
            )
            if results and isinstance(results[0], dict):
                style_kwargs.update(results[0])
        
        label = ttk.Label(
            self.tooltip,
            text=display_text,
            **style_kwargs
        )
        label.pack()
        
        # Execute post-show hook
        self.execute_hook(
            HookPoint.TOOLTIP_SHOWN.value,
            tooltip=self.tooltip,
            widget=self.widget
        )
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            # Execute pre-hide hook
            self.execute_hook(
                HookPoint.TOOLTIP_HIDE.value,
                tooltip=self.tooltip,
                widget=self.widget
            )
            self.tooltip.destroy()
            self.tooltip = None

def create_tooltip(widget, text, plugin_manager=None):
    """Helper function to create a tooltip."""
    return ToolTip(widget, text, plugin_manager)