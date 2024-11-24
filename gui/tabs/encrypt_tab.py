import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileInput, FileListInput, DirectoryInput
from core.utils import generate_key_file, compute_file_hash, verify_file_integrity, secure_delete
from core.aes_crypt import encrypt_file, decrypt_file

class EncryptTab(BaseTab):
    """Encryption tab implementation."""
    
    def __init__(self, parent: ttk.Notebook):
        super().__init__(parent, "File Encryption")
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the encryption tab interface."""
        # File selection
        self.file_list = FileListInput(
            self.content_frame,
            "Input Files (Multiple Selection)"
        )
        
        # Key file section
        key_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        key_frame.pack(fill='x', pady=5)
        
        self.key_input = FileInput(
            key_frame,
            "Key File (Text/Image)"
        )
        
        # Generate key checkbox
        self.generate_key = tk.BooleanVar()
        generate_key_check = ttk.Checkbutton(
            key_frame,
            text="Generate Key",
            variable=self.generate_key,
            command=self._toggle_key_input
        )
        generate_key_check.pack(anchor='w', pady=(5, 0))
        
        # Output directory
        self.output_dir = DirectoryInput(
            self.content_frame,
            "Output Directory"
        )
        
        # Security options
        security_frame = ttk.LabelFrame(
            self.content_frame,
            text="Security Options",
            style='Tab.TFrame'
        )
        security_frame.pack(fill='x', pady=5)
        
        # Hash verification option
        self.compute_hash = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            security_frame,
            text="Compute file hash (SHA-256)",
            variable=self.compute_hash
        ).pack(anchor='w', padx=5, pady=2)
        
        # Secure deletion option
        self.secure_delete = tk.BooleanVar()
        ttk.Checkbutton(
            security_frame,
            text="Securely delete original files after encryption",
            variable=self.secure_delete
        ).pack(anchor='w', padx=5, pady=2)
        
        # Action button
        btn_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            btn_frame,
            text="Encrypt Files",
            command=self._start_encryption,
            style='Action.TButton'
        ).pack(side='right')
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before processing."""
        if not self.file_list.get():  # Changed from get_files() to get()
            self.show_error("Please select at least one file to encrypt")
            return False
            
        if not self.output_dir.get():
            self.show_error("Please select an output directory")
            return False
            
        if not self.generate_key.get() and not self.key_input.get():
            self.show_error("Please select a key file or enable 'Generate Key'")
            return False
            
        return True
    
    def _start_encryption(self):
        """Start the encryption process."""
        self.files_to_process = self.file_list.get()  # Changed from get_files() to get()
        self.start_processing(self._process_encryption, self._validate_inputs)
    
    def _process_encryption(self):
        """Process files for encryption."""
        try:
            total_files = len(self.files_to_process)
            success = True
            
            # Generate or get key file
            if self.generate_key.get():
                key_file = generate_key_file(self.output_dir.get())
                self.update_status(f"Generated key file: {key_file}")
            else:
                key_file = self.key_input.get()
            
            for i, input_file in enumerate(self.files_to_process):
                try:
                    file_name = os.path.basename(input_file)
                    
                    # Compute original hash if verification is enabled
                    original_hash = None
                    if self.compute_hash.get():
                        self.update_status(f"Computing hash for {file_name}")
                        original_hash = compute_file_hash(input_file)
                    
                    # Encrypt file
                    self.update_status(f"Encrypting {file_name}")
                    output_path = self._generate_output_filename(
                        input_file,
                        self.output_dir.get(),
                        suffix=".stegecrypt",
                        keep_extension=False
                    )
                    encrypt_file(input_file, key_file, output_path)
                    
                    # Verify encryption if enabled
                    if self.compute_hash.get():
                        self.update_status(f"Verifying encryption for {file_name}")
                        verify_filename = f"temp_verify_{os.path.basename(input_file)}"
                        temp_decrypt = os.path.join(self.output_dir.get(), verify_filename)
                        
                        try:
                            decrypt_file(output_path, key_file, temp_decrypt)
                            if not verify_file_integrity(temp_decrypt, original_hash):
                                raise ValueError("Encryption verification failed")
                        finally:
                            if os.path.exists(temp_decrypt):
                                os.remove(temp_decrypt)
                    
                    # Securely delete original if requested
                    if self.secure_delete.get():
                        self.update_status(f"Securely deleting {file_name}")
                        if not secure_delete(input_file):
                            self.show_warning(
                                f"Could not securely delete {file_name}. "
                                "The file may still be present."
                            )
                    
                    # Update progress
                    self.update_progress(i + 1, total_files)
                    
                except Exception as e:
                    self.show_error(f"Failed to process {file_name}: {str(e)}")
                    success = False
            
            if success:
                self.show_success(
                    f"Successfully processed {total_files} files!\n\n"
                    f"Output directory: {self.output_dir.get()}\n"
                    f"{'Generated key: ' + key_file if self.generate_key.get() else ''}"
                )
                self.clear_fields()
            
        except Exception as e:
            self.show_error(str(e))
    
    def _toggle_key_input(self):
        """Toggle key input based on generate key checkbox."""
        if self.generate_key.get():
            self.key_input.configure(state='disabled')
            self.key_input.clear()
        else:
            self.key_input.configure(state='normal')
    
    def clear_fields(self):
        """Clear all input fields."""
        self.file_list.clear()
        if not self.generate_key.get():
            self.key_input.clear()
        self.progress_bar.reset()