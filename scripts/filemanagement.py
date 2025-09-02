# ─── STANDARD LIBRARY IMPORTS ──────────────────────────────────────────────────────
from typing import List, Dict, Any

# ─── THIRD-PARTY IMPORTS ────────────────────────────────────────────────────────────
import pymupdf
from langchain_text_splitters import TokenTextSplitter
from tika import parser


# ─── LOCAL IMPORTS ──────────────────────────────────────────────────────────────────
from utils import load_config, setup_logger, count_tokens


# ─── LOGGER & CONFIG ────────────────────────────────────────────────────────────────
config = load_config()
logger = setup_logger(__name__, config)




def get_text_from_file(filepath: str, **kwargs):
    """
    Extract text from various file formats using Apache Tika.
    Optimized for large files with extended timeout and error handling.
    
    Args:
        filepath (str): Path to the file to extract text from
        **kwargs: Additional arguments for Tika parser
        
    Returns:
        dict: Parsed file content with 'content' key containing text
    """
    # Extended timeout for large files (10 minutes)
    request_options = {"timeout": 600}
    
    try:
        logger.info(f"Extracting text from {filepath}")
        parsed_file = parser.from_file(filepath, requestOptions=request_options, **kwargs)
        
        if not parsed_file or not parsed_file.get('content'):
            logger.warning(f"No content extracted from {filepath}")
            return {'content': ''}
            
        content = parsed_file.get('content', '')
        content_length = len(content)
        token_count = count_tokens(content)
        logger.info(f"Successfully extracted {content_length:,} characters ({token_count:,} tokens) from {filepath}")
        
        return parsed_file
        
    except Exception as e:
        logger.error(f"Failed to extract text from {filepath}: {str(e)}")
        # Return empty content instead of failing completely
        return {'content': ''}


def get_text_with_pages(filepath: str) -> Dict[str, Any]:
    """
    Extract text from PDF files page by page using PyMuPDF.
    Tracks page numbers for each portion of text.
    
    Args:
        filepath (str): Path to the PDF file
        
    Returns:
        dict: Contains 'content' (full text) and 'page_map' (character positions to page numbers)
    """
    if not filepath.lower().endswith('.pdf'):
        # Fall back to regular text extraction for non-PDF files
        return get_text_from_file(filepath)
    
    try:
        logger.info(f"Extracting text with page tracking from {filepath}")
        
        doc = pymupdf.open(filepath)
        full_text = ""
        page_map = []  # List of (start_char, end_char, page_num) tuples
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Always track page boundaries, even if empty
            start_char = len(full_text)
            full_text += page_text
            end_char = len(full_text)
            
            # Ensure each page has at least a minimal width to avoid zero-width entries
            # This prevents issues with page mapping when pages have no text
            if end_char == start_char:
                end_char = start_char + 1  # Give empty pages a minimal width
            
            # Add to page map regardless of content (empty pages still need to be tracked)
            page_map.append((start_char, end_char, page_num + 1))  # 1-based page numbers
        
        doc.close()
        
        character_count = len(full_text)
        token_count = count_tokens(full_text)
        logger.info(f"Successfully extracted {character_count:,} characters ({token_count:,} tokens) from {len(page_map)} pages")
        
        return {
            'content': full_text,
            'page_map': page_map
        }
        
    except Exception as e:
        logger.error(f"Failed to extract text with pages from {filepath}: {str(e)}")
        # Fall back to regular text extraction
        return get_text_from_file(filepath)


