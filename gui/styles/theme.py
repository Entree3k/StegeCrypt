from tkinter import ttk
from .material import MaterialColors, MaterialFonts

def configure_app_style():
    """Configure the application's ttk styles."""
    style = ttk.Style()
    
    # Frame styles
    style.configure('Main.TFrame', background=MaterialColors.BG_COLOR)
    style.configure('Header.TFrame', background=MaterialColors.BG_COLOR)
    style.configure('Tab.TFrame', background=MaterialColors.WHITE)
    style.configure('Status.TFrame', background=MaterialColors.BG_COLOR)
    
    # Label styles
    style.configure('Header.TLabel',
                   font=MaterialFonts.HEADER,
                   background=MaterialColors.BG_COLOR,
                   foreground=MaterialColors.PRIMARY_COLOR)
    
    style.configure('SubHeader.TLabel',
                   font=MaterialFonts.SUBHEADER,
                   background=MaterialColors.BG_COLOR,
                   foreground=MaterialColors.SECONDARY_COLOR)
    
    style.configure('Section.TLabel',
                   font=MaterialFonts.BODY,
                   background=MaterialColors.WHITE,
                   padding=(0, 10, 0, 5))
                   
    style.configure('Status.TLabel',
                   font=MaterialFonts.CAPTION,
                   background=MaterialColors.BG_COLOR)
                   
    style.configure('Progress.TLabel',
                   font=MaterialFonts.CAPTION,
                   background=MaterialColors.WHITE)

    # Button styles
    style.configure('Action.TButton',
                   font=MaterialFonts.BUTTON,
                   padding=(15, 8))
    
    # Entry styles
    style.configure('Path.TEntry',
                   font=MaterialFonts.INPUT)