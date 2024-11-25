import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, List, Tuple, Callable
from ..styles.material import MaterialColors

class FileListInput:
    """A reusable file list component with add/remove capabilities."""
    def __init__(
        self,
        parent: ttk.Frame,
        label_text: str,
        height: int = 5,
        filetypes: Optional[List[Tuple[str, str]]] = None,
        on_change: Optional[Callable[[List[str]], None]] = None
    ):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.pack(fill='x', padx=20, pady=5)
        
        self.on_change = on_change
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).pack(anchor='w')
        
        # Create listbox with scrollbar
        self.list_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.list_frame.pack(fill='both', expand=True, pady=5)
        
        self.scrollbar = ttk.Scrollbar(self.list_frame)
        self.scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(
            self.list_frame,
            height=height,
            selectmode='extended',
            yscrollcommand=self.scrollbar.set,
            bg=MaterialColors.WHITE,
            relief='solid'
        )
        self.listbox.pack(side='left', fill='both', expand=True)
        
        self.scrollbar.config(command=self.listbox.yview)
        
        # Buttons frame
        self.btn_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.btn_frame.pack(fill='x', pady=5)
        
        # Add files button
        self.add_btn = ttk.Button(
            self.btn_frame,
            text="Add Files",
            command=lambda: self._add_files(filetypes),
            style='Action.TButton'
        )
        self.add_btn.pack(side='left', padx=5)
        
        # Remove selected button
        self.remove_btn = ttk.Button(
            self.btn_frame,
            text="Remove Selected",
            command=self._remove_selected,
            style='Action.TButton'
        )
        self.remove_btn.pack(side='left')
    
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
    def __init__(
        self, 
        parent: ttk.Frame,
        label_text: str,
        filetypes: Optional[List[Tuple[str, str]]] = None,
        on_change: Optional[Callable[[str], None]] = None
    ):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.pack(fill='x', padx=20, pady=5)
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).pack(anchor='w')
        
        # Input frame
        self.input_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.input_frame.pack(fill='x', pady=5)
        
        # File path variable
        self.path_var = tk.StringVar()
        if on_change:
            self.path_var.trace_add('write', lambda *args: on_change(self.path_var.get()))
        
        # Entry field
        self.entry = ttk.Entry(
            self.input_frame,
            textvariable=self.path_var,
            style='Path.TEntry'
        )
        self.entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        # Browse button
        browse_cmd = lambda: self.path_var.set(
            filedialog.askopenfilename(filetypes=filetypes) if filetypes 
            else filedialog.askopenfilename()
        )
        
        self.browse_btn = ttk.Button(
            self.input_frame,
            text="Browse",
            command=browse_cmd,
            style='Action.TButton'
        )
        self.browse_btn.pack(side='right')
    
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
    def __init__(
        self,
        parent: ttk.Frame,
        label_text: str,
        on_change: Optional[Callable[[str], None]] = None
    ):
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.pack(fill='x', padx=20, pady=5)
        
        # Label
        ttk.Label(
            self.frame,
            text=label_text,
            style='Section.TLabel'
        ).pack(anchor='w')
        
        # Input frame
        self.input_frame = ttk.Frame(self.frame, style='Tab.TFrame')
        self.input_frame.pack(fill='x', pady=5)
        
        # Directory path variable
        self.path_var = tk.StringVar()
        if on_change:
            self.path_var.trace_add('write', lambda *args: on_change(self.path_var.get()))
        
        # Entry field
        self.entry = ttk.Entry(
            self.input_frame,
            textvariable=self.path_var,
            style='Path.TEntry'
        )
        self.entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        # Browse button
        self.browse_btn = ttk.Button(
            self.input_frame,
            text="Browse",
            command=lambda: self.path_var.set(filedialog.askdirectory()),
            style='Action.TButton'
        )
        self.browse_btn.pack(side='right')
    
    def get(self) -> str:
        """Get the current directory path."""
        return self.path_var.get()
    
    def set(self, value: str):
        """Set the directory path."""
        self.path_var.set(value)
    
    def clear(self):
        """Clear the directory path."""
        self.path_var.set('')