"""
Custom orange and black theme configuration for the UI.
"""

import customtkinter as ctk


class OrangeBlackTheme:
    """
    Custom orange and black color theme.
    """
    
    # Primary colors
    BLACK_PRIMARY = "#000000"
    BLACK_SECONDARY = "#1a1a1a"
    BLACK_TERTIARY = "#2d2d2d"
    
    # Orange accent colors
    ORANGE_PRIMARY = "#FF6B35"      # Bright orange for main accents
    ORANGE_SECONDARY = "#FF8C42"    # Lighter orange for hover states
    ORANGE_TERTIARY = "#FF4500"     # Darker orange for active states
    ORANGE_LIGHT = "#FFA366"        # Light orange for subtle highlights
    
    # Text colors
    TEXT_PRIMARY = "#FFFFFF"        # White text on dark backgrounds
    TEXT_SECONDARY = "#B0B0B0"      # Gray text for secondary info
    TEXT_TERTIARY = "#808080"       # Darker gray for disabled/placeholder text
    
    # UI element colors
    FRAME_BG = BLACK_SECONDARY      # Frame backgrounds
    CARD_BG = BLACK_TERTIARY        # Card/panel backgrounds
    INPUT_BG = BLACK_TERTIARY       # Input field backgrounds
    BORDER_COLOR = "#404040"        # Border colors
    
    @classmethod
    def apply_theme(cls):
        """Apply the custom orange and black theme to customtkinter."""
        
        # Set appearance mode to dark
        ctk.set_appearance_mode("dark")
        
        # Use the built-in dark theme and modify it
        try:
            # Get the current theme and modify it
            current_theme = ctk.ThemeManager.theme.copy()
            
            # Update specific widget colors while preserving the base structure
            if "CTk" in current_theme:
                current_theme["CTk"]["fg_color"] = [cls.BLACK_PRIMARY, cls.BLACK_PRIMARY]
            
            if "CTkToplevel" in current_theme:
                current_theme["CTkToplevel"]["fg_color"] = [cls.BLACK_PRIMARY, cls.BLACK_PRIMARY]
            
            if "CTkFrame" in current_theme:
                current_theme["CTkFrame"].update({
                    "corner_radius": 8,
                    "border_width": 0,
                    "fg_color": [cls.FRAME_BG, cls.FRAME_BG],
                    "top_fg_color": [cls.FRAME_BG, cls.FRAME_BG],
                    "border_color": [cls.BORDER_COLOR, cls.BORDER_COLOR]
                })
            
            if "CTkButton" in current_theme:
                current_theme["CTkButton"].update({
                    "corner_radius": 6,
                    "border_width": 0,
                    "fg_color": [cls.ORANGE_PRIMARY, cls.ORANGE_PRIMARY],
                    "hover_color": [cls.ORANGE_SECONDARY, cls.ORANGE_SECONDARY],
                    "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                    "text_color_disabled": [cls.TEXT_TERTIARY, cls.TEXT_TERTIARY]
                })
            
            if "CTkLabel" in current_theme:
                current_theme["CTkLabel"].update({
                    "corner_radius": 0,
                    "fg_color": "transparent",
                    "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
                })
            
            if "CTkEntry" in current_theme:
                current_theme["CTkEntry"].update({
                    "corner_radius": 6,
                    "border_width": 1,
                    "fg_color": [cls.INPUT_BG, cls.INPUT_BG],
                    "border_color": [cls.BORDER_COLOR, cls.BORDER_COLOR],
                    "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                    "placeholder_text_color": [cls.TEXT_TERTIARY, cls.TEXT_TERTIARY]
                })
            
            if "CTkTextbox" in current_theme:
                current_theme["CTkTextbox"].update({
                    "corner_radius": 6,
                    "border_width": 1,
                    "fg_color": [cls.INPUT_BG, cls.INPUT_BG],
                    "border_color": [cls.BORDER_COLOR, cls.BORDER_COLOR],
                    "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                    "scrollbar_button_color": [cls.ORANGE_PRIMARY, cls.ORANGE_PRIMARY],
                    "scrollbar_button_hover_color": [cls.ORANGE_SECONDARY, cls.ORANGE_SECONDARY]
                })
            
            if "CTkScrollableFrame" in current_theme:
                current_theme["CTkScrollableFrame"].update({
                    "corner_radius": 6,
                    "border_width": 0,
                    "fg_color": [cls.FRAME_BG, cls.FRAME_BG],
                    "scrollbar_button_color": [cls.ORANGE_PRIMARY, cls.ORANGE_PRIMARY],
                    "scrollbar_button_hover_color": [cls.ORANGE_SECONDARY, cls.ORANGE_SECONDARY]
                })
            
            if "CTkScrollbar" in current_theme:
                current_theme["CTkScrollbar"].update({
                    "corner_radius": 6,
                    "border_spacing": 4,
                    "fg_color": "transparent",
                    "button_color": [cls.ORANGE_PRIMARY, cls.ORANGE_PRIMARY],
                    "button_hover_color": [cls.ORANGE_SECONDARY, cls.ORANGE_SECONDARY]
                })
            
            # Apply the modified theme
            ctk.ThemeManager.theme = current_theme
            return True
            
        except Exception as e:
            print(f"Warning: Could not apply custom theme: {e}")
            # Fallback - just set appearance mode
            ctk.set_appearance_mode("dark")
            return False
    
    @classmethod
    def get_accent_color(cls) -> str:
        """Get the primary accent color."""
        return cls.ORANGE_PRIMARY
    
    @classmethod
    def get_hover_color(cls) -> str:
        """Get the hover accent color."""
        return cls.ORANGE_SECONDARY
    
    @classmethod
    def get_primary_bg(cls) -> str:
        """Get the primary background color."""
        return cls.BLACK_PRIMARY
    
    @classmethod
    def get_secondary_bg(cls) -> str:
        """Get the secondary background color."""
        return cls.FRAME_BG
    
    @classmethod
    def get_text_color(cls) -> str:
        """Get the primary text color."""
        return cls.TEXT_PRIMARY
    
    @classmethod
    def get_secondary_text_color(cls) -> str:
        """Get the secondary text color."""
        return cls.TEXT_SECONDARY
