"""
Backend service for chat functionality.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from scripts.clients import AzureClient, ChatAgent
from scripts.vectordb import QdrantManager
from scripts.filemanagement import get_text_from_page_range
from utils import setup_logger, load_config


class ChatService:
    """
    Service class that handles chat functionality and knowledge base interactions.
    """
    
    def __init__(self):
        """Initialize the chat service with required clients."""
        self.logger = setup_logger(self.__class__.__name__, load_config())
        
        try:
            # Initialize AI clients with default model
            self.default_model = 'gpt-5-chat'
            self.chat_agent = None  # Will be created dynamically
            self.embedding_client = AzureClient('text_embedding_3_large')
            self.qdrant_client = QdrantManager()
            
            # Create initial chat agent with default model
            self._create_chat_agent(self.default_model)
            
            self.logger.info("Chat service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chat service: {str(e)}")
            raise
    
    def _create_chat_agent(self, model_name: str):
        """Create a new chat agent with the specified model."""
        try:
            # Store the current cost before creating new agent
            current_cost = 0.0
            if self.chat_agent and hasattr(self.chat_agent, 'client'):
                current_cost = self.chat_agent.client.telemetry_manager.total_price
            
            if self.chat_agent:
                # Clear conversation history from previous agent
                self.chat_agent.clear_conversation()
            
            self.chat_agent = ChatAgent(AzureClient(model_name))
            
            # Restore the accumulated cost to the new agent
            if current_cost > 0:
                self.chat_agent.client.telemetry_manager.total_price = current_cost
            
            self.logger.info(f"Created chat agent with model: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create chat agent with model {model_name}: {str(e)}")
            # Fallback to default model
            if model_name != self.default_model:
                self.logger.warning(f"Falling back to default model: {self.default_model}")
                self._create_chat_agent(self.default_model)
            else:
                raise
    
    def set_model(self, model_name: str):
        """Set the AI model to use for chat responses."""
        try:
            if model_name != getattr(self.chat_agent, 'client', None):
                self._create_chat_agent(model_name)
                self.logger.info(f"Switched to model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to switch to model {model_name}: {str(e)}")
            raise
    
    def search_knowledge_base(self, query: str, limit: int = None, source_filter: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query (str): User's search query
            limit (int, optional): Maximum number of results to return. Uses config if None.
            source_filter (List[str], optional): List of category names to search in. If None, searches all sources.
            
        Returns:
            List[Dict]: List of search results with context
        """
        try:
            # Get search limit from config if not provided
            if limit is None:
                config = load_config()
                limit = config.get('vector_database', {}).get('search_limit', 10)
            
            self.logger.info(f"Searching knowledge base for: {query} (limit: {limit}, source_filter: {source_filter if source_filter else 'All categories'})")
            
            # Get embeddings for the query
            vector_message = self.embedding_client.get_embeddings(query)
            
            # Search vector database using category names directly
            if source_filter:
                # Search specific category names
                search_results = self.qdrant_client.search_vectors(
                    'smart_advocate', 
                    vector_message, 
                    vector_name=source_filter,  # Pass list of category names
                    limit=limit
                )
                self.logger.info(f"Found {len(search_results)} results from selected categories: {source_filter}")
            else:
                # Search all available category names
                vector_names = self.qdrant_client.get_vector_names('smart_advocate')
                search_results = self.qdrant_client.search_vectors(
                    'smart_advocate', 
                    vector_message, 
                    vector_name=vector_names,  # Pass all category names
                    limit=limit
                )
                self.logger.info(f"Found {len(search_results)} results from all categories")
            
            # Extract and enrich results with actual text content
            context_chunks = []
            
            for i, result in enumerate(search_results):
                payload = result.payload
                source_file = payload['source']
                start_page = payload['start_page']
                end_page = payload['end_page']
                page_range = payload['page_range']
                
                self.logger.debug(f"Processing result {i+1}: {Path(source_file).name} pages {page_range}")
                
                # Extract text from the specific page range
                page_text = get_text_from_page_range(source_file, start_page, end_page)
                
                if page_text:
                    context_chunks.append({
                        'text': page_text,
                        'source': source_file,
                        'page_range': page_range,
                        'score': result.score,
                        'start_page': start_page,
                        'end_page': end_page
                    })
                    self.logger.debug(f"Successfully extracted text for result {i+1}")
                else:
                    self.logger.warning(f"Could not extract text from {Path(source_file).name} pages {page_range}")
            
            self.logger.info(f"Returning {len(context_chunks)} results with text content")
            return context_chunks
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {str(e)}")
            raise
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> tuple[Optional[str], float]:
        """
        Generate an AI response using the provided context.
        
        Args:
            query (str): Original user query
            context_chunks (List[Dict]): Relevant context from knowledge base
            
        Returns:
            tuple: (AI-generated response, total cost) or (None, 0.0) if generation fails
        """
        if not context_chunks:
            self.logger.warning("No context chunks provided for response generation")
            return None, 0.0
        
        try:
            self.logger.info(f"Generating AI response using {len(context_chunks)} context chunks")
            
            # Build context string for the AI
            context_text = "\n\n---\n\n".join([
                f"Source: {Path(chunk['source']).name} (Pages {chunk['page_range']})\n{chunk['text']}"
                for chunk in context_chunks
            ])
            
            # Create the complete message with context
            user_message_with_context = f"{query}\n\nCONTEXT:\n{context_text}"
            
            # Generate AI response
            ai_response = self.chat_agent.chat(user_message_with_context)
            
            # Get the total cost from the client's telemetry manager
            total_cost = self.chat_agent.client.telemetry_manager.total_price
            
            self.logger.info("Successfully generated AI response")
            return ai_response, total_cost
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {str(e)}")
            raise

    
    def get_available_sources(self) -> List[str]:
        """
        Get all available category names (document types) from the vector database.
        
        Returns:
            List[str]: List of available category names
        """
        try:
            self.logger.info("Retrieving available category names from vector database")
            vector_names = self.qdrant_client.get_vector_names('smart_advocate')
            self.logger.info(f"Found {len(vector_names)} category names")
            return vector_names
        except Exception as e:
            self.logger.error(f"Error retrieving available category names: {str(e)}")
            return []
    
    def reset_for_new_search(self):
        """Reset the chat service to a fresh state for a new search."""
        try:
            # Clear the chat agent's message history
            self.chat_agent.clear_conversation()
            
            # Note: Cost tracking is NOT reset here - it persists across searches for the session
            
            # Reset any other state as needed
            # (Add other state resets here if needed in the future)
            
            self.logger.info("Chat service reset for new search - conversation history cleared, cost tracking maintained")
        except Exception as e:
            self.logger.error(f"Error resetting chat service: {str(e)}")
            # Don't raise here, continue with search even if reset fails
            pass
