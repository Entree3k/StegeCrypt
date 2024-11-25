# core/plugin_hooks.py
from enum import Enum, auto
from typing import Dict, Any, Callable, List
from dataclasses import dataclass

class HookPriority(Enum):
    """Priority levels for hook execution."""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()

@dataclass
class HookInfo:
    """Information about a hook."""
    name: str
    description: str
    parameters: Dict[str, type]
    return_type: type = None

class PluginHooks:
    """Defines all available plugin hooks."""
    
    # Program lifecycle hooks
    INIT = HookInfo(
        name="init",
        description="Called when the application starts",
        parameters={"app": "GalleryViewer"}
    )
    
    SHUTDOWN = HookInfo(
        name="shutdown",
        description="Called when the application is closing",
        parameters={"app": "GalleryViewer"}
    )
    
    # UI hooks
    CREATE_MENUS = HookInfo(
        name="create_menus",
        description="Called when creating application menus",
        parameters={"menu_manager": "MenuManager"}
    )
    
    CONTEXT_MENU = HookInfo(
        name="context_menu",
        description="Called when showing context menu",
        parameters={
            "menu": "tk.Menu",
            "event": "tk.Event"
        }
    )
    
    MODIFY_LAYOUT = HookInfo(
        name="modify_layout",
        description="Called after creating main layout",
        parameters={"ui_components": "UIComponents"}
    )
    
    # File operation hooks
    PRE_DECRYPT = HookInfo(
        name="pre_decrypt",
        description="Called before file decryption",
        parameters={
            "input_path": str,
            "key_file": str
        }
    )
    
    POST_DECRYPT = HookInfo(
        name="post_decrypt",
        description="Called after file decryption",
        parameters={
            "input_path": str,
            "output_path": str,
            "file_type": str
        }
    )
    
    SCAN_DIRECTORY = HookInfo(
        name="scan_directory",
        description="Called after scanning directory",
        parameters={
            "directory": str,
            "files": List[str]
        }
    )
    
    CACHE_CLEARED = HookInfo(
        name="cache_cleared",
        description="Called after clearing file cache",
        parameters={}
    )
    
    # Viewer hooks
    VIEWER_CREATED = HookInfo(
        name="viewer_created",
        description="Called after creating media viewer",
        parameters={
            "viewer": "tk.Toplevel",
            "file_path": str
        }
    )
    
    # Export hooks
    EXPORT = HookInfo(
        name="export",
        description="Called when exporting files",
        parameters={
            "files": List[str],
            "destination": str
        }
    )
    
    @classmethod
    def get_all_hooks(cls) -> Dict[str, HookInfo]:
        """Get all available hooks."""
        return {
            name: value for name, value in cls.__dict__.items()
            if isinstance(value, HookInfo)
        }