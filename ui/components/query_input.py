"""
Query input component for search functionality.
"""

import customtkinter as ctk
import json
from typing import Callable, Optional
from pathlib import Path
from ..theme import OrangeBlackTheme
from .chunk_slider import ChunkSlider
from utils import setup_logger, load_config


class QueryInputFrame(ctk.CTkFrame):
    """
    Frame containing query input field and search button.
    """
    
    def __init__(self, parent, on_search: Callable[[], None]):
        super().__init__(parent)
        
        # Setup logging
        self.logger = setup_logger(self.__class__.__name__, load_config())
        
        self.on_search = on_search
        self.available_models = self._load_available_models()
        self._setup_ui()
    
    def _load_available_models(self) -> dict:
        """Load available Azure models from client configs."""
        try:
            config_path = Path(__file__).parent.parent.parent / "scripts" / "clients" / "client_configs.json"
            with open(config_path, 'r') as f:
                configs = json.load(f)
            return configs.get("azure_clients", {})
        except Exception as e:
            print(f"Warning: Could not load model configs: {e}")
            return {}
    
    def _setup_ui(self):
        """Setup the query input interface."""
        
        # Configure grid - 3 columns: left (query), middle (spacing), right (controls)
        self.grid_columnconfigure(0, weight=3)  # Query input gets more space
        self.grid_columnconfigure(1, weight=0)  # Spacing column
        self.grid_columnconfigure(2, weight=1)  # Controls get less space
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="💭 Ask a Question",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 5))
        
        # Left side: Query input section
        instruction_label = ctk.CTkLabel(
            self,
            text="Enter your question about the knowledge base:",
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        instruction_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))
        
        # Query input field
        self.query_entry = ctk.CTkTextbox(
            self,
            height=80,
            font=ctk.CTkFont(size=14),
            wrap="word",
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.query_entry.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Search button (positioned under example questions)
        self.search_button = ctk.CTkButton(
            self,
            text="🔍 Search",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_search_click,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.search_button.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # PDF Processor button (disabled by default)
        self.pdf_processor_button = ctk.CTkButton(
            self,
            text="📚 Add PDFs to Database",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=self._open_pdf_processor,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color(),
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            state="disabled"  # Disabled by default
        )
        self.pdf_processor_button.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Initialize tooltip for PDF processor button
        self.pdf_tooltip = None
        
        # Session cost display
        self.session_cost_label = ctk.CTkLabel(
            self,
            text="💰 Session Cost: $0.000000",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        self.session_cost_label.grid(row=7, column=0, sticky="w", padx=15, pady=(0, 5))
        
        # Session cost description
        self.session_cost_description = ctk.CTkLabel(
            self,
            text="Total cost for this session",
            font=ctk.CTkFont(size=10),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        self.session_cost_description.grid(row=8, column=0, sticky="w", padx=15, pady=(0, 15))
        
        # Right side: Model selection and search limit controls
        # Model selection section (hidden by default)
        self.model_label = ctk.CTkLabel(
            self,
            text="🤖 AI Model:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        self.model_label.grid(row=1, column=2, sticky="w", padx=(0, 15), pady=(0, 5))
        
        # Model selection dropdown
        self.model_var = ctk.StringVar(value="gpt-5-chat")  # Default model
        self.model_dropdown = ctk.CTkOptionMenu(
            self,
            values=list(self.available_models.keys()),
            variable=self.model_var,
            font=ctk.CTkFont(size=12),
            fg_color=OrangeBlackTheme.INPUT_BG,
            button_color=OrangeBlackTheme.get_accent_color(),
            button_hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color(),
            dropdown_fg_color=OrangeBlackTheme.INPUT_BG,
            dropdown_text_color=OrangeBlackTheme.get_text_color(),
            dropdown_hover_color=OrangeBlackTheme.get_hover_color()
        )
        self.model_dropdown.grid(row=2, column=2, sticky="ew", padx=(0, 15), pady=(0, 5))
        
        # Model description
        self.model_description = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_secondary_text_color(),
            wraplength=280,
            justify="center"
        )
        self.model_description.grid(row=3, column=2, sticky="ew", padx=(0, 15), pady=(0, 10))
        
        # Search limit section (hidden by default)
        self.limit_label = ctk.CTkLabel(
            self,
            text="🔍 Chunk Selection:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        self.limit_label.grid(row=5, column=2, sticky="w", padx=(0, 15), pady=(0, 5))
        
        # Draggable chunk slider
        self.chunk_slider = ChunkSlider(
            self,
            initial_value=10,
            on_value_change=self._on_chunk_limit_change
        )
        self.chunk_slider.grid(row=6, column=2, sticky="ew", padx=(0, 15), pady=(0, 5))
        
        # Search limit description
        self.limit_description = ctk.CTkLabel(
            self,
            text="Drag the slider to select number of relevant chunks (1-30)",
            font=ctk.CTkFont(size=10),
            text_color=OrangeBlackTheme.get_secondary_text_color(),
            wraplength=200
        )
        self.limit_description.grid(row=7, column=2, sticky="ew", padx=(0, 15), pady=(0, 10))
        
        # Update description for default model
        self._update_model_description()
        
        # Bind model selection change
        self.model_dropdown.configure(command=self._on_model_change)
        
        # Bind Enter key (Ctrl+Enter for multiline)
        self.query_entry.bind("<Control-Return>", lambda e: self._on_search_click())
        
        # Focus on query input
        self.query_entry.focus()
        
        # Example queries section (positioned under query input on left side)
        self._add_example_queries()
        
        # Initially hide admin controls (admin mode disabled by default)
        self._hide_admin_controls()
        
        # Setup tooltip for PDF processor button
        self._setup_pdf_tooltip()
    
    def _on_model_change(self, selected_model: str):
        """Handle model selection change."""
        self._update_model_description()
    
    def _update_model_description(self):
        """Update the model description based on selected model."""
        selected_model = self.model_var.get()
        if selected_model in self.available_models:
            model_info = self.available_models[selected_model]
            description = model_info.get("description", "No description available")
            
            # Add pricing information if available
            pricing = model_info.get("pricing", {})
            if pricing and pricing.get("input") is not None and pricing.get("output") is not None:
                # Format pricing to ensure full decimal values are displayed
                input_price = f"{pricing['input']:.2f}" if isinstance(pricing['input'], (int, float)) else str(pricing['input'])
                output_price = f"{pricing['output']:.2f}" if isinstance(pricing['output'], (int, float)) else str(pricing['output'])
                pricing_text = f"💰 Input: ${input_price}/1M tokens\n   Output: ${output_price}/1M tokens"
                full_description = f"{description}\n\n{pricing_text}"
            else:
                full_description = description
            
            self.model_description.configure(text=full_description)
        else:
            self.model_description.configure(text="Model information not available")
    
    def get_selected_model(self) -> str:
        """Get the currently selected model name."""
        return self.model_var.get()
    
    def get_selected_model_config(self) -> dict:
        """Get the configuration for the currently selected model."""
        selected_model = self.model_var.get()
        return self.available_models.get(selected_model, {})
    
    def _add_example_queries(self):
        """Add example query buttons for user convenience."""
        
        examples_label = ctk.CTkLabel(
            self,
            text="📝 Example Questions:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_secondary_text_color()
        )
        examples_label.grid(row=3, column=0, sticky="w", padx=15, pady=(10, 5))
        
        # Example queries
        self.default_examples = [
            "How do I add a client's signature to their contact card?",
            "What are the steps for creating a new case?",
            "How do I edit the contact information of a client?"
        ]
        
        examples_frame = ctk.CTkFrame(self, fg_color="transparent")
        examples_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))
        examples_frame.grid_columnconfigure(0, weight=1)
        
        # Store references to example buttons for later updates
        self.example_buttons = []
        
        for i, example in enumerate(self.default_examples):
            example_btn = ctk.CTkButton(
                examples_frame,
                text=example,
                font=ctk.CTkFont(size=11),
                height=25,
                fg_color="transparent",
                border_width=1,
                border_color=OrangeBlackTheme.BORDER_COLOR,
                text_color=OrangeBlackTheme.get_secondary_text_color(),
                hover_color=OrangeBlackTheme.get_secondary_bg(),
                command=lambda ex=example: self._set_example_query(ex)
            )
            example_btn.grid(row=i, column=0, sticky="ew", pady=2)
            self.example_buttons.append(example_btn)
    
    def update_example_questions(self, new_examples: list):
        """
        Update the example questions with new suggestions from AI responses.
        
        Args:
            new_examples (list): List of new example questions to display
        """
        # Only update if we have new examples, otherwise keep current state
        if not new_examples:
            return
        
        # Limit to maximum of 3 examples (same as default)
        max_examples = min(len(new_examples), len(self.example_buttons))
        
        # Update existing buttons with new text
        for i in range(max_examples):
            example = new_examples[i]
            button = self.example_buttons[i]
            
            button.configure(text=example)
            # Fix lambda closure issue by using default parameter
            button.configure(command=lambda ex=example: self._set_example_query(ex))
            
            # Make sure button is visible
            button.grid()
        
        # Hide any extra buttons if we have fewer new examples than buttons
        for i in range(max_examples, len(self.example_buttons)):
            self.example_buttons[i].grid_remove()
    
    def reset_to_default_examples(self):
        """Reset the example questions back to the default examples."""
        self.update_example_questions(self.default_examples)
    
    def _set_example_query(self, query: str):
        """Set an example query in the input field."""
        self.query_entry.delete("1.0", "end")
        self.query_entry.insert("1.0", query)
    
    def _on_search_click(self):
        """Handle search button click."""
        if self.on_search:
            self.on_search()
    
    def _open_pdf_processor(self):
        """Open the PDF processor window."""
        try:
            from .pdf_processor import PDFProcessorWindow
            PDFProcessorWindow(self)
        except ImportError as e:
            print(f"Failed to import PDF processor: {e}")
        except Exception as e:
            print(f"Failed to open PDF processor: {e}")
    
    def _show_admin_controls(self):
        """Show the admin control elements (model selection and limit) and adjust grid layout."""
        # Show model selection elements
        self.model_label.grid(row=1, column=2, sticky="w", padx=(0, 15), pady=(0, 5))
        self.model_dropdown.grid(row=2, column=2, sticky="ew", padx=(0, 15), pady=(0, 5))
        self.model_description.grid(row=3, column=2, sticky="ew", padx=(0, 15), pady=(0, 10))
        
        # Show limit control elements
        self.limit_label.grid(row=5, column=2, sticky="w", padx=(0, 15), pady=(0, 5))
        self.chunk_slider.grid(row=6, column=2, sticky="ew", padx=(0, 15), pady=(0, 5))
        self.limit_description.grid(row=7, column=2, sticky="w", padx=(0, 15), pady=(0, 10))
        
        # Adjust grid configuration to give space to admin controls
        self.grid_columnconfigure(0, weight=3)  # Query input gets more space
        self.grid_columnconfigure(1, weight=0)  # Spacing column
        self.grid_columnconfigure(2, weight=1)  # Controls get less space
    
    def _hide_admin_controls(self):
        """Hide the admin control elements and adjust grid layout."""
        # Hide model selection elements
        self.model_label.grid_remove()
        self.model_dropdown.grid_remove()
        self.model_description.grid_remove()
        
        # Hide limit control elements
        self.limit_label.grid_remove()
        self.chunk_slider.grid_remove()
        self.limit_description.grid_remove()
        
        # Adjust grid configuration to give all space to query input
        self.grid_columnconfigure(0, weight=1)  # Query input gets all space
        self.grid_columnconfigure(1, weight=0)  # Spacing column (unused)
        self.grid_columnconfigure(2, weight=0)  # Controls column (unused)
    
    def _setup_pdf_tooltip(self):
        """Setup tooltip for PDF processor button."""
        from .tooltip import Tooltip
        self.pdf_tooltip = Tooltip(
            self.pdf_processor_button,
            "Enable admin mode to use this feature",
            delay=200  # Reduced delay for faster appearance
        )
    
    def set_admin_mode(self, enabled: bool):
        """Set admin mode state and update UI accordingly."""
        if enabled:
            self._show_admin_controls()
            # Hide tooltip when admin mode is enabled
            if self.pdf_tooltip:
                self.pdf_tooltip.update_text("")
        else:
            self._hide_admin_controls()
            # Show tooltip when admin mode is disabled
            if self.pdf_tooltip:
                self.pdf_tooltip.update_text("Enable admin mode to use this feature")
    
    def get_query(self) -> str:
        """
        Get the current query text.
        
        Returns:
            str: The query text
        """
        return self.query_entry.get("1.0", "end-1c").strip()
    
    def clear_query(self):
        """Clear the query input field."""
        self.query_entry.delete("1.0", "end")
    
    def set_loading(self, loading: bool):
        """
        Set the loading state of the search button.
        
        Args:
            loading (bool): Whether to show loading state
        """
        if loading:
            self.search_button.configure(
                text="🔄 Searching...",
                state="disabled"
            )
        else:
            self.search_button.configure(
                text="🔍 Search",
                state="normal"
            )
    
    def focus_input(self):
        """Focus the query input field."""
        self.query_entry.focus()
    
    def _on_chunk_limit_change(self, value: int):
        """
        Handle chunk limit change from slider.
        
        Args:
            value (int): New chunk limit value
        """
        # The slider already handles validation, so we just need to log the change
        self.logger.debug(f"Chunk limit changed to: {value}")
    
    def get_search_limit(self) -> int:
        """
        Get the user-specified search limit.
        
        Returns:
            int: The search limit from the slider (1-30)
        """
        return self.chunk_slider.get_value()
    
    def update_session_cost(self, cost: float):
        """
        Update the session cost display.
        
        Args:
            cost (float): The total session cost to display
        """
        self.session_cost_label.configure(text=f"💰 Session Cost: ${cost:.6f}")
    
    def reset_session_cost(self):
        """Reset the session cost display to zero."""
        self.session_cost_label.configure(text="💰 Session Cost: $0.000000")
    
    def reset_search_limit_to_default(self):
        """Reset the search limit to the default value from config."""
        try:
            from utils import load_config
            config = load_config()
            default_limit = config.get('vector_database', {}).get('search_limit', 10)
            self.limit_var.set(str(default_limit))
        except Exception:
            # Fallback to hardcoded default
            self.limit_var.set("10")
    
    def validate_search_limit(self) -> bool:
        """
        Validate the current search limit input.
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            limit = int(self.limit_var.get())
            return 0 < limit <= 100
        except (ValueError, TypeError):
            return False
