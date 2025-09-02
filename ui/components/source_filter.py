"""
Source filter component for filtering search results by document sources.
"""

import customtkinter as ctk
import re
from typing import List, Callable, Optional
from pathlib import Path
from ..theme import OrangeBlackTheme


class SourceFilterFrame(ctk.CTkFrame):
    """
    Frame containing source filtering controls.
    """
    
    def __init__(self, parent, on_source_filter_change: Callable[[List[str]], None]):
        super().__init__(parent)
        
        self.on_source_filter_change = on_source_filter_change
        self.selected_sources = set()
        self.available_sources = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the source filter interface."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📚 Source Filter",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Description
        description_label = ctk.CTkLabel(
            self,
            text="Select specific documents to search within:",
            font=ctk.CTkFont(size=11),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        description_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))
        
        # Source selection frame
        self.sources_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            border_width=1
        )
        self.sources_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Select all/none buttons frame
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        # Select all button
        self.select_all_button = ctk.CTkButton(
            buttons_frame,
            text="Select All",
            font=ctk.CTkFont(size=11),
            height=30,
            command=self._select_all_sources,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.select_all_button.pack(side="left", padx=(0, 5))
        
        # Select none button
        self.select_none_button = ctk.CTkButton(
            buttons_frame,
            text="Select None",
            font=ctk.CTkFont(size=11),
            height=30,
            command=self._select_none_sources,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.select_none_button.pack(side="left", padx=(5, 0))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="No sources loaded",
            font=ctk.CTkFont(size=10),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        self.status_label.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 5))
    
    def load_sources(self, sources: List[str]):
        """
        Load available vector names into the filter.
        
        Args:
            sources (List[str]): List of vector names (document types)
        """
        self.available_sources = sources
        self._clear_source_checkboxes()
        self._create_source_checkboxes()
        
        # Select all sources by default
        self._select_all_sources()
        
        self._update_status()
    
    def _clear_source_checkboxes(self):
        """Clear all existing source checkboxes."""
        for widget in self.sources_frame.winfo_children():
            widget.destroy()
    
    def _create_source_checkboxes(self):
        """Create checkboxes for each available vector name."""
        if not self.available_sources:
            return
        
        for vector_name in self.available_sources:
            # Create a frame for this vector name
            source_group_frame = ctk.CTkFrame(
                self.sources_frame,
                fg_color="transparent"
            )
            source_group_frame.pack(fill="x", padx=5, pady=2)
            
            # Create checkbox for this vector name
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(
                source_group_frame,
                text=vector_name.replace('_', ' ').title(),  # Make it more readable
                variable=var,
                font=ctk.CTkFont(size=11),
                fg_color=OrangeBlackTheme.get_accent_color(),
                hover_color=OrangeBlackTheme.get_hover_color(),
                text_color=OrangeBlackTheme.get_text_color(),
                command=lambda v=var, name=vector_name: self._on_source_toggle(v, name)
            )
            checkbox.pack(side="left", padx=(0, 5))
            
            # Store the checkbox variable for later access
            checkbox.var = var
            checkbox.vector_name = vector_name
    

    
    def _on_source_toggle(self, var: ctk.BooleanVar, vector_name: str):
        """
        Handle source checkbox toggle.
        
        Args:
            var (ctk.BooleanVar): The checkbox variable
            vector_name (str): The vector name for this document type
        """
        if var.get():
            # Add this vector name
            self.selected_sources.add(vector_name)
        else:
            # Remove this vector name
            self.selected_sources.discard(vector_name)
        
        # Update status label to reflect new count
        self._update_status()
        
        # Notify parent of the change
        self.on_source_filter_change(list(self.selected_sources))
    
    def _select_all_sources(self):
        """Select all available vector names."""
        self.selected_sources.clear()
        self.selected_sources.update(self.available_sources)
        
        # Update all checkboxes
        for widget in self.sources_frame.winfo_children():
            # Each widget is a frame containing a checkbox
            for child in widget.winfo_children():
                if hasattr(child, 'var') and hasattr(child, 'vector_name'):
                    child.var.set(True)
        
        # Update status label to reflect new count
        self._update_status()
        
        # Notify parent of the change
        self.on_source_filter_change(list(self.selected_sources))
    
    def _select_none_sources(self):
        """Deselect all vector names."""
        self.selected_sources.clear()
        
        # Update all checkboxes
        for widget in self.sources_frame.winfo_children():
            if widget.winfo_children():  # Check if widget has children
                for child in widget.winfo_children():
                    if hasattr(child, 'var'):
                        child.var.set(False)
        
        # Update status label to reflect new count
        self._update_status()
        
        # Notify parent of the change
        self.on_source_filter_change(list(self.selected_sources))
    
    def _update_status(self):
        """Update the status label."""
        if not self.available_sources:
            self.status_label.configure(text="No document types loaded")
        else:
            total_sources = len(self.available_sources)
            selected_count = len(self.selected_sources)
            if selected_count == 0:
                self.status_label.configure(text=f"⚠️  No document types selected ({total_sources} available)")
            elif selected_count == total_sources:
                self.status_label.configure(text=f"✅ All document types selected ({total_sources} total)")
            else:
                self.status_label.configure(text=f"📚 {selected_count}/{total_sources} document types selected")
    
    def get_selected_sources(self) -> List[str]:
        """
        Get the currently selected vector names.
        
        Returns:
            List[str]: List of selected vector names
        """
        return list(self.selected_sources)
    
    def clear_selection(self):
        """Clear the current source selection."""
        self._select_none_sources()
