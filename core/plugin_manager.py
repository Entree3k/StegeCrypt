import os
import json
import zipfile
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Any, Callable
from .plugin_base import BasePlugin

class PluginManager:
    """Manages plugin lifecycle and hook system."""
    
    def __init__(self):
        self.plugins: Dict[str, 'Plugin'] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.plugin_dir = Path(__file__).parent.parent / 'plugins'
        self.temp_dir = Path(__file__).parent.parent / 'temp' / 'plugins'
        
        # Create plugin directories if they don't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize hooks
        self._initialize_hooks()
    
    def _initialize_hooks(self):
        """Initialize available hook points."""
        hook_points = [
            'init',              # Program initialization
            'shutdown',          # Program shutdown
            'create_menus',      # Menu creation
            'context_menu',      # Context menu creation
            'pre_decrypt',       # Before file decryption
            'post_decrypt',      # After file decryption
            'modify_layout',     # UI layout modification
            'viewer_created',    # When media viewer is created
            'export',           # File export
            'settings_changed'   # When settings are modified
        ]
        
        for hook in hook_points:
            self.hooks[hook] = []
    
    def load_plugins(self):
        """Load all plugins from the plugins directory."""
        try:
            # Clean temp directory
            self._clean_temp_dir()
            
            # Scan for plugin zip files
            for plugin_file in self.plugin_dir.glob('*.zip'):
                try:
                    self._load_plugin(plugin_file)
                except Exception as e:
                    logging.error(f"Failed to load plugin {plugin_file}: {e}")
                    
            logging.info(f"Loaded {len(self.plugins)} plugins successfully")
            
        except Exception as e:
            logging.error(f"Error loading plugins: {e}")
    
    def _load_plugin(self, plugin_path: Path):
        """Load a single plugin from a zip file."""
        try:
            # Create temp directory for plugin
            plugin_temp_dir = self.temp_dir / plugin_path.stem
            plugin_temp_dir.mkdir(exist_ok=True)
            
            # Extract plugin
            with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                zip_ref.extractall(plugin_temp_dir)
            
            # Read plugin manifest
            manifest_path = plugin_temp_dir / 'plugin.json'
            if not manifest_path.exists():
                raise ValueError(f"No plugin.json found in {plugin_path}")
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Validate manifest
            required_fields = ['name', 'version', 'entry_point', 'hooks']
            missing_fields = [field for field in required_fields if field not in manifest]
            if missing_fields:
                raise ValueError(f"Missing required fields in plugin.json: {missing_fields}")
            
            # Load plugin module
            module_path, class_name = manifest['entry_point'].split('.')
            module_file = plugin_temp_dir / f"{module_path}.py"
            
            spec = importlib.util.spec_from_file_location(module_path, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class
            plugin_class = getattr(module, class_name)
            if not issubclass(plugin_class, BasePlugin):
                raise TypeError(f"Plugin class must inherit from BasePlugin class")
            
            # Initialize plugin
            plugin = plugin_class()
            plugin.manifest = manifest
            plugin.path = plugin_temp_dir
            
            # Register plugin hooks
            for hook in manifest['hooks']:
                if hook not in self.hooks:
                    logging.warning(f"Unknown hook '{hook}' in plugin {manifest['name']}")
                    continue
                if hasattr(plugin, hook):
                    self.hooks[hook].append(getattr(plugin, hook))
            
            # Store plugin
            self.plugins[manifest['name']] = plugin
            logging.info(f"Successfully loaded plugin: {manifest['name']} v{manifest['version']}")
            
        except Exception as e:
            logging.error(f"Failed to load plugin {plugin_path}: {e}")
            raise
    
    def run_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Run all registered callbacks for a hook."""
        results = []
        for callback in self.hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logging.error(f"Error running hook {hook_name}: {e}")
        return results
    
    def _clean_temp_dir(self):
        """Clean up temporary plugin files."""
        try:
            for item in self.temp_dir.iterdir():
                if item.is_dir():
                    for subitem in item.iterdir():
                        try:
                            if subitem.is_file():
                                subitem.unlink()
                        except Exception as e:
                            logging.error(f"Error deleting {subitem}: {e}")
                    item.rmdir()
        except Exception as e:
            logging.error(f"Error cleaning temp directory: {e}")
    
    def shutdown(self):
        """Clean up plugins on shutdown."""
        try:
            # Run shutdown hooks
            self.run_hook('shutdown')
            
            # Clean up
            self._clean_temp_dir()
            
        except Exception as e:
            logging.error(f"Error during plugin shutdown: {e}")


class Plugin:
    """Base class for plugins."""
    
    def __init__(self):
        self.manifest = None
        self.path = None
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin setting."""
        if not self.manifest or 'settings' not in self.manifest:
            return default
            
        setting = self.manifest['settings'].get(key)
        if not setting:
            return default
            
        return setting.get('default', default)
    
    def save_setting(self, key: str, value: Any):
        """Save a plugin setting."""
        # To be implemented with settings system
        pass