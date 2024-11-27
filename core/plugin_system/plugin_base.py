from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

class HookPoint(Enum):
    """Define all available hook points in the application."""
    # Application lifecycle hooks
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    
    # GUI hooks
    GUI_INIT = "gui_init"
    GUI_TAB_INIT = "gui_tab_init"
    MENU_INIT = "menu_init"
    
    # CLI hooks
    CLI_INIT = "cli_init"
    
    # Core operation hooks
    PRE_ENCRYPT = "pre_encrypt"
    POST_ENCRYPT = "post_encrypt"
    PRE_DECRYPT = "pre_decrypt"
    POST_DECRYPT = "post_decrypt"
    PRE_EMBED = "pre_embed"
    POST_EMBED = "post_embed"
    PRE_EXTRACT = "pre_extract"
    POST_EXTRACT = "post_extract"
    
    # Manager initialization hooks
    UTILS_INIT = "utils_init"
    CRYPTO_INIT = "crypto_init"
    STEGO_INIT = "stego_init"
    
    # Crypto hooks
    PRE_KEY_GENERATION = "pre_key_generation"
    POST_KEY_GENERATION = "post_key_generation"
    PRE_ENCRYPTION_ALGORITHM = "pre_encryption_algorithm"
    POST_ENCRYPTION_ALGORITHM = "post_encryption_algorithm"
    
    # Steganography hooks
    PRE_EMBED_ALGORITHM = "pre_embed_algorithm"
    POST_EMBED_ALGORITHM = "post_embed_algorithm"
    PRE_EXTRACT_ALGORITHM = "pre_extract_algorithm"
    POST_EXTRACT_ALGORITHM = "post_extract_algorithm"
    
    # File operation hooks
    FILE_LIST_INIT = "file_list_init"
    FILE_SELECTION = "file_selection"
    FILE_INPUT_INIT = "file_input_init"
    FILE_BROWSE = "file_browse"
    DIR_INPUT_INIT = "dir_input_init"
    DIR_BROWSE = "dir_browse"
    
    # Utils hooks
    PRE_FILE_HASH = "pre_file_hash"
    POST_FILE_HASH = "post_file_hash"
    PRE_SECURE_DELETE = "pre_secure_delete"
    POST_SECURE_DELETE = "post_secure_delete"
    
    # Progress and status hooks
    STATUS_BAR_INIT = "status_bar_init"
    STATUS_UPDATE = "status_update"
    PROGRESS_BAR_INIT = "progress_bar_init"
    PROGRESS_UPDATE = "progress_update"
    PROGRESS_START = "progress_start"
    PROGRESS_RESET = "progress_reset"
    PROGRESS_TIME_ESTIMATE = "progress_time_estimate"
    PROGRESS_TIME_FORMAT = "progress_time_format"
    
    # UI component hooks
    TOOLTIP_POSITION = "tooltip_position"
    TOOLTIP_TEXT = "tooltip_text"
    TOOLTIP_STYLE = "tooltip_style"
    TOOLTIP_SHOWN = "tooltip_shown"
    TOOLTIP_HIDE = "tooltip_hide"
    
    # Status message hooks
    STATUS_ERROR = "status_error"
    STATUS_WARNING = "status_warning"
    STATUS_SUCCESS = "status_success"
    STATUS_CLEANUP = "status_cleanup"
    
    # Tab Cleanup hooks
    TAB_CLEANUP = "tab_cleanup"

@dataclass
class PluginMetadata:
    """Plugin metadata container."""
    name: str
    version: str
    author: str
    description: str
    hooks: List[str]
    dependencies: List[str]
    min_app_version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata instance from dictionary."""
        return cls(
            name=data.get('name', 'Unknown Plugin'),
            version=data.get('version', '0.0.1'),
            author=data.get('author', 'Unknown'),
            description=data.get('description', ''),
            hooks=data.get('hooks', []),
            dependencies=data.get('dependencies', []),
            min_app_version=data.get('min_app_version', '1.0.0')
        )

class PluginBase(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup when plugin is disabled."""
        pass
    
    def get_hook_handlers(self) -> Dict[str, callable]:
        """Return a dictionary of hook point handlers."""
        return {}
    
    def get_gui_components(self) -> Dict[str, Any]:
        """Return any GUI components the plugin provides."""
        return {}