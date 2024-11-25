import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileListInput, DirectoryInput
from core.steganography import extract_from_image

class ExtractTab(BaseTab):
    """Extract data tab implementation."""
    
    def __init__(self, parent: ttk.Notebook):
        super().__init__(parent, "Extract Hidden Data")
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the extract tab interface."""
        # Image selection
        self.image_list = FileListInput(
            self.content_frame,
            "Images with Hidden Data (Multiple Selection)",
            filetypes=[("PNG files", "*.png")]
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
            text="Extract Data",
            command=self._start_extraction,
            style='Action.TButton'
        ).pack(side='right')
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.image_list.get():
            self.show_error("Please select images to extract from")
            return False
        
        if not self.output_dir.get():
            self.show_error("Please select an output directory")
            return False
        
        return True
    
    def _start_extraction(self):
        """Start the extraction process."""
        self.files_to_process = self.image_list.get()
        self.start_processing(self._process_extraction, self._validate_inputs)
    
    def _process_extraction(self):
        """Process files for extraction."""
        try:
            total_files = len(self.files_to_process)
            success = True
            
            for i, image_file in enumerate(self.files_to_process):
                try:
                    file_name = os.path.basename(image_file)
                    self.update_status(f"Extracting from {file_name}")
                    
                    output_path = self._generate_output_filename(
                        image_file,
                        self.output_dir.get(),
                        suffix="_extracted",
                        keep_extension=False
                    )
                    
                    extract_from_image(image_file, output_path)
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.show_error(f"Failed to extract from {file_name}: {str(e)}")
                    success = False
            
            if success:
                self.show_success("Successfully extracted data from all images!")
                self.clear_fields()
            
        except Exception as e:
            self.show_error(str(e))
    
    def clear_fields(self):
        """Clear all input fields."""
        self.image_list.clear()
        self.progress_bar.reset()