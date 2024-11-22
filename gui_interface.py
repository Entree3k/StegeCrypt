import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.aes_crypt import encrypt_file, decrypt_file
from core.steganography import embed_in_image, extract_from_image
from core.utils import (
    validate_file, 
    log_progress, 
    generate_key_file, 
    compute_file_hash,
    verify_file_integrity,
    secure_delete
)
from gui_utils import MaterialStyle, ProgressManager
import threading
import os
from datetime import datetime
import time
from typing import List, Tuple

class StegeCryptGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("StegeCrypt")
        self.window.geometry("800x800")
        self.window.minsize(800, 800)
        self.window.configure(bg=MaterialStyle.BG_COLOR)
        
        # Configure styles
        self.setup_styles()
        
        # Main container with adjusted padding
        self.main_container = ttk.Frame(self.window, style='Main.TFrame')
        self.main_container.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Header
        self.setup_header()
        
        # Notebook for tabs
        self.setup_notebook()
        
        # Status bar
        self.setup_status_bar()
        
        # Initialize file lists
        self.files_to_process = []
        self.current_file_index = 0
        self.processing_start_time = 0

    def setup_notebook(self):
        """Setup the main notebook with tabs."""
        self.notebook = ttk.Notebook(self.main_container)
        
        # Create simple frames for each tab
        self.encrypt_frame = ttk.Frame(self.notebook, style='Tab.TFrame')
        self.decrypt_frame = ttk.Frame(self.notebook, style='Tab.TFrame')
        self.embed_frame = ttk.Frame(self.notebook, style='Tab.TFrame')
        self.extract_frame = ttk.Frame(self.notebook, style='Tab.TFrame')
        
        # Add frames to notebook
        self.notebook.add(self.encrypt_frame, text="  Encrypt  ")
        self.notebook.add(self.decrypt_frame, text="  Decrypt  ")
        self.notebook.add(self.embed_frame, text="  Embed Data  ")
        self.notebook.add(self.extract_frame, text="  Extract Data  ")
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Setup tabs
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_embed_tab()
        self.setup_extract_tab()

    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.configure('Main.TFrame', background=MaterialStyle.BG_COLOR)
        style.configure('Header.TFrame', background=MaterialStyle.BG_COLOR)
        style.configure('Tab.TFrame', background=MaterialStyle.WHITE)
        
        # Labels
        style.configure('Header.TLabel',
                       font=('Helvetica', 24, 'bold'),
                       background=MaterialStyle.BG_COLOR,
                       foreground=MaterialStyle.PRIMARY_COLOR)
        
        style.configure('SubHeader.TLabel',
                       font=('Helvetica', 12),
                       background=MaterialStyle.BG_COLOR,
                       foreground=MaterialStyle.SECONDARY_COLOR)
        
        style.configure('Section.TLabel',
                       font=('Helvetica', 11),
                       background=MaterialStyle.WHITE,
                       padding=(0, 10, 0, 5))
                       
        style.configure('Status.TLabel',
                       font=('Helvetica', 10),
                       background=MaterialStyle.BG_COLOR)
                       
        style.configure('Progress.TLabel',
                       font=('Helvetica', 10),
                       background=MaterialStyle.WHITE)

        # Buttons
        style.configure('Action.TButton',
                       font=('Helvetica', 10),
                       padding=(15, 8))  # Slightly reduced padding
        
        # Frames
        style.configure('Status.TFrame',
                       background=MaterialStyle.BG_COLOR)

    def setup_header(self):
        """Setup the application header."""
        header = ttk.Frame(self.main_container, style='Header.TFrame')
        header.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(
            header,
            text="StegeCrypt",
            style='Header.TLabel'
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header,
            text="Secure File Encryption & Steganography",
            style='SubHeader.TLabel'
        )
        subtitle_label.pack()

    def setup_status_bar(self):
        """Setup the status bar with progress information."""
        status_frame = ttk.Frame(self.window, style='Status.TFrame')
        status_frame.pack(fill='x', side='bottom', padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(
            status_frame, 
            text="Ready", 
            style='Status.TLabel'
        )
        self.status_label.pack(side='left', padx=5)
        
        # Time remaining label
        self.time_label = ttk.Label(
            status_frame, 
            text="", 
            style='Status.TLabel'
        )
        self.time_label.pack(side='right', padx=5)
        
        # Detailed progress label
        self.progress_detail = ttk.Label(
            status_frame,
            text="",
            style='Status.TLabel'
        )
        self.progress_detail.pack(side='right', padx=5)

    def setup_tooltips(self):
        """Setup tooltips for various UI elements."""
        self.tooltips = {}
        
        def create_tooltip(widget, text):
            tooltip = ToolTip(widget, text)
            self.tooltips[widget] = tooltip
        
        # Add tooltips to various elements
        create_tooltip(
            self.encrypt_frame, 
            "Encrypt files using AES-256 encryption.\nSupports multiple file selection."
        )
        create_tooltip(
            self.decrypt_frame,
            "Decrypt previously encrypted files.\nRequires the original key file."
        )
        create_tooltip(
            self.embed_frame,
            "Hide encrypted data within an image using steganography."
        )
        create_tooltip(
            self.extract_frame,
            "Extract hidden data from an image that contains embedded information."
        )

    def setup_encrypt_tab(self):
        """Setup the encryption tab with multiple file selection."""
        ttk.Label(
            self.encrypt_frame,
            text="File Encryption",
            font=('Helvetica', 14, 'bold'),
            background=MaterialStyle.WHITE,
            foreground=MaterialStyle.PRIMARY_COLOR
        ).pack(pady=10, padx=20, anchor='w')

        # Multiple file selection listbox
        self.input_files_list = self.create_file_list(
            self.encrypt_frame,
            "Input Files (Multiple Selection)"
        )
        
        # Key file section with generate key option
        key_frame = ttk.Frame(self.encrypt_frame, style='Tab.TFrame')
        key_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(
            key_frame,
            text="Key File (Text/Image)",
            style='Section.TLabel'
        ).pack(anchor='w')
        
        key_input_frame = ttk.Frame(key_frame, style='Tab.TFrame')
        key_input_frame.pack(fill='x', pady=5)
        
        self.key_path = tk.StringVar()
        self.key_entry = ttk.Entry(
            key_input_frame,
            textvariable=self.key_path,
            style='Path.TEntry'
        )
        self.key_entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        browse_btn = ttk.Button(
            key_input_frame,
            text="Browse",
            command=lambda: self.key_path.set(filedialog.askopenfilename()),
            style='Action.TButton'
        )
        browse_btn.pack(side='right')
        
        # Generate key checkbox
        self.generate_key = tk.BooleanVar()
        generate_key_check = ttk.Checkbutton(
            key_frame,
            text="Generate Key",
            variable=self.generate_key,
            command=self._toggle_key_entry
        )
        generate_key_check.pack(anchor='w', pady=(5, 0))
        
        # Output directory
        self.output_dir = self.create_directory_input(
            self.encrypt_frame,
            "Output Directory"
        )

        # Security options frame
        security_frame = ttk.LabelFrame(
            self.encrypt_frame,
            text="Security Options",
            style='Tab.TFrame'
        )
        security_frame.pack(fill='x', padx=20, pady=5)
    
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
        
        # Progress bar with percentage
        self.progress_frame = ttk.Frame(self.encrypt_frame, style='Tab.TFrame')
        self.progress_frame.pack(fill='x', padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.encrypt_progress = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            variable=self.progress_var
        )
        self.encrypt_progress.pack(fill='x', side='left', expand=True)
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="0%",
            style='Progress.TLabel'
        )
        self.progress_label.pack(side='right', padx=5)
        
        # Action buttons
        btn_frame = ttk.Frame(self.encrypt_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Encrypt Files",
            command=self._encrypt_files,
            style='Action.TButton'
        ).pack(side='right')

    def _encrypt_files(self):
        """Handle encryption of multiple files."""
        # Get list of files to process
        self.files_to_process = list(self.input_files_list.get(0, 'end'))
        
        if not self.files_to_process:
            messagebox.showerror("Error", "Please select at least one file to encrypt")
            return
            
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
            
        if not self.generate_key.get() and not self.key_path.get():
            messagebox.showerror("Error", "Please select a key file or enable 'Generate Key'")
            return
        
        # Reset progress
        self.current_file_index = 0
        self.progress_var.set(0)
        self.processing_start_time = time.time()
        
        # Start processing thread
        threading.Thread(target=self._process_files).start()

    def _process_files(self):
        """Process multiple files for encryption."""
        try:
            total_files = len(self.files_to_process)
            success = True
        
            # Generate or get key file
            if self.generate_key.get():
                key_file = generate_key_file(self.output_dir.get())
                self.status_label.config(text=f"Generated key file: {key_file}")
            else:
                key_file = self.key_path.get()
        
            for i, input_file in enumerate(self.files_to_process):
                self.current_file_index = i
                file_name = os.path.basename(input_file)
                
                try:
                    # Compute original hash if verification is enabled
                    original_hash = None
                    if self.compute_hash.get():
                        self.status_label.config(text=f"Computing hash for {file_name}")
                        original_hash = compute_file_hash(input_file)
                
                    # Generate output path and encrypt
                    self.status_label.config(text=f"Encrypting {file_name}")
                    output_path = self._generate_output_filename(
                        input_file,
                        self.output_dir.get()
                    )
                    encrypt_file(input_file, key_file, output_path)
                
                    # Verify the encryption if enabled
                    if self.compute_hash.get():
                        self.status_label.config(text=f"Verifying encryption for {file_name}")
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
                        try:
                            self.status_label.config(text=f"Securely deleting {file_name}")
                            # Make sure any file handles are closed
                            import gc
                            gc.collect()  # Force garbage collection to close any lingering handles
            
                            if not secure_delete(input_file):
                                raise Exception("Failed to securely delete file")
                
                        except Exception as e:
                            messagebox.showwarning(
                                "Warning",
                                f"Could not securely delete {file_name}. The file may still be present.\n"
                                f"Error: {str(e)}"
                            )
                
                    # Update progress
                    progress = ((i + 1) / total_files) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"{progress:.1f}%")
                    self._update_time_remaining(i + 1, total_files)
                
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to process {file_name}: {str(e)}")
                    success = False
        
            if success:
                messagebox.showinfo(
                    "Success",
                    f"Successfully processed {total_files} files!\n\n"
                    f"Output directory: {self.output_dir.get()}\n"
                    f"{'Generated key: ' + key_file if self.generate_key.get() else ''}"
                )
                # Clear fields after successful operation
                self.clear_encrypt_fields()
        
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.status_label.config(text="Ready")
            self.time_label.config(text="")
            self.progress_detail.config(text="")

    def _process_decryption(self):
        """Process multiple files for decryption."""
        try:
            total_files = len(self.files_to_process)
            success = True
            
            for i, input_file in enumerate(self.files_to_process):
                self.current_file_index = i
                
                # Update status
                file_name = os.path.basename(input_file)
                self.status_label.config(
                    text=f"Decrypting {file_name} ({i + 1}/{total_files})"
                )
                
                try:
                    # Generate output path
                    output_base = self._generate_output_filename(
                        input_file,
                        self.decrypt_output_dir.get(),
                        is_encrypted=False
                    )
                    
                    # Decrypt file
                    decrypt_file(
                        input_file,
                        self.decrypt_key_path.get(),
                        output_base
                    )
                    
                    # Update progress
                    progress = ((i + 1) / total_files) * 100
                    self.decrypt_progress_var.set(progress)
                except Exception as e:
                    messagebox.showerror("Decryption Error", f"Failed to decrypt {file_name}: {str(e)}")
                    success = False
                    continue
                
                # Update time remaining
                self._update_time_remaining(i + 1, total_files)
            
            if success:
                messagebox.showinfo(
                    "Success",
                    f"Successfully decrypted {total_files} files!\n\n"
                    f"Output directory: {self.decrypt_output_dir.get()}"
                )
                # Clear fields after successful operation
                self.clear_decrypt_fields()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.status_label.config(text="Ready")
            self.time_label.config(text="")
            self.progress_detail.config(text="")

    def _embed_data(self):
        """Handle embedding data in images."""
        carrier = self.carrier_path.get()
        if not carrier:
            messagebox.showerror("Error", "Please select a carrier image")
            return
        
        data_files = list(self.stego_data_list.get(0, 'end'))
        if not data_files:
            messagebox.showerror("Error", "Please select data files to embed")
            return
        
        if not self.stego_output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        success = True
        total_files = len(data_files)
        self.embed_progress_var.set(0)
        self.processing_start_time = time.time()

        # Process each file
        for i, data_file in enumerate(data_files):
            try:
                # Update status
                file_name = os.path.basename(data_file)
                self.status_label.config(
                    text=f"Embedding {file_name} ({i + 1}/{total_files})"
                )

                output_path = os.path.join(
                    self.stego_output_dir.get(),
                    f"stego_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                embed_in_image(carrier, data_file, output_path)
                
                # Update progress
                progress = ((i + 1) / total_files) * 100
                self.embed_progress_var.set(progress)
                
                # Update time remaining
                self._update_time_remaining(i + 1, total_files)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to embed {os.path.basename(data_file)}: {str(e)}")
                success = False

        if success:
            messagebox.showinfo(
                "Success",
                "Successfully embedded all data files!"
            )
            # Clear fields after successful operation
            self.clear_embed_fields()

        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")

    def _extract_data(self):
        """Handle extracting data from images."""
        images = list(self.extract_images_list.get(0, 'end'))
        if not images:
            messagebox.showerror("Error", "Please select images to extract from")
            return
        
        if not self.extract_output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        success = True
        total_images = len(images)
        self.extract_progress_var.set(0)
        self.processing_start_time = time.time()

        # Process each image
        for i, image in enumerate(images):
            try:
                # Update status
                file_name = os.path.basename(image)
                self.status_label.config(
                    text=f"Extracting from {file_name} ({i + 1}/{total_images})"
                )

                output_base = os.path.join(
                    self.extract_output_dir.get(),
                    f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                extract_from_image(image, output_base)
                
                # Update progress
                progress = ((i + 1) / total_images) * 100
                self.extract_progress_var.set(progress)
                
                # Update time remaining
                self._update_time_remaining(i + 1, total_images)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract from {os.path.basename(image)}: {str(e)}")
                success = False

        if success:
            messagebox.showinfo(
                "Success",
                "Successfully extracted data from all images!"
            )
            # Clear fields after successful operation
            self.clear_extract_fields()

        self.status_label.config(text="Ready")
        self.time_label.config(text="")
        self.progress_detail.config(text="")

    def _update_time_remaining(self, completed_files: int, total_files: int):
        """Update the time remaining estimate."""
        if completed_files == 0:
            return
            
        elapsed_time = time.time() - self.processing_start_time
        avg_time_per_file = elapsed_time / completed_files
        remaining_files = total_files - completed_files
        estimated_remaining = avg_time_per_file * remaining_files
        
        # Format time remaining
        if estimated_remaining < 60:
            time_text = f"{estimated_remaining:.0f} seconds remaining"
        else:
            minutes = estimated_remaining // 60
            seconds = estimated_remaining % 60
            time_text = f"{minutes:.0f}m {seconds:.0f}s remaining"
        
        self.time_label.config(text=time_text)
        self.progress_detail.config(
            text=f"File {completed_files}/{total_files}"
        )

    def _toggle_key_entry(self):
        """Toggle key entry based on generate key checkbox."""
        if self.generate_key.get():
            self.key_entry.configure(state='disabled')
            self.key_path.set('')
        else:
            self.key_entry.configure(state='normal')

    def _generate_output_filename(self, input_path: str, output_dir: str, is_encrypted: bool = True) -> str:
        """Generate output filename with timestamp."""
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if is_encrypted:
            return os.path.join(output_dir, f"{name}_{timestamp}.stegecrypt")
        return os.path.join(output_dir, f"{name}_{timestamp}{ext}")
        
    def create_file_list(self, parent, label_text, filetypes=None):
        """Create a listbox for multiple file selection."""
        frame = ttk.Frame(parent, style='Tab.TFrame')
        frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(frame, text=label_text, style='Section.TLabel').pack(anchor='w')
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(frame, style='Tab.TFrame')
        list_frame.pack(fill='both', expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(
            list_frame,
            height=5,
            selectmode='extended',
            yscrollcommand=scrollbar.set,
            bg=MaterialStyle.WHITE,
            relief='solid'
        )
        listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Buttons frame
        btn_frame = ttk.Frame(frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', pady=5)
        
        def add_files():
            if filetypes:
                files = filedialog.askopenfilenames(filetypes=filetypes)
            else:
                files = filedialog.askopenfilenames()
            for file in files:
                listbox.insert('end', file)
        
        def remove_selected():
            selection = listbox.curselection()
            for index in reversed(selection):
                listbox.delete(index)
        
        ttk.Button(
            btn_frame,
            text="Add Files",
            command=add_files,
            style='Action.TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="Remove Selected",
            command=remove_selected,
            style='Action.TButton'
        ).pack(side='left')
        
        return listbox

    def create_directory_input(self, parent, label_text):
        """Create a directory input field with browse button."""
        frame = ttk.Frame(parent, style='Tab.TFrame')
        frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(frame, text=label_text, style='Section.TLabel').pack(anchor='w')
        
        input_frame = ttk.Frame(frame, style='Tab.TFrame')
        input_frame.pack(fill='x', pady=5)
        
        var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=var, style='Path.TEntry')
        entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        browse_btn = ttk.Button(
            input_frame,
            text="Browse",
            command=lambda: var.set(filedialog.askdirectory()),
            style='Action.TButton'
        )
        browse_btn.pack(side='right')
        
        return var

    def create_file_input(self, parent, label_text, filetypes=None):
        """Create a single file input field with browse button."""
        frame = ttk.Frame(parent, style='Tab.TFrame')
        frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(frame, text=label_text, style='Section.TLabel').pack(anchor='w')
        
        input_frame = ttk.Frame(frame, style='Tab.TFrame')
        input_frame.pack(fill='x', pady=5)
        
        var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=var, style='Path.TEntry')
        entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        if filetypes:
            browse_cmd = lambda: var.set(filedialog.askopenfilename(filetypes=filetypes))
        else:
            browse_cmd = lambda: var.set(filedialog.askopenfilename())
            
        browse_btn = ttk.Button(
            input_frame,
            text="Browse",
            command=browse_cmd,
            style='Action.TButton'
        )
        browse_btn.pack(side='right')
        
        return var
        
    def setup_decrypt_tab(self):
        """Setup the decryption tab with multiple file selection."""
        ttk.Label(
            self.decrypt_frame,
            text="File Decryption",
            font=('Helvetica', 14, 'bold'),
            background=MaterialStyle.WHITE,
            foreground=MaterialStyle.PRIMARY_COLOR
        ).pack(pady=10, padx=20, anchor='w')

        # Multiple file selection listbox
        self.decrypt_files_list = self.create_file_list(
            self.decrypt_frame,
            "Encrypted Files (Multiple Selection)",
            filetypes=[("StegeCrypt files", "*.stegecrypt")]
        )
        
        # Key file selection
        key_frame = ttk.Frame(self.decrypt_frame, style='Tab.TFrame')
        key_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(
            key_frame,
            text="Key File",
            style='Section.TLabel'
        ).pack(anchor='w')
        
        key_input_frame = ttk.Frame(key_frame, style='Tab.TFrame')
        key_input_frame.pack(fill='x', pady=5)
        
        self.decrypt_key_path = tk.StringVar()
        key_entry = ttk.Entry(
            key_input_frame,
            textvariable=self.decrypt_key_path,
            style='Path.TEntry'
        )
        key_entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        browse_btn = ttk.Button(
            key_input_frame,
            text="Browse",
            command=lambda: self.decrypt_key_path.set(filedialog.askopenfilename()),
            style='Action.TButton'
        )
        browse_btn.pack(side='right')

        # Output directory
        self.decrypt_output_dir = self.create_directory_input(
            self.decrypt_frame,
            "Output Directory"
        )
        
        # Action buttons and progress
        btn_frame = ttk.Frame(self.decrypt_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        self.decrypt_progress_var = tk.DoubleVar()
        self.decrypt_progress = ttk.Progressbar(
            self.decrypt_frame,
            mode='determinate',
            variable=self.decrypt_progress_var
        )
        self.decrypt_progress.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Decrypt Files",
            command=self._decrypt_files,
            style='Action.TButton'
        ).pack(side='right')
        
        # Add security options frame
        security_frame = ttk.LabelFrame(
            self.decrypt_frame,
            text="Security Options",
            style='Tab.TFrame'
        )
        security_frame.pack(fill='x', padx=20, pady=5)
    
        # Hash verification option
        self.verify_hash = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            security_frame,
            text="Verify file integrity after decryption",
            variable=self.verify_hash
        ).pack(anchor='w', padx=5, pady=2)

    def setup_embed_tab(self):
        """Setup the embed tab."""
        ttk.Label(
            self.embed_frame,
            text="Embed Data in Image",
            font=('Helvetica', 14, 'bold'),
            background=MaterialStyle.WHITE,
            foreground=MaterialStyle.PRIMARY_COLOR
        ).pack(pady=10, padx=20, anchor='w')

        # Carrier image selection
        self.carrier_path = self.create_file_input(
            self.embed_frame,
            "Carrier Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        
        # Data file selection (multiple)
        self.stego_data_list = self.create_file_list(
            self.embed_frame,
            "Data Files to Hide (Multiple Selection)"
        )
        
        # Output directory
        self.stego_output_dir = self.create_directory_input(
            self.embed_frame,
            "Output Directory"
        )
        
        # Progress and action
        btn_frame = ttk.Frame(self.embed_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        self.embed_progress_var = tk.DoubleVar()
        self.embed_progress = ttk.Progressbar(
            self.embed_frame,
            mode='determinate',
            variable=self.embed_progress_var
        )
        self.embed_progress.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Embed Data",
            command=self._embed_data,
            style='Action.TButton'
        ).pack(side='right')

    def setup_extract_tab(self):
        """Setup the extract tab."""
        ttk.Label(
            self.extract_frame,
            text="Extract Hidden Data",
            font=('Helvetica', 14, 'bold'),
            background=MaterialStyle.WHITE,
            foreground=MaterialStyle.PRIMARY_COLOR
        ).pack(pady=10, padx=20, anchor='w')
        
        # Image selection (multiple)
        self.extract_images_list = self.create_file_list(
            self.extract_frame,
            "Images with Hidden Data (Multiple Selection)",
            filetypes=[("PNG files", "*.png")]
        )
        
        # Output directory
        self.extract_output_dir = self.create_directory_input(
            self.extract_frame,
            "Output Directory"
        )
        
        # Progress and action
        btn_frame = ttk.Frame(self.extract_frame, style='Tab.TFrame')
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        self.extract_progress_var = tk.DoubleVar()
        self.extract_progress = ttk.Progressbar(
            self.extract_frame,
            mode='determinate',
            variable=self.extract_progress_var
        )
        self.extract_progress.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Extract Data",
            command=self._extract_data,
            style='Action.TButton'
        ).pack(side='right')

    def _decrypt_files(self):
        """Handle decryption of multiple files."""
        # Get list of files to process
        self.files_to_process = list(self.decrypt_files_list.get(0, 'end'))
        
        if not self.files_to_process:
            messagebox.showerror("Error", "Please select files to decrypt")
            return
        
        if not self.decrypt_key_path.get():
            messagebox.showerror("Error", "Please select a key file")
            return
        
        if not self.decrypt_output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        # Reset progress
        self.current_file_index = 0
        self.decrypt_progress_var.set(0)
        self.processing_start_time = time.time()
        
        # Start processing thread
        threading.Thread(target=self._process_decryption).start()

    def _process_decryption(self):
        """Process multiple files for decryption."""
        try:
            total_files = len(self.files_to_process)
            
            for i, input_file in enumerate(self.files_to_process):
                self.current_file_index = i
                
                # Update status
                file_name = os.path.basename(input_file)
                self.status_label.config(
                    text=f"Decrypting {file_name} ({i + 1}/{total_files})"
                )
                
                # Generate output path
                output_base = self._generate_output_filename(
                    input_file,
                    self.decrypt_output_dir.get(),
                    is_encrypted=False
                )
                
                try:
                    # Decrypt file
                    decrypt_file(
                        input_file,
                        self.decrypt_key_path.get(),
                        output_base
                    )
                except ValueError as e:
                    messagebox.showerror("Decryption Error", str(e))
                    continue
                
                # Update progress
                progress = ((i + 1) / total_files) * 100
                self.decrypt_progress_var.set(progress)
                
                # Update time remaining
                self._update_time_remaining(i + 1, total_files)
            
            messagebox.showinfo(
                "Success",
                f"Successfully decrypted {total_files} files!\n\n"
                f"Output directory: {self.decrypt_output_dir.get()}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.status_label.config(text="Ready")
            self.time_label.config(text="")
            self.progress_detail.config(text="")

    def _embed_data(self):
        """Handle embedding data in images."""
        carrier = self.carrier_path.get()
        if not carrier:
            messagebox.showerror("Error", "Please select a carrier image")
            return
        
        data_files = list(self.stego_data_list.get(0, 'end'))
        if not data_files:
            messagebox.showerror("Error", "Please select data files to embed")
            return
        
        if not self.stego_output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        # Process each file
        for i, data_file in enumerate(data_files):
            try:
                output_path = os.path.join(
                    self.stego_output_dir.get(),
                    f"stego_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                embed_in_image(carrier, data_file, output_path)
                
                # Update progress
                progress = ((i + 1) / len(data_files)) * 100
                self.embed_progress_var.set(progress)
                
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _extract_data(self):
        """Handle extracting data from images."""
        images = list(self.extract_images_list.get(0, 'end'))
        if not images:
            messagebox.showerror("Error", "Please select images to extract from")
            return
        
        if not self.extract_output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        # Process each image
        for i, image in enumerate(images):
            try:
                output_base = os.path.join(
                    self.extract_output_dir.get(),
                    f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                extract_from_image(image, output_base)
                
                # Update progress
                progress = ((i + 1) / len(images)) * 100
                self.extract_progress_var.set(progress)
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def clear_encrypt_fields(self):
        """Clear all fields in the encrypt tab except output directory."""
        self.input_files_list.delete(0, tk.END)
        if not self.generate_key.get():
            self.key_path.set('')
        self.progress_var.set(0)
        self.progress_label.config(text="0%")

    def clear_decrypt_fields(self):
        """Clear all fields in the decrypt tab except output directory."""
        self.decrypt_files_list.delete(0, tk.END)
        self.decrypt_key_path.set('')
        self.decrypt_progress_var.set(0)

    def clear_embed_fields(self):
        """Clear all fields in the embed tab except output directory."""
        self.carrier_path.set('')
        self.stego_data_list.delete(0, tk.END)
        self.embed_progress_var.set(0)

    def clear_extract_fields(self):
        """Clear all fields in the extract tab except output directory."""
        self.extract_images_list.delete(0, tk.END)
        self.extract_progress_var.set(0)