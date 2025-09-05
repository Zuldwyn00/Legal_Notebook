"""
Password dialog component for securing PDF processor access.
"""

import customtkinter as ctk
from typing import Optional, Callable
import os
from dotenv import load_dotenv

from ..theme import OrangeBlackTheme


class PasswordDialog(ctk.CTkToplevel):
    """
    Password dialog for securing access to PDF processor.
    """
    
    def __init__(self, parent, on_success: Callable[[], None], on_cancel: Callable[[], None] = None):
        super().__init__(parent)
        
        # Load environment variables
        load_dotenv()
        
        # Configure window
        self.title("🔐 Password Required")
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Set appearance
        self.configure(fg_color=OrangeBlackTheme.get_primary_bg())
        
        # Store callbacks
        self.on_success = on_success
        self.on_cancel = on_cancel or (lambda: None)
        
        # Get password from environment
        self.required_password = os.getenv("ADD_FILE_PASS", "")
        
        # Setup UI
        self._setup_ui()
        
        # Center the window on parent
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Center the window
        self._center_window()
        
    def _setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color=OrangeBlackTheme.get_primary_bg())
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔐 Password Required",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=OrangeBlackTheme.get_text_color()
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Enter password to access PDF processor:",
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        desc_label.pack(pady=(0, 20))
        
        # Password entry frame
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 20))
        
        # Password label
        password_label = ctk.CTkLabel(
            password_frame,
            text="Password:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_text_color()
        )
        password_label.pack(anchor="w", pady=(0, 5))
        
        # Password entry
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Enter password...",
            font=ctk.CTkFont(size=12),
            height=35,
            show="*",  # Hide password characters
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            border_color=OrangeBlackTheme.BORDER_COLOR,
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.password_entry.pack(fill="x", pady=(0, 10))
        self.password_entry.bind("<Return>", lambda e: self._check_password())
        
        # Error message label
        self.error_label = ctk.CTkLabel(
            password_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#FF6B6B"  # Red color for errors
        )
        self.error_label.pack(anchor="w")
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=self._on_cancel,
            fg_color="#6B7280",  # Gray color
            hover_color="#4B5563",
            text_color="white"
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Submit button
        submit_btn = ctk.CTkButton(
            button_frame,
            text="✅ Submit",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=self._check_password,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        submit_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Focus on password entry
        self.password_entry.focus()
        
    def _center_window(self):
        """Center the window on the parent."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def _check_password(self):
        """Check if the entered password is correct."""
        entered_password = self.password_entry.get().strip()
        
        if not self.required_password:
            self.error_label.configure(text="❌ Password not configured in environment")
            return
            
        if not entered_password:
            self.error_label.configure(text="❌ Please enter a password")
            return
            
        if entered_password == self.required_password:
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text="❌ Incorrect password")
            self.password_entry.delete(0, "end")  # Clear the entry
            self.password_entry.focus()
            
    def _on_cancel(self):
        """Handle cancel button click."""
        self.destroy()
        self.on_cancel()
