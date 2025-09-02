"""
Results display component for showing search results.
"""

import customtkinter as ctk
from typing import List, Dict, Any
from pathlib import Path
from ..theme import OrangeBlackTheme


class ResultsDisplayFrame(ctk.CTkFrame):
    """
    Frame for displaying search results from the knowledge base.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent_window = parent
        self.is_expanded = False
        self.sidebar_width = 350  # Full width when expanded
        self.collapsed_width = 120  # Minimal width when collapsed - just enough for arrow + "Results" + count
        self.width_change_handler = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the results display interface."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Set initial width for sidebar (start collapsed)
        self.configure(width=self.collapsed_width)
        
        # Add sidebar styling
        self.configure(
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        )
        
        # Header with toggle button
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Title and toggle button container
        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="w")
        
        self.toggle_button = ctk.CTkButton(
            title_container,
            text="▶",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=25,
            height=25,
            command=self._toggle_expansion,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color()
        )
        self.toggle_button.pack(side="left", padx=(0, 5))
        
        self.results_title = ctk.CTkLabel(
            title_container,
            text="📊 Results",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        self.results_title.pack(side="left")
        
        self.results_count = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        self.results_count.grid(row=0, column=1, sticky="e", padx=(0, 5))
        
        # Set initial count
        self.results_count.configure(text="0 results")
        
        # Scrollable results area (initially hidden)
        self.results_scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            scrollbar_button_color=OrangeBlackTheme.get_accent_color(),
            scrollbar_button_hover_color=OrangeBlackTheme.get_hover_color()
        )
        self.results_scrollable.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.results_scrollable.grid_columnconfigure(0, weight=1)
        
        # Start collapsed
        self.results_scrollable.grid_remove()
        self.is_expanded = False
        self.toggle_button.configure(text="▶")  # Show expand arrow initially
        self.grid_propagate(False)  # Start with minimal height
        
        # Initial empty state
        self._show_empty_state()
    
    def _show_empty_state(self):
        """Show empty state when no results."""
        empty_label = ctk.CTkLabel(
            self.results_scrollable,
            text="🔍 Enter a query above to search the knowledge base",
            font=ctk.CTkFont(size=14),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        empty_label.grid(row=0, column=0, pady=50)
    
    def clear(self):
        """Clear all results from the display."""
        for widget in self.results_scrollable.winfo_children():
            widget.destroy()
        
        self.results_count.configure(text="0 results")
        self._show_empty_state()
        
        # Collapse when clearing
        if self.is_expanded:
            self._toggle_expansion()
    
    def display_results(self, results: List[Dict[str, Any]]):
        """
        Display search results.
        
        Args:
            results (List[Dict]): List of search result dictionaries
        """
        # Clear existing results
        for widget in self.results_scrollable.winfo_children():
            widget.destroy()
        
        if not results:
            self._show_no_results()
            return
        
        # Update count
        self.results_count.configure(text=f"{len(results)} results")
        
        # Display each result
        for i, result in enumerate(results):
            self._create_result_card(result, i)
        
        # Auto-expand when new results are available
        self.auto_expand_on_results()
    
    def _show_no_results(self):
        """Show message when no results found."""
        self.results_count.configure(text="0 results")
        
        no_results_label = ctk.CTkLabel(
            self.results_scrollable,
            text="❌ No relevant information found in the knowledge base.\nTry rephrasing your question or using different keywords.",
            font=ctk.CTkFont(size=14),
            text_color=OrangeBlackTheme.get_secondary_text_color(),
            justify="center"
        )
        no_results_label.grid(row=0, column=0, pady=50)
    
    def _create_result_card(self, result: Dict[str, Any], index: int):
        """
        Create a card for displaying a single search result.
        
        Args:
            result (Dict): Search result data
            index (int): Result index
        """
        card_frame = ctk.CTkFrame(
            self.results_scrollable,
            fg_color=OrangeBlackTheme.CARD_BG,
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        )
        card_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=5)
        card_frame.grid_columnconfigure(0, weight=1)
        
        # Header with source and score
        header_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Result number and source
        source_text = f"📄 Result {index + 1}: {Path(result['source']).name}"
        source_label = ctk.CTkLabel(
            header_frame,
            text=source_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        source_label.grid(row=0, column=0, sticky="w")
        
        # Relevance score
        score_text = f"Relevance: {result['score']:.3f}"
        score_label = ctk.CTkLabel(
            header_frame,
            text=score_text,
            font=ctk.CTkFont(size=11),
            text_color=OrangeBlackTheme.get_accent_color(),
            anchor="e"
        )
        score_label.grid(row=0, column=1, sticky="e")
        
        # Page range
        page_info = f"📑 Pages: {result['page_range']}"
        page_label = ctk.CTkLabel(
            header_frame,
            text=page_info,
            font=ctk.CTkFont(size=11),
            text_color=OrangeBlackTheme.get_secondary_text_color(),
            anchor="w"
        )
        page_label.grid(row=1, column=0, columnspan=2, sticky="w")
        
        # Content preview
        content_preview = self._create_content_preview(result.get('text', ''))
        
        content_textbox = ctk.CTkTextbox(
            card_frame,
            height=120,
            font=ctk.CTkFont(size=12),
            wrap="word",
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            text_color=OrangeBlackTheme.get_text_color(),
            scrollbar_button_color=OrangeBlackTheme.get_accent_color(),
            scrollbar_button_hover_color=OrangeBlackTheme.get_hover_color()
        )
        content_textbox.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
        content_textbox.insert("1.0", content_preview)
        content_textbox.configure(state="disabled")  # Read-only
    
    def _create_content_preview(self, text: str, max_length: int = 2000) -> str:
        """
        Create a preview of the content text.
        
        Args:
            text (str): Full text content
            max_length (int): Maximum preview length
            
        Returns:
            str: Truncated preview text
        """
        if not text:
            return "Content not available"
        
        # Clean up the text
        text = text.strip()
        
        if len(text) <= max_length:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_length].rsplit(' ', 1)[0]
        return f"{truncated}..."
    
    def _toggle_expansion(self):
        """Toggle the expansion state of the results section."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # Show results and update button
            self.results_scrollable.grid()
            self.toggle_button.configure(text="◀")
            self.configure(width=self.sidebar_width)  # Expand width
            # Allow the frame to expand to full height
            self.grid_propagate(True)  # Re-enable automatic height expansion
            # Notify parent of width change
            if self.width_change_handler:
                self.width_change_handler(True)
        else:
            # Hide results and update button
            self.results_scrollable.grid_remove()
            self.toggle_button.configure(text="▶")
            self.configure(width=self.collapsed_width)  # Collapse width
            # Force the frame to only take up the height it needs
            self.grid_propagate(False)  # Prevent automatic height expansion
            # Notify parent of width change
            if self.width_change_handler:
                self.width_change_handler(False)
    
    def set_width_change_handler(self, handler):
        """
        Set the callback handler for width changes.
        
        Args:
            handler: Function to call when width changes
        """
        self.width_change_handler = handler
    
    def auto_expand_on_results(self):
        """Automatically expand when results are available."""
        if not self.is_expanded:
            self._toggle_expansion()
    
    def jump_to_result(self, result_index: int):
        """
        Jump to and highlight a specific search result.
        
        Args:
            result_index (int): 1-based index of the result to jump to
        """
        # Ensure results are expanded and visible
        if not self.is_expanded:
            self._toggle_expansion()
        
        # Give the UI more time to expand and render completely
        self.after(200, lambda: self._perform_jump_to_result(result_index))
    
    def _perform_jump_to_result(self, result_index: int):
        """
        Perform the actual jump to result after UI is ready.
        
        Args:
            result_index (int): 1-based index of the result to jump to
        """
        # Convert to 0-based index
        zero_based_index = result_index - 1
        
        # Find the result card widget
        result_widgets = [w for w in self.results_scrollable.winfo_children() 
                         if isinstance(w, ctk.CTkFrame)]
        
        if 0 <= zero_based_index < len(result_widgets):
            target_widget = result_widgets[zero_based_index]
            
            # Clear previous highlights
            self._clear_result_highlights()
            
            # Highlight the target result
            self._highlight_result(target_widget, result_index)
            
            # Try multiple approaches to scroll to the widget
            self._scroll_to_widget(target_widget)
            
            # Also try scrolling by grid position as a backup
            self.after(100, lambda: self._scroll_to_grid_position(zero_based_index))
            
            # Try the most direct method: scroll the widget into view
            self.after(200, lambda: self._scroll_widget_into_view(target_widget))
        else:
            print(f"Result index {result_index} out of range. Available results: {len(result_widgets)}")
    
    def _scroll_to_grid_position(self, grid_index: int):
        """
        Alternative scrolling method using grid position.
        
        Args:
            grid_index (int): 0-based grid index of the result to scroll to
        """
        try:
            # Get the actual widget at this grid position
            result_widgets = [w for w in self.results_scrollable.winfo_children() 
                             if isinstance(w, ctk.CTkFrame)]
            
            if 0 <= grid_index < len(result_widgets):
                target_widget = result_widgets[grid_index]
                
                # Get the widget's actual position
                target_widget.update_idletasks()
                widget_y = target_widget.winfo_y()
                
                # Try to scroll to this position using multiple methods
                try:
                    canvas = self.results_scrollable._parent_canvas
                    
                    # Method 1: Scroll by pixels
                    canvas.yview_scroll(int(widget_y), "pixels")
                    return
                    
                except Exception as e:
                    # Method 2: Try using scrollbar
                    try:
                        scrollbar = self.results_scrollable._scrollbar
                        # Calculate scroll fraction based on widget position
                        scrollable_height = self.results_scrollable.winfo_height()
                        
                        # Use estimated content height like in main method
                        estimated_content_height = max(scrollable_height * 2, widget_y + 216 + 100)
                        scroll_fraction = widget_y / estimated_content_height
                        scroll_fraction = max(0.0, min(1.0, scroll_fraction))
                        
                        scrollbar.set(scroll_fraction, scroll_fraction + 0.1)
                        return
                    except Exception as e2:
                        pass
                        
        except Exception as e:
            print(f"Error in grid position scrolling: {e}")
    
    def _scroll_widget_into_view(self, widget: ctk.CTkFrame):
        """
        Most direct method to scroll a widget into view.
        
        Args:
            widget: The widget to scroll into view
        """
        try:
            # Force geometry update
            widget.update_idletasks()
            self.results_scrollable.update_idletasks()
            
            # Get widget position
            widget_y = widget.winfo_y()
            widget_height = widget.winfo_height()
            
            # Get viewport dimensions
            viewport_height = self.results_scrollable.winfo_height()
            
            # If widget is below the viewport, scroll down
            if widget_y > viewport_height:
                try:
                    # Calculate how much to scroll to bring widget into view
                    scroll_amount = widget_y - (viewport_height / 2)
                    
                    # Try scrolling by pixels first
                    canvas = self.results_scrollable._parent_canvas
                    canvas.yview_scroll(int(scroll_amount), "pixels")
                    return
                    
                except Exception as e:
                    # Try using scrollbar
                    try:
                        scrollbar = self.results_scrollable._scrollbar
                        # Get current scroll position and move down
                        current_pos = scrollbar.get()[0]
                        new_pos = min(1.0, current_pos + 0.3)  # Move down by 30%
                        scrollbar.set(new_pos, new_pos + 0.1)
                        return
                    except Exception as e2:
                        pass
            
            elif widget_y < 0:
                # Widget is above the viewport, scroll up
                try:
                    canvas = self.results_scrollable._parent_canvas
                    canvas.yview_scroll(int(widget_y), "pixels")
                    return
                except Exception as e:
                    pass
                
        except Exception as e:
            print(f"Error scrolling widget into view: {e}")
    
    def _clear_result_highlights(self):
        """Clear all result highlights."""
        for widget in self.results_scrollable.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(border_width=1, border_color=OrangeBlackTheme.BORDER_COLOR)
    
    def _highlight_result(self, widget: ctk.CTkFrame, result_number: int):
        """
        Highlight a specific result widget.
        
        Args:
            widget: The result card widget to highlight
            result_number: The result number for logging
        """
        # Add orange border and slight glow effect
        widget.configure(
            border_width=3,
            border_color=OrangeBlackTheme.get_accent_color()
        )
        
        # Schedule removal of highlight after 3 seconds
        widget.after(3000, lambda: widget.configure(
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        ))
    
    def _scroll_to_widget(self, widget: ctk.CTkFrame):
        """
        Scroll the results view to show the specified widget.
        
        Args:
            widget: The widget to scroll to
        """
        try:
            # Force geometry update
            widget.update_idletasks()
            self.results_scrollable.update_idletasks()
            
            # Get the widget's position relative to the scrollable frame
            widget_y = widget.winfo_y()
            widget_height = widget.winfo_height()
            
            # Get the scrollable frame dimensions
            scrollable_height = self.results_scrollable.winfo_height()
            
            # Always try to scroll if widget is not at the top
            if widget_y > 0:
                
                # Method 1: Try to scroll the widget into view using canvas yview_moveto
                try:
                    canvas = self.results_scrollable._parent_canvas
                    
                    # Calculate scroll fraction based on widget position
                    # Use a more aggressive approach - assume content is scrollable
                    # Calculate how much of the content is above this widget
                    estimated_content_height = max(scrollable_height * 2, widget_y + widget_height + 100)
                    scroll_fraction = widget_y / estimated_content_height
                    scroll_fraction = max(0.0, min(1.0, scroll_fraction))
                    
                    canvas.yview_moveto(scroll_fraction)
                    return
                        
                except Exception as e:
                    pass
                
                # Method 2: Try using the scrollbar directly with calculated fraction
                try:
                    scrollbar = self.results_scrollable._scrollbar
                    
                    # Calculate scroll fraction based on widget position
                    estimated_content_height = max(scrollable_height * 2, widget_y + widget_height + 100)
                    scroll_fraction = widget_y / estimated_content_height
                    scroll_fraction = max(0.0, min(1.0, scroll_fraction))
                    
                    scrollbar.set(scroll_fraction, scroll_fraction + 0.1)
                    return
                    
                except Exception as e:
                    pass
                
                # Method 3: Try incremental scrolling
                try:
                    scrollbar = self.results_scrollable._scrollbar
                    current_pos = scrollbar.get()[0]
                    
                    # Move down by a percentage based on widget position
                    if widget_y > scrollable_height:
                        # Widget is well below viewport, move down significantly
                        new_pos = min(1.0, current_pos + 0.4)
                    elif widget_y > scrollable_height / 2:
                        # Widget is in lower half, move down moderately
                        new_pos = min(1.0, current_pos + 0.2)
                    else:
                        # Widget is in upper half, move down slightly
                        new_pos = min(1.0, current_pos + 0.1)
                    
                    scrollbar.set(new_pos, new_pos + 0.1)
                    return
                    
                except Exception as e:
                    pass
                
                
        except Exception as e:
            print(f"Error scrolling to widget: {e}")  # For debugging
