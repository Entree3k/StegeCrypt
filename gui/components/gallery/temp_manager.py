import os
from datetime import datetime
from pathlib import Path
import logging
import shutil
import hashlib

class TempManager:
    def __init__(self, secure_storage):
        """Initialize temporary file manager with secure storage."""
        self.secure_storage = secure_storage
        self.setup_temp_directory()
        self.handles = {}
        logging.info("TempManager initialized with secure storage")
    
    def setup_temp_directory(self):
        """Setup temporary directory in program root."""
        try:
            # Get program root directory
            root_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            self.temp_dir = root_dir / 'temp'
            
            # Create subdirectories
            self.temp_dir.mkdir(exist_ok=True)
            (self.temp_dir / 'videos').mkdir(exist_ok=True)
            (self.temp_dir / 'images').mkdir(exist_ok=True)
            (self.temp_dir / 'decrypted').mkdir(exist_ok=True)
            
            # Set permissions
            os.chmod(self.temp_dir, 0o700)
            for subdir in self.temp_dir.iterdir():
                if subdir.is_dir():
                    os.chmod(subdir, 0o700)
            
            logging.info(f"Created temp directory at: {self.temp_dir}")
            
        except Exception as e:
            logging.error(f"Error setting up temp directory: {e}")
            raise
    
    def get_temp_path(self, prefix="decrypt_", suffix=""):
        """Generate a temporary file path in the appropriate subdirectory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}{timestamp}{suffix}"
        
        # Choose subdirectory based on file type
        if suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            subdir = 'videos'
        elif suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            subdir = 'images'
        else:
            subdir = 'decrypted'
        
        temp_path = self.temp_dir / subdir / filename
        return str(temp_path)
    
    def create_temp_file(self, original_path, content):
        """Create a temporary file with encrypted content."""
        try:
            # Generate temp path
            _, ext = os.path.splitext(original_path)
            temp_path = self.get_temp_path(suffix=ext)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # Encrypt and write content
            encrypted_content = self.secure_storage._fernet.encrypt(content)
            with open(temp_path, 'wb') as f:
                f.write(encrypted_content)
            
            # Create and store handle
            handle = SecureFileHandle(self.secure_storage, temp_path, original_path)
            self.handles[temp_path] = handle
            
            logging.info(f"Created temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logging.error(f"Failed to create temporary file: {e}")
            raise
    
    def get_secure_handle(self, temp_path):
        """Get a secure file handle for a temporary file."""
        try:
            if temp_path in self.handles:
                return self.handles[temp_path]
            
            if os.path.exists(temp_path):
                handle = SecureFileHandle(self.secure_storage, temp_path, temp_path)
                self.handles[temp_path] = handle
                return handle
            
            logging.error(f"No file found at: {temp_path}")
            return None
            
        except Exception as e:
            logging.error(f"Failed to get secure handle: {e}")
            return None
    
    def clean_temp_files(self):
        """Clean all temporary files securely."""
        try:
            if not self.temp_dir.exists():
                return
                
            # Clear handles
            self.handles.clear()
            
            # Clean each subdirectory
            for subdir in ['videos', 'images', 'decrypted']:
                subdir_path = self.temp_dir / subdir
                if subdir_path.exists():
                    for file_path in subdir_path.glob('*'):
                        try:
                            if file_path.is_file():
                                # Securely overwrite file
                                size = file_path.stat().st_size
                                with open(file_path, 'wb') as f:
                                    f.write(os.urandom(size))
                                # Delete file
                                file_path.unlink()
                        except Exception as e:
                            logging.error(f"Error cleaning file {file_path}: {e}")
            
            logging.info("Temporary files cleaned successfully")
            
        except Exception as e:
            logging.error(f"Error cleaning temporary files: {e}")
            raise
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.clean_temp_files()
        except:
            pass
            
class SecureFileHandle:
    """Handle for secure temporary files."""
    
    def __init__(self, storage, temp_path, original_path):
        self.storage = storage
        self.temp_path = temp_path
        self.original_path = original_path
    
    def read(self):
        """Read and decrypt file content."""
        try:
            with open(self.temp_path, 'rb') as f:
                encrypted_content = f.read()
            return self.storage._fernet.decrypt(encrypted_content)
        except Exception as e:
            logging.error(f"Error reading secure file: {e}")
            raise
    
    def write(self, content):
        """Encrypt and write content."""
        try:
            encrypted_content = self.storage._fernet.encrypt(content)
            with open(self.temp_path, 'wb') as f:
                f.write(encrypted_content)
        except Exception as e:
            logging.error(f"Error writing secure file: {e}")
            raise