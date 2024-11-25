import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileInput, FileListInput, DirectoryInput
from core.steganography import embed_in_image

class EmbedTab(BaseTab):
    """Embed data tab implementation."""
    
    def __init__(self, parent: ttk.Notebook):
        super().__init__(parent, "Embed Data in Image")
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the embed tab interface."""
        # Carrier image selection
        self.carrier_input = FileInput(
            self.content_frame,
            "Carrier Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        
        # Data file selection
        self.data_list = FileListInput(
            self.content_frame,
            "Data Files to Hide (Multiple Selection)"
        )
        
        # Output directory
        self.output_dir = DirectoryInput(
            self.content_frame,
            "Output Directory"
        )
        
        # Action button
        btn_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            btn_frame,
            text="Embed Data",
            command=self._start_embedding,
            style='Action.TButton'
        ).pack(side='right')
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.carrier_input.get():
            self.show_error("Please select a carrier image")
            return False
        
        if not self.data_list.get():  # Changed from get_files() to get()
            self.show_error("Please select data files to embed")
            return False
        
        if not self.output_dir.get():
            self.show_error("Please select an output directory")
            return False
        
        return True
    
    def _start_embedding(self):
        """Start the embedding process."""
        self.files_to_process = self.data_list.get()  # Changed from get_files() to get()
        self.start_processing(self._process_embedding, self._validate_inputs)
    
    def _process_embedding(self):
        """Process files for embedding."""
        try:
            total_files = len(self.files_to_process)
            success = True
            carrier = self.carrier_input.get()
            
            for i, data_file in enumerate(self.files_to_process):
                try:
                    file_name = os.path.basename(data_file)
                    self.update_status(f"Embedding {file_name}")
                    
                    output_path = self._generate_output_filename(
                        data_file,
                        self.output_dir.get(),
                        suffix="_stego",
                        keep_extension=False
                    ) + ".png"
                    
                    embed_in_image(carrier, data_file, output_path)
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.show_error(f"Failed to embed {file_name}: {str(e)}")
                    success = False
            
            if success:
                self.show_success("Successfully embedded all data files!")
                self.clear_fields()
            
        except Exception as e:
            self.show_error(str(e))
    
    def clear_fields(self):
        """Clear all input fields."""
        self.carrier_input.clear()
        self.data_list.clear()
        self.progress_bar.reset()