"""
Custom draggable slider component for chunk selection with discrete steps.
"""

import customtkinter as ctk
from typing import Callable, Optional
from ..theme import OrangeBlackTheme


class ChunkSlider(ctk.CTkFrame):
    """
    A custom draggable slider for selecting chunk count with discrete steps (1-30).
    """
    
    def __init__(self, parent, initial_value: int = 10, on_value_change: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        
        self.min_value = 1
        self.max_value = 30
        self.current_value = initial_value
        self.on_value_change = on_value_change
        
        # Slider dimensions
        self.slider_width = 200
        self.slider_height = 20
        self.handle_size = 16
        
        self._setup_ui()
        # Schedule handle position update after layout is complete
        self.after(100, self._update_handle_position)
    
    def _setup_ui(self):
        """Setup the slider interface."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Main slider container
        self.slider_container = ctk.CTkFrame(self, fg_color="transparent")
        self.slider_container.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.slider_container.grid_columnconfigure(0, weight=1)
        
        # Value display
        self.value_label = ctk.CTkLabel(
            self.slider_container,
            text=f"Chunks: {self.current_value}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        self.value_label.grid(row=0, column=0, pady=(0, 5))
        
        # Slider track
        self.track_frame = ctk.CTkFrame(
            self.slider_container,
            height=self.slider_height,
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            border_width=1
        )
        self.track_frame.grid(row=1, column=0, sticky="ew", pady=2)
        self.track_frame.grid_propagate(False)
        
        # Configure track grid
        self.track_frame.grid_columnconfigure(0, weight=1)
        self.track_frame.grid_rowconfigure(0, weight=1)
        
        
        # Slider handle
        self.handle = ctk.CTkButton(
            self.track_frame,
            text="",
            width=self.handle_size,
            height=self.handle_size,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            border_width=0,
            corner_radius=self.handle_size // 2,
            command=self._on_handle_click
        )
        self.handle.grid(row=0, column=0, sticky="w", padx=2)
        
        # Bind mouse events for dragging
        self.handle.bind("<Button-1>", self._start_drag)
        self.handle.bind("<B1-Motion>", self._on_drag)
        self.handle.bind("<ButtonRelease-1>", self._end_drag)
        
        # Bind track clicks for jumping to position
        self.track_frame.bind("<Button-1>", self._on_track_click)
    
    
    def _start_drag(self, event):
        """Start dragging the handle."""
        # Store the initial mouse position and value
        self.drag_start_x = event.x_root
        self.drag_start_value = self.current_value
    
    def _on_drag(self, event):
        """Handle dragging the handle."""
        if not hasattr(self, 'drag_start_x'):
            return
        
        # Get the track frame's position on screen
        track_x = self.track_frame.winfo_rootx()
        track_width = self.track_frame.winfo_width()
        
        if track_width <= 0:
            return
        
        # Calculate mouse position relative to track frame
        mouse_x = event.x_root - track_x
        
        # Convert to fraction of track width
        fraction = mouse_x / track_width
        fraction = max(0.0, min(1.0, fraction))
        
        # Convert to discrete value
        new_value = int(self.min_value + fraction * (self.max_value - self.min_value))
        new_value = max(self.min_value, min(self.max_value, new_value))
        
        if new_value != self.current_value:
            self.set_value(new_value)
    
    def _end_drag(self, event):
        """End dragging the handle."""
        if hasattr(self, 'drag_start_x'):
            delattr(self, 'drag_start_x')
            delattr(self, 'drag_start_value')
    
    def _on_handle_click(self):
        """Handle direct click on the handle (no action needed for dragging)."""
        pass
    
    def _on_track_click(self, event):
        """Handle clicks on the track to jump to a position."""
        # Calculate position as fraction of track width
        track_width = self.track_frame.winfo_width()
        if track_width <= 0:
            return
        
        # Use relative coordinates within the track frame
        click_x = event.x
        fraction = click_x / track_width
        fraction = max(0.0, min(1.0, fraction))
        
        # Convert to discrete value
        new_value = int(self.min_value + fraction * (self.max_value - self.min_value))
        new_value = max(self.min_value, min(self.max_value, new_value))
        
        self.set_value(new_value)
    
    def _update_handle_position(self):
        """Update the handle position based on current value."""
        if not hasattr(self, 'track_frame') or not hasattr(self, 'handle'):
            return
        
        # Calculate position as fraction
        fraction = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        
        # Update handle position
        track_width = self.track_frame.winfo_width()
        if track_width > 0:
            # Calculate available space for the handle (track width minus handle size and padding)
            available_width = track_width - self.handle_size - 4  # 4px total padding
            handle_x = int(fraction * available_width)
            handle_x = max(0, min(handle_x, available_width))  # Clamp to valid range
            self.handle.grid_configure(padx=(handle_x, 0))
    
    def set_value(self, value: int):
        """
        Set the slider value.
        
        Args:
            value (int): The value to set (1-30)
        """
        # Clamp value to valid range
        value = max(self.min_value, min(self.max_value, value))
        
        if value != self.current_value:
            self.current_value = value
            self.value_label.configure(text=f"Chunks: {self.current_value}")
            self._update_handle_position()
            
            # Notify callback
            if self.on_value_change:
                self.on_value_change(self.current_value)
    
    def get_value(self) -> int:
        """
        Get the current slider value.
        
        Returns:
            int: Current value (1-30)
        """
        return self.current_value
    
    def update_idletasks(self):
        """Override to update handle position after layout."""
        super().update_idletasks()
        self._update_handle_position()
    
    def after(self, ms, func=None, *args):
        """Override to ensure handle position is updated after layout."""
        result = super().after(ms, func, *args)
        if ms == 0 and func is None:  # This is typically called for layout updates
            self._update_handle_position()
        return result
