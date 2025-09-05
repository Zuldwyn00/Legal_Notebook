"""
Tooltip component for showing helpful information on hover.
"""

import customtkinter as ctk
from ..theme import OrangeBlackTheme


class Tooltip:
    """
    A simple tooltip widget that appears on hover.
    """
    
    def __init__(self, widget, text, delay=500):
        """
        Initialize tooltip for a widget.
        
        Args:
            widget: The widget to attach the tooltip to
            text: The text to display in the tooltip
            delay: Delay in milliseconds before showing tooltip
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Motion>", self._on_motion)
    
    def _on_enter(self, event):
        """Handle mouse enter event."""
        # Store the initial mouse position relative to the widget's window
        self.mouse_x = event.x_root
        self.mouse_y = event.y_root
        self._schedule_tooltip()
    
    def _on_leave(self, event):
        """Handle mouse leave event."""
        self._cancel_tooltip()
        self._hide_tooltip()
    
    def _on_motion(self, event):
        """Handle mouse motion event - no action needed for static tooltip."""
        pass
    
    def _schedule_tooltip(self):
        """Schedule tooltip to appear after delay."""
        self._cancel_tooltip()
        self.after_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _cancel_tooltip(self):
        """Cancel scheduled tooltip."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
    
    def _show_tooltip(self):
        """Show the tooltip window."""
        if self.tooltip_window or not self.text:
            return
        
        # Create tooltip window as a child of the widget's toplevel window
        # This ensures it appears on the same monitor as the main window
        parent_window = self.widget.winfo_toplevel()
        self.tooltip_window = ctk.CTkToplevel(parent_window)
        self.tooltip_window.wm_overrideredirect(True)
        
        # Configure tooltip appearance
        self.tooltip_window.configure(fg_color=OrangeBlackTheme.get_secondary_bg())
        
        # Create label
        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            font=ctk.CTkFont(size=11),
            text_color=OrangeBlackTheme.get_text_color(),
            fg_color="transparent"
        )
        label.pack(padx=8, pady=4)
        
        # Update the window to get actual size
        self.tooltip_window.update_idletasks()
        
        # Get tooltip dimensions
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()
        
        # Get parent window position and dimensions for boundary checking
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        # Calculate position relative to the mouse cursor
        # Position tooltip below and to the right of the mouse cursor
        x = self.mouse_x + 10
        y = self.mouse_y + 10
        
        # Adjust if tooltip would go off the right edge of the parent window
        if x + tooltip_width > parent_x + parent_width:
            x = self.mouse_x - tooltip_width - 10  # Show to the left of cursor
        
        # Adjust if tooltip would go off the bottom edge of the parent window
        if y + tooltip_height > parent_y + parent_height:
            y = self.mouse_y - tooltip_height - 10  # Show above cursor
        
        # Ensure tooltip doesn't go off the left edge of the parent window
        if x < parent_x:
            x = parent_x + 10
        
        # Ensure tooltip doesn't go off the top edge of the parent window
        if y < parent_y:
            y = parent_y + 10
        
        # Set the final position using screen coordinates
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Make sure tooltip is on top
        self.tooltip_window.lift()
        self.tooltip_window.attributes("-topmost", True)
    
    def _hide_tooltip(self):
        """Hide the tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def update_text(self, text):
        """Update the tooltip text."""
        self.text = text
    
    def destroy(self):
        """Clean up the tooltip."""
        self._cancel_tooltip()
        self._hide_tooltip()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")
        self.widget.unbind("<Motion>")
