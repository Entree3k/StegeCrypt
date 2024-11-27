from PIL import Image
import numpy as np
from core.utils import validate_file, log_progress
from core.plugin_system.plugin_base import HookPoint
import os
from datetime import datetime

MAGIC_MARKER = "STEGO2024"  # Clear marker for data validation
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for processing
SUPPORTED_FORMATS = {'.png', '.bmp', '.jpg', '.jpeg', '.tiff', '.gif'}

class SteganographyError(Exception):
    pass

def int_to_bits(value, bit_length):
    return format(value, f'0{bit_length}b')

def bits_to_int(bits):
    return int(bits, 2)

def str_to_bits(s):
    return ''.join(format(ord(c), '08b') for c in s)

def bits_to_str(bits):
    try:
        return ''.join(chr(bits_to_int(bits[i:i+8])) for i in range(0, len(bits), 8))
    except Exception as e:
        raise SteganographyError(f"Failed to convert bits to string: {str(e)}")

def validate_image_format(filepath: str) -> bool:
    """Validate if the image format is supported."""
    ext = os.path.splitext(filepath.lower())[1]
    return ext in SUPPORTED_FORMATS

def verify_stego_data(image_path: str) -> bool:
    """Verify if an image contains steganographic data."""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = list(img.getdata())
        
        # Calculate how many pixels we need for the marker
        marker_bits_needed = len(MAGIC_MARKER) * 8
        pixels_needed = (marker_bits_needed + 2) // 3  # Round up to nearest pixel
        
        # Get bits for the marker
        extracted_bits = ''
        for i in range(pixels_needed):
            r, g, b = pixels[i]
            extracted_bits += str(r & 1)
            extracted_bits += str(g & 1)
            extracted_bits += str(b & 1)
            
            if len(extracted_bits) >= marker_bits_needed:
                break
        
        # Trim to exact marker length
        marker_bits = extracted_bits[:marker_bits_needed]
        try:
            marker = bits_to_str(marker_bits)
            print(f"Debug - Found marker: {marker}")
            print(f"Debug - Raw marker bits: {marker_bits}")
            return marker == MAGIC_MARKER
        except Exception as e:
            print(f"Debug - Marker extraction failed: {str(e)}")
            print(f"Debug - Raw bits: {marker_bits}")
            return False
    except Exception as e:
        print(f"Debug - Image processing failed: {str(e)}")
        return False

