import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
from gui.material_colors import MaterialColors
import threading
import time
import math
import logging

class ImageViewer(tk.Toplevel):
    """Image viewer window with zooming and panning capabilities."""
    def __init__(self, parent, file_path):
        """Initialize the image viewer."""
        super().__init__(parent)
        self.title("Image Viewer")
        self.withdraw()  # Hide window while loading
        
        # Store parent and file path
        self.parent = parent
        self.file_path = file_path
        
        # Initialize variables
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_speed = 0.8
        self.zoom_acceleration = 1.2
        self.last_zoom_time = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.animation_active = False
        self.consecutive_zooms = 0
        self.zoom_direction = 0
        self.image_cache = {}
        
        try:
            logging.info("Initializing ImageViewer...")
            
            # Get secure handle from parent's file manager
            secure_handle = parent.file_manager.get_decrypted_file(file_path)
            if not secure_handle:
                raise Exception("Failed to get secure file handle")
            
            # Read image data
            image_data = secure_handle.read()
            if not image_data:
                raise Exception("Failed to read image data")
            
            # Load image
            self.load_image(image_data)
            
            # Show window
            self.deiconify()
            
            # Run viewer creation hook for plugins
            if hasattr(self.parent, 'plugin_manager') and self.parent.plugin_manager:
                logging.info("Running viewer_created hook...")
                self.parent.plugin_manager.run_hook('viewer_created', self, file_path)
                logging.info("viewer_created hook completed")
            else:
                logging.warning("No plugin manager available for viewer_created hook")
            
        except Exception as e:
            logging.error(f"Failed to load image: {e}")
            messagebox.showerror("Error", str(e))
            self.destroy()
            return
    
    def load_image(self, image_data):
        """Load image from bytes."""
        try:
            # Set PIL to handle large images
            Image.MAX_IMAGE_PIXELS = None
            
            # Load image from bytes
            self.original_image = Image.open(BytesIO(image_data))
            
            # Calculate initial window size
            screen_width = self.winfo_screenwidth() * 0.8
            screen_height = self.winfo_screenheight() * 0.8
            
            # Calculate initial scale to fit screen
            width_ratio = screen_width / self.original_image.width
            height_ratio = screen_height / self.original_image.height
            self.initial_zoom = min(width_ratio, height_ratio)
            self.zoom_level = self.initial_zoom
            self.target_zoom = self.initial_zoom
            
            # Store original dimensions
            self.orig_width = self.original_image.width
            self.orig_height = self.original_image.height
            
            # Create UI components
            self.setup_ui()
            
            # Display initial image
            self.update_image()
            
            # Center window
            self.center_window()
            
            # Make window modal
            self.transient(self.master)
            self.grab_set()
            
            # Bind cleanup
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            raise Exception(f"Failed to load image: {e}")
    
    def setup_ui(self):
        """Setup UI components."""
        logging.info("Setting up ImageViewer UI...")
        # Configure window style
        self.configure(bg=MaterialColors.BACKGROUND)
        
        # Create main container
        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True)
        
        # Create control frame for plugins FIRST
        self.control_frame = ttk.Frame(
            self,
            style='Gallery.TFrame',
            padding=5
        )
        self.control_frame.pack(side='top', fill='x')
        logging.info("Created control frame for plugins")
        # Create canvas for image
        self.canvas = tk.Canvas(
            self.container,
            bg=MaterialColors.BACKGROUND,
            highlightthickness=0,
            xscrollincrement=1,
            yscrollincrement=1
        )
        
        # Create scrollbars
        self.h_scroll = ttk.Scrollbar(
            self.container,
            orient='horizontal',
            command=self.canvas.xview
        )
        self.v_scroll = ttk.Scrollbar(
            self.container,
            orient='vertical',
            command=self.canvas.yview
        )
        
        # Configure canvas scrolling
        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )
        
        # Pack scrollbars and canvas
        self.h_scroll.pack(side='bottom', fill='x')
        self.v_scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Add status bar
        self.status_bar = ttk.Label(
            self,
            text="Zoom: 100%",
            style='Status.TLabel',
            padding=(5, 2)
        )
        self.status_bar.pack(side='bottom', fill='x')
        
        # Create image on canvas
        self.canvas_image = self.canvas.create_image(
            0, 0,
            anchor='nw',
            tags='image'
        )
        
        # Bind events
        self.bind_events()
    
    def bind_events(self):
        """Bind all event handlers."""
        # Mouse wheel for zooming
        self.bind_all('<MouseWheel>', self.on_mousewheel)       # Windows
        self.bind_all('<Button-4>', self.on_mousewheel)         # Linux scroll up
        self.bind_all('<Button-5>', self.on_mousewheel)         # Linux scroll down
        
        # Mouse events for panning
        self.canvas.bind('<Button-1>', self.start_pan)
        self.canvas.bind('<B1-Motion>', self.pan_image)
        self.canvas.bind('<ButtonRelease-1>', self.stop_pan)
        
        # Mouse position tracking
        self.canvas.bind('<Motion>', self.update_mouse_position)
        
        # Key bindings
        self.bind('<Escape>', lambda e: self.on_closing())
        self.bind('<Control-plus>', lambda e: self.zoom_in())
        self.bind('<Control-minus>', lambda e: self.zoom_out())
        self.bind('<Control-0>', lambda e: self.reset_zoom())
    
    def update_mouse_position(self, event):
        """Track mouse position for centered zooming."""
        self.mouse_x = self.canvas.canvasx(event.x)
        self.mouse_y = self.canvas.canvasy(event.y)
    
    def start_pan(self, event):
        """Start image panning."""
        self.is_panning = True
        self.canvas.config(cursor="fleur")
        self.pan_x = event.x
        self.pan_y = event.y
    
    def pan_image(self, event):
        """Pan the image."""
        if self.is_panning:
            dx = self.pan_x - event.x
            dy = self.pan_y - event.y
            
            self.canvas.xview_scroll(dx, 'units')
            self.canvas.yview_scroll(dy, 'units')
            
            self.pan_x = event.x
            self.pan_y = event.y
    
    def stop_pan(self, event):
        """Stop image panning."""
        self.is_panning = False
        self.canvas.config(cursor="")
    
    def smooth_zoom(self):
        """Animate zoom smoothly."""
        if abs(self.zoom_level - self.target_zoom) > 0.001:
            # Calculate zoom interpolation with acceleration
            speed = self.zoom_speed * (1 + (self.consecutive_zooms * 0.1))
            diff = self.target_zoom - self.zoom_level
            step = diff * speed
            
            # Apply the zoom change
            self.zoom_level += step
            
            # Update image
            self.update_image(True)
            
            # Schedule next frame
            self.after(10, self.smooth_zoom)
        else:
            self.zoom_level = self.target_zoom
            self.animation_active = False
            self.consecutive_zooms = 0
            self.update_image()
            
            # Clear image cache if it's too large
            if len(self.image_cache) > 10:
                self.image_cache.clear()
    
    def update_image(self, from_animation=False):
        """Update the displayed image with current zoom level."""
        try:
            # Calculate new size
            new_width = int(self.orig_width * self.zoom_level)
            new_height = int(self.orig_height * self.zoom_level)
            
            # Get visible area of canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate scroll center points
            if not from_animation:
                self.scroll_center_x = self.mouse_x / canvas_width
                self.scroll_center_y = self.mouse_y / canvas_height
            
            # Check cache for resized image
            cache_key = (new_width, new_height)
            if cache_key in self.image_cache:
                self.photo = self.image_cache[cache_key]
            else:
                # Resize image using appropriate resampling
                if self.zoom_level < 1.0:
                    resample = Image.Resampling.LANCZOS
                else:
                    resample = Image.Resampling.NEAREST
                
                resized_image = self.original_image.resize(
                    (new_width, new_height),
                    resample
                )
                
                # Convert to PhotoImage and cache
                self.photo = ImageTk.PhotoImage(resized_image)
                self.image_cache[cache_key] = self.photo
            
            # Update canvas
            self.canvas.itemconfig(self.canvas_image, image=self.photo)
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            
            # Center on zoom point
            if not from_animation:
                visible_width = min(canvas_width, new_width)
                visible_height = min(canvas_height, new_height)
                
                x_scroll = max(0, (new_width - visible_width) * self.scroll_center_x)
                y_scroll = max(0, (new_height - visible_height) * self.scroll_center_y)
                
                self.canvas.xview_moveto(x_scroll / new_width)
                self.canvas.yview_moveto(y_scroll / new_height)
            
            # Update status bar
            zoom_percent = int(self.zoom_level * 100)
            self.status_bar.configure(text=f"Zoom: {zoom_percent}%")
            
        except Exception as e:
            logging.error(f"Error updating image: {e}")
    
    def on_mousewheel(self, event):
        """Handle mouse wheel events for zooming."""
        if event.widget is not self.canvas:
            return "break"
        
        # Calculate zoom factor based on wheel direction
        current_time = time.time()
        
        if event.num == 5 or event.delta < 0:
            factor = 0.9  # Zoom out
            new_direction = -1
        else:
            factor = 1.1  # Zoom in
            new_direction = 1
        
        # Check for consecutive zooms
        if current_time - self.last_zoom_time < 0.2 and new_direction == self.zoom_direction:
            self.consecutive_zooms += 1
            factor = factor ** (1 + (self.consecutive_zooms * 0.1))
        else:
            self.consecutive_zooms = 0
            
        self.zoom_direction = new_direction
        self.last_zoom_time = current_time
        
        # Calculate new target zoom
        new_target = self.target_zoom * factor
        
        # Clamp zoom level
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, new_target))
        
        # Start smooth zoom animation
        if not self.animation_active:
            self.animation_active = True
            self.smooth_zoom()
        
        return "break"
    
    def zoom_in(self):
        """Zoom in by keyboard shortcut."""
        self.target_zoom = min(self.max_zoom, self.zoom_level * 1.1)
        if not self.animation_active:
            self.animation_active = True
            self.smooth_zoom()
    
    def zoom_out(self):
        """Zoom out by keyboard shortcut."""
        self.target_zoom = max(self.min_zoom, self.zoom_level * 0.9)
        if not self.animation_active:
            self.animation_active = True
            self.smooth_zoom()
    
    def reset_zoom(self):
        """Reset to initial zoom level."""
        self.target_zoom = self.initial_zoom
        if not self.animation_active:
            self.animation_active = True
            self.smooth_zoom()
    
    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        
        window_width = min(
            self.orig_width * self.initial_zoom + self.v_scroll.winfo_width(),
            self.winfo_screenwidth() * 0.8
        )
        window_height = min(
            self.orig_height * self.initial_zoom + self.h_scroll.winfo_height(),
            self.winfo_screenheight() * 0.8
        )
        
        x = (self.winfo_screenwidth() - window_width) // 2
        y = (self.winfo_screenheight() - window_height) // 2
        
        self.geometry(f"{int(window_width)}x{int(window_height)}+{int(x)}+{int(y)}")
    
    def on_closing(self):
        """Cleanup when closing the window."""
        try:
            self.animation_active = False
            self.image_cache.clear()
            if hasattr(self, 'original_image'):
                self.original_image.close()
            self.unbind_all('<MouseWheel>')
            self.unbind_all('<Button-4>')
            self.unbind_all('<Button-5>')
            self.grab_release()
            self.destroy()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            self.destroy()