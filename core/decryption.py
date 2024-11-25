import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import struct
import tempfile
from typing import Tuple

# Constants
CHUNK_SIZE = 64 * 1024  # 64 KB chunks
SALT = b'stegecrypt_salt'
MAGIC_BYTES = b'STEGECRYPT'  # File format identifier

class DecryptionError(Exception):
    """Custom exception for decryption errors."""
    pass

def derive_key(key_file_path: str) -> bytes:
    """
    Derive an encryption key from a key file using PBKDF2.
    
    Args:
        key_file_path (str): Path to the key file
        
    Returns:
        bytes: Derived key for encryption/decryption
        
    Raises:
        DecryptionError: If key derivation fails
    """
    try:
        with open(key_file_path, 'rb') as key_file:
            key_data = key_file.read()
            
        # Create initial hash of key data
        hash_key = hashlib.sha256(key_data).digest()
        
        # Use PBKDF2 to derive final key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=SALT,
            iterations=100_000,
            backend=default_backend()
        )
        
        return kdf.derive(hash_key)
        
    except Exception as e:
        raise DecryptionError(f"Failed to process key file: {str(e)}")

def verify_encrypted_file(file_path: str) -> Tuple[bytes, str]:
    """
    Verify that a file is a valid encrypted file and read its header.
    
    Args:
        file_path (str): Path to the encrypted file
        
    Returns:
        Tuple[bytes, str]: (IV, file extension)
        
    Raises:
        DecryptionError: If file verification fails
    """
    try:
        with open(file_path, 'rb') as f:
            # Check magic bytes
            magic = f.read(len(MAGIC_BYTES))
            if magic != MAGIC_BYTES:
                raise DecryptionError("Invalid file format or not a StegeCrypt file")
            
            # Read extension length and extension
            ext_length = struct.unpack('<I', f.read(4))[0]
            extension = f.read(ext_length).decode('utf-8')
            
            # Read initialization vector
            iv = f.read(16)
            
            if not all([magic, extension, iv]):
                raise DecryptionError("Incomplete or corrupted file header")
                
            return iv, extension
            
    except Exception as e:
        raise DecryptionError(f"Failed to verify encrypted file: {str(e)}")

def decrypt_file(input_file: str, key_file: str, output_file: str) -> str:
    """
    Decrypt a file using AES-256 CFB mode.
    
    Args:
        input_file (str): Path to the encrypted file
        key_file (str): Path to the key file
        output_file (str): Path where decrypted file should be saved
        
    Returns:
        str: Path to the decrypted file (may include original extension)
        
    Raises:
        DecryptionError: If decryption fails
    """
    temp_file = None
    
    try:
        # Derive key from key file
        key = derive_key(key_file)
        
        # Verify file and get IV and extension
        iv, extension = verify_encrypted_file(input_file)
        
        # Setup cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CFB(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Create output path with original extension
        output_dir = os.path.dirname(output_file)
        output_name = os.path.splitext(os.path.basename(output_file))[0]
        final_output = os.path.join(output_dir, output_name + extension)
        
        # Create a temporary file first
        temp_fd, temp_file = tempfile.mkstemp(suffix=extension)
        os.close(temp_fd)
        
        # Decrypt file in chunks
        with open(input_file, 'rb') as infile:
            # Skip header
            infile.seek(len(MAGIC_BYTES) + 4 + len(extension.encode()) + 16)
            
            with open(temp_file, 'wb') as outfile:
                while True:
                    chunk = infile.read(CHUNK_SIZE)
                    if not chunk:
                        break
                        
                    decrypted_chunk = decryptor.update(chunk)
                    outfile.write(decrypted_chunk)
                    
                # Write final block
                outfile.write(decryptor.finalize())
        
        # Move temp file to final location
        if os.path.exists(final_output):
            os.remove(final_output)
        os.rename(temp_file, final_output)
        temp_file = None  # Prevent deletion in finally block
        
        return final_output
        
    except DecryptionError as e:
        raise e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {str(e)}")
    finally:
        # Clean up temporary file if it exists
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

def decrypt_to_memory(input_file: str, key_file: str) -> Tuple[bytes, str]:
    """
    Decrypt a file into memory instead of writing to disk.
    
    Args:
        input_file (str): Path to the encrypted file
        key_file (str): Path to the key file
        
    Returns:
        Tuple[bytes, str]: (decrypted data, file extension)
        
    Raises:
        DecryptionError: If decryption fails
    """
    try:
        # Derive key from key file
        key = derive_key(key_file)
        
        # Verify file and get IV and extension
        iv, extension = verify_encrypted_file(input_file)
        
        # Setup cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CFB(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt file
        decrypted_data = bytearray()
        
        with open(input_file, 'rb') as infile:
            # Skip header
            infile.seek(len(MAGIC_BYTES) + 4 + len(extension.encode()) + 16)
            
            while True:
                chunk = infile.read(CHUNK_SIZE)
                if not chunk:
                    break
                    
                decrypted_chunk = decryptor.update(chunk)
                decrypted_data.extend(decrypted_chunk)
            
            # Add final block
            decrypted_data.extend(decryptor.finalize())
        
        return bytes(decrypted_data), extension
        
    except DecryptionError as e:
        raise e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {str(e)}")

def is_valid_encrypted_file(file_path: str) -> bool:
    """
    Check if a file appears to be a valid encrypted file.
    
    Args:
        file_path (str): Path to the file to check
        
    Returns:
        bool: True if file appears to be valid, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(len(MAGIC_BYTES))
            return magic == MAGIC_BYTES
    except:
        return False