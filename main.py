

import qdrant_client
from scripts.filemanagement import FileManager, get_text_from_file, get_text_with_pages, get_text_from_page_range
from scripts.vectordb import QdrantManager
from pathlib import Path
from utils import *

from scripts.clients import  AzureClient, ChatAgent

# ─── LOGGER & CONFIG ────────────────────────────────────────────────────────────────
config = load_config()
logger = setup_logger(__name__, config)




def embedding_test(filepath: str, batch_size: int = 50):
    """
    Memory-efficient document ingestion pipeline for large files.
    Processes documents in batches to handle any file size.
    
    Args:
        filepath (str): Path to directory containing documents
        batch_size (int): Number of chunks to process in each batch. Defaults to 50.
    """
    def normalize_vector_name(filename: str) -> str:
        """
        Normalize filename to create clean, lowercase vector name.
        
        Args:
            filename (str): Original filename
            
        Returns:
            str: Normalized, lowercase vector name
        """
        import re
        # Remove extension and get stem
        name = Path(filename).stem
        # Remove trailing numbers and underscores
        name = name.rstrip('0123456789_')
        # Remove special characters and punctuation
        name = re.sub(r'[!@#$%^&*()+=<>?:"{}|\\[\]`~;,.]', '', name)
        # Clean up multiple spaces and trim, then convert to lowercase and replace spaces with underscores
        return '_'.join(name.split()).lower()
    
    ensure_directories()
    embedding_agent = AzureClient(client_config="text_embedding_3_large")
    filemanager = FileManager()
    qdrantmanager = QdrantManager()
    
    # Convert to Path object and get the base directory for relative path calculation
    base_dir = Path(filepath).resolve()
    files = find_files(base_dir)
    
    # First pass: collect all unique vector names to create collection schema
    print("🔍 Discovering vector names for collection schema...")
    vector_names = set()
    for file in files:
        vector_name = normalize_vector_name(file.name)
        vector_names.add(vector_name)
        print(f"  📝 Found vector name: '{vector_name}' from {file.name}")
    vector_names.add("chunk")
    # Create collection with all discovered vector names
    print(f"\n🏗️  Creating collection 'smart_advocate' with {len(vector_names)} vector names...")
    vector_config = {}
    for name in sorted(vector_names):
        vector_config[name] = qdrant_client.http.models.VectorParams(
            size=3072, 
            distance=qdrant_client.http.models.Distance.COSINE
        )
        print(f"  ✅ Added vector: '{name}'")
    
    qdrantmanager.create_collection("smart_advocate", vector_config)
    print("✅ Collection created successfully!\n")
    

    progress = len(files)
    print(f"Found {progress} files")
    processed_files_data = load_from_json()

    for file in files:
        # Store the path as it was passed in (scripts/data/pdfs) + the filename
        # This ensures we get the correct relative path structure
        relative_path = f"{filepath}/{file.name}"
        filename_str = relative_path

        if filename_str in processed_files_data:
            progress -= 1
            print(f"Skipping already processed file: {file.name}")
            continue
            
        print(f"Processing file {file.name} (size: {file.stat().st_size / (1024*1024):.2f} MB)")
        
        try:
            # Memory-efficient text extraction with page tracking
            file_text = get_text_with_pages(str(file))
            
            if not file_text or not file_text.get('content'):
                print(f"⚠️  No text content extracted from {file.name}, skipping...")
                continue
                
            file_chunks = filemanager.text_splitter(file_text)
            total_chunks = len(file_chunks)
            print(f"Split into {total_chunks} chunks")
            
            # Process chunks in batches to prevent memory overflow
            chunks_processed = 0
            
            for batch_start in range(0, total_chunks, batch_size):
                batch_end = min(batch_start + batch_size, total_chunks)
                current_batch = file_chunks[batch_start:batch_end]
                
                print(f"Processing batch {batch_start//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} "
                      f"(chunks {batch_start+1}-{batch_end})")
                
                embeddings = []
                payloads = []
                
                # Generate embeddings for current batch
                for i, chunk in enumerate(current_batch):
                    global_chunk_index = batch_start + i
                    chunk_embedding = embedding_agent.get_embeddings(chunk['content'])
                    embeddings.append(chunk_embedding)
                    
                    # Create payload with full relative source file path from project root
                    payload = {
                        "source": relative_path,
                        "chunk_index": global_chunk_index,
                        "start_page": chunk['start_page'],
                        "end_page": chunk['end_page'],
                        "page_range": f"{chunk['start_page']}-{chunk['end_page']}" if chunk['start_page'] != chunk['end_page'] else str(chunk['start_page']),
                        "file_size_mb": round(file.stat().st_size / (1024*1024), 2),
                        "total_chunks": total_chunks,
                        "link": ""  # Website link for the PDF (can be populated later)
                    }
                    payloads.append(payload)
                
                # Extract clean vector name from source file path
                vector_name = normalize_vector_name(file.name)
                print(f"📝 Setting vector name: '{vector_name}' for chunks from {file.name}")
                
                # Upload batch to Qdrant
                qdrantmanager.add_embeddings_batch(
                    collection_name="smart_advocate",
                    embeddings=embeddings,
                    metadatas=payloads,
                    vector_name=vector_name,
                )
                
                chunks_processed += len(current_batch)
                print(f"✅ Uploaded batch ({len(current_batch)} chunks) - "
                      f"Progress: {chunks_processed}/{total_chunks} chunks")
                
                # Clear batch data to free memory
                del embeddings, payloads, current_batch
            
            print(f"✅ Successfully processed {file.name}: {chunks_processed} total chunks")
            
        except Exception as e:
            print(f"❌ Error processing {file.name}: {str(e)}")
            logger.error(f"Failed to process {file.name}: {str(e)}")
            continue

        # Mark file as processed
        processed_files_data[filename_str] = True
        save_to_json(processed_files_data)
        progress -= 1
        print(f"📊 Overall progress: {len(files) - progress}/{len(files)} files completed")
        print(f"Finished processing and marked {file.name} as complete.\n")


