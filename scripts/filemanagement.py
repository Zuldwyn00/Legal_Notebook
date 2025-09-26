# ─── STANDARD LIBRARY IMPORTS ──────────────────────────────────────────────────────
from typing import List, Dict, Any

# ─── THIRD-PARTY IMPORTS ────────────────────────────────────────────────────────────
import pymupdf
from langchain_text_splitters import TokenTextSplitter
from tika import parser
import os


# ─── LOCAL IMPORTS ──────────────────────────────────────────────────────────────────
from utils import load_config, setup_logger, count_tokens


# ─── LOGGER & CONFIG ────────────────────────────────────────────────────────────────
config = load_config()
logger = setup_logger(__name__, config)

# Cache for accessible scanner path to avoid repeated path testing
_accessible_scanner_path_cache = None

# Global flag to enable/disable scanner folder detection
# Set to False to use relative paths only, True to detect scanner folder paths
ENABLE_SCANNER_DETECTION = False


# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────────

# ─── SCANNER FOLDER PATH DETECTION ────────────────────────────────────────────────
# NOTE: The following functions are specifically for detecting scanner folder paths
# on network drives. If you want to use relative paths only, set ENABLE_SCANNER_DETECTION = False
# at the top of this file.
#
# TO DISABLE SCANNER DETECTION: Change ENABLE_SCANNER_DETECTION = False above.
# This will make the system use relative paths only.

