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
        filetypes: Optional[List[Tuple[str, str]]] = None
    ):
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
    
    def _add_files(self, filetypes: Optional[List[Tuple[str, str]]] = None):
        """Add files to the list."""
        if filetypes:
            files = filedialog.askopenfilenames(filetypes=filetypes)
        else:
            files = filedialog.askopenfilenames()
        
        for file in files:
            self.listbox.insert('end', file)
    
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