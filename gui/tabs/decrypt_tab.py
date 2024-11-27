import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileListInput, FileInput, DirectoryInput
from core.aes_crypt import decrypt_file
from core.plugin_system.plugin_base import HookPoint

class DecryptTab(BaseTab):
    """Decryption tab implementation."""
    
    def __init__(self, parent: ttk.Notebook, plugin_manager=None):
        super().__init__(parent, "File Decryption", plugin_manager)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the decryption tab interface."""
        current_row = 0
        
        # File selection
        self.file_list = FileListInput(
            self.content_frame,
            "Encrypted Files (Multiple Selection)",
            filetypes=[("StegeCrypt files", "*.stegecrypt")]
        )
        self.file_list.frame.grid(row=current_row, column=0, sticky='ew')
        current_row += 1
        
        # Key file selection
        self.key_input = FileInput(
            self.content_frame,
            "Key File"
        )
        self.key_input.frame.grid(row=current_row, column=0, sticky='ew', pady=5)
        current_row += 1
        
        # Output directory
        self.output_dir = DirectoryInput(
            self.content_frame,
            "Output Directory"
        )
        self.output_dir.frame.grid(row=current_row, column=0, sticky='ew', pady=5)
        current_row += 1
        
        # Security options
        security_frame = ttk.LabelFrame(
            self.content_frame,
            text="Security Options",
            style='Tab.TFrame'
        )
        security_frame.grid(row=current_row, column=0, sticky='ew', pady=5)
        security_frame.grid_columnconfigure(0, weight=1)
        current_row += 1
        
        # Hash verification option
        self.verify_hash = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            security_frame,
            text="Verify file integrity after decryption",
            variable=self.verify_hash
        ).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        
        # Action button
        btn_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        btn_frame.grid(row=current_row, column=0, sticky='ew', pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Button(
            btn_frame,
            text="Decrypt Files",
            command=self._start_decryption,
            style='Action.TButton'
        ).grid(row=0, column=1, sticky='e')
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.file_list.get():
            self.show_error("Please select files to decrypt")
            return False
        
        if not self.key_input.get():
            self.show_error("Please select a key file")
            return False
        
        if not self.output_dir.get():
            self.show_error("Please select an output directory")
            return False
        
        return True
    
    def _start_decryption(self):
        """Start the decryption process."""
        self.files_to_process = self.file_list.get()
        self.start_processing(self._process_decryption, self._validate_inputs)
    
    def _process_decryption(self):
        """Process files for decryption."""
        try:
            total_files = len(self.files_to_process)
            success = True
            
            # Execute pre-decryption hook
            self.execute_hook(
                HookPoint.PRE_DECRYPT.value,
                files=self.files_to_process,
                key_file=self.key_input.get()
            )
            
            for i, input_file in enumerate(self.files_to_process):
                try:
                    file_name = os.path.basename(input_file)
                    self.update_status(f"Decrypting {file_name}")
                    
                    # Generate output path and decrypt
                    output_path = self._generate_output_filename(
                        input_file,
                        self.output_dir.get(),
                        keep_extension=True
                    )
                    
                    decrypt_file(
                        input_file,
                        self.key_input.get(),
                        output_path
                    )
                    
                    # Execute post-decryption hook for this file
                    self.execute_hook(
                        HookPoint.POST_DECRYPT.value,
                        input_file=input_file,
                        output_file=output_path,
                        success=True
                    )
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.execute_hook(
                        HookPoint.POST_DECRYPT.value,
                        input_file=input_file,
                        error=str(e),
                        success=False
                    )
                    self.show_error(f"Failed to decrypt {file_name}: {str(e)}")
                    success = False
                    continue
            
            if success:
                self.show_success(
                    f"Successfully decrypted {total_files} files!\n\n"
                    f"Output directory: {self.output_dir.get()}"
                )
                self.clear_fields()
            
        except Exception as e:
            self.show_error(str(e))
    
    def clear_fields(self):
        """Clear all input fields."""
        self.file_list.clear()
        self.key_input.clear()
        self.progress_bar.reset()