import os
import hashlib
import sys
import random
import string
from datetime import datetime
import secrets
from typing import Optional
from .plugin_system.plugin_base import HookPoint

class UtilsManager:
    """Manages utility operations with plugin support."""
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        if self.plugin_manager:
            self.plugin_manager.execute_hook(HookPoint.UTILS_INIT.value, manager=self)
    
    def execute_hook(self, hook_point: str, **kwargs) -> list:
        """Execute hook with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                print(f"Plugin error during {hook_point}: {str(e)}")
        return []
    
    def compute_file_hash(self, file_path: str, hash_type: str = 'sha256') -> str:
        """Compute the hash of a file using specified algorithm."""
        # Execute pre-hash hook
        self.execute_hook(
            HookPoint.PRE_FILE_HASH.value,
            file_path=file_path,
            hash_type=hash_type
        )
        
        try:
            if hash_type == 'sha256':
                hasher = hashlib.sha256()
            elif hash_type == 'sha512':
                hasher = hashlib.sha512()
            elif hash_type == 'md5':
                hasher = hashlib.md5()
            else:
                raise ValueError("Unsupported hash type")

            file_size = os.path.getsize(file_path)
            processed_size = 0
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
                    processed_size += len(chunk)
                    progress = (processed_size / file_size) * 100
                    sys.stdout.write(f"\rComputing hash: {progress:.1f}%")
                    sys.stdout.flush()
            
            hash_value = hasher.hexdigest()
            
            # Execute post-hash hook
            results = self.execute_hook(
                HookPoint.POST_FILE_HASH.value,
                file_path=file_path,
                hash_type=hash_type,
                hash_value=hash_value
            )
            
            # Allow plugins to modify the hash value
            if results and isinstance(results[0], str):
                hash_value = results[0]
            
            return hash_value
            
        except Exception as e:
            raise ValueError(f"Failed to compute hash: {str(e)}")
    
    def secure_delete(self, file_path: str, passes: int = 3) -> bool:
        """Securely delete a file by overwriting it multiple times."""
        if not os.path.exists(file_path):
            return False

        try:
            file_size = os.path.getsize(file_path)
            
            # Force garbage collection to release file handles
            import gc
            gc.collect()
            
            import time
            time.sleep(0.1)  # Small delay to ensure file handles are released
            
            # Perform overwrite passes
            for pass_num in range(passes):
                with open(file_path, "wb") as f:
                    # Use different patterns for each pass
                    for chunk in range(0, file_size, 65536):  # 64KB chunks
                        write_size = min(65536, file_size - chunk)
                        if pass_num == 0:
                            f.write(os.urandom(write_size))  # Random data
                        elif pass_num == 1:
                            f.write(b'\x00' * write_size)    # All zeros
                        else:
                            f.write(b'\xFF' * write_size)    # All ones
                        
                    # Force write to disk
                    f.flush()
                    os.fsync(f.fileno())
            
            # Close file handle and wait
            time.sleep(0.1)
            
            # Multiple deletion attempts
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    os.remove(file_path)
                    if not os.path.exists(file_path):
                        return True
                except Exception:
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                        continue
                    raise
            
            return not os.path.exists(file_path)
            
        except Exception as e:
            print(f"Error during secure deletion: {str(e)}")
            try:
                # Fallback to normal deletion
                os.remove(file_path)
                return not os.path.exists(file_path)
            except:
                return False
    
    def generate_key_file(self, directory: str, size_bytes: int = 1024) -> str:
        """Generate a random key file."""
        # Execute pre-key-generation hook
        self.execute_hook(
            HookPoint.PRE_KEY_GENERATION.value,
            directory=directory,
            size_bytes=size_bytes
        )
        
        try:
            # Validate directory
            if not directory:
                raise ValueError("Output directory is required")
            if not os.path.exists(directory):
                raise ValueError("Output directory does not exist")
            if not os.path.isdir(directory):
                raise ValueError("Specified path is not a directory")

            # Generate random data
            random_data = os.urandom(size_bytes)
            
            # Generate random filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            filename = f"key_{timestamp}_{random_suffix}.key"
            
            # Create full path
            key_path = os.path.join(directory, filename)
            
            # Write key file
            with open(key_path, 'wb') as f:
                f.write(random_data)
            
            # Execute post-key-generation hook
            self.execute_hook(
                HookPoint.POST_KEY_GENERATION.value,
                key_path=key_path,
                success=True
            )
            
            return key_path
            
        except Exception as e:
            self.execute_hook(
                HookPoint.POST_KEY_GENERATION.value,
                directory=directory,
                error=str(e),
                success=False
            )
            raise ValueError(f"Failed to generate key file: {str(e)}")

# Create global utils manager instance
utils_manager = None

def init_utils_manager(plugin_manager=None):
    """Initialize the global utils manager."""
    global utils_manager
    utils_manager = UtilsManager(plugin_manager)
    return utils_manager

# Global utility functions that use the manager
def validate_file(file_path):
    """Verify that a file exists."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

def log_progress(current, total):
    """Display a progress bar."""
    percentage = (current / total) * 100
    sys.stdout.write(f"\rProgress: {percentage:.2f}%")
    sys.stdout.flush()

def compute_file_hash(file_path: str, hash_type: str = 'sha256') -> str:
    """Global compute hash function."""
    if not utils_manager:
        raise RuntimeError("Utils manager not initialized")
    return utils_manager.compute_file_hash(file_path, hash_type)

def verify_file_integrity(file_path: str, original_hash: str, hash_type: str = 'sha256') -> bool:
    """Verify file integrity by comparing hashes."""
    current_hash = compute_file_hash(file_path, hash_type)
    return current_hash.lower() == original_hash.lower()

def secure_delete(file_path: str, passes: int = 3) -> bool:
    """Global secure delete function."""
    if not utils_manager:
        raise RuntimeError("Utils manager not initialized")
    return utils_manager.secure_delete(file_path, passes)

def generate_key_file(directory: str, size_bytes: int = 1024) -> str:
    """Global key file generation function."""
    if not utils_manager:
        raise RuntimeError("Utils manager not initialized")
    return utils_manager.generate_key_file(directory, size_bytes)