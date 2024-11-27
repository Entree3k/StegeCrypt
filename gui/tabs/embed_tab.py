import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileInput, FileListInput, DirectoryInput
from core.steganography import embed_in_image
from core.plugin_system.plugin_base import HookPoint

class EmbedTab(BaseTab):
    """Embed data tab implementation."""
    
    def __init__(self, parent: ttk.Notebook, plugin_manager=None):
        super().__init__(parent, "Embed Data in Image", plugin_manager)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the embed tab interface."""
        current_row = 0
        
        # Carrier image selection
        self.carrier_input = FileInput(
            self.content_frame,
            "Carrier Image",
            filetypes=[
                ("All supported images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("TIFF files", "*.tiff")
            ]
        )
        self.carrier_input.frame.grid(row=current_row, column=0, sticky='ew')
        current_row += 1
        
        # Data file selection
        self.data_list = FileListInput(
            self.content_frame,
            "Data Files to Hide (Multiple Selection)"
        )
        self.data_list.frame.grid(row=current_row, column=0, sticky='ew', pady=5)
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
            text="Embed Data",
            command=self._start_embedding,
            style='Action.TButton'
        ).grid(row=0, column=1, sticky='e')
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.carrier_input.get():
            self.show_error("Please select a carrier image")
            return False
        
        if not self.data_list.get():
            self.show_error("Please select data files to embed")
            return False
        
        if not self.output_dir.get():
            self.show_error("Please select an output directory")
            return False
        
        return True
    
    def _start_embedding(self):
        """Start the embedding process."""
        self.files_to_process = self.data_list.get()
        self.start_processing(self._process_embedding, self._validate_inputs)
    
    def _process_embedding(self):
        """Process files for embedding."""
        try:
            total_files = len(self.files_to_process)
            success = True
            carrier = self.carrier_input.get()
            
            # Execute pre-embed hook
            self.execute_hook(
                HookPoint.PRE_EMBED.value,
                carrier_image=carrier,
                files=self.files_to_process
            )
            
            for i, data_file in enumerate(self.files_to_process):
                try:
                    file_name = os.path.basename(data_file)
                    self.update_status(f"Embedding {file_name}")
                    
                    # Always output as PNG for data integrity
                    output_path = self._generate_output_filename(
                        data_file,
                        self.output_dir.get(),
                        suffix="_stego",
                        keep_extension=False
                    ) + ".png"
                    
                    # Embed the data
                    embed_in_image(carrier, data_file, output_path)
                    
                    # Execute post-embed hook for this file
                    self.execute_hook(
                        HookPoint.POST_EMBED.value,
                        carrier_image=carrier,
                        data_file=data_file,
                        output_file=output_path,
                        success=True
                    )
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.execute_hook(
                        HookPoint.POST_EMBED.value,
                        carrier_image=carrier,
                        data_file=data_file,
                        error=str(e),
                        success=False
                    )
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