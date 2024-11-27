import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

class PluginManagerGUI:
    """GUI for managing plugins."""
    
    def __init__(self, parent, plugin_manager):
        self.window = tk.Toplevel(parent)
        self.window.title("Plugin Manager")
        self.window.geometry("800x600")
        self.window.minsize(800, 600)
        self.plugin_manager = plugin_manager
        
        # Configure window style
        self.window.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Header
        ttk.Label(
            main_frame,
            text="Plugin Manager",
            font=('Helvetica', 16, 'bold'),
            foreground='#2196F3'
        ).pack(anchor='w', pady=(0, 15))
        
        # Plugins list frame
        list_frame = ttk.LabelFrame(main_frame, text="Installed Plugins")
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create treeview for plugins
        self.tree = ttk.Treeview(
            list_frame,
            columns=('Name', 'Status', 'Version', 'Author'),
            show='headings'
        )
        
        # Configure treeview columns
        self.tree.heading('Name', text='Plugin Name')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Version', text='Version')
        self.tree.heading('Author', text='Author')
        
        self.tree.column('Name', width=200)
        self.tree.column('Status', width=100)
        self.tree.column('Version', width=100)
        self.tree.column('Author', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Plugin details frame
        details_frame = ttk.LabelFrame(main_frame, text="Plugin Details")
        details_frame.pack(fill='x', pady=(0, 10))
        
        # Info frame for plugin information
        self.info_frame = ttk.Frame(details_frame)
        self.info_frame.pack(fill='x', padx=10, pady=5)
        
        # Config frame for plugin configuration
        self.config_frame = ttk.LabelFrame(details_frame, text="Plugin Configuration")
        self.config_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_plugin_select)
        
        # Load plugins
        self.load_plugins()
        
        # Add a status bar frame at the bottom
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill='x', pady=(5, 0))
        
        # Add help text
        ttk.Label(
            self.status_frame,
            text="Select a plugin to view its details and configuration options",
            font=('Helvetica', 9, 'italic')
        ).pack(side='left')
    
    def _load_plugin_states(self):
        """Load plugin states from file."""
        config_path = Path("plugins/plugin_states.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        # Default to enabled if no state file exists
        return {}

    def _save_plugin_states(self):
        """Save plugin states to file."""
        config_path = Path("plugins/plugin_states.json")
        states = self._load_plugin_states()  # Load existing states
        
        # Update states based on current plugin status
        for plugin_name in states:
            states[plugin_name]['enabled'] = plugin_name in self.plugin_manager.plugins
                
        try:
            with open(config_path, 'w') as f:
                json.dump(states, f, indent=2)
        except Exception as e:
            print(f"Failed to save plugin states: {str(e)}")
    
    def on_plugin_select(self, event):
        """Handle plugin selection in treeview."""
        selection = self.tree.selection()
        if not selection:
            return
            
        plugin_name = selection[0]
        plugin = self.plugin_manager.plugins.get(plugin_name)
        stored_metadata = self._load_plugin_metadata()
        
        # Clear existing frames
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        
        # Get metadata either from active plugin or stored data
        metadata = None
        if plugin and hasattr(plugin, 'metadata'):
            metadata = plugin.metadata
        else:
            metadata_dict = stored_metadata.get(plugin_name, {})
            # Create a simple metadata-like object
            class SimpleMetadata:
                pass
            metadata = SimpleMetadata()
            metadata.name = metadata_dict.get('name', plugin_name)
            metadata.version = metadata_dict.get('version', 'N/A')
            metadata.author = metadata_dict.get('author', 'N/A')
            metadata.description = metadata_dict.get('description', '')
        
        # Show plugin info
        ttk.Label(
            self.info_frame,
            text=f"Plugin: {metadata.name}",
            font=('Helvetica', 10, 'bold')
        ).pack(side='left', padx=(0, 10))
        
        # Get plugin status
        states = self._load_plugin_states()
        is_enabled = states.get(plugin_name, {}).get('enabled', True)
        
        # Add enable/disable button
        ttk.Button(
            self.info_frame,
            text="Disable" if is_enabled else "Enable",
            command=lambda: self.toggle_plugin(plugin_name, not is_enabled)
        ).pack(side='left')
        
        # Show description
        if metadata.description:
            ttk.Label(
                self.info_frame,
                text=metadata.description,
                wraplength=600,
                justify='left'
            ).pack(fill='x', pady=(10, 0))
        
        # Show configuration if plugin is enabled and supports it
        if plugin and is_enabled:
            if hasattr(plugin, 'create_config_ui'):
                plugin.create_config_ui(self.config_frame)
            else:
                ttk.Label(
                    self.config_frame,
                    text="This plugin has no configurable options.",
                    font=('Helvetica', 9, 'italic')
                ).pack(pady=10)
        else:
            ttk.Label(
                self.config_frame,
                text="Enable the plugin to access its configuration options.",
                font=('Helvetica', 9, 'italic')
            ).pack(pady=10)
    
    def toggle_plugin(self, plugin_name: str, enable: bool):
        """Toggle plugin enabled/disabled state."""
        if enable:
            self.enable_plugin(plugin_name)
        else:
            self.disable_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name):
        """Enable a plugin."""
        try:
            # Try to load the plugin ZIP file
            plugin_path = Path(f"plugins/{plugin_name}.zip")
            if not plugin_path.exists():
                self.show_status_message(f"Plugin file not found: {plugin_name}.zip", error=True)
                return

            # Get current states
            states = self._load_plugin_states()
            
            # Try to enable the plugin
            if self.plugin_manager.load_plugin(plugin_path):
                # Update state file
                if plugin_name not in states:
                    states[plugin_name] = {}
                states[plugin_name]['enabled'] = True
                
                # Save updated states
                with open(Path("plugins/plugin_states.json"), 'w') as f:
                    json.dump(states, f, indent=2)
                
                # Save metadata from newly enabled plugin
                plugin = self.plugin_manager.plugins.get(plugin_name)
                if plugin and hasattr(plugin, 'metadata'):
                    self._save_plugin_metadata(plugin_name, {
                        'name': plugin.metadata.name,
                        'version': plugin.metadata.version,
                        'author': plugin.metadata.author,
                        'description': plugin.metadata.description
                    })
                
                # Refresh UI
                self.load_plugins()
                
                # Re-select the plugin to update its details
                self.tree.selection_set(plugin_name)
                self.on_plugin_select(None)
                
                self.show_status_message("Plugin enabled successfully")
            else:
                self.show_status_message("Failed to enable plugin", error=True)
        except Exception as e:
            self.show_status_message(f"Failed to enable plugin: {str(e)}", error=True)

    def disable_plugin(self, plugin_name):
        """Disable a plugin."""
        try:
            # Get current states
            states = self._load_plugin_states()
            
            # Disable the plugin
            plugin = self.plugin_manager.plugins.get(plugin_name)
            if plugin and hasattr(plugin, 'cleanup'):
                plugin.cleanup()
            
            # Remove from active plugins
            self.plugin_manager.plugins.pop(plugin_name, None)
            
            # Update state file
            if plugin_name not in states:
                states[plugin_name] = {}
            states[plugin_name]['enabled'] = False
            
            # Save updated states
            with open(Path("plugins/plugin_states.json"), 'w') as f:
                json.dump(states, f, indent=2)
            
            # Refresh UI
            self.load_plugins()
            
            # Re-select the plugin to update its details
            self.tree.selection_set(plugin_name)
            self.on_plugin_select(None)
            
            self.show_status_message("Plugin disabled successfully")
        except Exception as e:
            self.show_status_message(f"Failed to disable plugin: {str(e)}", error=True)
            
    def _load_plugin_metadata(self):
        """Load plugin metadata from stored file."""
        metadata_path = Path("plugins/plugin_metadata.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_plugin_metadata(self, plugin_name: str, metadata: dict):
        """Save plugin metadata to file."""
        metadata_path = Path("plugins/plugin_metadata.json")
        current_metadata = self._load_plugin_metadata()
        
        # Update metadata for this plugin
        current_metadata[plugin_name] = metadata
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(current_metadata, f, indent=2)
        except Exception as e:
            print(f"Failed to save plugin metadata: {str(e)}")

    def load_plugins(self):
        """Load installed plugins into the treeview."""
        self.tree.delete(*self.tree.get_children())
        
        # Load plugin states and metadata
        states = self._load_plugin_states()
        stored_metadata = self._load_plugin_metadata()
        
        # Load all plugins from the plugins directory
        plugins_dir = Path("plugins")
        if not plugins_dir.exists():
            return
            
        for plugin_file in plugins_dir.glob("*.zip"):
            plugin_name = plugin_file.stem
            is_enabled = states.get(plugin_name, {}).get('enabled', True)
            
            # Get metadata from active plugin or stored metadata
            plugin = self.plugin_manager.plugins.get(plugin_name)
            if plugin and hasattr(plugin, 'metadata'):
                # Plugin is active, save its metadata for future use
                metadata = {
                    'name': plugin.metadata.name,
                    'version': plugin.metadata.version,
                    'author': plugin.metadata.author,
                    'description': plugin.metadata.description
                }
                self._save_plugin_metadata(plugin_name, metadata)
            else:
                # Plugin is disabled, use stored metadata
                metadata = stored_metadata.get(plugin_name, {
                    'name': plugin_name,
                    'version': 'N/A',
                    'author': 'N/A',
                    'description': ''
                })
            
            # Insert into treeview with consistent metadata
            self.tree.insert(
                '',
                'end',
                iid=plugin_name,
                values=(
                    metadata['name'],
                    'Enabled' if is_enabled else 'Disabled',
                    metadata['version'],
                    metadata['author']
                )
            )
                
    def show_status_message(self, message: str, error: bool = False):
        """Show a status message in the UI."""
        # Clear any existing status message
        for widget in self.info_frame.winfo_children():
            if hasattr(widget, 'status_label'):
                widget.destroy()
        
        # Create status label with appropriate style
        label = ttk.Label(
            self.info_frame,
            text=message,
            foreground='red' if error else 'green',
            font=('Helvetica', 9)
        )
        label.status_label = True  # Mark as status label
        label.pack(side='right', padx=5)
        
        # Schedule label to be removed after 3 seconds
        self.window.after(3000, lambda: label.destroy() if label.winfo_exists() else None)