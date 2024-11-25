import tkinter as tk
from tkinter import ttk
from gui.material_colors import MaterialColors

class UIComponents:
    def __init__(self, gallery):
        self.gallery = gallery
        self.gallery_frame = None
        self.status_label = None
        self.progress_var = None
        self.progress_bar = None
        
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        
        style.configure(
            'Gallery.TFrame',
            background=MaterialColors.BACKGROUND
        )
        
        style.configure(
            'Header.TLabel',
            background=MaterialColors.BACKGROUND,
            foreground=MaterialColors.PRIMARY_DARK,
            font=('Helvetica', 16, 'bold')
        )
        
        style.configure(
            'Status.TLabel',
            background=MaterialColors.BACKGROUND,
            foreground=MaterialColors.TEXT_SECONDARY,
            font=('Helvetica', 10)
        )
        
        style.configure(
            'Action.TButton',
            padding=10,
            font=('Helvetica', 10)
        )
    
    def create_layout(self):
        """Create the main application layout."""
        # Main container
        main_container = ttk.Frame(
            self.gallery,
            style='Gallery.TFrame',
            padding=20
        )
        main_container.pack(fill='both', expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Allow plugins to modify layout
        self.gallery.plugin_manager.run_hook('modify_layout', self)
        
        # Toolbar
        self.create_toolbar(main_container)
        
        # Status bar
        self.create_status_bar(main_container)
        
        # Progress bar
        self.create_progress_bar(main_container)
        
        # Gallery area
        self.create_gallery_area(main_container)
    
    def show_context_menu(self, event):
        """Show context menu with plugin additions."""
        menu = tk.Menu(self.gallery, tearoff=0)
        
        # Add default menu items
        # ...
        
        # Let plugins add their items
        self.gallery.plugin_manager.run_hook('context_menu', menu, event)
        
        # Show menu
        menu.post(event.x_root, event.y_root)
    
    def update_layout(self):
        """Update layout on window resize or configuration change."""
        if self.gallery_frame:
            # Update gallery frame layout
            self.update_gallery_grid()
            
            # Update canvas scrollregion if it exists
            if hasattr(self, 'canvas'):
                self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def update_gallery_grid(self):
        """Update gallery grid layout."""
        if not self.gallery_frame:
            return
            
        # Get current window width
        window_width = self.gallery_frame.winfo_width()
        
        # Calculate number of columns based on window width
        thumbnail_width = 170  # thumbnail width + padding
        columns = max(1, window_width // thumbnail_width)
        
        # Reconfigure grid
        for i in range(columns):
            self.gallery_frame.grid_columnconfigure(i, weight=1)
        
        # Rearrange thumbnails
        thumbnails = self.gallery_frame.winfo_children()
        for i, thumbnail in enumerate(thumbnails):
            row = i // columns
            col = i % columns
            thumbnail.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
    
    def create_header(self, parent):
        """Create the application header."""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill='x', pady=(0, 20))
        
        ttk.Label(
            header,
            text="StegeCrypt Gallery",
            style='Header.TLabel'
        ).pack()
    
    def create_toolbar(self, parent):
        """Create the toolbar with action buttons."""
        toolbar = ttk.Frame(parent, style='Gallery.TFrame')
        toolbar.pack(fill='x', pady=(0, 20))
        
        ttk.Button(
            toolbar,
            text="Select Directory",
            command=self.gallery.event_handlers.select_directory,
            style='Action.TButton'
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            toolbar,
            text="Select Key",
            command=self.gallery.event_handlers.select_key,
            style='Action.TButton'
        ).pack(side='left', padx=(0, 10))
    
    def create_status_bar(self, parent):
        """Create the status bar."""
        self.status_label = ttk.Label(
            parent,
            text="Select a directory to begin",
            style='Status.TLabel'
        )
        self.status_label.pack(fill='x', pady=(0, 10))
    
    def create_progress_bar(self, parent):
        """Create the progress bar."""
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            parent,
            mode='determinate',
            variable=self.progress_var
        )
    
    def create_gallery_area(self, parent):
        """Create the scrollable gallery area."""
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(
            parent,
            bg=MaterialColors.BACKGROUND,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            parent,
            orient='vertical',
            command=self.canvas.yview
        )
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create gallery frame
        self.gallery_frame = ttk.Frame(self.canvas, style='Gallery.TFrame')
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.gallery_frame,
            anchor='nw'
        )
        
        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Bind events
        self.gallery_frame.bind('<Configure>', lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox('all')
        ))
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind mousewheel scrolling
        self.bind_mousewheel()
    
    def on_canvas_configure(self, event):
        """Handle canvas resize."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.update_gallery_grid()
    
    def bind_mousewheel(self):
        """Bind mousewheel scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            
        self.canvas.bind_all('<MouseWheel>', _on_mousewheel)
    
    def clear_gallery(self):
        """Clear all items from the gallery frame."""
        if self.gallery_frame:
            for widget in self.gallery_frame.winfo_children():
                widget.destroy()
    
    def update_status(self, text):
        """Update the status label text."""
        if self.status_label:
            self.status_label.configure(text=text)
    
    def update_progress(self, value):
        """Update the progress bar value."""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(value)
    
    def show_progress_bar(self):
        """Show the progress bar."""
        if self.progress_bar:
            self.progress_bar.pack(fill='x', pady=(0, 10))
    
    def hide_progress_bar(self):
        """Hide the progress bar."""
        if self.progress_bar:
            self.progress_bar.pack_forget()