import os
import json
import zipfile
import importlib.util
import importlib.machinery
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .plugin_base import PluginBase, PluginMetadata, HookPoint

class PluginManager:
    """Manages plugin loading, unloading, and hook execution."""
    
    def __init__(self, plugins_dir: str = "plugins", builtin_themes_dir: str = "plugins/themes"):
        self.plugins_dir = plugins_dir
        self.themes_dir = builtin_themes_dir
        self.plugins: Dict[str, PluginBase] = {}
        self.hooks: Dict[str, List[callable]] = {}
        
        # Create necessary directories
        os.makedirs(plugins_dir, exist_ok=True)
        os.makedirs(builtin_themes_dir, exist_ok=True)
        
        # Initialize hook points
        for hook in HookPoint:
            self.hooks[hook.value] = []
        
        # Setup logging
        self.logger = logging.getLogger('PluginManager')
    
    def load_plugins(self) -> None:
        """Load all plugins."""
        self.logger.info("Loading plugins and themes...")
        
        # Load built-in themes first
        self._load_builtin_themes()
        
        # Load plugins from zip files
        for item in os.listdir(self.plugins_dir):
            if item.endswith('.zip'):
                plugin_path = os.path.join(self.plugins_dir, item)
                try:
                    self.load_plugin(plugin_path)
                except Exception as e:
                    self.logger.error(f"Failed to load plugin {item}: {str(e)}")
    
    def _load_builtin_themes(self) -> None:
        """Load built-in themes."""
        for theme_dir in os.listdir(self.themes_dir):
            theme_path = os.path.join(self.themes_dir, theme_dir)
            if os.path.isdir(theme_path):
                try:
                    self._load_theme(theme_path)
                except Exception as e:
                    self.logger.error(f"Failed to load theme {theme_dir}: {str(e)}")
    
    def _load_theme(self, theme_path: str) -> bool:
        """Load a built-in theme."""
        try:
            # Read metadata
            metadata_path = os.path.join(theme_path, 'metadata.json')
            with open(metadata_path, 'r') as f:
                metadata = PluginMetadata.from_dict(json.load(f))
            
            # Load theme module
            module_path = os.path.join(theme_path, 'plugin.py')
            theme_name = os.path.basename(theme_path)
            spec = importlib.util.spec_from_file_location(f"theme_{theme_name}", module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"theme_{theme_name}"] = module
            spec.loader.exec_module(module)
            
            # Initialize theme
            theme_class = getattr(module, 'Plugin')
            theme = theme_class()
            theme.metadata = metadata
            
            if theme.initialize():
                self.plugins[theme_name] = theme
                self._register_hooks(theme)
                self.logger.info(f"Successfully loaded theme: {metadata.name} v{metadata.version}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load theme {theme_path}: {str(e)}")
            return False
    
    def load_plugin(self, plugin_path: str | Path) -> bool:
        """Load a single plugin from zip file."""
        try:
            # Convert Path to string if needed
            plugin_path = str(plugin_path) if isinstance(plugin_path, Path) else plugin_path
            plugin_name = Path(plugin_path).stem
            
            with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                # Read metadata directly from zip
                with zip_ref.open('metadata.json') as f:
                    metadata = PluginMetadata.from_dict(json.loads(f.read().decode('utf-8')))

                # Read plugin code
                with zip_ref.open('plugin.py') as f:
                    plugin_code = f.read().decode('utf-8')

                # Create a module spec
                spec = importlib.util.spec_from_loader(
                    plugin_name,
                    loader=importlib.machinery.SourceFileLoader(plugin_name, plugin_path)
                )
                module = importlib.util.module_from_spec(spec)
                
                # Execute the plugin code in the module's namespace
                exec(plugin_code, module.__dict__)
                sys.modules[plugin_name] = module

                # Initialize plugin
                plugin_class = getattr(module, 'Plugin')
                plugin = plugin_class()
                plugin.metadata = metadata

                if plugin.initialize():
                    self.plugins[plugin_name] = plugin
                    self._register_hooks(plugin)
                    self.logger.info(f"Successfully loaded plugin: {metadata.name} v{metadata.version}")
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {str(e)}")
            return False
    
    def _validate_dependencies(self, metadata: PluginMetadata) -> bool:
        """Validate plugin dependencies."""
        for dependency in metadata.dependencies:
            if dependency not in self.plugins:
                self.logger.error(f"Missing dependency: {dependency}")
                return False
        return True
    
    def _register_hooks(self, plugin: PluginBase) -> None:
        """Register all hooks provided by the plugin."""
        handlers = plugin.get_hook_handlers()
        for hook_point, handler in handlers.items():
            if hook_point in self.hooks:
                self.hooks[hook_point].append(handler)
    
    def execute_hook(self, hook_point: str, **kwargs) -> List[Any]:
        """Execute all handlers for a given hook point."""
        results = []
        if hook_point in self.hooks:
            for handler in self.hooks[hook_point]:
                try:
                    result = handler(**kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error executing hook {hook_point}: {str(e)}")
        return results
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin dynamically."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
            
        try:
            # Call plugin's enable method
            if hasattr(plugin, 'enable') and plugin.enable():
                # Register hooks
                handlers = plugin._register_hooks()
                for hook_point, handler in handlers.items():
                    if hook_point in self.hooks:
                        self.hooks[hook_point].append(handler)
                return True
        except Exception as e:
            self.logger.error(f"Failed to enable plugin {plugin_name}: {str(e)}")
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin dynamically."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
            
        try:
            # Call plugin's disable method
            if hasattr(plugin, 'disable') and plugin.disable():
                # Remove hooks
                hook_points = plugin._unregister_hooks()
                for hook_point in hook_points:
                    if hook_point in self.hooks:
                        self.hooks[hook_point] = [
                            h for h in self.hooks[hook_point] 
                            if not h.__self__ == plugin
                        ]
                return True
        except Exception as e:
            self.logger.error(f"Failed to disable plugin {plugin_name}: {str(e)}")
        return False
    
    def cleanup(self) -> None:
        """Clean up all plugins."""
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                self.logger.info(f"Cleaned up plugin: {plugin_name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin {plugin_name}: {str(e)}")
        
        self.plugins.clear()
        for hook_list in self.hooks.values():
            hook_list.clear()