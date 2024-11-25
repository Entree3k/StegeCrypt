# core/plugin_base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import tkinter as tk
from pathlib import Path

class BasePlugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self.name: str = None
        self.version: str = None
        self.description: str = None
        self.manifest: Dict[str, Any] = {}
        self.path: Path = None
        self.enabled: bool = True
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
    
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin setting."""
        if not self.manifest or 'settings' not in self.manifest:
            return default
        setting = self.manifest['settings'].get(key)
        if not setting:
            return default
        return setting.get('default', default)
    
    def save_setting(self, key: str, value: Any) -> None:
        """Save a plugin setting."""
        pass

class FileHandlerPlugin(BasePlugin):
    """Base class for file handling plugins."""
    
    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Check if plugin can handle this file type."""
        pass
    
    @abstractmethod
    def process_file(self, file_path: str) -> bool:
        """Process the file."""
        pass

class ExportPlugin(BasePlugin):
    """Base class for export plugins."""
    
    @abstractmethod
    def export(self, file_path: str, destination: str) -> bool:
        """Export file to destination."""
        pass
    
    def get_export_options(self) -> Dict[str, Any]:
        """Get export options configuration."""
        return {}

class ViewerPlugin(BasePlugin):
    """Base class for viewer plugins."""
    
    @abstractmethod
    def can_view(self, file_type: str) -> bool:
        """Check if plugin can view this file type."""
        pass
    
    @abstractmethod
    def create_viewer(self, parent: tk.Widget, file_path: str) -> tk.Widget:
        """Create viewer widget."""
        pass

class MenuPlugin(BasePlugin):
    """Base class for menu plugins."""
    
    def add_menu_items(self, menu: tk.Menu) -> None:
        """Add items to menu."""
        pass
    
    def add_context_menu_items(self, menu: tk.Menu, event: tk.Event) -> None:
        """Add items to context menu."""
        pass

class FilterPlugin(BasePlugin):
    """Base class for filter plugins."""
    
    @abstractmethod
    def apply_filter(self, image_data: bytes) -> bytes:
        """Apply filter to image data."""
        pass
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get filter options configuration."""
        return {}