def run_ocr_on_folder(folder_path: str):
    """
    Applies OCR to all PDF files in a specified folder.

    Args:
        folder_path (str): The path to the folder containing PDF files.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.error(f"Provided path '{folder_path}' is not a valid directory.")
        return

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        logger.info(f"No PDF files found in '{folder_path}'.")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process.")
    for pdf_file in pdf_files:
        try:
            apply_ocr(str(pdf_file))
        except Exception as e:
            logger.error(f"An error occurred while processing {pdf_file.name}: {e}")

def test_chat():
    # Initialize the chat agent with Azure client
    chat_agent = ChatAgent(AzureClient('gpt-4.1'))
    embedding_client = AzureClient('text_embedding_3_small')        
    qdrant_client = QdrantManager()
         
    # Test query
    message = "How do I add a clients signature to their contact card?"
    print(f"🔍 Query: {message}")
    
    # Get embeddings and search vector database
    vector_message = embedding_client.get_embeddings(message)
    found_data = qdrant_client.search_vectors('smart_advocate', vector_message, limit=10)
    
    print(f"\n📊 Found {len(found_data)} relevant chunks:")
    
    # Extract actual text content from found page ranges
    context_chunks = []
    for i, result in enumerate(found_data):
        payload = result.payload
        source_file = payload['source']
        start_page = payload['start_page']
        end_page = payload['end_page']
        page_range = payload['page_range']
        
        print(f"\n📄 Result {i+1}:")
        print(f"   Source: {Path(source_file).name}")
        print(f"   Pages: {page_range}")

        # Extract text from the specific page range
        page_text = get_text_from_page_range(source_file, start_page, end_page)
        
        if page_text:
            context_chunks.append({
                'text': page_text,
                'source': Path(source_file).name,
                'page_range': page_range,
                'score': result.score
            })

        else:
            print(f"   ⚠️  Could not extract text from pages {page_range}")
    
    # Generate AI response using context
    if context_chunks:
        print(f"\n🤖 Generating AI response using {len(context_chunks)} context chunks...")
        
        # Build context string for the AI (the prompt in prompts.yaml will handle formatting)
        context_text = "\n\n---\n\n".join([
            f"Source: {chunk['source']} (Pages {chunk['page_range']})\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        # The chat agent will use the legal_chat prompt from prompts.yaml which expects context
        user_message_with_context = f"{message}\n\nCONTEXT:\n{context_text}"
        
        # Get AI response
        ai_response = chat_agent.chat(user_message_with_context)
        print(f"\n💬 AI Response:\n{ai_response}")
        
    else:
        print("\n❌ No usable context found - cannot generate AI response")
            

def main():
    """
    Main function - uncomment the function you want to test.
    """

    embedding_test("scripts/data/pdfs")
    

if __name__ == "__main__":
    main()