class FileManager:

    def __init__(self):
        self.config = config

    def find_page_range(self, chunk_start: int, chunk_end: int, page_map: List[tuple]) -> Dict[str, int]:
        """
        Find the page range for a given chunk based on character positions.
        
        Args:
            chunk_start (int): Starting character position of chunk
            chunk_end (int): Ending character position of chunk
            page_map (List[tuple]): List of (start_char, end_char, page_num) tuples
            
        Returns:
            Dict[str, int]: Dictionary with 'start_page' and 'end_page'
        """
        start_page = None
        end_page = None
        
        # Validate inputs
        if not page_map:
            logger.warning("Empty page map provided")
            return {'start_page': 1, 'end_page': 1}
        
        if chunk_start >= chunk_end:
            logger.warning(f"Invalid chunk range: start ({chunk_start}) >= end ({chunk_end})")
            return {'start_page': 1, 'end_page': 1}
        
        for start_char, end_char, page_num in page_map:
            # Check if chunk overlaps with this page
            if chunk_start < end_char and chunk_end > start_char:
                if start_page is None:
                    start_page = page_num
                end_page = page_num
        
        # If no pages found, try to find the closest page
        if start_page is None:
            logger.warning(f"No page mapping found for chunk chars {chunk_start}-{chunk_end}")
            
            # Find the page that contains the chunk start position
            for start_char, end_char, page_num in page_map:
                if chunk_start >= start_char and chunk_start < end_char:
                    start_page = page_num
                    end_page = page_num
                    break
            
            # If still no page found, find the nearest page by distance
            if start_page is None:
                min_distance = float('inf')
                nearest_page = 1
                
                for start_char, end_char, page_num in page_map:
                    # Calculate distance to chunk start
                    if chunk_start < start_char:
                        distance = start_char - chunk_start
                    elif chunk_start >= end_char:
                        distance = chunk_start - end_char + 1
                    else:
                        distance = 0
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_page = page_num
                
                start_page = nearest_page
                end_page = nearest_page
        
        result = {
            'start_page': start_page or 1,
            'end_page': end_page or start_page or 1
        }
        
        return result

    def text_splitter(
        self, text: Dict[str, Any], chunkSize: int = 2000, chunkOverlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Splits text into chunks and tracks page ranges for each chunk.
        
        Args:
            text (Dict[str, Any]): Parsed document dict with 'content' and optional 'page_map'
            chunkSize (int): Max tokens per chunk. Defaults to 2000.
            chunkOverlap (int): Tokens to overlap between chunks. Defaults to 200.
            
        Returns:
            List[Dict[str, Any]]: List of dicts with 'content', 'start_page', 'end_page'
        """
        splitter = TokenTextSplitter(
            encoding_name="o200k_base",
            chunk_size=chunkSize,
            chunk_overlap=chunkOverlap,
        )
        
        content = text["content"]
        page_map = text.get("page_map", [])
        
        # Get chunk boundaries
        chunks = splitter.split_text(content)
        
        # Track character positions and find page ranges
        chunk_data = []
        char_position = 0
        
        for i, chunk_text in enumerate(chunks):
            chunk_start = char_position
            chunk_end = char_position + len(chunk_text)
            
            # Find page range for this chunk
            if page_map:
                page_range = self.find_page_range(chunk_start, chunk_end, page_map)
            else:
                # If no page map available, default to unknown pages
                page_range = {'start_page': 1, 'end_page': 1}
                logger.warning(f"No page map available for chunk {i+1}, defaulting to page 1")
            
            chunk_data.append({
                'content': chunk_text,
                'start_page': page_range['start_page'],
                'end_page': page_range['end_page']
            })
            
            char_position = chunk_end
        
        # Calculate total token count for all chunks
        total_tokens = sum(count_tokens(chunk['content']) for chunk in chunk_data)
        logger.info(f"Split into {len(chunk_data)} chunks with page tracking (total: {total_tokens:,} tokens)")
        return chunk_data


def get_text_from_page_range(filepath: str, start_page: int, end_page: int) -> str:
    """
    Extract text from specific page range in a PDF file.
    
    Args:
        filepath (str): Path to the PDF file
        start_page (int): Starting page number (1-based)
        end_page (int): Ending page number (1-based)
        
    Returns:
        str: Text content from the specified page range
    """
    if not filepath.lower().endswith('.pdf'):
        # For non-PDF files, fall back to full text extraction
        result = get_text_from_file(filepath)
        return result.get('content', '') if result else ''
    
    try:
        logger.debug(f"Extracting text from pages {start_page}-{end_page} in {filepath}")
        
        doc = pymupdf.open(filepath)
        extracted_text = ""
        
        # Convert to 0-based indexing and ensure valid range
        start_idx = max(0, start_page - 1)
        end_idx = min(len(doc), end_page)  # Fixed: was end_page - 1, should be end_page
        
        # Validate page range
        if start_idx >= len(doc):
            logger.warning(f"Start page {start_page} is beyond document length ({len(doc)} pages)")
            doc.close()
            return ""
        
        if end_idx <= start_idx:
            logger.warning(f"Invalid page range: start_page {start_page} >= end_page {end_page}")
            doc.close()
            return ""
        
        for page_num in range(start_idx, end_idx):
            page = doc[page_num]
            page_text = page.get_text()
            extracted_text += page_text
        
        doc.close()
        
        character_count = len(extracted_text)
        token_count = count_tokens(extracted_text)
        logger.debug(f"Extracted {character_count:,} characters ({token_count:,} tokens) from pages {start_page}-{end_page}")
        return extracted_text
        
    except Exception as e:
        logger.error(f"Failed to extract text from pages {start_page}-{end_page} in {filepath}: {str(e)}")
        return ""


# ─── DEBUG FUNCTIONS ────────────────────────────────────────────────────────────────

def debug_page_mapping(filepath: str, chunk_start: int = 0, chunk_end: int = None):
    """
    Debug function to inspect page mapping for a specific file and chunk range.
    
    Args:
        filepath (str): Path to the PDF file
        chunk_start (int): Starting character position to check
        chunk_end (int): Ending character position to check (if None, uses chunk_start + 100)
    """
    if not filepath.lower().endswith('.pdf'):
        logger.warning("Debug function only works with PDF files")
        return
    
    try:
        doc = pymupdf.open(filepath)
        total_pages = len(doc)
        logger.info(f"PDF has {total_pages} pages")
        
        # Extract text with page tracking
        text_data = get_text_with_pages(filepath)
        page_map = text_data.get('page_map', [])
        
        logger.info(f"Page map has {len(page_map)} entries")
        for i, (start_char, end_char, page_num) in enumerate(page_map):
            logger.info(f"Entry {i+1}: chars {start_char}-{end_char} -> page {page_num}")
        
        # Test specific chunk range
        if chunk_end is None:
            chunk_end = chunk_start + 100
        
        logger.info(f"Testing chunk range: chars {chunk_start}-{chunk_end}")
        
        # Find page range for this chunk
        filemanager = FileManager()
        page_range = filemanager.find_page_range(chunk_start, chunk_end, page_map)
        logger.info(f"Chunk maps to pages: {page_range}")
        
        # Test text extraction
        extracted_text = get_text_from_page_range(filepath, page_range['start_page'], page_range['end_page'])
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        
        doc.close()
        
    except Exception as e:
        logger.error(f"Error in debug function: {str(e)}")
