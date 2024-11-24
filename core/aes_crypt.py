import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import struct

# Constants
CHUNK_SIZE = 64 * 1024  # 64 KB chunks
SALT = b'stegecrypt_salt'
MAGIC_BYTES = b'STEGECRYPT'  # File format identifier

def derive_key(key_file_path):
    """Derive an encryption key from a key file."""
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
    return kdf.derive(hash_key)

def encrypt_file(input_file, key_file, output_file):
    """Encrypt a file using AES-256."""
    key = derive_key(key_file)
    iv = os.urandom(16)
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

def decrypt_file(input_file, key_file, output_file):
    """Decrypt a file using AES-256."""
    try:
        key = derive_key(key_file)
        
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
                return final_output
            except Exception:
                # Clean up failed decryption file
                if os.path.exists(final_output):
                    os.remove(final_output)
                raise ValueError("Decryption failed: Invalid key")

    except (ValueError, struct.error) as e:
        raise ValueError(str(e))