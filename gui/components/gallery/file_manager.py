import os
import logging
from tkinter import messagebox
from core.decryption import decrypt_file, decrypt_to_memory, DecryptionError

class FileManager:
    def __init__(self, temp_manager, plugin_manager=None):
        self.encrypted_files = []
        self.decrypted_cache = {}
        self.file_types = {}
        self.temp_manager = temp_manager
        self.plugin_manager = plugin_manager
    
    def scan_directory(self, directory):
        """Scan directory for encrypted files."""
        if not directory or not os.path.exists(directory):
            return []
        
        try:
            # Get all .stegecrypt files in the directory
            encrypted_files = [
                f for f in os.listdir(directory)
                if f.lower().endswith('.stegecrypt')
            ]
            
            # Store the files with full paths
            self.encrypted_files = [os.path.join(directory, f) for f in encrypted_files]
            
            logging.info(f"Found {len(encrypted_files)} encrypted files")
            
            # Run plugin hook if available
            if self.plugin_manager:
                self.plugin_manager.run_hook('scan_directory', directory, encrypted_files)
                
            return encrypted_files
            
        except Exception as e:
            logging.error(f"Failed to scan directory: {e}")
            messagebox.showerror("Error", f"Failed to scan directory: {str(e)}")
            return []
    
    def decrypt_file(self, input_path, key_file, output_path):
        """Decrypt a file and store in secure storage."""
        try:
            if not key_file:
                raise ValueError("No key file selected")
                
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"File not found: {input_path}")
            
            # Check if already decrypted
            if input_path in self.decrypted_cache:
                return self.decrypted_cache[input_path]
            
            logging.info(f"Decrypting file: {input_path}")
            
            # Run pre-decrypt hook if available
            if self.plugin_manager:
                self.plugin_manager.run_hook('pre_decrypt', input_path, key_file)
            
            # Decrypt file to memory
            decrypted_data, extension = decrypt_to_memory(input_path, key_file)
            
            # Create secure temporary file with content
            temp_path = self.temp_manager.create_temp_file(
                original_path=input_path + extension,
                content=decrypted_data
            )
            
            # Cache the path and file type
            self.decrypted_cache[input_path] = temp_path
            self.file_types[input_path] = extension.lower()
            
            # Run post-decrypt hook if available
            if self.plugin_manager:
                self.plugin_manager.run_hook('post_decrypt', input_path, temp_path, extension)
            
            logging.info(f"Successfully decrypted file: {input_path}")
            return temp_path
            
        except Exception as e:
            logging.error(f"Failed to decrypt file {input_path}: {e}")
            return None
    
    def get_decrypted_file(self, file_path):
        """Get secure handle for decrypted file."""
        try:
            if not file_path:
                raise ValueError("No file path provided")
                
            file_path = os.path.normpath(file_path)  # Normalize path separators
            
            if file_path in self.decrypted_cache:
                handle = self.temp_manager.get_secure_handle(self.decrypted_cache[file_path])
                if handle:
                    return handle
                    
            logging.error(f"No decrypted file found for {file_path}")
            return None
            
        except Exception as e:
            logging.error(f"Failed to get secure handle for {file_path}: {e}")
            return None
    
    def get_file_type(self, input_path):
        """Get cached file type."""
        return self.file_types.get(input_path)    
  
    def clear_cache(self):
        """Clear decrypted file cache."""
        try:
            self.decrypted_cache.clear()
            self.file_types.clear()
            logging.info("File cache cleared")
            
            # Run plugin hook if available
            if self.plugin_manager:
                self.plugin_manager.run_hook('cache_cleared')
                
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")
            
    def __del__(self):
        """Cleanup on deletion."""
        self.clear_cache()