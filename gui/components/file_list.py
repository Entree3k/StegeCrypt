import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, List, Tuple
from ..styles.material import MaterialColors

class FileList:
    """A reusable file list component with add/remove capabilities."""
    def __init__(
        self,
        parent: ttk.Frame,
        label_text: str,
        height: int = 5,
        filetypes: Optional[List[Tuple[str, str]]] = None,
        on_change: Optional[Callable[[List[str]], None]] = None,
        plugin_manager=None
    ):
        self.plugin_manager = plugin_manager
        self.frame = ttk.Frame(parent, style='Tab.TFrame')
        self.frame.pack(fill='x', padx=20, pady=5)
        
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
        
        self.filetypes = filetypes
    
        # Let plugins customize the component
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.FILE_LIST_INIT.value,
                component=self,
                frame=self.frame,
                listbox=self.listbox,
                button_frame=self.btn_frame
            )
    
    def _add_files(self, filetypes: Optional[List[Tuple[str, str]]] = None):
        """Add files to the list with plugin hooks."""
        if filetypes:
            files = filedialog.askopenfilenames(filetypes=filetypes)
        else:
            files = filedialog.askopenfilenames()
        
        # Allow plugins to filter/modify selected files
        if self.plugin_manager:
            results = self.plugin_manager.execute_hook(
                HookPoint.FILE_SELECTION.value,
                files=files,
                component=self
            )
            if results and isinstance(results[0], list):
                files = results[0]
        
        for file in files:
            self.listbox.insert('end', file)
            
        if self.on_change:
            self.on_change(self.get())
            
    def add_custom_button(self, text: str, command: Callable, **kwargs) -> ttk.Button:
        """Allow plugins to add custom buttons."""
        btn = ttk.Button(
            self.btn_frame,
            text=text,
            command=command,
            style='Action.TButton',
            **kwargs
        )
        btn.pack(side='left', padx=5)
        return btn
    
    def _remove_selected(self):
        """Remove selected files from the list."""
        selection = self.listbox.curselection()
        for index in reversed(selection):
            self.listbox.delete(index)
    
    def get_files(self) -> List[str]:
        """Get all files in the list."""
        return list(self.listbox.get(0, 'end'))
    
    def clear(self):
        """Clear all files from the list."""
        self.listbox.delete(0, tk.END)