def detect_network_drive_mapping() -> str:
    """
    Detect the actual network drive mapping for the scanner path.
    This helps when the drive letter might be different (S:, F:, etc.).
    
    Returns:
        str: The mapped drive path if found, or empty string if not found
    """
    try:
        import subprocess
        import re
        
        # Get all mapped drives using net use command
        result = subprocess.run(['net', 'use'], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            # Look for drives mapped to the scanner IP
            for line in result.stdout.split('\n'):
                if '192.168.1.20' in line and 'scanner' in line.lower():
                    # Extract drive letter from the line
                    match = re.search(r'([A-Z]):\s+\\\\192\.168\.1\.20\\scanner', line)
                    if match:
                        drive_letter = match.group(1)
                        logger.info("Found network drive mapping: %s: -> \\\\192.168.1.20\\scanner", drive_letter)
                        return f"{drive_letter}:\\"
        
        logger.debug("No network drive mapping found for scanner IP")
        return ''
        
    except Exception as e:
        logger.debug("Error detecting network drive mapping: %s", str(e))
        return ''


def find_accessible_scanner_path() -> str:
    """
    Dynamically find the accessible scanner path by testing different possible locations.
    Uses caching to avoid repeated path testing on subsequent calls.
    
    SCANNER-SPECIFIC FUNCTION: This function is designed specifically for detecting
    scanner folder paths on network drives. To disable scanner path detection and use
    relative paths only, set ENABLE_SCANNER_DETECTION = False at the top of this file.
    
    Returns:
        str: The first accessible scanner path found, or empty string if none found
    """
    global _accessible_scanner_path_cache
    
    # Return cached result if available
    if _accessible_scanner_path_cache is not None:
        return _accessible_scanner_path_cache
    
    # Check if scanner detection is enabled
    if not ENABLE_SCANNER_DETECTION:
        logger.debug("Scanner detection disabled, using relative paths only")
        _accessible_scanner_path_cache = ''
        return ''
    
    # Get the base path from config (e.g., "S:\\JustinPinter\\Legal_Notebook")
    base_path = config.get('vector_database', {}).get('root_path', '')
    if not base_path or not base_path.strip():
        _accessible_scanner_path_cache = ''
        return ''
    
    # =============================================================================
    # SCANNER PATH DETECTION LOGIC
    # =============================================================================
    
    # Extract the project folder name (e.g., "Legal_Notebook")
    project_folder = os.path.basename(os.path.normpath(base_path))
    
    # Extract the parent folder name (e.g., "JustinPinter")
    # From "S:\JustinPinter\Legal_Notebook" -> "JustinPinter"
    parent_folder = os.path.basename(os.path.dirname(os.path.normpath(base_path)))
    
    # Try to detect the actual network drive mapping first
    detected_drive = detect_network_drive_mapping()
    
    # Define possible scanner paths to test
    possible_paths = [
        base_path,  # Direct path from config (S:\JustinPinter\Legal_Notebook)
        f"\\\\192.168.1.20\\scanner\\scan\\{parent_folder}\\{project_folder}",  # UNC path with IP (most reliable)
        f"\\\\192.168.1.20\\scanner\\{parent_folder}\\{project_folder}",  # Alternative UNC structure
    ]
    
    # Add detected drive paths if we found a mapping
    if detected_drive:
        possible_paths.extend([
            f"{detected_drive}scan\\{parent_folder}\\{project_folder}",  # Using detected drive
            f"{detected_drive}scanner\\scan\\{parent_folder}\\{project_folder}",  # Alternative with detected drive
        ])
    
    # Add common drive letter variations
    for drive_letter in ['S', 'F', 'Z', 'X']:  # Common network drive letters
        possible_paths.extend([
            f"{drive_letter}:\\scanner\\scan\\{parent_folder}\\{project_folder}",
            f"{drive_letter}:\\scan\\{parent_folder}\\{project_folder}",
        ])
    
    # =============================================================================
    # END SCANNER PATH DETECTION LOGIC
    # =============================================================================
    
    # Test each path to find the first accessible one
    logger.debug("Testing %d possible scanner paths...", len(possible_paths))
    for i, path in enumerate(possible_paths, 1):
        try:
            normalized_path = os.path.normpath(path)
            logger.debug("Testing path %d/%d: '%s'", i, len(possible_paths), normalized_path)
            if os.path.exists(normalized_path) and os.access(normalized_path, os.R_OK):
                logger.info("Found accessible scanner path: '%s'", normalized_path)
                _accessible_scanner_path_cache = normalized_path
                return normalized_path
        except (OSError, PermissionError) as e:
            logger.debug("Path '%s' not accessible: %s", path, str(e))
            continue
    
    logger.warning("No accessible scanner path found, using relative paths")
    _accessible_scanner_path_cache = ''
    return ''


def clear_scanner_path_cache():
    """
    Clear the cached scanner path. Useful for testing or if network paths change.
    """
    global _accessible_scanner_path_cache
    _accessible_scanner_path_cache = None
    logger.debug("Scanner path cache cleared")


def set_scanner_detection(enabled: bool):
    """
    Enable or disable scanner folder detection.
    
    Args:
        enabled (bool): True to enable scanner detection, False to use relative paths only
    """
    global ENABLE_SCANNER_DETECTION, _accessible_scanner_path_cache
    
    ENABLE_SCANNER_DETECTION = enabled
    # Clear cache when changing detection mode
    _accessible_scanner_path_cache = None
    
    if enabled:
        logger.info("Scanner detection enabled")
    else:
        logger.info("Scanner detection disabled - using relative paths only")


def resolve_file_path(filepath: str) -> str:
    """
    Resolve file path by prepending accessible root_path from config.
    Dynamically detects the correct scanner path based on user access level.
    Handles both Windows backslashes and Unix forward slashes properly.
    
    Args:
        filepath (str): Original file path (relative or absolute)
        
    Returns:
        str: Resolved file path with accessible root_path prepended if found
    """
    # Find the accessible scanner path dynamically
    root_path = find_accessible_scanner_path()
    
    if root_path and root_path.strip():
        # Normalize the root path to handle both forward and backward slashes
        root_path = os.path.normpath(root_path)
        logger.debug("Using accessible rootpath: '%s', adding to filepath: '%s'", root_path, filepath)
        return os.path.join(root_path, filepath)
    
    # Fallback to relative path if no accessible root path found
    logger.debug("No accessible root path found, using relative path: '%s'", filepath)
    return filepath


def with_root_path(func):
    """
    Decorator that automatically resolves file paths by prepending root_path from config.
    The decorated function should have 'filepath' as its first parameter.
    """
    def wrapper(*args, **kwargs):
        # Get the filepath from the first argument
        if args:
            filepath = args[0]
            # Resolve the filepath with root_path
            resolved_filepath = resolve_file_path(filepath)
            # Replace the first argument with the resolved filepath
            args = (resolved_filepath,) + args[1:]
        return func(*args, **kwargs)
    return wrapper




@with_root_path
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


@with_root_path
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


@with_root_path
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

@with_root_path
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
