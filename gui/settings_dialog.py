import tkinter as tk
from tkinter import ttk, messagebox
from core.settings_manager import settings_manager
from core.logging_config import configure_logging

class SettingsDialog:
    """Settings dialog for StegeCrypt."""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x500")
        self.window.minsize(400, 500)
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Logging section
        logging_frame = ttk.LabelFrame(main_frame, text="Logging Settings", padding=10)
        logging_frame.pack(fill='x', pady=(0, 10))
        
        # Enable logging
        self.logging_enabled = tk.BooleanVar(value=settings_manager.get("logging", "enabled"))
        ttk.Checkbutton(
            logging_frame,
            text="Enable Logging",
            variable=self.logging_enabled,
            command=self._toggle_logging
        ).pack(anchor='w')
        
        # Log level
        ttk.Label(logging_frame, text="Log Level:").pack(anchor='w', pady=(10, 0))
        self.log_level = tk.StringVar(value=settings_manager.get("logging", "level"))
        level_combo = ttk.Combobox(
            logging_frame,
            textvariable=self.log_level,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly"
        )
        level_combo.pack(fill='x')
        
        # File logging
        self.file_logging = tk.BooleanVar(value=settings_manager.get("logging", "file_logging"))
        ttk.Checkbutton(
            logging_frame,
            text="Enable File Logging",
            variable=self.file_logging
        ).pack(anchor='w', pady=(10, 0))
        
        # Console logging
        self.console_logging = tk.BooleanVar(value=settings_manager.get("logging", "console_logging"))
        ttk.Checkbutton(
            logging_frame,
            text="Enable Console Logging",
            variable=self.console_logging
        ).pack(anchor='w')
        
        # Max log files
        ttk.Label(logging_frame, text="Maximum Log Files:").pack(anchor='w', pady=(10, 0))
        self.max_logs = tk.StringVar(value=str(settings_manager.get("logging", "max_logs")))
        ttk.Entry(logging_frame, textvariable=self.max_logs).pack(fill='x')
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="Save",
            command=self._save_settings
        ).pack(side='right', padx=(5, 0))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy
        ).pack(side='right')
    
    def _toggle_logging(self):
        """Enable/disable logging controls based on main toggle."""
        state = 'normal' if self.logging_enabled.get() else 'disabled'
        for widget in self.window.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Entry, ttk.Combobox)) and child.winfo_pathname != self.logging_enabled:
                        child.configure(state=state)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        settings_manager.set("logging", "enabled", self.logging_enabled.get())
        settings_manager.set("logging", "level", self.log_level.get())
        settings_manager.set("logging", "file_logging", self.file_logging.get())
        settings_manager.set("logging", "console_logging", self.console_logging.get())
        
        try:
            max_logs = int(self.max_logs.get())
            settings_manager.set("logging", "max_logs", max_logs)
        except ValueError:
            messagebox.showerror("Error", "Maximum log files must be a number")
            return
        
        configure_logging(settings_manager)
        self.window.destroy()