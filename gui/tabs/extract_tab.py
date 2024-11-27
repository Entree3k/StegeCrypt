import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileListInput, DirectoryInput
from core.steganography import extract_from_image
from core.plugin_system.plugin_base import HookPoint

class ExtractTab(BaseTab):
    """Extract data tab implementation."""
    
    def __init__(self, parent: ttk.Notebook, plugin_manager=None):
        super().__init__(parent, "Extract Hidden Data", plugin_manager)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the extract tab interface."""
        current_row = 0
        
        # Image selection
        self.image_list = FileListInput(
            self.content_frame,
            "Images with Hidden Data (Multiple Selection)",
            filetypes=[
                ("All supported images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("TIFF files", "*.tiff")
            ]
        )
        self.image_list.frame.grid(row=current_row, column=0, sticky='ew')
        current_row += 1
        
        # Output directory
        self.output_dir = DirectoryInput(
            self.content_frame,
            "Output Directory"
        )
        self.output_dir.frame.grid(row=current_row, column=0, sticky='ew', pady=5)
        current_row += 1
        
        # Action button
        btn_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        btn_frame.grid(row=current_row, column=0, sticky='ew', pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Button(
            btn_frame,
            text="Extract Data",
            command=self._start_extraction,
            style='Action.TButton'
        ).grid(row=0, column=1, sticky='e')
    
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
            
            # Execute pre-extract hook
            self.execute_hook(
                HookPoint.PRE_EXTRACT.value,
                files=self.files_to_process
            )
            
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
                    
                    # Execute post-extract hook for this file
                    self.execute_hook(
                        HookPoint.POST_EXTRACT.value,
                        image_file=image_file,
                        output_file=output_path,
                        success=True
                    )
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.execute_hook(
                        HookPoint.POST_EXTRACT.value,
                        image_file=image_file,
                        error=str(e),
                        success=False
                    )
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