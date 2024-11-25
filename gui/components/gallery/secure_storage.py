import os
import hashlib
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from threading import Lock
import atexit
import json
import logging
import shutil

class SecureFileHandle:
    """Secure file handle wrapper."""
    def __init__(self, storage, path, original_path):
        self.storage = storage
        self.path = path
        self.original_path = original_path
        self._ensure_parent_exists()

    def _ensure_parent_exists(self):
        """Ensure parent directory exists."""
        parent = Path(self.path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def read(self):
        """Read decrypted content."""
        return self.storage.read_temp_file(self.path)

    def write(self, content):
        """Write encrypted content."""
        self.storage.write_temp_file(self.path, content)

class SecureTempStorage:
    def __init__(self):
        """Initialize secure temporary storage."""
        self.temp_dir = None
        self._fernet = None
        self._file_handles = {}
        self._lock = Lock()
        self._initialize_crypto()
        self._setup_temp_directory()
        self._integrity_hash = self._calculate_integrity_hash()
        self.is_cleaned_up = False
        atexit.register(self.cleanup)

    def _initialize_crypto(self):
        """Initialize encryption key for temporary files."""
        try:
            session_seed = os.urandom(32)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'secure_temp_storage',
                iterations=100_000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(session_seed))
            self._fernet = Fernet(key)
        except Exception as e:
            logging.error(f"Failed to initialize crypto: {e}")
            raise

    def _setup_temp_directory(self):
        """Create secure temporary directory."""
        try:
            # Get program root directory
            root_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.temp_dir = root_dir / 'temp'
            
            # Create subdirectories
            self.temp_dir.mkdir(exist_ok=True)
            (self.temp_dir / 'data').mkdir(exist_ok=True)
            (self.temp_dir / 'cache').mkdir(exist_ok=True)
            (self.temp_dir / 'session').mkdir(exist_ok=True)
            
            # Set secure permissions
            os.chmod(self.temp_dir, 0o700)
            for subdir in self.temp_dir.iterdir():
                if subdir.is_dir():
                    os.chmod(subdir, 0o700)
            
            logging.info(f"Secure temporary directory created at {self.temp_dir}")
        except Exception as e:
            logging.error(f"Failed to setup temporary directory: {e}")
            raise

    def create_temp_file(self, original_path, content=None):
        """Create a secure temporary file."""
        if self.is_cleaned_up:
            raise Exception("Storage has been cleaned up")

        with self._lock:
            try:
                # Generate secure filename
                encrypted_name = self._encrypt_filename(original_path)
                temp_path = self.temp_dir / 'data' / encrypted_name

                # Ensure parent directory exists
                temp_path.parent.mkdir(parents=True, exist_ok=True)

                # Create handle
                handle = SecureFileHandle(self, str(temp_path), original_path)
                
                # Encrypt and write content if provided
                if content is not None:
                    handle.write(content)

                # Store handle
                self._file_handles[str(temp_path)] = handle
                
                return str(temp_path)
            except Exception as e:
                logging.error(f"Failed to create temporary file: {e}")
                raise

    def read_temp_file(self, temp_path):
        """Read and decrypt a temporary file."""
        if self.is_cleaned_up:
            raise Exception("Storage has been cleaned up")

        try:
            with open(temp_path, 'rb') as f:
                encrypted_content = f.read()
            return self._fernet.decrypt(encrypted_content)
        except Exception as e:
            logging.error(f"Failed to read temporary file: {e}")
            raise

    def write_temp_file(self, temp_path, content):
        """Write encrypted content to a temporary file."""
        if self.is_cleaned_up:
            raise Exception("Storage has been cleaned up")

        try:
            encrypted_content = self._fernet.encrypt(content)
            with open(temp_path, 'wb') as f:
                f.write(encrypted_content)
            self._integrity_hash = self._calculate_integrity_hash()
        except Exception as e:
            logging.error(f"Failed to write temporary file: {e}")
            raise

    def get_file_handle(self, temp_path):
        """Get secure file handle."""
        if self.is_cleaned_up:
            logging.error("Storage has been cleaned up")
            return None
            
        try:
            temp_path = os.path.normpath(temp_path)
            if temp_path in self._file_handles:
                return self._file_handles[temp_path]
                
            if os.path.exists(temp_path):
                handle = SecureFileHandle(self, temp_path, temp_path)
                self._file_handles[temp_path] = handle
                return handle
                
            logging.error(f"No file found at path: {temp_path}")
            return None
            
        except Exception as e:
            logging.error(f"Failed to get file handle: {e}")
            return None

    def verify_integrity(self):
        """Verify the integrity of the temporary directory."""
        if self.is_cleaned_up:
            return False
        return self._calculate_integrity_hash() == self._integrity_hash

    def cleanup(self):
        """Clean up temporary files and directory."""
        if self.is_cleaned_up:
            return

        try:
            if self.temp_dir and self.temp_dir.exists():
                # Securely overwrite files
                for file_path in self.temp_dir.rglob('*'):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        with open(file_path, 'wb') as f:
                            f.write(os.urandom(size))

                # Remove directory and contents
                shutil.rmtree(str(self.temp_dir), ignore_errors=True)
                logging.info("Secure temporary storage cleaned up successfully")
        except Exception as e:
            logging.error(f"Error during secure cleanup: {e}")
        finally:
            self.is_cleaned_up = True
            self._file_handles.clear()

    def _encrypt_filename(self, filename):
        """Encrypt filename to prevent information leakage."""
        return hashlib.sha256(str(filename).encode()).hexdigest()

    def _calculate_integrity_hash(self):
        """Calculate integrity hash of the temporary directory."""
        hasher = hashlib.sha256()
        if self.temp_dir and self.temp_dir.exists():
            for path in sorted(self.temp_dir.rglob('*')):
                hasher.update(str(path).encode())
                if path.is_file():
                    hasher.update(str(path.stat().st_mtime).encode())
        return hasher.hexdigest()

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()