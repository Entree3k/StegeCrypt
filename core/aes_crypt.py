import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import struct
from typing import Optional
from .plugin_system.plugin_base import HookPoint

# Constants
CHUNK_SIZE = 64 * 1024  # 64 KB chunks
SALT = b'stegecrypt_salt'
MAGIC_BYTES = b'STEGECRYPT'  # File format identifier

class CryptoManager:
    """Manages cryptographic operations with plugin support."""
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        if self.plugin_manager:
            self.plugin_manager.execute_hook(HookPoint.CRYPTO_INIT.value, manager=self)
    
    def execute_hook(self, hook_point: str, **kwargs) -> list:
        """Execute hook with proper error handling."""
        if self.plugin_manager:
            try:
                return self.plugin_manager.execute_hook(hook_point, **kwargs)
            except Exception as e:
                print(f"Plugin error during {hook_point}: {str(e)}")
        return []

    def derive_key(self, key_file_path: str) -> bytes:
        """Derive an encryption key from a key file."""
        # Execute pre-key-generation hook
        self.execute_hook(
            HookPoint.PRE_KEY_GENERATION.value,
            key_file=key_file_path
        )
        
        try:
            with open(key_file_path, 'rb') as key_file:
                key_data = key_file.read()
            
            hash_key = hashlib.sha256(key_data).digest()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=SALT,
                iterations=100_000,
                backend=default_backend()
            )
            derived_key = kdf.derive(hash_key)
            
            # Execute post-key-generation hook
            results = self.execute_hook(
                HookPoint.POST_KEY_GENERATION.value,
                key_file=key_file_path,
                derived_key=derived_key
            )
            
            # Allow plugins to modify the derived key
            if results and isinstance(results[0], bytes):
                derived_key = results[0]
                
            return derived_key
            
        except Exception as e:
            raise ValueError(f"Failed to derive key: {str(e)}")

    def encrypt_file(self, input_file: str, key_file: str, output_file: str) -> None:
        """Encrypt a file using AES-256."""
        key = self.derive_key(key_file)
        iv = os.urandom(16)
        
        # Execute pre-encryption hook
        self.execute_hook(
            HookPoint.PRE_ENCRYPTION_ALGORITHM.value,
            operation="encrypt",
            input_file=input_file,
            key=key,
            iv=iv
        )
        
        try:
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Get original file extension
            _, ext = os.path.splitext(input_file)
            ext_bytes = ext.encode('utf-8')
            ext_length = len(ext_bytes)

            with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
                # Write format identifier
                outfile.write(MAGIC_BYTES)
                
                # Write extension length and extension
                outfile.write(struct.pack('<I', ext_length))
                outfile.write(ext_bytes)
                
                # Write IV
                outfile.write(iv)
                
                # Write encrypted data
                while chunk := infile.read(CHUNK_SIZE):
                    encrypted_chunk = encryptor.update(chunk)
                    outfile.write(encrypted_chunk)
                outfile.write(encryptor.finalize())
            
            # Execute post-encryption hook
            self.execute_hook(
                HookPoint.POST_ENCRYPTION_ALGORITHM.value,
                operation="encrypt",
                input_file=input_file,
                output_file=output_file,
                success=True
            )
            
        except Exception as e:
            self.execute_hook(
                HookPoint.POST_ENCRYPTION_ALGORITHM.value,
                operation="encrypt",
                input_file=input_file,
                error=str(e),
                success=False
            )
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt_file(self, input_file: str, key_file: str, output_file: str) -> str:
        """Decrypt a file using AES-256."""
        key = self.derive_key(key_file)
        
        # Execute pre-decryption hook
        self.execute_hook(
            HookPoint.PRE_ENCRYPTION_ALGORITHM.value,
            operation="decrypt",
            input_file=input_file,
            key=key
        )
        
        try:
            with open(input_file, 'rb') as infile:
                # Verify file format
                magic = infile.read(len(MAGIC_BYTES))
                if magic != MAGIC_BYTES:
                    raise ValueError("Invalid file format or not a StegeCrypt file")
                
                # Read original extension
                ext_length = struct.unpack('<I', infile.read(4))[0]
                ext = infile.read(ext_length).decode('utf-8')
                
                # Read IV
                iv = infile.read(16)
                cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                
                # Create output path with original extension
                output_dir = os.path.dirname(output_file)
                output_name = os.path.splitext(os.path.basename(output_file))[0]
                final_output = os.path.join(output_dir, output_name + ext)
                
                try:
                    with open(final_output, 'wb') as outfile:
                        while chunk := infile.read(CHUNK_SIZE):
                            try:
                                decrypted_chunk = decryptor.update(chunk)
                                outfile.write(decrypted_chunk)
                            except Exception:
                                raise ValueError("Decryption failed: Invalid key")
                        outfile.write(decryptor.finalize())
                    
                    # Execute post-decryption hook
                    self.execute_hook(
                        HookPoint.POST_ENCRYPTION_ALGORITHM.value,
                        operation="decrypt",
                        input_file=input_file,
                        output_file=final_output,
                        success=True
                    )
                    
                    return final_output
                    
                except Exception as e:
                    # Clean up failed decryption file
                    if os.path.exists(final_output):
                        os.remove(final_output)
                    
                    self.execute_hook(
                        HookPoint.POST_ENCRYPTION_ALGORITHM.value,
                        operation="decrypt",
                        input_file=input_file,
                        error=str(e),
                        success=False
                    )
                    
                    raise ValueError("Decryption failed: Invalid key")

        except (ValueError, struct.error) as e:
            raise ValueError(str(e))

# Create global crypto manager instance
crypto_manager = None

def init_crypto_manager(plugin_manager=None):
    """Initialize the global crypto manager."""
    global crypto_manager
    crypto_manager = CryptoManager(plugin_manager)
    return crypto_manager

def encrypt_file(input_file: str, key_file: str, output_file: str) -> None:
    """Global encrypt file function."""
    if not crypto_manager:
        raise RuntimeError("Crypto manager not initialized")
    return crypto_manager.encrypt_file(input_file, key_file, output_file)

def decrypt_file(input_file: str, key_file: str, output_file: str) -> str:
    """Global decrypt file function."""
    if not crypto_manager:
        raise RuntimeError("Crypto manager not initialized")
    return crypto_manager.decrypt_file(input_file, key_file, output_file)