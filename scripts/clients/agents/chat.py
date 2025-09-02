from pathlib import Path
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage

from ..base import BaseClient
from ..caching.cacheschema import SummaryCacheEntry
from utils import load_prompt, count_tokens, setup_logger, load_config




class ChatAgent:
    def __init__(self, client: BaseClient):

        if client.__class__ == BaseClient:
            raise ValueError(
            "Cannot use BaseClient directly. Please provide a concrete implementation "
            "that inherits from BaseClient (e.g., AzureClient)."
            )
        
        self.client = client
        self.prompt = load_prompt('legal_chat')
        self.logger = setup_logger(self.__class__.__name__, load_config())
        self.logger.info(
            "Initialized %s with %s", self.__class__.__name__, client.__class__.__name__
        )

    def chat(self, user_message: str) -> str:
        """
        Process a single chat message and return the AI response.
        
        Args:
            user_message (str): The user's input message.
            
        Returns:
            str: The AI's response.
        """
        # Add system prompt if this is the first message
        if not self.client.message_history:
            self.client.add_message(SystemMessage(content=self.prompt))
        
        # Add user message to client's message history
        user_msg = HumanMessage(content=user_message)
        self.client.add_message(user_msg)
        
        try:
            # Use client's invoke method which handles message history automatically
            response = self.client.invoke()
            self.logger.info("Generated response for user message")
            return response.content
        except Exception as e:
            self.logger.error("Error generating response: %s", str(e))
            raise
    
    def chat_loop(self) -> None:
        """
        Start an interactive chat loop with the AI.
        """
        print("🤖 Chat started! Type 'quit', 'exit', or 'bye' to end the conversation.\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                
                # Skip empty messages
                if not user_input:
                    continue
                
                # Get AI response
                print("🤖 Thinking...")
                ai_response = self.chat(user_input)
                
                # Display response
                print(f"AI: {ai_response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                self.logger.error("Chat loop error: %s", str(e))
    
    def clear_conversation(self) -> None:
        """
        Clear the conversation history.
        """
        self.client.clear_history()
        self.logger.info("Cleared conversation history")