# StegeCrypt Commands Guide

## Installation
```bash
pip install -r requirements.txt
```

## Basic Usage

### GUI Mode
```bash
python main.py
```

### CLI Mode Commands

#### 1. Encrypt File
```bash
python cli_interface.py encrypt -i <input_file> -k <key_file> -o <output_file>
```
- `-i`: Input file to encrypt
- `-k`: Key file (text/image)
- `-o`: Output encrypted file (.stegecrypt)

Example:
```bash
python cli_interface.py encrypt -i secret.txt -k mykey.txt -o secret.stegecrypt
```

#### 2. Decrypt File
```bash
python cli_interface.py decrypt -i <encrypted_file> -k <key_file> -o <output_file>
```
- `-i`: Encrypted file (.stegecrypt)
- `-k`: Same key file used for encryption
- `-o`: Output decrypted file

Example:
```bash
python cli_interface.py decrypt -i secret.stegecrypt -k mykey.txt -o decrypted_secret.txt
```

#### 3. Embed Data in Image
```bash
python cli_interface.py embed -im <image_file> -d <data_file> -o <output_image>
```
- `-im`: Input image
- `-d`: Data file to embed
- `-o`: Output image with embedded data

Example:
```bash
python cli_interface.py embed -im carrier.png -d secret.stegecrypt -o output.png
```

#### 4. Extract Data from Image
```bash
python cli_interface.py extract -im <image_file> -o <output_file>
```
- `-im`: Image containing embedded data
- `-o`: Output file for extracted data

Example:
```bash
python cli_interface.py extract -im output.png -o extracted.stegecrypt
```

## Supported File Types
- Input files: Any file type
- Key files: .txt, .png, .jpg, .jpeg
- Encrypted files: .stegecrypt
- Carrier images: .png
