# StegeCrypt

A secure file encryption and steganography tool built with Python. StegeCrypt allows you to encrypt files using AES-256 encryption and hide data within images using steganographic techniques.

## Features

- AES-256 encryption for secure file protection
- Steganography support for hiding data in images
- Intuitive GUI interface with drag & drop support
- Batch processing capabilities
- Key file generation
- Support for both text and image key files
- Progress tracking and detailed status updates

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stegecrypt.git
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode
```bash
python main.py
```

### CLI Mode
```bash
# Encrypt a file
python cli_interface.py encrypt -i <input_file> -k <key_file> -o <output_file>

# Decrypt a file
python cli_interface.py decrypt -i <encrypted_file> -k <key_file> -o <output_file>

# Embed data in image
python cli_interface.py embed -im <image_file> -d <data_file> -o <output_image>

# Extract data from image
python cli_interface.py extract -im <image_file> -o <output_file>
```

## Supported File Types
- Encryption: Any file type
- Key files: .txt, .png, .jpg, .jpeg
- Encrypted files: .stegecrypt
- Steganography carrier images: .png

## Requirements
- Python 3.8+
- cryptography>=41.0.7
- pillow>=10.2.0
- numpy>=1.26.3
- tkinterdnd2>=0.3.0

## Security Features
- AES-256 encryption
- Secure key generation
- File integrity verification
- Custom encrypted file format

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
