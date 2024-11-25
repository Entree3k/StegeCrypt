import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import os
import logging
from io import BytesIO
import tempfile
from gui.components.image_viewer import ImageViewer
from gui.components.video_player import VideoPlayer
from gui.material_colors import MaterialColors

class ThumbnailManager:
    def __init__(self, gallery):
        self.gallery = gallery
        self.thumbnail_size = (150, 150)
        Image.MAX_IMAGE_PIXELS = None
        
        # Define supported file types
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        
        # Video signatures for file type detection
        self.video_signatures = {
            b'ftyp',  # MP4
            b'RIFF',  # AVI
            b'\x1aE\xdf\xa3',  # MKV
            b'movi'  # AVI alternate
        }
    
    def create_thumbnail_frame(self, filepath, filename):
        """Create a thumbnail frame for a file."""
        frame = ttk.Frame(
            self.gallery.ui.gallery_frame,
            style='Thumbnail.TFrame',
            padding=10
        )
        
        try:
            logging.info(f"Creating thumbnail for {filename}")
            
            # Normalize file path
            filepath = os.path.normpath(os.path.join(self.gallery.current_directory, filename))
            
            # Try to decrypt the file
            decrypted_path = self.gallery.file_manager.decrypt_file(
                filepath,
                self.gallery.key_file,
                self.gallery.temp_manager.get_temp_path()
            )
            
            if decrypted_path:
                # Get secure handle
                secure_handle = self.gallery.temp_manager.get_secure_handle(decrypted_path)
                if not secure_handle:
                    raise Exception("Failed to get secure handle")
                
                # Read decrypted data
                decrypted_data = secure_handle.read()
                if not decrypted_data:
                    raise Exception("Failed to read decrypted data")
                
                # Try to determine file type from decrypted data
                file_type = self.determine_file_type_from_data(decrypted_data)
                
                if file_type == 'video':
                    self.create_video_thumbnail(frame, decrypted_data, filepath)
                elif file_type == 'image':
                    self.create_image_thumbnail(frame, decrypted_data, filepath)
                else:
                    self.create_error_thumbnail(frame, "Unsupported file type")
            else:
                self.create_error_thumbnail(frame, "Decryption failed")
            
        except Exception as e:
            logging.error(f"Failed to process {filename}: {str(e)}")
            self.create_error_thumbnail(frame, str(e))
        
        # Add filename
        if len(filename) > 20:
            filename = filename[:17] + "..."
        ttk.Label(
            frame,
            text=filename,
            background=MaterialColors.SURFACE,
            style='Thumbnail.TLabel'
        ).pack(pady=(5, 0))
        
        return frame
    
    def determine_file_type_from_data(self, data):
        """Determine if data is an image or video."""
        try:
            # Try to open as image first
            Image.open(BytesIO(data))
            return 'image'
        except Exception:
            # Check video signatures
            header = data[:20]
            for sig in self.video_signatures:
                if sig in header:
                    return 'video'
            # Try to read with OpenCV as last resort
            try:
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    temp_file.write(data)
                    temp_file.flush()
                    cap = cv2.VideoCapture(temp_file.name)
                    is_video = cap.isOpened()
                    cap.release()
                    os.unlink(temp_file.name)
                    if is_video:
                        return 'video'
            except:
                pass
            return 'unknown'
    
    def create_video_thumbnail(self, frame, video_data, original_path):
        """Create video thumbnail with play button overlay."""
        try:
            # Create temporary file for video data
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                logging.info(f"Creating temporary video file for thumbnail")
                temp_video.write(video_data)
                temp_video.flush()
                
                # Open video file
                cap = cv2.VideoCapture(temp_video.name)
                if not cap.isOpened():
                    raise Exception("Could not open video file")
                
                try:
                    # Get total frames
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    if total_frames > 0:
                        # Try to get frame from 25% into video
                        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 4)
                    
                    ret, frame_img = cap.read()
                    if not ret:
                        raise Exception("Could not read video frame")
                    
                    # Process video frame
                    frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                    height, width = frame_img.shape[:2]
                    ratio = min(self.thumbnail_size[0]/width, self.thumbnail_size[1]/height)
                    new_size = (int(width * ratio), int(height * ratio))
                    frame_img = cv2.resize(frame_img, new_size)
                    
                    # Convert to PhotoImage
                    image = Image.fromarray(frame_img)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Create thumbnail container
                    container = ttk.Frame(frame, style='Thumbnail.TFrame')
                    container.pack(pady=5)
                    
                    # Create image label
                    img_label = ttk.Label(
                        container,
                        image=photo,
                        style='Thumbnail.TLabel'
                    )
                    img_label.image = photo  # Keep reference
                    img_label.pack()
                    
                    # Add play overlay
                    play_overlay = ttk.Label(
                        container,
                        text="▶",
                        font=('Helvetica', 24),
                        foreground='white',
                        background='black'
                    )
                    play_overlay.place(relx=0.5, rely=0.5, anchor='center')
                    
                    # Bind click events
                    for widget in (container, img_label, play_overlay):
                        widget.bind(
                            '<Button-1>',
                            lambda e, p=original_path: self.gallery.event_handlers.view_media(p)
                        )
                        
                finally:
                    cap.release()
                    
            # Clean up temporary file
            try:
                os.unlink(temp_video.name)
            except:
                pass
                
        except Exception as e:
            logging.error(f"Error creating video thumbnail: {e}")
            self.create_error_thumbnail(frame, "Video thumbnail error")
    
    def create_image_thumbnail(self, frame, image_data, original_path):
        """Create image thumbnail with click handling."""
        try:
            # Open image from bytes
            img = Image.open(BytesIO(image_data))
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = ttk.Label(
                frame,
                image=photo,
                style='Thumbnail.TLabel'
            )
            label.image = photo  # Keep reference
            label.pack(pady=(0, 5))
            label.bind(
                '<Button-1>',
                lambda e, p=original_path: self.gallery.event_handlers.view_media(p)
            )
        except Exception as e:
            logging.error(f"Error creating image thumbnail: {e}")
            self.create_error_thumbnail(frame, "Image thumbnail error")
    
    def create_error_thumbnail(self, frame, error_text="Error"):
        """Create an error thumbnail."""
        ttk.Label(
            frame,
            text="❌",
            font=('Helvetica', 32),
            background=MaterialColors.SURFACE,
            style='Thumbnail.TLabel'
        ).pack(pady=10)
        
        # Add error text
        ttk.Label(
            frame,
            text=error_text,
            background=MaterialColors.SURFACE,
            style='Thumbnail.TLabel',
            wraplength=140
        ).pack(pady=(0, 5))
    
    def clear_cache(self):
        """Clear any cached thumbnails."""
        pass
        
    def __del__(self):
        """Cleanup on deletion."""
        logging.debug("ThumbnailManager cleanup")