# core/settings.py
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class Settings:
    """Manages application and plugin settings."""
    
    def __init__(self, app_root: Path):
        self.app_root = app_root
        self.settings_dir = app_root / 'settings'
        self.settings_file = self.settings_dir / 'settings.json'
        self.plugin_settings_dir = self.settings_dir / 'plugins'
        
        # Create settings directories
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Load settings
        self.app_settings = self._load_settings(self.settings_file)
        self.plugin_settings: Dict[str, Dict] = {}
    
    def _load_settings(self, settings_file: Path) -> Dict:
        """Load settings from JSON file."""
        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading settings from {settings_file}: {e}")
            return {}
    
    def _save_settings(self, settings: Dict, settings_file: Path) -> bool:
        """Save settings to JSON file."""
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving settings to {settings_file}: {e}")
            return False
    
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting."""
        return self.app_settings.get(key, default)
    
    def set_app_setting(self, key: str, value: Any) -> bool:
        """Set application setting."""
        self.app_settings[key] = value
        return self._save_settings(self.app_settings, self.settings_file)
    
    def load_plugin_settings(self, plugin_name: str) -> Dict:
        """Load settings for a specific plugin."""
        if plugin_name in self.plugin_settings:
            return self.plugin_settings[plugin_name]
            
        settings_file = self.plugin_settings_dir / f"{plugin_name}.json"
        settings = self._load_settings(settings_file)
        self.plugin_settings[plugin_name] = settings
        return settings
    
    def save_plugin_settings(self, plugin_name: str, settings: Dict) -> bool:
        """Save settings for a specific plugin."""
        settings_file = self.plugin_settings_dir / f"{plugin_name}.json"
        self.plugin_settings[plugin_name] = settings
        return self._save_settings(settings, settings_file)
    
    def get_plugin_setting(
        self,
        plugin_name: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get specific plugin setting."""
        settings = self.load_plugin_settings(plugin_name)
        return settings.get(key, default)
    
    def set_plugin_setting(
        self,
        plugin_name: str,
        key: str,
        value: Any
    ) -> bool:
        """Set specific plugin setting."""
        settings = self.load_plugin_settings(plugin_name)
        settings[key] = value
        return self.save_plugin_settings(plugin_name, settings)
    
    def clear_plugin_settings(self, plugin_name: str) -> bool:
        """Clear all settings for a plugin."""
        try:
            settings_file = self.plugin_settings_dir / f"{plugin_name}.json"
            if settings_file.exists():
                settings_file.unlink()
            if plugin_name in self.plugin_settings:
                del self.plugin_settings[plugin_name]
            return True
        except Exception as e:
            logging.error(f"Error clearing plugin settings for {plugin_name}: {e}")
            return False
    
    def get_all_plugin_settings(self) -> Dict[str, Dict]:
        """Get settings for all plugins."""
        settings = {}
        for settings_file in self.plugin_settings_dir.glob('*.json'):
            plugin_name = settings_file.stem
            settings[plugin_name] = self._load_settings(settings_file)
        return settings
    
    def reset_to_defaults(self, plugin_name: str = None) -> bool:
        """Reset settings to defaults.
        
        Args:
            plugin_name: If provided, only reset that plugin's settings.
                       If None, reset all settings.
        """
        try:
            if plugin_name:
                # Reset specific plugin
                settings_file = self.plugin_settings_dir / f"{plugin_name}.json"
                if settings_file.exists():
                    settings_file.unlink()
                if plugin_name in self.plugin_settings:
                    del self.plugin_settings[plugin_name]
            else:
                # Reset all settings
                if self.settings_file.exists():
                    self.settings_file.unlink()
                self.app_settings = {}
                
                # Clear all plugin settings
                for settings_file in self.plugin_settings_dir.glob('*.json'):
                    settings_file.unlink()
                self.plugin_settings.clear()
            
            return True
            
        except Exception as e:
            logging.error(f"Error resetting settings: {e}")
            return False
    
    def import_settings(self, settings_file: Path) -> bool:
        """Import settings from a file."""
        try:
            imported_settings = self._load_settings(settings_file)
            if not imported_settings:
                return False
                
            # Import app settings
            if 'app_settings' in imported_settings:
                self.app_settings = imported_settings['app_settings']
                self._save_settings(self.app_settings, self.settings_file)
            
            # Import plugin settings
            if 'plugin_settings' in imported_settings:
                for plugin_name, settings in imported_settings['plugin_settings'].items():
                    self.save_plugin_settings(plugin_name, settings)
            
            return True
            
        except Exception as e:
            logging.error(f"Error importing settings: {e}")
            return False
    
    def export_settings(self, export_file: Path) -> bool:
        """Export all settings to a file."""
        try:
            export_data = {
                'app_settings': self.app_settings,
                'plugin_settings': self.get_all_plugin_settings()
            }
            
            return self._save_settings(export_data, export_file)
            
        except Exception as e:
            logging.error(f"Error exporting settings: {e}")
            return False
    
    def validate_plugin_settings(self, plugin_name: str, manifest: Dict) -> bool:
        """Validate plugin settings against manifest."""
        try:
            if 'settings' not in manifest:
                return True
                
            settings = self.load_plugin_settings(plugin_name)
            manifest_settings = manifest['settings']
            
            # Check each setting
            for key, setting_info in manifest_settings.items():
                if key in settings:
                    # Validate type
                    expected_type = setting_info.get('type')
                    if expected_type and not isinstance(settings[key], eval(expected_type)):
                        logging.warning(
                            f"Invalid type for setting {key} in plugin {plugin_name}"
                        )
                        return False
                    
                    # Validate range if applicable
                    if 'range' in setting_info:
                        min_val, max_val = setting_info['range']
                        if not min_val <= settings[key] <= max_val:
                            logging.warning(
                                f"Setting {key} in plugin {plugin_name} out of range"
                            )
                            return False
                
                else:
                    # Set default value if missing
                    if 'default' in setting_info:
                        settings[key] = setting_info['default']
            
            # Save validated settings
            self.save_plugin_settings(plugin_name, settings)
            return True
            
        except Exception as e:
            logging.error(f"Error validating plugin settings: {e}")
            return False