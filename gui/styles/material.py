from dataclasses import dataclass

@dataclass
class MaterialColors:
    """Material Design color constants."""
    BG_COLOR: str = "#f0f0f0"
    PRIMARY_COLOR: str = "#2196F3"
    SECONDARY_COLOR: str = "#757575"
    SUCCESS_COLOR: str = "#4CAF50"
    WARNING_COLOR: str = "#FFC107"
    ERROR_COLOR: str = "#f44336"
    DARK_PRIMARY: str = "#1976D2"
    LIGHT_PRIMARY: str = "#BBDEFB"
    WHITE: str = "#FFFFFF"
    BLACK: str = "#000000"

class MaterialFonts:
    """Material Design font configurations."""
    HEADER = ('Helvetica', 24, 'bold')
    SUBHEADER = ('Helvetica', 12)
    BODY = ('Helvetica', 11)
    CAPTION = ('Helvetica', 10)
    
    # Button and input text
    BUTTON = ('Helvetica', 10)
    INPUT = ('Helvetica', 10)