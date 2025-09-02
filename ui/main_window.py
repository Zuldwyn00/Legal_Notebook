"""
Main application window for the NotebookLM-style chat interface.
"""

import customtkinter as ctk
import threading
from typing import Optional, List
from pathlib import Path

from .components.query_input import QueryInputFrame
from .components.results_display import ResultsDisplayFrame
from .components.ai_response import AIResponseFrame
from .components.source_filter import SourceFilterFrame
from .services.chat_service import ChatService
from .theme import OrangeBlackTheme
from utils import setup_logger, load_config


class MainWindow(ctk.CTk):
    """
    Main application window with chat interface.
    """
    
    def __init__(self):
        super().__init__()
        
        # Setup logging
        self.logger = setup_logger(self.__class__.__name__, load_config())
        
        # Apply custom orange and black theme
        OrangeBlackTheme.apply_theme()
        
        # Initialize services
        self.chat_service = ChatService()
        
        # Initialize source filter state
        self.current_source_filter = None
        
        # Configure window
        self.title("AI Knowledge Assistant")
        self.geometry("1200x800")
        self.minsize(1000, 700)  # Increased minimum size to prevent layout issues
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=OrangeBlackTheme.get_primary_bg())
        
        # Setup UI
        self._setup_layout()
        self._setup_components()
        self._bind_events()
        
        self.logger.info("Main window initialized")
    
    def _setup_layout(self):
        """Configure the main layout grid."""
        # Configure columns for sidebar + main content layout
        self.grid_columnconfigure(0, weight=0, minsize=120)  # Sidebar - starts collapsed
        self.grid_columnconfigure(1, weight=1)  # Main content - expandable
        self.grid_rowconfigure(0, weight=0)  # Header - fixed size
        self.grid_rowconfigure(1, weight=0)  # Query input - fixed size
        self.grid_rowconfigure(2, weight=1)  # Main content area - expandable
    
    def _setup_components(self):
        """Initialize and place UI components."""
        
        # Header - spans both columns
        header_frame = ctk.CTkFrame(self, fg_color=OrangeBlackTheme.get_secondary_bg())
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 AI Knowledge Assistant",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        title_label.pack(pady=15)
        
        # Query input section - spans both columns
        self.query_frame = QueryInputFrame(
            self,
            on_search=self._handle_search
        )
        self.query_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Left sidebar frame (contains source filter and results)
        self.left_sidebar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_sidebar_frame.grid(row=2, column=0, sticky="nsew", padx=(10, 5), pady=5)
        
        # Configure left sidebar grid - use columns for side-by-side layout
        self.left_sidebar_frame.grid_columnconfigure(0, weight=0, minsize=200)  # Source filter - fixed width
        self.left_sidebar_frame.grid_columnconfigure(1, weight=1)  # Results - expandable
        self.left_sidebar_frame.grid_rowconfigure(0, weight=1)  # Both components take full height
        
        # Source filter frame (left side of sidebar)
        self.source_filter_frame = SourceFilterFrame(
            self.left_sidebar_frame,
            on_source_filter_change=self._handle_source_filter_change
        )
        self.source_filter_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Results sidebar (right side of sidebar)
        self.results_frame = ResultsDisplayFrame(self.left_sidebar_frame)
        self.results_frame.grid(row=0, column=1, sticky="nsew")
        
        # AI response section (main content - right side)
        self.ai_response_frame = AIResponseFrame(self)
        self.ai_response_frame.grid(row=2, column=1, sticky="nsew", padx=(5, 10), pady=5)
        
        # Set up citation click handler
        self.ai_response_frame.set_citation_click_handler(self._handle_citation_click)
        
        # Set up sidebar width change handler
        self.results_frame.set_width_change_handler(self._handle_sidebar_width_change)
        
        # Initialize source filter with available sources
        self._initialize_source_filter()
    
    def _initialize_source_filter(self):
        """Initialize the source filter with available sources from the vector database."""
        try:
            # Get available sources in a background thread to avoid blocking UI
            def load_sources():
                try:
                    sources = self.chat_service.get_available_sources()
                    # Update UI on main thread
                    self.after(0, self._update_source_filter, sources)
                except Exception as e:
                    self.logger.error(f"Failed to load sources: {e}")
                    # Show error on main thread
                    self.after(0, self._show_error, f"Failed to load sources: {str(e)}")
            
            # Start loading sources in background
            source_thread = threading.Thread(target=load_sources, daemon=True)
            source_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error initializing source filter: {e}")
    
    def _update_source_filter(self, sources: List[str]):
        """Update the source filter with available sources."""
        try:
            self.source_filter_frame.load_sources(sources)
            self.logger.info(f"Source filter updated with {len(sources)} sources")
        except Exception as e:
            self.logger.error(f"Error updating source filter: {e}")
    
    def _handle_source_filter_change(self, selected_sources: List[str]):
        """Handle changes in source filter selection."""
        self.logger.info(f"Source filter changed: {len(selected_sources)} sources selected")
        # Store the current selection for use in searches
        self.current_source_filter = selected_sources
    
    def _bind_events(self):
        """Bind keyboard shortcuts and events."""
        # Bind Ctrl+Enter to search from anywhere in the window
        self.bind("<Control-Return>", lambda e: self._handle_search())
    
    def _handle_search(self):
        """Handle search query with threading to prevent UI freezing."""
        query = self.query_frame.get_query()
        
        if not query.strip():
            self._show_error("Please enter a query")
            return
        
        # Get selected model and update chat service
        selected_model = self.query_frame.get_selected_model()
        try:
            self.chat_service.set_model(selected_model)
        except Exception as e:
            self._show_error(f"Failed to switch to model {selected_model}: {str(e)}")
            return
        
        # Disable search button and show loading
        self.query_frame.set_loading(True)
        
        # Clear previous results and responses
        self.results_frame.clear()
        self.ai_response_frame.clear()
        
        # Reset chat service to fresh state (clear conversation history)
        self.chat_service.reset_for_new_search()
        
        # Show searching message
        self.ai_response_frame.display_searching_message()
        
        # Run search in background thread
        search_thread = threading.Thread(
            target=self._perform_search,
            args=(query,),
            daemon=True
        )
        search_thread.start()
    
    def _perform_search(self, query: str):
        """
        Perform the actual search operation in background thread.
        
        Args:
            query (str): User's search query
        """
        try:
            self.logger.info(f"Starting search for query: {query}")
            
            # Get user-specified search limit
            search_limit = self.query_frame.get_search_limit()
            self.logger.info(f"Using search limit: {search_limit}")
            
            # Search for relevant chunks with source filtering
            search_results = self.chat_service.search_knowledge_base(
                query, 
                limit=search_limit,
                source_filter=self.current_source_filter
            )
            
            # Update UI on main thread
            self.after(0, self._update_search_results, search_results)
            
            if search_results:
                # Generate AI response
                ai_response, total_cost = self.chat_service.generate_response(query, search_results)
                self.after(0, self._update_ai_response, ai_response, total_cost)
            else:
                self.after(0, self._update_ai_response, None, 0.0)
                
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            self.after(0, self._show_error, f"Search failed: {str(e)}")
        finally:
            # Reset search state and re-enable search button
            self.after(0, self._reset_search_state)
    
    def _update_search_results(self, results):
        """Update the results display with search results."""
        self.results_frame.display_results(results)
    
    def _update_ai_response(self, response: Optional[str], total_cost: float = 0.0):
        """Update the AI response display."""
        if response:
            # Display the response and get suggested searches
            suggested_searches = self.ai_response_frame.display_response(response, total_cost)
            
            # Update session cost display
            self.query_frame.update_session_cost(total_cost)
            
            # Update example questions with suggested searches if available
            if suggested_searches:
                self.logger.info(f"Extracted {len(suggested_searches)} suggested searches from AI response")
                self.logger.debug(f"Suggested searches: {suggested_searches}")
                self.query_frame.update_example_questions(suggested_searches)
            else:
                # Keep current examples if no suggestions found
                self.logger.debug("No suggested searches found, keeping current examples")
        else:
            self.ai_response_frame.display_no_context_message()
            # Reset to default examples when no response
            self.query_frame.reset_to_default_examples()
    
    def _show_error(self, message: str):
        """Show error message to user."""
        self.ai_response_frame.display_error(message)
    
    def _handle_citation_click(self, citation_number: int):
        """
        Handle clicks on citation numbers in the AI response.
        
        Args:
            citation_number (int): The clicked citation number (1-based)
        """
        self.logger.info(f"Citation {citation_number} clicked")
        
        # Jump to the corresponding search result
        self.results_frame.jump_to_result(citation_number)
    
    def _reset_search_state(self):
        """Reset the search state to allow new searches."""
        self.current_search_active = False
        self.query_frame.set_loading(False)
        self.logger.debug("Search state reset - ready for new search")
    
    def _handle_sidebar_width_change(self, is_expanded: bool):
        """
        Handle sidebar width changes to update the grid layout.
        
        Args:
            is_expanded (bool): Whether the sidebar is expanded
        """
        if is_expanded:
            # Sidebar is expanded, give it more space for side-by-side layout
            self.grid_columnconfigure(0, weight=0, minsize=500)  # Increased for source filter + results side by side
        else:
            # Sidebar is collapsed, minimize its space
            self.grid_columnconfigure(0, weight=0, minsize=120)
        
        # Force layout update
        self.update_idletasks()
    
    def run(self):
        """Start the application."""
        self.logger.info("Starting application")
        self.mainloop()


def main():
    """Main entry point for the UI application."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
