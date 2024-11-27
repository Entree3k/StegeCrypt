import os
import tkinter as tk
from tkinter import ttk
from typing import Optional

from .base_tab import BaseTab
from ..components.file_input import FileInput, FileListInput, DirectoryInput
from core.utils import generate_key_file, compute_file_hash, verify_file_integrity, secure_delete
from core.aes_crypt import encrypt_file, decrypt_file
from core.plugin_system.plugin_base import HookPoint

class EncryptTab(BaseTab):
    """Encryption tab implementation."""
    
    def __init__(self, parent: ttk.Notebook, plugin_manager=None):
        super().__init__(parent, "File Encryption", plugin_manager)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the encryption tab interface."""
        # Configure grid layout
        current_row = 0
        
        # File selection
        self.file_list = FileListInput(
            self.content_frame,
            "Input Files (Multiple Selection)"
        )
        self.file_list.frame.grid(row=current_row, column=0, sticky='ew')
        current_row += 1
        
        # Key file section
        key_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        key_frame.grid(row=current_row, column=0, sticky='ew', pady=5)
        key_frame.grid_columnconfigure(0, weight=1)
        current_row += 1
        
        self.key_input = FileInput(
            key_frame,
            "Key File (Text/Image)"
        )
        self.key_input.frame.grid(row=0, column=0, sticky='ew')
        
        # Generate key checkbox
        self.generate_key = tk.BooleanVar()
        generate_key_check = ttk.Checkbutton(
            key_frame,
            text="Generate Key",
            variable=self.generate_key,
            command=self._toggle_key_input
        )
        generate_key_check.grid(row=1, column=0, sticky='w', pady=(5, 0))
        
        # Output directory
        self.output_dir = DirectoryInput(
            self.content_frame,
            "Output Directory"
        )
        self.output_dir.frame.grid(row=current_row, column=0, sticky='ew')
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
        self.compute_hash = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            security_frame,
            text="Compute file hash (SHA-256)",
            variable=self.compute_hash
        ).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        
        # Secure deletion option
        self.secure_delete = tk.BooleanVar()
        ttk.Checkbutton(
            security_frame,
            text="Securely delete original files after encryption",
            variable=self.secure_delete
        ).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        
        # Action button
        btn_frame = ttk.Frame(self.content_frame, style='Tab.TFrame')
        btn_frame.grid(row=current_row, column=0, sticky='ew', pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)  # Push button to right
        current_row += 1
        
        ttk.Button(
            btn_frame,
            text="Encrypt Files",
            command=self._start_encryption,
            style='Action.TButton'
        ).grid(row=0, column=1, sticky='e')  # Column 1 to be on right side
    
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
            failed_files = []
            
            # Execute pre-encryption hook
            self.plugin_manager.execute_hook(
                HookPoint.PRE_ENCRYPT.value,
                files=self.files_to_process
            )
            
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
                    
                    # Execute post-encryption hook for success
                    self.plugin_manager.execute_hook(
                        HookPoint.POST_ENCRYPT.value,
                        input_file=input_file,
                        output_file=output_path,
                        success=True
                    )
                    
                except Exception as e:
                    failed_files.append((input_file, str(e)))
                    self.plugin_manager.execute_hook(
                        HookPoint.POST_ENCRYPT.value,
                        input_file=input_file,
                        error=str(e),
                        success=False
                    )
                    self.show_error(f"Failed to process {file_name}: {str(e)}")
                    success = False
                    continue
                    
                finally:
                    # Update progress regardless of success/failure
                    self.update_progress(i + 1, total_files)
            
            # Handle secure deletion after all files are processed
            if self.secure_delete.get():
                for input_file in self.files_to_process:
                    if input_file not in [f[0] for f in failed_files]:  # Only delete successfully encrypted files
                        file_name = os.path.basename(input_file)
                        self.update_status(f"Securely deleting {file_name}")
                        if secure_delete(input_file):
                            self.update_status(f"Successfully deleted {file_name}")
                        else:
                            self.show_warning(
                                f"Could not securely delete {file_name}. "
                                "The file may still be present."
                            )
            
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