from tkinter import filedialog, messagebox, ttk
import os
import threading
from gui.components.image_viewer import ImageViewer
from gui.components.video_player import VideoPlayer
from gui.material_colors import MaterialColors  # Added this import

class EventHandlers:
    def __init__(self, gallery):
        self.gallery = gallery
    
    def select_directory(self):
        """Handle directory selection."""
        directory = filedialog.askdirectory()
        if directory:
            self.gallery.current_directory = directory
            self.scan_directory()
    
    def select_key(self):
        """Handle key file selection."""
        key_file = filedialog.askopenfilename(
            title="Select Key File",
            filetypes=[
                ("All Key Files", "*.key;*.txt;*.png;*.jpg;*.jpeg"),
                ("Key files", "*.key"),
                ("Text files", "*.txt"),
                ("Image files", "*.png;*.jpg;*.jpeg"),
                ("All files", "*.*")
            ]
        )
        if key_file:
            self.gallery.key_file = key_file
            self.gallery.ui.update_status(
                f"Key loaded: {os.path.basename(key_file)}"
            )
            if self.gallery.encrypted_files:  # Only decrypt if we have files
                self.decrypt_files()
    
    def scan_directory(self):
        """Scan selected directory for encrypted files."""
        if not self.gallery.current_directory:
            return
        
        # Clear existing state
        self.gallery.encrypted_files = []
        self.gallery.ui.clear_gallery()
        
        # Find encrypted files
        self.gallery.encrypted_files = self.gallery.file_manager.scan_directory(
            self.gallery.current_directory
        )
        
        if not self.gallery.encrypted_files:
            self.gallery.ui.update_status("No encrypted files found")
            return
        
        # Show status message
        count = len(self.gallery.encrypted_files)
        if self.gallery.key_file:
            self.decrypt_files()  # If we already have a key, start decryption
        else:
            self.gallery.ui.update_status(
                f"Found {count} encrypted files - Select key to view"
            )
            self.show_placeholders()  # Show placeholders until key is selected
    
    def show_placeholders(self):
        """Show placeholder thumbnails for encrypted files."""
        columns = 4
        for i, filename in enumerate(self.gallery.encrypted_files):
            frame = self.create_locked_thumbnail(filename)
            frame.grid(row=i//columns, column=i%columns, padx=10, pady=10, sticky='nsew')
            # Configure grid weights
            self.gallery.ui.gallery_frame.grid_columnconfigure(i % columns, weight=1)
            self.gallery.ui.gallery_frame.grid_rowconfigure(i // columns, weight=1)
    
    def create_locked_thumbnail(self, filename):
        """Create a locked file thumbnail."""
        frame = ttk.Frame(
            self.gallery.ui.gallery_frame,
            style='Thumbnail.TFrame',
            padding=10
        )
        
        # Container for content
        container = ttk.Frame(frame, style='Thumbnail.TFrame')
        container.pack(expand=True, fill='both')
        
        # Lock icon
        ttk.Label(
            container,
            text="🔒",
            font=('Helvetica', 32),
            background=MaterialColors.SURFACE,
            style='Thumbnail.TLabel'
        ).pack(pady=10, expand=True)
        
        # Filename (truncated if needed)
        if len(filename) > 20:
            filename = filename[:17] + "..."
        ttk.Label(
            container,
            text=filename,
            background=MaterialColors.SURFACE,
            style='Thumbnail.TLabel'
        ).pack(pady=(0, 5), expand=True)
        
        return frame
    
    def decrypt_files(self):
        """Handle decryption of files and thumbnail creation."""
        if not self.gallery.key_file:
            self.gallery.ui.update_status("Please select a key file first")
            return
            
        if not self.gallery.encrypted_files:
            self.gallery.ui.update_status("No encrypted files to decrypt")
            return
        
        self.gallery.ui.show_progress_bar()
        self.gallery.ui.update_progress(0)
        
        def process_files():
            try:
                total_files = len(self.gallery.encrypted_files)
                columns = 4
                current_row = 0
                current_col = 0
                
                # Clear existing thumbnails
                self.gallery.ui.clear_gallery()
                
                for i, filename in enumerate(self.gallery.encrypted_files):
                    filepath = os.path.join(
                        self.gallery.current_directory,
                        filename
                    )
                    
                    self.gallery.ui.update_status(
                        f"Processing {i + 1}/{total_files}: {filename}"
                    )
                    
                    frame = self.gallery.thumbnail_manager.create_thumbnail_frame(
                        filepath,
                        filename
                    )
                    frame.grid(
                        row=current_row, 
                        column=current_col, 
                        padx=10, 
                        pady=10, 
                        sticky='nsew'
                    )
                    
                    # Configure grid weights
                    self.gallery.ui.gallery_frame.grid_columnconfigure(current_col, weight=1)
                    self.gallery.ui.gallery_frame.grid_rowconfigure(current_row, weight=1)
                    
                    current_col += 1
                    if current_col >= columns:
                        current_col = 0
                        current_row += 1
                    
                    # Update progress
                    progress = ((i + 1) / total_files) * 100
                    self.gallery.ui.update_progress(progress)
                
                self.gallery.ui.update_status("Ready")
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                self.gallery.ui.hide_progress_bar()
        
        threading.Thread(target=process_files, daemon=True).start()
    
    def view_media(self, filepath):
        """Handle media file viewing."""
        try:
            # Ensure file is decrypted
            if filepath not in self.gallery.file_manager.decrypted_cache:
                if not self.gallery.key_file:
                    messagebox.showerror("Error", "Please select a key file first")
                    return
                    
                # Try to decrypt the file
                decrypted_path = self.gallery.file_manager.decrypt_file(
                    filepath,
                    self.gallery.key_file,
                    self.gallery.temp_manager.get_temp_path()
                )
                
                if not decrypted_path:
                    raise Exception("Failed to decrypt file")
            
            # Get file type
            file_type = self.gallery.file_manager.file_types.get(filepath, '').lower()
            
            # Open appropriate viewer
            if file_type in {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}:
                VideoPlayer(self.gallery, filepath)
            else:
                ImageViewer(self.gallery, filepath)
                
        except Exception as e:
            logging.error(f"Failed to view media {filepath}: {e}")
            messagebox.showerror("Error", str(e))