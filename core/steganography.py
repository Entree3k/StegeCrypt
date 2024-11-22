from PIL import Image
import numpy as np
from core.utils import validate_file, log_progress
import os
import struct

MAGIC_MARKER = "STEGO2024"  # Clear marker for data validation

class SteganographyError(Exception):
    pass

def int_to_bits(value, bit_length):
    return format(value, f'0{bit_length}b')

def bits_to_int(bits):
    return int(bits, 2)

def str_to_bits(s):
    return ''.join(format(ord(c), '08b') for c in s)

def bits_to_str(bits):
    return ''.join(chr(bits_to_int(bits[i:i+8])) for i in range(0, len(bits), 8))

def embed_in_image(image_path: str, data_path: str, output_path: str) -> None:
    """Embed data from a file into an image using LSB steganography."""
    try:
        validate_file(image_path)
        validate_file(data_path)
        
        # Read and prepare the image
        img = Image.open(image_path)
        img = img.convert('RGB')
        width, height = img.size
        pixels = list(img.getdata())
        
        # Prepare file data
        _, ext = os.path.splitext(data_path)
        with open(data_path, 'rb') as f:
            file_data = f.read()
        
        # Convert marker to bits
        marker_bits = str_to_bits(MAGIC_MARKER)
        
        # Convert extension to bits
        ext_bits = str_to_bits(ext)
        ext_length_bits = int_to_bits(len(ext_bits), 32)
        
        # Convert file data to bits
        data_bits = ''.join(format(b, '08b') for b in file_data)
        data_length_bits = int_to_bits(len(file_data), 32)
        
        # Combine all bits with clear markers
        all_bits = (
            marker_bits +           # Magic marker
            ext_length_bits +       # Length of extension in bits
            ext_bits +             # Extension bits
            data_length_bits +     # Length of data in bytes
            data_bits              # Actual data bits
        )
        
        print(f"Embedding: Marker({len(marker_bits)}), Ext({len(ext_bits)}), Data({len(data_bits)}) bits")
        
        # Check if image is large enough
        available_bits = len(pixels) * 3
        if len(all_bits) > available_bits:
            raise SteganographyError(
                f"Image too small. Needs {len(all_bits)} bits but only has {available_bits} available."
            )
        
        # Embed data
        new_pixels = []
        bit_index = 0
        
        for pixel in pixels:
            r, g, b = pixel
            if bit_index < len(all_bits):
                r = (r & ~1) | int(all_bits[bit_index])
                bit_index += 1
            if bit_index < len(all_bits):
                g = (g & ~1) | int(all_bits[bit_index])
                bit_index += 1
            if bit_index < len(all_bits):
                b = (b & ~1) | int(all_bits[bit_index])
                bit_index += 1
            new_pixels.append((r, g, b))
            
            if bit_index % 1000000 == 0:
                log_progress(bit_index, len(all_bits))
        
        # Create and save new image
        new_img = Image.new('RGB', (width, height))
        new_img.putdata(new_pixels)
        new_img.save(output_path, 'PNG')
        
        print(f"Successfully embedded {len(file_data)} bytes with extension {ext}")
        
    except Exception as e:
        raise SteganographyError(f"Failed to embed data: {str(e)}")

def extract_from_image(image_path: str, output_path: str) -> None:
    """Extract hidden data from an image."""
    try:
        validate_file(image_path)
        
        # Read the image
        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = list(img.getdata())
        
        # Extract bits
        extracted_bits = ''
        for r, g, b in pixels:
            extracted_bits += str(r & 1)
            extracted_bits += str(g & 1)
            extracted_bits += str(b & 1)
        
        # Verify magic marker
        marker_length = len(MAGIC_MARKER) * 8
        marker_bits = extracted_bits[:marker_length]
        try:
            marker = bits_to_str(marker_bits)
            if marker != MAGIC_MARKER:
                raise SteganographyError("No hidden data found (Invalid marker)")
        except Exception:
            raise SteganographyError("No hidden data found")
        
        current_pos = marker_length
        
        # Read extension length
        ext_length_bits = extracted_bits[current_pos:current_pos + 32]
        ext_length = bits_to_int(ext_length_bits)
        current_pos += 32
        
        # Read extension
        ext_bits = extracted_bits[current_pos:current_pos + ext_length]
        try:
            extension = bits_to_str(ext_bits)
            if not extension.startswith('.'):
                raise SteganographyError("Invalid extension format")
        except Exception:
            raise SteganographyError("Invalid extension data")
        current_pos += ext_length
        
        # Read data length
        data_length_bits = extracted_bits[current_pos:current_pos + 32]
        data_length = bits_to_int(data_length_bits)
        current_pos += 32
        
        if data_length * 8 > len(extracted_bits) - current_pos:
            raise SteganographyError("Data length exceeds available bits")
        
        # Extract data
        data_bits = extracted_bits[current_pos:current_pos + (data_length * 8)]
        data = bytes(bits_to_int(data_bits[i:i+8]) for i in range(0, len(data_bits), 8))
        
        # Save extracted data
        output_path_with_ext = os.path.splitext(output_path)[0] + extension
        with open(output_path_with_ext, 'wb') as f:
            f.write(data)
        
        print(f"Successfully extracted {data_length} bytes to: {output_path_with_ext}")
        return output_path_with_ext
        
    except SteganographyError as e:
        raise e
    except Exception as e:
        raise SteganographyError(f"Failed to extract data: {str(e)}")