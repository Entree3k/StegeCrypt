import argparse
import os
import logging
from core.aes_crypt import encrypt_file, decrypt_file
from core.steganography import embed_in_image, extract_from_image
from plugin_base import HookPoint

class CLIInterface:
    """CLI interface with plugin support."""
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        
        # Execute CLI initialization hook
        if self.plugin_manager:
            self.plugin_manager.execute_hook(
                HookPoint.CLI_INIT.value,
                interface=self
            )
    
    def encrypt(self, args):
        """Handle encryption command."""
        try:
            # Execute pre-encrypt hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.PRE_ENCRYPT.value,
                    input_file=args.input,
                    key_file=args.key,
                    output_file=args.output
                )
            
            # Perform encryption
            encrypt_file(args.input, args.key, args.output)
            
            # Execute post-encrypt hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_ENCRYPT.value,
                    input_file=args.input,
                    output_file=args.output,
                    success=True
                )
            
            print(f"Encryption complete! Output file: {args.output}")
            
        except Exception as e:
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_ENCRYPT.value,
                    input_file=args.input,
                    error=str(e),
                    success=False
                )
            logging.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, args):
        """Handle decryption command."""
        try:
            # Execute pre-decrypt hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.PRE_DECRYPT.value,
                    input_file=args.input,
                    key_file=args.key,
                    output_file=args.output
                )
            
            # Perform decryption
            decrypt_file(args.input, args.key, args.output)
            
            # Execute post-decrypt hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_DECRYPT.value,
                    input_file=args.input,
                    output_file=args.output,
                    success=True
                )
            
            print(f"Decryption complete! Output file: {args.output}")
            
        except Exception as e:
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_DECRYPT.value,
                    input_file=args.input,
                    error=str(e),
                    success=False
                )
            logging.error(f"Decryption failed: {str(e)}")
            raise
    
    def embed(self, args):
        """Handle embed command."""
        try:
            # Execute pre-embed hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.PRE_EMBED.value,
                    image_file=args.image,
                    data_file=args.data,
                    output_file=args.output
                )
            
            # Perform embedding
            embed_in_image(args.image, args.data, args.output)
            
            # Execute post-embed hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_EMBED.value,
                    image_file=args.image,
                    data_file=args.data,
                    output_file=args.output,
                    success=True
                )
            
            print(f"Data embedded successfully! Output image: {args.output}")
            
        except Exception as e:
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_EMBED.value,
                    image_file=args.image,
                    data_file=args.data,
                    error=str(e),
                    success=False
                )
            logging.error(f"Embedding failed: {str(e)}")
            raise
    
    def extract(self, args):
        """Handle extract command."""
        try:
            # Execute pre-extract hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.PRE_EXTRACT.value,
                    image_file=args.image,
                    output_file=args.output
                )
            
            # Perform extraction
            extract_from_image(args.image, args.output)
            
            # Execute post-extract hook
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_EXTRACT.value,
                    image_file=args.image,
                    output_file=args.output,
                    success=True
                )
            
            print(f"Data extracted successfully! Output file: {args.output}")
            
        except Exception as e:
            if self.plugin_manager:
                self.plugin_manager.execute_hook(
                    HookPoint.POST_EXTRACT.value,
                    image_file=args.image,
                    error=str(e),
                    success=False
                )
            logging.error(f"Extraction failed: {str(e)}")
            raise

def main(plugin_manager=None):
    """Main CLI entry point."""
    cli = CLIInterface(plugin_manager)
    
    parser = argparse.ArgumentParser(
        description="Encrypt and decrypt files using AES-256 and steganography"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file")
    encrypt_parser.add_argument("-i", "--input", required=True, help="Path to input file")
    encrypt_parser.add_argument("-k", "--key", required=True, help="Path to key file (text or image)")
    encrypt_parser.add_argument("-o", "--output", required=True, help="Path to save the encrypted file")
    encrypt_parser.set_defaults(func=cli.encrypt)

    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a file")
    decrypt_parser.add_argument("-i", "--input", required=True, help="Path to encrypted file")
    decrypt_parser.add_argument("-k", "--key", required=True, help="Path to key file (text or image)")
    decrypt_parser.add_argument("-o", "--output", required=True, help="Path to save the decrypted file")
    decrypt_parser.set_defaults(func=cli.decrypt)

    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Embed data into an image")
    embed_parser.add_argument("-im", "--image", required=True, help="Path to image file")
    embed_parser.add_argument("-d", "--data", required=True, help="Path to data file (encrypted)")
    embed_parser.add_argument("-o", "--output", required=True, help="Path to save the output image")
    embed_parser.set_defaults(func=cli.embed)

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract data from an image")
    extract_parser.add_argument("-im", "--image", required=True, help="Path to image file")
    extract_parser.add_argument("-o", "--output", required=True, help="Path to save the extracted data")
    extract_parser.set_defaults(func=cli.extract)

    # Let plugins add their own commands
    if plugin_manager:
        plugin_manager.execute_hook(
            HookPoint.CLI_INIT.value,
            parser=parser,
            subparsers=subparsers
        )

    # Parse arguments and call appropriate function
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()