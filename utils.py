import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def format_grid_10_digit(grid_str):
    """
    Formats a grid string to a 10-digit grid (e.g., "0123405678").
    Handles 8-digit grids by appending '00' to easting and northing.
    Removes spaces from the input grid string.
    """
    grid_str = str(grid_str).replace(" ", "")
    if len(grid_str) == 8:
        easting = grid_str[:4] + "0"
        northing = grid_str[4:] + "0"
        return f"{int(easting):05d}{int(northing):05d}"
    elif len(grid_str) == 10:
        return grid_str
    else:
        # If it's not 8 or 10 digits, return as is, or raise an error, depending on desired strictness.
        # For now, we'll return it as is, assuming other validation handles invalid formats.
        return grid_str