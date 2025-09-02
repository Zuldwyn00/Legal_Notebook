
from typing import List
from utils import count_tokens, setup_logger, load_config

class TelemetryManager:
    def __init__(self, client_config: dict):
        self.input_price = client_config.get("pricing").get("input")
        self.output_price = client_config.get("pricing").get("output")
        self.total_price = 0

        self.config = load_config()
        self.logger = setup_logger(self.__class__.__name__, self.config)


    def calculate_price(self, text: str | List, is_input: bool):
        # Handle both string and list inputs
        if isinstance(text, list):
            # Extract text content from message objects using lambda
            text_content = " ".join(map(lambda msg: getattr(msg, 'content', str(msg)), text))
        else:
            text_content = str(text)
        
        tokens = count_tokens(text_content)
        
        if is_input:
            price = (tokens / 1_000_000) * self.input_price
        else:
            price = (tokens / 1_000_000) * self.output_price

        self.logger.info("Tokens: %d, %s, Price per 1M tokens: $%.2f, Estimated price: '$%.6f'", 
                        tokens, "INPUT" if is_input else "OUTPUT", 
                        self.input_price if is_input else self.output_price, price)
        self.total_price += price