class StegoManager:
    """Manager class for steganography operations."""
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        if self.plugin_manager:
            self.plugin_manager.execute_hook(HookPoint.STEGO_INIT.value, manager=self)
    
    def embed(self, image_path: str, data_path: str, output_path: str) -> str:
        """Embed data into an image."""
        try:
            validate_file(image_path)
            validate_file(data_path)
            
            print(f"\nDebug - Starting embedding process")
            print(f"Debug - Image: {image_path}")
            print(f"Debug - Data file: {data_path}")
            
            # Validate image format
            if not validate_image_format(image_path):
                raise SteganographyError(
                    "Unsupported image format. Supported formats: PNG, BMP, JPEG, TIFF, GIF"
                )
            
            # Read and prepare the image
            try:
                img = Image.open(image_path)
                print(f"Debug - Image format: {img.format}")
                print(f"Debug - Image mode: {img.mode}")
                
                # Special handling for GIF animations
                if img.format == 'GIF' and getattr(img, 'is_animated', False):
                    print("Note: For animated GIFs, only the first frame will be used.")
                    img.seek(0)
                
                img = img.convert('RGB')
                width, height = img.size
                pixels = list(img.getdata())
                print(f"Debug - Image dimensions: {width}x{height}")
                print(f"Debug - Total pixels: {len(pixels)}")
            except Exception as e:
                raise SteganographyError(f"Failed to process image: {str(e)}")
            
            # Generate output filename - always use PNG for output
            output_dir = os.path.dirname(output_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"stega_{timestamp}.png"  # Force PNG
            output_path = os.path.join(output_dir, output_name)
            
            # Prepare file data and extension
            _, ext = os.path.splitext(data_path)
            if not ext:
                ext = '.bin'  # Ensure we always have an extension
                
            # Read file data
            with open(data_path, 'rb') as f:
                file_data = f.read()
            
            print(f"Debug - File size: {len(file_data)} bytes")
            print(f"Debug - File extension: {ext}")
            
            # Convert marker to bits
            marker_bits = str_to_bits(MAGIC_MARKER)
            print(f"Debug - Marker bits length: {len(marker_bits)}")
            print(f"Debug - Marker bits: {marker_bits}")
            
            # Convert extension to bits
            ext_bits = str_to_bits(ext)
            ext_length_bits = int_to_bits(len(ext_bits), 32)
            print(f"Debug - Extension bits length: {len(ext_bits)}")
            
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
            
            print(f"Debug - Total embedding structure:")
            print(f"  - Marker: {len(marker_bits)} bits")
            print(f"  - Extension length: {len(ext_length_bits)} bits")
            print(f"  - Extension: {len(ext_bits)} bits")
            print(f"  - Data length: {len(data_length_bits)} bits")
            print(f"  - Data: {len(data_bits)} bits")
            print(f"  - Total: {len(all_bits)} bits")
            
            # Check if image is large enough
            available_bits = len(pixels) * 3
            print(f"Debug - Available bits in image: {available_bits}")
            if len(all_bits) > available_bits:
                raise SteganographyError(
                    f"Image too small. Needs {len(all_bits)} bits but only has {available_bits} available."
                )
            
            # Embed data
            new_pixels = []
            bit_index = 0
            total_bits = len(all_bits)
            
            for i in range(len(pixels)):
                r, g, b = pixels[i]
                new_r, new_g, new_b = r, g, b
                
                # Modify each color channel if we still have bits to embed
                if bit_index < total_bits:
                    new_r = (r & ~1) | int(all_bits[bit_index])
                    bit_index += 1
                    
                if bit_index < total_bits:
                    new_g = (g & ~1) | int(all_bits[bit_index])
                    bit_index += 1
                    
                if bit_index < total_bits:
                    new_b = (b & ~1) | int(all_bits[bit_index])
                    bit_index += 1
                
                new_pixels.append((new_r, new_g, new_b))
                
                if bit_index >= total_bits:
                    # Add remaining pixels unchanged
                    new_pixels.extend(pixels[i+1:])
                    break
                
                if bit_index % 1000000 == 0:
                    log_progress(bit_index, total_bits)
            
            # Add remaining pixels unchanged
            new_pixels.extend(pixels[len(new_pixels):])
            
            # Create and save new image as PNG
            new_img = Image.new('RGB', (width, height))
            new_img.putdata(new_pixels)
            new_img.save(output_path, 'PNG', optimize=False, compress_level=0)
            
            # Verify the embedding
            print("\nDebug - Verifying embedded data...")
            if verify_stego_data(output_path):
                print("Debug - Verification successful!")
            else:
                print("Debug - WARNING: Verification failed!")
            
            print(f"Successfully embedded {len(file_data)} bytes with extension {ext}")
            return output_path
            
        except Exception as e:
            raise SteganographyError(f"Failed to embed data: {str(e)}")
    
    def extract(self, image_path: str, output_path: str) -> str:
        """Extract data from an image."""
        try:
            validate_file(image_path)
            
            print(f"\nDebug - Starting extraction process")
            print(f"Debug - Image: {image_path}")
            
            # Validate image format
            if not validate_image_format(image_path):
                raise SteganographyError(
                    "Unsupported image format. Supported formats: PNG, BMP, JPEG, TIFF, GIF"
                )
            
            # Read the image
            try:
                img = Image.open(image_path)
                print(f"Debug - Image format: {img.format}")
                print(f"Debug - Image mode: {img.mode}")
                
                if img.format == 'GIF' and getattr(img, 'is_animated', False):
                    img.seek(0)  # Use first frame for animated GIFs
                    
                img = img.convert('RGB')
                pixels = list(img.getdata())
                available_bits = len(pixels) * 3  # Total available bits
                print(f"Debug - Total pixels: {len(pixels)}")
                print(f"Debug - Available bits: {available_bits}")
            except Exception as e:
                raise SteganographyError(f"Failed to process image: {str(e)}")
            
            # Extract initial bits
            extracted_bits = ''
            marker_length = len(MAGIC_MARKER) * 8
            min_header_bits = marker_length + 32  # Marker + ext length
            pixels_needed = (min_header_bits + 2) // 3  # Round up to nearest pixel
            
            print(f"Debug - Extracting initial {min_header_bits} bits from {pixels_needed} pixels")
            
            for i in range(pixels_needed):
                if i >= len(pixels):
                    raise SteganographyError("Image too small to contain valid data")
                r, g, b = pixels[i]
                extracted_bits += str(r & 1)
                extracted_bits += str(g & 1)
                extracted_bits += str(b & 1)
                
                if len(extracted_bits) >= min_header_bits:
                    break
                    
            print(f"Debug - Extracted {len(extracted_bits)} initial bits")
            print(f"Debug - First {min_header_bits} bits: {extracted_bits[:min_header_bits]}")
            
            # Verify magic marker
            marker_bits = extracted_bits[:marker_length]
            try:
                marker = bits_to_str(marker_bits)
                print(f"Debug - Found marker: {marker}")
                print(f"Debug - Raw marker bits: {marker_bits}")
                if marker != MAGIC_MARKER:
                    print(f"Debug - Invalid marker found: {marker}, expected: {MAGIC_MARKER}")
                    raise SteganographyError("No hidden data found (Invalid marker)")
            except Exception as e:
                print(f"Debug - Marker extraction failed: {str(e)}")
                print(f"Debug - First {len(marker_bits)} bits: {marker_bits}")
                raise SteganographyError("No hidden data found")
            
            current_pos = marker_length
            
            # Read extension length
            ext_length_bits = extracted_bits[current_pos:current_pos + 32]
            ext_length = bits_to_int(ext_length_bits)
            print(f"Debug - Extension length: {ext_length} bits")
            if ext_length > 256:  # Reasonable maximum extension length
                raise SteganographyError("Invalid extension length")
            current_pos += 32
            
            # Extract more bits if needed for extension
            while len(extracted_bits) < current_pos + ext_length:
                pixel_index = len(extracted_bits) // 3
                if pixel_index >= len(pixels):
                    raise SteganographyError("Unexpected end of image data")
                r, g, b = pixels[pixel_index]
                extracted_bits += str(r & 1)
                extracted_bits += str(g & 1)
                extracted_bits += str(b & 1)
            
            # Read extension
            ext_bits = extracted_bits[current_pos:current_pos + ext_length]
            try:
                extension = bits_to_str(ext_bits)
                print(f"Debug - Found extension: {extension}")
                if not extension.startswith('.'):
                    print("Debug - Invalid extension format, using .bin")
                    extension = '.bin'
            except Exception:
                print("Debug - Failed to extract extension, using .bin")
                extension = '.bin'
            current_pos += ext_length
            
            # Make sure we have enough bits for data length
            while len(extracted_bits) < current_pos + 32:
                pixel_index = len(extracted_bits) // 3
                if pixel_index >= len(pixels):
                    raise SteganographyError("Unexpected end of image data")
                r, g, b = pixels[pixel_index]
                extracted_bits += str(r & 1)
                extracted_bits += str(g & 1)
                extracted_bits += str(b & 1)
            
            # Read data length
            data_length_bits = extracted_bits[current_pos:current_pos + 32]
            data_length = bits_to_int(data_length_bits)
            print(f"Debug - Data length: {data_length} bytes")
            current_pos += 32
            
            # Validate data length
            required_bits = current_pos + (data_length * 8)
            if required_bits > available_bits:
                raise SteganographyError(
                    f"Data length ({data_length} bytes) exceeds available capacity "
                    f"({(available_bits - current_pos) // 8} bytes)"
                )
            
            # Extract data bits
            print("Debug - Extracting data bits...")
            needed_pixels = (required_bits + 2) // 3  # Round up to nearest pixel
            for pixel_index in range(len(extracted_bits) // 3, needed_pixels):
                if pixel_index >= len(pixels):
                    raise SteganographyError("Unexpected end of image data")
                r, g, b = pixels[pixel_index]
                extracted_bits += str(r & 1)
                extracted_bits += str(g & 1)
                extracted_bits += str(b & 1)
                
                if pixel_index % 100000 == 0:
                    progress = (len(extracted_bits) / required_bits) * 100
                    log_progress(progress, 100)
            
            # Extract data bytes
            data_bits = extracted_bits[current_pos:current_pos + (data_length * 8)]
            try:
                data = bytes(bits_to_int(data_bits[i:i+8]) 
                           for i in range(0, len(data_bits), 8))
                print(f"Debug - Successfully converted {len(data)} bytes of data")
            except Exception as e:
                print(f"Debug - Failed to convert data bits: {str(e)}")
                raise SteganographyError(f"Failed to convert data bits: {str(e)}")
            
            # Generate output filename
            output_dir = os.path.dirname(output_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"extracted_{timestamp}{extension}"
            final_output = os.path.join(output_dir, output_name)
            
            # Save extracted data
            try:
                with open(final_output, 'wb') as f:
                    f.write(data)
                print(f"Debug - Successfully wrote {len(data)} bytes to {final_output}")
            except Exception as e:
                print(f"Debug - Failed to save extracted data: {str(e)}")
                raise SteganographyError(f"Failed to save extracted data: {str(e)}")
            
            return final_output
            
        except SteganographyError:
            raise
        except Exception as e:
            raise SteganographyError(f"Failed to extract data: {str(e)}")

# Global manager instance
stego_manager = None

def init_stego_manager(plugin_manager=None):
    """Initialize global steganography manager."""
    global stego_manager
    stego_manager = StegoManager(plugin_manager)
    return stego_manager

# Global function wrappers
def embed_in_image(image_path: str, data_path: str, output_path: str) -> str:
    """Global embed function."""
    if not stego_manager:
        raise RuntimeError("Stego manager not initialized")
    return stego_manager.embed(image_path, data_path, output_path)

def extract_from_image(image_path: str, output_path: str) -> str:
    """Global extract function."""
    if not stego_manager:
        raise RuntimeError("Stego manager not initialized")
    return stego_manager.extract(image_path, output_path)