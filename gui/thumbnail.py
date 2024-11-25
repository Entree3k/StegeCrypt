import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from .material_colors import MaterialColors
import os

class ImageThumbnail(ttk.Frame):
    """Thumbnail widget for displaying image previews."""
    
    def __init__(self, parent, image_path: str, size=(150, 150), **kwargs):
        super().__init__(parent, **kwargs)
        
        self.image_path = image_path
        self.size = size
        self.is_selected = False
        
        # Configure frame
        self.configure(
            padding=5,
            style='Thumbnail.TFrame'
        )
        
        # Create thumbnail
        self.thumbnail = self.create_thumbnail()
        
        # Create image container
        self.image_container = ttk.Frame(
            self,
            style='ThumbnailImage.TFrame'
        )
        self.image_container.pack(pady=2)
        
        self.image_label = ttk.Label(
            self.image_container,
            image=self.thumbnail,
            style='Thumbnail.TLabel'
        )
        self.image_label.image = self.thumbnail  # Prevent garbage collection
        self.image_label.pack()
        
        # Create filename label
        filename = os.path.basename(image_path)
        if len(filename) > 20:
            filename = filename[:17] + "..."
            
        self.name_label = ttk.Label(
            self,
            text=filename,
            wraplength=140,
            justify='center',
            style='ThumbnailText.TLabel'
        )
        self.name_label.pack(pady=(2, 0))
        
        # Bind events
        self.bind('<Enter>', self.on_hover)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
        
        # Bind children events
        for child in [self.image_label, self.name_label]:
            child.bind('<Enter>', self.on_hover)
            child.bind('<Leave>', self.on_leave)
            child.bind('<Button-1>', self.on_click)
    
    def create_thumbnail(self) -> ImageTk.PhotoImage:
        """Create a thumbnail of the image."""
        try:
            with Image.open(self.image_path) as img:
                img.thumbnail(self.size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception:
            # Create placeholder for invalid/unreadable images
            placeholder = Image.new('RGB', self.size, color='gray')
            return ImageTk.PhotoImage(placeholder)
    
    def on_hover(self, event=None):
        """Handle mouse hover."""
        if not self.is_selected:
            self.configure(style='ThumbnailHover.TFrame')
    
    def on_leave(self, event=None):
        """Handle mouse leave."""
        if not self.is_selected:
            self.configure(style='Thumbnail.TFrame')
    
    def on_click(self, event=None):
        """Handle click event."""
        self.toggle_selection()
        # Propagate click event
        self.event_generate('<<ThumbnailSelected>>')
    
    def toggle_selection(self):
        """Toggle selection state."""
        self.is_selected = not self.is_selected
        if self.is_selected:
            self.configure(style='ThumbnailSelected.TFrame')
        else:
            self.configure(style='Thumbnail.TFrame')
    
    @staticmethod
    def setup_styles():
        """Configure ttk styles for thumbnails."""
        style = ttk.Style()
        
        # Frame styles
        style.configure(
            'Thumbnail.TFrame',
            background=MaterialColors.SURFACE
        )
        style.configure(
            'ThumbnailHover.TFrame',
            background=MaterialColors.HOVER
        )
        style.configure(
            'ThumbnailSelected.TFrame',
            background=MaterialColors.SELECTED
        )
        style.configure(
            'ThumbnailImage.TFrame',
            background=MaterialColors.SURFACE
        )
        
        # Label styles
        style.configure(
            'Thumbnail.TLabel',
            background=MaterialColors.SURFACE
        )
        style.configure(
            'ThumbnailText.TLabel',
            background=MaterialColors.SURFACE,
            font=('Helvetica', 9),
            foreground=MaterialColors.TEXT_SECONDARY
        )