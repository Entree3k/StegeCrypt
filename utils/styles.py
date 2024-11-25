from tkinter import ttk
from gui.material_colors import MaterialColors

def configure_styles():
    """Configure ttk styles for the application."""
    style = ttk.Style()
    
    # Main styles
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
    
    # Thumbnail styles
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
    
    # Video player styles
    style.configure(
        'VideoControl.TFrame',
        background=MaterialColors.BACKGROUND
    )
    
    style.configure(
        'VideoTime.TLabel',
        background=MaterialColors.BACKGROUND,
        font=('Helvetica', 10)
    )