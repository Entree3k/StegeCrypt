import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, List, Tuple, Callable
from ..styles.material import MaterialColors

class FileListInput:
    """A reusable file list component with add/remove capabilities."""
    def __init__(self, parent, label_text, height=5, filetypes=None, on_change=None):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.grid_columnconfigure(0, weight=1)
        self.on_change = on_change
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).grid(row=0, column=0, sticky='w')
        
        # Listbox and scrollbar container
        list_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        list_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.scrollbar = ttk.Scrollbar(list_frame)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.listbox = tk.Listbox(
            list_frame,
            height=height,
            yscrollcommand=self.scrollbar.set
        )
        self.listbox.grid(row=0, column=0, sticky='nsew')
        
        self.scrollbar.config(command=self.listbox.yview)
        
        # Buttons container
        btn_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        btn_frame.grid(row=2, column=0, sticky='ew', pady=5)
        
        ttk.Button(
            btn_frame,
            text="Add Files",
            command=lambda: self._add_files(filetypes)
        ).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Remove Selected",
            command=self._remove_selected
        ).grid(row=0, column=1)
    
    def _add_files(self, filetypes: Optional[List[Tuple[str, str]]] = None):
        """Add files to the list."""
        if filetypes:
            files = filedialog.askopenfilenames(filetypes=filetypes)
        else:
            files = filedialog.askopenfilenames()
        
        for file in files:
            self.listbox.insert('end', file)
            
        if self.on_change:
            self.on_change(self.get())
    
    def _remove_selected(self):
        """Remove selected files from the list."""
        selection = self.listbox.curselection()
        for index in reversed(selection):
            self.listbox.delete(index)
            
        if self.on_change:
            self.on_change(self.get())
    
    def get(self) -> List[str]:
        """Get all files in the list."""
        return list(self.listbox.get(0, 'end'))
    
    def clear(self):
        """Clear all files from the list."""
        self.listbox.delete(0, tk.END)
        if self.on_change:
            self.on_change([])
            
    def set_state(self, state: str):
        """Set the state of the buttons."""
        self.add_btn.configure(state=state)
        self.remove_btn.configure(state=state)

class FileInput:
    """A reusable file input component with browse button."""
    def __init__(self, parent, label_text, filetypes=None, on_change=None):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.grid_columnconfigure(1, weight=1)  # Entry gets extra space
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, sticky='w')
        
        # Path variable
        self.path_var = tk.StringVar()
        if on_change:
            self.path_var.trace_add('write', lambda *args: on_change(self.path_var.get()))
        
        # Entry field
        self.entry = ttk.Entry(
            self.frame,
            textvariable=self.path_var,
            style='Path.TEntry'
        )
        self.entry.grid(row=1, column=0, columnspan=2, sticky='ew', padx=(0, 5))
        
        # Browse button
        self.browse_btn = ttk.Button(
            self.frame,
            text="Browse",
            command=lambda: self.path_var.set(
                filedialog.askopenfilename(filetypes=filetypes) if filetypes 
                else filedialog.askopenfilename()
            )
        )
        self.browse_btn.grid(row=1, column=2, sticky='e')
    
    def _browse(self):
        """Browse for file with plugin hooks."""
        if self.plugin_manager:
            results = self.plugin_manager.execute_hook(
                HookPoint.FILE_BROWSE.value,
                component=self,
                filetypes=self.filetypes
            )
            if results and isinstance(results[0], str):
                self.path_var.set(results[0])
                return

        # Default browse behavior
        path = filedialog.askopenfilename(filetypes=self.filetypes)
        if path:
            self.path_var.set(path)
    
    def get(self) -> str:
        """Get the current file path."""
        return self.path_var.get()
    
    def set(self, value: str):
        """Set the file path."""
        self.path_var.set(value)
    
    def clear(self):
        """Clear the file path."""
        self.path_var.set('')
        
    def configure(self, **kwargs):
        """Configure the input's attributes."""
        if 'state' in kwargs:
            self.entry.configure(state=kwargs['state'])
            self.browse_btn.configure(state=kwargs['state'])

class DirectoryInput:
    """A reusable directory input component with browse button."""
    def __init__(self, parent, label_text, on_change=None):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.grid_columnconfigure(1, weight=1)  # Entry gets extra space
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, sticky='w')
        
        # Path variable
        self.path_var = tk.StringVar()
        if on_change:
            self.path_var.trace_add('write', lambda *args: on_change(self.path_var.get()))
        
        # Entry field
        self.entry = ttk.Entry(
            self.frame,
            textvariable=self.path_var,
            style='Path.TEntry'
        )
        self.entry.grid(row=1, column=0, columnspan=2, sticky='ew', padx=(0, 5))
        
        # Browse button
        self.browse_btn = ttk.Button(
            self.frame,
            text="Browse",
            command=lambda: self.path_var.set(filedialog.askdirectory())
        )
        self.browse_btn.grid(row=1, column=2, sticky='e')
    
    def get(self) -> str:
        """Get the current directory path."""
        return self.path_var.get()
    
    def set(self, value: str):
        """Set the directory path."""
        self.path_var.set(value)
    
    def clear(self):
        """Clear the directory path."""
        self.path_var.set('')