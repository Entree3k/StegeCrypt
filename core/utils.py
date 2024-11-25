# utils.py
import os
import hashlib
import sys
import random
import string
from datetime import datetime
import secrets

def validate_file(file_path):
    """Verify that a file exists."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

def log_progress(current, total):
    """Display a progress bar."""
    percentage = (current / total) * 100
    sys.stdout.write(f"\rProgress: {percentage:.2f}%")
    sys.stdout.flush()

def compute_file_hash(file_path, hash_type='sha256'):
    """
    Compute the hash of a file using specified algorithm.
    
    Args:
        file_path: Path to the file
        hash_type: Hash algorithm to use ('sha256', 'sha512', or 'md5')
        
    Returns:
        str: Hex digest of the hash
    """
    validate_file(file_path)
    
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
    
    print("\nHash computation complete")
    return hasher.hexdigest()

def verify_file_integrity(file_path, original_hash, hash_type='sha256'):
    """
    Verify file integrity by comparing hashes.
    
    Args:
        file_path: Path to the file to verify
        original_hash: Original hash to compare against
        hash_type: Hash algorithm to use
        
    Returns:
        bool: True if hashes match, False otherwise
    """
    current_hash = compute_file_hash(file_path, hash_type)
    return current_hash.lower() == original_hash.lower()

def secure_delete(file_path, passes=3):
    """
    Securely delete a file by overwriting it multiple times.
    
    Args:
        file_path: Path to the file to delete
        passes: Number of overwrite passes (default 3)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(file_path):
        return False

    try:
        file_size = os.path.getsize(file_path)
        
        for pass_num in range(passes):
            with open(file_path, "wb") as f:
                # Pass 1: Random data
                if pass_num == 0:
                    f.write(secrets.token_bytes(file_size))
                # Pass 2: All zeros
                elif pass_num == 1:
                    f.write(b'\x00' * file_size)
                # Pass 3: All ones
                else:
                    f.write(b'\xFF' * file_size)
                # Ensure data is written to disk
                f.flush()
                os.fsync(f.fileno())
        
        # Close any open handles before deleting
        try:
            os.close(f.fileno())
        except:
            pass
            
        # Delete the file
        os.unlink(file_path)
        return True
        
    except Exception as e:
        print(f"Error during secure deletion: {str(e)}")
        # Try regular deletion as fallback
        try:
            os.remove(file_path)
            return True
        except:
            return False

def generate_key_file(directory: str, size_bytes: int = 1024) -> str:
    """
    Generate a random key file.
    
    Args:
        directory: Directory to save the key file
        size_bytes: Size of the key file in bytes (default 1KB)
    
    Returns:
        str: Path to the generated key file
    """
    # Validate directory
    if not directory:
        raise ValueError("Output directory is required")
    if not os.path.exists(directory):
        raise ValueError("Output directory does not exist")
    if not os.path.isdir(directory):
        raise ValueError("Specified path is not a directory")

    try:
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
        
        return key_path
        
    except IOError as e:
        raise ValueError(f"Failed to generate key file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error while generating key: {str(e)}")