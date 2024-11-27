import json
import os
from pathlib import Path

class SettingsManager:
    """Manages application settings with persistence."""
    
    DEFAULT_SETTINGS = {
        "logging": {
            "enabled": True,
            "level": "INFO",
            "max_logs": 2,
            "file_logging": True,
            "console_logging": True
        }
    }
    
    def __init__(self):
        self.settings_file = Path(__file__).parent / "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file or create with defaults."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults to ensure all settings exist
                    return self._merge_with_defaults(settings)
            except Exception:
                pass
        return self.DEFAULT_SETTINGS.copy()
    
    def _merge_with_defaults(self, settings: dict) -> dict:
        """Ensure all default settings exist in loaded settings."""
        merged = self.DEFAULT_SETTINGS.copy()
        for category, values in settings.items():
            if category in merged:
                merged[category].update(values)
        return merged
    
    def save(self):
        """Save current settings to file."""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, category: str, key: str) -> any:
        """Get a setting value."""
        return self.settings.get(category, {}).get(key)
    
    def set(self, category: str, key: str, value: any):
        """Set a setting value."""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save()

# Global settings manager instance
settings_manager = None

def init_settings_manager():
    """Initialize the global settings manager."""
    global settings_manager
    settings_manager = SettingsManager()
    return settings_manager