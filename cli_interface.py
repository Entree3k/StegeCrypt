import argparse
import os
from core.aes_crypt import encrypt_file, decrypt_file
from core.steganography import embed_in_image, extract_from_image

def encrypt(args):
    encrypt_file(args.input, args.key, args.output)
    print(f"Encryption complete! Output file: {args.output}")

def decrypt(args):
    decrypt_file(args.input, args.key, args.output)
    print(f"Decryption complete! Output file: {args.output}")

def embed(args):
    embed_in_image(args.image, args.data, args.output)
    print(f"Data embedded successfully! Output image: {args.output}")

def extract(args):
    extract_from_image(args.image, args.output)
    print(f"Data extracted successfully! Output file: {args.output}")

def main():
    parser = argparse.ArgumentParser(
        description="Encrypt and decrypt files using AES-256 and steganography"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file")
    encrypt_parser.add_argument("-i", "--input", required=True, help="Path to input file")
    encrypt_parser.add_argument("-k", "--key", required=True, help="Path to key file (text or image)")
    encrypt_parser.add_argument("-o", "--output", required=True, help="Path to save the encrypted file")
    encrypt_parser.set_defaults(func=encrypt)

    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a file")
    decrypt_parser.add_argument("-i", "--input", required=True, help="Path to encrypted file")
    decrypt_parser.add_argument("-k", "--key", required=True, help="Path to key file (text or image)")
    decrypt_parser.add_argument("-o", "--output", required=True, help="Path to save the decrypted file")
    decrypt_parser.set_defaults(func=decrypt)

    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Embed data into an image")
    embed_parser.add_argument("-im", "--image", required=True, help="Path to image file")
    embed_parser.add_argument("-d", "--data", required=True, help="Path to data file (encrypted)")
    embed_parser.add_argument("-o", "--output", required=True, help="Path to save the output image")
    embed_parser.set_defaults(func=embed)

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract data from an image")
    extract_parser.add_argument("-im", "--image", required=True, help="Path to image file")
    extract_parser.add_argument("-o", "--output", required=True, help="Path to save the extracted data")
    extract_parser.set_defaults(func=extract)

    # Parse arguments and call appropriate function
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
