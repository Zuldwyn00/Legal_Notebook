"""
AI response display component.
"""

import customtkinter as ctk
import re
from typing import Optional, Callable
from ..theme import OrangeBlackTheme


class AIResponseFrame(ctk.CTkFrame):
    """
    Frame for displaying AI-generated responses.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.on_citation_click = None  # Callback for citation clicks
        self._current_font_size = 16  # Default font size
        self._min_font_size = 8  # Minimum font size
        self._max_font_size = 32  # Maximum font size
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the AI response interface."""
        
        # Configure grid - ensure proper expansion
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title on the left
        self.response_title = ctk.CTkLabel(
            header_frame,
            text="🤖 AI Response",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        self.response_title.grid(row=0, column=0, sticky="w")
        
        # Zoom controls on the right
        zoom_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        zoom_frame.grid(row=0, column=1, sticky="e")
        
        # Zoom out button
        self.zoom_out_button = ctk.CTkButton(
            zoom_frame,
            text="−",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30,
            height=30,
            command=self._zoom_out,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color(),
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        )
        self.zoom_out_button.pack(side="left", padx=(0, 5))
        
        # Current font size display
        self.font_size_label = ctk.CTkLabel(
            zoom_frame,
            text=f"{self._current_font_size}px",
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_text_color(),
            width=50
        )
        self.font_size_label.pack(side="left", padx=5)
        
        # Zoom in button
        self.zoom_in_button = ctk.CTkButton(
            zoom_frame,
            text="+",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30,
            height=30,
            command=self._zoom_in,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color(),
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        )
        self.zoom_in_button.pack(side="left")
        
        # Response display area (larger font for better readability)
        self.response_textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=self._current_font_size, weight="normal"),
            wrap="word",
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            text_color=OrangeBlackTheme.get_text_color(),
            scrollbar_button_color=OrangeBlackTheme.get_accent_color(),
            scrollbar_button_hover_color=OrangeBlackTheme.get_hover_color(),
            height=300  # Set minimum height to prevent smushing
        )
        self.response_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Initial empty state
        self._show_empty_state()
    
    def _show_empty_state(self):
        """Show empty state when no response."""
        self.response_textbox.delete("1.0", "end")
        # Ensure current font size is applied
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        self.response_textbox.insert("1.0", "🤖 Ask a question above and I'll provide a detailed answer based on your knowledge base...")
        self.response_textbox.configure(state="disabled")
    
    def clear(self):
        """Clear the response display."""
        self._show_empty_state()
    
    def display_response(self, response: str, total_cost: float = 0.0):
        """
        Display an AI response with interactive citations and cost information.
        
        Args:
            response (str): The AI-generated response text
            total_cost (float): The total cost of the API call
            
        Returns:
            list: List of extracted suggested searches, if any
        """
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        
        # Ensure current font size is applied
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        
        # Extract suggested searches from the response
        suggested_searches = self.extract_suggested_searches(response)
        
        # Insert response and make citations interactive
        self._insert_response_with_citations(response)
        
        # Add cost information at the end
        if total_cost > 0:
            cost_text = f"\n\n---\n💰 Total Cost: ${total_cost:.6f}"
            self.response_textbox.insert("end", cost_text)
        
        self.response_textbox.configure(state="disabled")
        
        return suggested_searches
    
    @staticmethod
    def extract_suggested_searches(response: str) -> list:
        """
        Extract suggested searches from AI response text.
        
        Args:
            response (str): The AI response text
            
        Returns:
            list: List of suggested search queries, empty if none found
        """
        suggested_searches = []
        
        # Look for the section header first - more flexible patterns
        section_patterns = [
            r'Suggested Searches?\s*(?:\([^)]*\))?\s*:?\s*',
            r'Follow-up\s+Questions?\s*:?\s*',
            r'Related\s+Questions?\s*:?\s*',
            r'Additional\s+Searches?\s*:?\s*'
        ]
        
        for pattern in section_patterns:
            # Look for the pattern anywhere in the text
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                # Found the section, now extract bullet points from the rest of the text
                section_start = match.end()
                
                # Get the text after the section header
                remaining_text = response[section_start:]
                
                # Look for bullet points - handle multiple formats
                bullet_patterns = [
                    r'^\s*[-•*]\s*"([^"]+)"',  # - "quoted text"
                    r'^\s*[-•*]\s*([^\n]+)',   # - unquoted text
                    r'^\s*\d+\.\s*"([^"]+)"', # 1. "numbered quoted"
                    r'^\s*\d+\.\s*([^\n]+)'   # 1. numbered unquoted
                ]
                
                for bullet_pattern in bullet_patterns:
                    bullet_matches = re.finditer(bullet_pattern, remaining_text, re.MULTILINE)
                    
                    for bullet_match in bullet_matches:
                        text = bullet_match.group(1).strip()
                        if text and text not in suggested_searches:  # Avoid duplicates
                            suggested_searches.append(text)
                
                # If we found suggestions, break out of the section loop
                if suggested_searches:
                    break
        
        return suggested_searches
    
    def _insert_response_with_citations(self, response: str):
        """
        Insert response text and make citation numbers interactive and section headers colored.
        
        Args:
            response (str): The AI response text containing citations like [1], [2], etc.
        """
        # Pattern to match citation references like [1], [2], [10], etc.
        citation_pattern = r'\[(\d+)\]'
        
        # Pattern to match section headers (case insensitive, at start of line or after newline)
        section_header_pattern = r'(?:^|\n)(Direct Answer|Explanation|Sources|Follow-ups?|Summary|Conclusion|Key Points?|Important Notes?|Additional Information|Suggest(?:ed)?\s+Search(?:es)?)(?:\s*\n|$)'
        
        # Find all citations and their positions
        citations = list(re.finditer(citation_pattern, response))
        section_headers = list(re.finditer(section_header_pattern, response, re.IGNORECASE | re.MULTILINE))
        
        # If no special formatting needed, insert text normally
        if not citations and not section_headers:
            self.response_textbox.insert("1.0", response)
            return
        
        # Combine and sort all matches by position
        all_matches = []
        
        # Add citations
        for match in citations:
            all_matches.append({
                'type': 'citation',
                'match': match,
                'start': match.start(),
                'end': match.end()
            })
        
        # Add section headers
        for match in section_headers:
            all_matches.append({
                'type': 'section_header',
                'match': match,
                'start': match.start(1),  # Group 1 is the header text
                'end': match.end(1)
            })
        
        # Sort by start position
        all_matches.sort(key=lambda x: x['start'])
        
        # Insert text with formatting
        current_pos = 0
        insert_index = "1.0"
        
        for item in all_matches:
            match = item['match']
            
            # Insert text before this match
            before_text = response[current_pos:item['start']]
            if before_text:
                self.response_textbox.insert(insert_index, before_text)
                insert_index = self.response_textbox.index(f"{insert_index}+{len(before_text)}c")
            
            if item['type'] == 'citation':
                # Handle citation
                citation_text = match.group(0)  # e.g., "[1]"
                citation_number = int(match.group(1))  # e.g., 1
                
                # Insert the citation text
                start_index = insert_index
                self.response_textbox.insert(insert_index, citation_text)
                end_index = self.response_textbox.index(f"{insert_index}+{len(citation_text)}c")
                
                # Create a clickable tag for this citation
                tag_name = f"citation_{citation_number}"
                self.response_textbox.tag_add(tag_name, start_index, end_index)
                
                # Style the citation (no font option due to CustomTkinter scaling)
                self.response_textbox.tag_config(
                    tag_name,
                    foreground=OrangeBlackTheme.get_accent_color(),
                    underline=True
                )
                
                # Bind click event
                self.response_textbox.tag_bind(
                    tag_name,
                    "<Button-1>",
                    lambda e, num=citation_number: self._on_citation_clicked(num)
                )
                
                # Add hover effect
                self.response_textbox.tag_bind(
                    tag_name,
                    "<Enter>",
                    lambda e, tag=tag_name: self.response_textbox.tag_config(
                        tag, foreground=OrangeBlackTheme.get_hover_color()
                    )
                )
                self.response_textbox.tag_bind(
                    tag_name,
                    "<Leave>",
                    lambda e, tag=tag_name: self.response_textbox.tag_config(
                        tag, foreground=OrangeBlackTheme.get_accent_color()
                    )
                )
                
                insert_index = end_index
                current_pos = item['end']
                
            elif item['type'] == 'section_header':
                # Handle section header
                header_text = match.group(1)  # The header text without newlines
                
                # Insert the header text
                start_index = insert_index
                self.response_textbox.insert(insert_index, header_text)
                end_index = self.response_textbox.index(f"{insert_index}+{len(header_text)}c")
                
                # Create a tag for this section header
                tag_name = f"section_header_{len(all_matches)}"
                self.response_textbox.tag_add(tag_name, start_index, end_index)
                
                # Style the section header
                self.response_textbox.tag_config(
                    tag_name,
                    foreground=OrangeBlackTheme.get_accent_color()
                )
                
                insert_index = end_index
                current_pos = item['end']
        
        # Insert remaining text after last citation
        remaining_text = response[current_pos:]
        if remaining_text:
            self.response_textbox.insert(insert_index, remaining_text)
    
    def _on_citation_clicked(self, citation_number: int):
        """
        Handle citation click event.
        
        Args:
            citation_number (int): The number of the clicked citation (1-based)
        """
        if self.on_citation_click:
            self.on_citation_click(citation_number)
    
    def set_citation_click_handler(self, handler: Callable[[int], None]):
        """
        Set the callback function for citation clicks.
        
        Args:
            handler: Function to call when a citation is clicked, receives citation number
        """
        self.on_citation_click = handler
    
    def display_searching_message(self):
        """Display a searching message while search is in progress."""
        searching_msg = "🔍 Searching knowledge base and generating response...\n\nPlease wait while I find relevant information and prepare your answer."
        
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        # Ensure current font size is applied
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        self.response_textbox.insert("1.0", searching_msg)
        self.response_textbox.configure(state="disabled")
    
    def display_no_context_message(self):
        """Display message when no context was found."""
        no_context_msg = (
            "❌ No relevant information found in the knowledge base.\n\n"
            "I couldn't find any documents that match your question. "
            "Try rephrasing your question using different keywords, or check if the "
            "relevant documents have been uploaded to the knowledge base."
        )
        
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        # Ensure current font size is applied
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        self.response_textbox.insert("1.0", no_context_msg)
        self.response_textbox.configure(state="disabled")
    
    def display_error(self, error_message: str):
        """
        Display an error message.
        
        Args:
            error_message (str): Error message to display
        """
        error_msg = f"❌ Error: {error_message}"
        
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        # Ensure current font size is applied
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        self.response_textbox.insert("1.0", error_msg)
        self.response_textbox.configure(state="disabled")
    
    def _zoom_in(self):
        """Increase font size for better readability."""
        if self._current_font_size < self._max_font_size:
            self._current_font_size += 2
            self._update_font_size()
    
    def _zoom_out(self):
        """Decrease font size to fit more content."""
        if self._current_font_size > self._min_font_size:
            self._current_font_size -= 2
            self._update_font_size()
    
    def _update_font_size(self):
        """
        Update the font size of the response textbox and refresh the display.
        Preserves current content and formatting.
        """
        # Update the textbox font
        self.response_textbox.configure(
            font=ctk.CTkFont(size=self._current_font_size, weight="normal")
        )
        
        # Update the font size label
        self.font_size_label.configure(text=f"{self._current_font_size}px")
        
        # Update button states based on zoom limits
        self.zoom_in_button.configure(
            state="normal" if self._current_font_size < self._max_font_size else "disabled"
        )
        self.zoom_out_button.configure(
            state="normal" if self._current_font_size > self._min_font_size else "disabled"
        )
        
        # Force textbox to refresh and maintain word wrapping
        self.response_textbox.update_idletasks()
