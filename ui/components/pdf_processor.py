"""
PDF Processor component for processing PDF files and adding them to the vector database.
"""

import customtkinter as ctk
import threading
import os
import subprocess
from pathlib import Path
from typing import Callable, Optional, List
import sys
from datetime import datetime

# Add the scripts directory to the path to import required modules
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from ..theme import OrangeBlackTheme
from scripts.vectordb import QdrantManager
from scripts.filemanagement import FileManager, resolve_file_path
from scripts.clients import AzureClient
from utils import find_files, load_from_json, save_to_json, load_config
import qdrant_client


class PDFProcessorWindow(ctk.CTkToplevel):
    """
    Window for processing PDF files and adding them to the vector database.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configure window
        self.title("📚 PDF Processor")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Set appearance
        self.configure(fg_color=OrangeBlackTheme.get_primary_bg())
        
        # Initialize components
        self.qdrant_manager = None
        self.file_manager = None
        self.embedding_agent = None
        
        # Setup UI
        self._setup_ui()
        self._initialize_services()
        
        # Center the window on parent
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
    def _setup_ui(self):
        """Setup the user interface."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=OrangeBlackTheme.get_secondary_bg())
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📚 PDF Document Processor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        title_label.pack(pady=15)
        
        # Main content area
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Configuration section
        config_frame = ctk.CTkFrame(main_frame, fg_color=OrangeBlackTheme.get_secondary_bg())
        config_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 10))
        config_frame.grid_columnconfigure(1, weight=1)
        config_frame.grid_columnconfigure(2, weight=0)
        
        # PDF folder button (replaces instruction text)
        self.find_pdfs_btn = ctk.CTkButton(
            config_frame,
            text="📁 Open PDFs Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=self._open_pdf_folder,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color(),
            border_width=1,
            border_color=OrangeBlackTheme.BORDER_COLOR
        )
        self.find_pdfs_btn.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        
        # Vector name selection
        ctk.CTkLabel(
            config_frame,
            text="🏷️ Vector Name:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_text_color()
        ).grid(row=1, column=0, sticky="w", padx=10, pady=10)
        
        # Current vector name display
        self.vector_name_var = ctk.StringVar(value="chunk")
        self.vector_name_label = ctk.CTkLabel(
            config_frame,
            textvariable=self.vector_name_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        self.vector_name_label.grid(row=1, column=1, sticky="w", padx=(10, 10), pady=10)
        
        # Browse button for existing vector names
        self.browse_vectors_btn = ctk.CTkButton(
            config_frame,
            text="🔍 Choose Vector",
            font=ctk.CTkFont(size=11),
            height=30,
            command=self._browse_existing_vectors,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.browse_vectors_btn.grid(row=1, column=2, padx=(0, 10), pady=10)
        
        # Vector name explanation
        vector_note = ctk.CTkLabel(
            config_frame,
            text="💡 Vector names organize your embeddings (e.g., Use 'chunk' for uncategorized, 'training' for training documents)",
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_text_color()
        )
        vector_note.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 5))
        
        # OCR warning
        ocr_warning = ctk.CTkLabel(
            config_frame,
            text="⚠️ IMPORTANT: Ensure PDFs are OCRed before adding - image text will be lost without OCR!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FF6B6B"  # Red color for warning
        )
        ocr_warning.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 5))
        
        # Button frame for main action buttons
        button_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Process button
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Process PDFs",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_processing,
            fg_color=OrangeBlackTheme.get_accent_color(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.process_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Clear vector button
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear Vector",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_clearing,
            fg_color="#8B0000",  # Dark red color for destructive action
            hover_color="#A52A2A",  # Lighter red on hover
            text_color="white"
        )
        self.clear_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Progress and log section
        progress_frame = ctk.CTkFrame(main_frame, fg_color=OrangeBlackTheme.get_secondary_bg())
        progress_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        progress_frame.grid_columnconfigure(0, weight=1)
        progress_frame.grid_rowconfigure(1, weight=1)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to process PDFs",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OrangeBlackTheme.get_text_color()
        )
        self.progress_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 10), pady=(10, 5))
        self.progress_bar.set(0)
        
        # Log text area
        self.log_text = ctk.CTkTextbox(
            progress_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),
            fg_color=OrangeBlackTheme.INPUT_BG,
            border_color=OrangeBlackTheme.BORDER_COLOR,
            text_color=OrangeBlackTheme.get_text_color(),
            wrap="word"
        )
        self.log_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        
        # Scrollbar for log
        log_scrollbar = ctk.CTkScrollbar(progress_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=1, column=2, sticky="ns", pady=(0, 10))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
    def _initialize_services(self):
        """Initialize the required services."""
        try:
            self.qdrant_manager = QdrantManager()
            self.file_manager = FileManager()
            self.embedding_agent = AzureClient(client_config="text_embedding_3_large")
            self._log("✅ Services initialized successfully")
        except Exception as e:
            self._log(f"❌ Failed to initialize services: {str(e)}")
            self.process_btn.configure(state="disabled")
    
    def _browse_existing_vectors(self):
        """Browse existing vector names from the database."""
        try:
            # Get existing vector names
            vector_names = self.qdrant_manager.get_vector_names("smart_advocate")
            
            if not vector_names:
                self._log("ℹ️ No existing vectors found in collection 'smart_advocate'")
                return
            
            # Create selection dialog
            self._show_vector_selection_dialog(vector_names)
            
        except Exception as e:
            self._log(f"❌ Failed to get existing vectors: {str(e)}")
    
    def _show_vector_selection_dialog(self, vector_names: List[str]):
        """Show a dialog for selecting from existing vector names."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Vector Name")
        dialog.geometry("400x400")
        dialog.configure(fg_color=OrangeBlackTheme.get_primary_bg())
        dialog.transient(self)
        dialog.grab_set()
        
        # Configure grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text="Select Vector Name:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=OrangeBlackTheme.get_accent_color()
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Create a scrollable frame for vector names
        scrollable_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            scrollbar_button_color=OrangeBlackTheme.get_accent_color(),
            scrollbar_button_hover_color=OrangeBlackTheme.get_hover_color()
        )
        scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create buttons for each vector name
        for vector_name in vector_names:
            btn = ctk.CTkButton(
                scrollable_frame,
                text=vector_name,
                font=ctk.CTkFont(size=12),
                height=35,
                command=lambda name=vector_name: self._select_vector_name(name, dialog),
                fg_color="transparent",
                border_width=1,
                border_color=OrangeBlackTheme.BORDER_COLOR,
                text_color=OrangeBlackTheme.get_text_color(),
                hover_color=OrangeBlackTheme.get_hover_color()
            )
            btn.grid(row=len(scrollable_frame.winfo_children()), column=0, sticky="ew", padx=10, pady=2)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            dialog,
            text="Cancel",
            font=ctk.CTkFont(size=12),
            height=35,
            command=dialog.destroy,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        cancel_btn.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
    
    def _select_vector_name(self, vector_name: str, dialog):
        """Select a vector name and close the dialog."""
        self.vector_name_var.set(vector_name)
        self._log(f"✅ Selected vector name: {vector_name}")
        dialog.destroy()
    
    def _open_pdf_folder(self):
        """Open the PDF folder in the file explorer using root_path from config."""
        try:
            # Use resolve_file_path to prepend root_path to the relative path
            relative_pdf_path = "scripts/data/pdfs"
            resolved_pdf_path = resolve_file_path(relative_pdf_path)
            pdf_folder = Path(resolved_pdf_path)
            
            self._log(f"📁 Using resolved PDF folder: {pdf_folder}")
            
            # Check if folder exists
            if not pdf_folder.exists():
                self._log(f"❌ PDF folder does not exist: {pdf_folder}")
                return
            
            # Open folder in file explorer (Windows)
            # Note: explorer command returns non-zero exit status even on success
            result = subprocess.run(['explorer', str(pdf_folder)], 
                                  capture_output=True, text=True)
            
            # Check if the command actually failed (not just non-zero exit)
            if result.returncode != 0 and result.stderr:
                self._log(f"❌ Failed to open file explorer: {result.stderr}")
            else:
                self._log(f"📁 Opened PDF folder: {pdf_folder}")
            
        except Exception as e:
            self._log(f"❌ Error opening PDF folder: {str(e)}")
    
    def _start_processing(self):
        """Start the PDF processing in a background thread."""
        # Validate inputs
        if not self._validate_inputs():
            return
        
        # Disable buttons and show processing state
        self.process_btn.configure(text="🔄 Processing...", state="disabled")
        self.clear_btn.configure(state="disabled")
        self.find_pdfs_btn.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Start processing in background thread
        process_thread = threading.Thread(target=self._process_pdfs, daemon=True)
        process_thread.start()
    
    def _start_clearing(self):
        """Start the vector clearing in a background thread."""
        # Validate inputs
        if not self._validate_inputs():
            return
        
        # Show confirmation dialog
        vector_name = self.vector_name_var.get().strip()
        
        # Check if there are any vectors to clear
        collection_name = "smart_advocate"
        vector_count = self.qdrant_manager.count_vectors(collection_name, vector_name)
        
        if vector_count == 0:
            self._log(f"ℹ️ No vectors found with name '{vector_name}' - nothing to clear")
            return
        elif vector_count < 0:
            self._log(f"❌ Error checking vector count for '{vector_name}'")
            return
        
        if not self._confirm_clear_vector(vector_name):
            return
        
        # Disable buttons and show clearing state
        self.clear_btn.configure(text="🔄 Clearing...", state="disabled")
        self.process_btn.configure(state="disabled")
        self.find_pdfs_btn.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Start clearing in background thread
        clear_thread = threading.Thread(target=self._clear_vector, daemon=True)
        clear_thread.start()
    
    def _confirm_clear_vector(self, vector_name: str) -> bool:
        """Show confirmation dialog for clearing vectors."""
        # Get count of vectors that will be removed
        collection_name = "smart_advocate"
        vector_count = self.qdrant_manager.count_vectors(collection_name, vector_name)
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Vector Clearing")
        dialog.geometry("500x350")
        dialog.configure(fg_color=OrangeBlackTheme.get_primary_bg())
        dialog.transient(self)
        dialog.grab_set()
        
        # Configure grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Warning title
        title_label = ctk.CTkLabel(
            dialog,
            text="⚠️ WARNING: Destructive Action",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF6B6B"
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Warning message with count
        if vector_count > 0:
            count_text = f"Found {vector_count} vectors to delete"
        elif vector_count == 0:
            count_text = "No vectors found with this name"
        else:
            count_text = "Unable to count vectors (error occurred)"
        
        message_text = f"""You are about to PERMANENTLY DELETE all vectors with the name:

"{vector_name}"

{count_text}

This action will:
• Remove all embeddings for this vector from the database
• Remove corresponding entries from the processed files list
• Make files available for re-processing

This action CANNOT be undone!

Are you sure you want to continue?"""
        
        message_label = ctk.CTkLabel(
            dialog,
            text=message_text,
            font=ctk.CTkFont(size=12),
            text_color=OrangeBlackTheme.get_text_color(),
            justify="left"
        )
        message_label.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=dialog.destroy,
            fg_color=OrangeBlackTheme.get_secondary_bg(),
            hover_color=OrangeBlackTheme.get_hover_color(),
            text_color=OrangeBlackTheme.get_text_color()
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Confirm button
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Yes, Clear Vectors",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            command=lambda: self._confirm_and_close(dialog),
            fg_color="#8B0000",
            hover_color="#A52A2A",
            text_color="white"
        )
        confirm_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Store the result
        self._clear_confirmed = False
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return self._clear_confirmed
    
    def _confirm_and_close(self, dialog):
        """Confirm the clearing action and close dialog."""
        self._clear_confirmed = True
        dialog.destroy()
    
    def _validate_inputs(self) -> bool:
        """Validate user inputs."""
        # Use resolve_file_path to prepend root_path to the relative path
        relative_pdf_path = "scripts/data/pdfs"
        resolved_pdf_path = resolve_file_path(relative_pdf_path)
        
        if not os.path.exists(resolved_pdf_path):
            self._log(f"❌ PDF folder does not exist: {resolved_pdf_path}")
            return False
        
        return True
    
    def _process_pdfs(self):
        """Process PDF files following the embedding_test logic."""
        try:
            # Use resolve_file_path to prepend root_path to the relative path
            relative_pdf_path = "scripts/data/pdfs"
            folder_path = resolve_file_path(relative_pdf_path)
            
            vector_name = self.vector_name_var.get().strip()
            batch_size = 50  # Fixed batch size
            
            self._log(f"🚀 Starting PDF processing...")
            self._log(f"📁 Folder: {folder_path}")
            self._log(f"🏷️ Vector name: {vector_name}")
            self._log(f"📦 Batch size: {batch_size}")
            
            # Find PDF files
            base_dir = Path(folder_path).resolve()
            files = find_files(base_dir)
            
            if not files:
                self._log("❌ No PDF files found in the specified folder")
                self.after(0, self._reset_processing_state)
                return
            
            self._log(f"📚 Found {len(files)} PDF files")
            
            # Load processed files list
            processed_files_data = load_from_json()
            self._log(f"📋 Loaded {len(processed_files_data)} already processed files")
            
            # Filter out already processed files
            unprocessed_files = []
            for file in files:
                # Convert file path to the format used in processed_files.json
                relative_path = str(file.relative_to(Path(__file__).parent.parent.parent))
                
                # Normalize path separators for comparison (handle both / and \ paths)
                normalized_relative_path = relative_path.replace("\\", "/")
                
                # Check if file is already processed (handle both forward and backward slashes)
                is_processed = False
                for processed_path in processed_files_data.keys():
                    normalized_processed_path = processed_path.replace("\\", "/")
                    if normalized_relative_path.lower() == normalized_processed_path.lower():
                        is_processed = True
                        break
                
                if not is_processed:
                    unprocessed_files.append(file)
                else:
                    self._log(f"⏭️ Skipping already processed: {file.name}")
            
            if not unprocessed_files:
                self._log("✅ All files have already been processed!")
                self.after(0, self._reset_processing_state)
                return
            
            self._log(f"🔄 Processing {len(unprocessed_files)} unprocessed files")
            files = unprocessed_files  # Use only unprocessed files
            
            # Check if collection exists, create if it doesn't
            try:
                collection_info = self.qdrant_manager.client.get_collection("smart_advocate")
                self._log("✅ Using existing collection 'smart_advocate'")
            except Exception:
                self._log("🏗️ Creating new collection 'smart_advocate'")
                vector_config = {
                    vector_name: qdrant_client.http.models.VectorParams(
                        size=3072, 
                        distance=qdrant_client.http.models.Distance.COSINE
                    )
                }
                self.qdrant_manager.create_collection("smart_advocate", vector_config)
                self._log("✅ Collection created successfully")
            
            # Process files
            total_files = len(files)
            processed_files = 0
            
            for file in files:
                try:
                    self._log(f"📄 Processing: {file.name}")
                    
                    # Extract text with pages
                    from scripts.filemanagement import get_text_with_pages
                    file_text = get_text_with_pages(str(file))
                    
                    if not file_text or not file_text.get('content'):
                        self._log(f"⚠️ No text content extracted from {file.name}, skipping...")
                        continue
                    
                    # Split text into chunks
                    file_chunks = self.file_manager.text_splitter(file_text)
                    total_chunks = len(file_chunks)
                    self._log(f"✂️ Split into {total_chunks} chunks")
                    
                    # Process chunks in batches
                    chunks_processed = 0
                    
                    for batch_start in range(0, total_chunks, batch_size):
                        batch_end = min(batch_start + batch_size, total_chunks)
                        current_batch = file_chunks[batch_start:batch_end]
                        
                        self._log(f"📦 Processing batch {batch_start//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}")
                        
                        embeddings = []
                        payloads = []
                        
                        # Generate embeddings for current batch
                        for i, chunk in enumerate(current_batch):
                            global_chunk_index = batch_start + i
                            chunk_embedding = self.embedding_agent.get_embeddings(chunk['content'])
                            embeddings.append(chunk_embedding)
                            
                            # Create payload
                            payload = {
                                "source": f"{folder_path}/{file.name}",
                                "chunk_index": global_chunk_index,
                                "start_page": chunk['start_page'],
                                "end_page": chunk['end_page'],
                                "page_range": f"{chunk['start_page']}-{chunk['end_page']}" if chunk['start_page'] != chunk['end_page'] else str(chunk['start_page']),
                                "file_size_mb": round(file.stat().st_size / (1024*1024), 2),
                                "total_chunks": total_chunks,
                                "link": ""
                            }
                            payloads.append(payload)
                        
                        # Upload batch to Qdrant
                        self.qdrant_manager.add_embeddings_batch(
                            collection_name="smart_advocate",
                            embeddings=embeddings,
                            metadatas=payloads,
                            vector_name=vector_name,
                        )
                        
                        chunks_processed += len(current_batch)
                        self._log(f"✅ Uploaded batch ({len(current_batch)} chunks)")
                        
                        # Update progress
                        progress = (processed_files + chunks_processed / total_chunks) / total_files
                        self.after(0, self.progress_bar.set, progress)
                        
                        # Clear batch data to free memory
                        del embeddings, payloads, current_batch
                    
                    self._log(f"✅ Successfully processed {file.name}: {chunks_processed} total chunks")
                    
                    # Mark file as processed in the JSON file
                    relative_path = str(file.relative_to(Path(__file__).parent.parent.parent))
                    # Normalize to forward slashes for consistency
                    normalized_path = relative_path.replace("\\", "/")
                    processed_files_data[normalized_path] = True
                    save_to_json(processed_files_data)
                    self._log(f"📝 Updated processed files list")
                    
                    processed_files += 1
                    
                    # Update progress
                    progress = processed_files / total_files
                    self.after(0, self.progress_bar.set, progress)
                    
                except Exception as e:
                    self._log(f"❌ Error processing {file.name}: {str(e)}")
                    continue
            
            self._log(f"🎉 Processing complete! Processed {processed_files}/{total_files} files")
            self.after(0, self.progress_bar.set, 1.0)
            
        except Exception as e:
            self._log(f"❌ Processing failed: {str(e)}")
        finally:
            self.after(0, self._reset_processing_state)
    
    def _clear_vector(self):
        """Clear vectors from the database and update processed files list."""
        try:
            vector_name = self.vector_name_var.get().strip()
            collection_name = "smart_advocate"
            
            self._log(f"🗑️ Starting vector clearing...")
            self._log(f"🏷️ Vector name: {vector_name}")
            self._log(f"📦 Collection: {collection_name}")
            
            # Get file information BEFORE clearing vectors
            files_to_remove = self._get_files_for_vector(vector_name, collection_name)
            
            # Use the clear_vector method from QdrantManager
            success = self.qdrant_manager.clear_vector(collection_name, vector_name)
            
            if success:
                self._log(f"✅ Successfully cleared all vectors with name '{vector_name}'")
                
                # Update processed_files.json to remove entries for this vector
                self._update_processed_files_after_clear(files_to_remove)
                
                self._log(f"🎉 Vector clearing complete!")
            else:
                self._log(f"❌ Failed to clear vectors with name '{vector_name}'")
            
            self.after(0, self.progress_bar.set, 1.0)
            
        except Exception as e:
            self._log(f"❌ Vector clearing failed: {str(e)}")
        finally:
            self.after(0, self._reset_clearing_state)
    
    def _get_files_for_vector(self, vector_name: str, collection_name: str):
        """Get list of files that have the specified vector name BEFORE clearing."""
        try:
            # Get all points from the collection to see which files have this vector name
            all_points = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=True
            )[0]
            
            # Find files that have the specified vector name
            files_to_remove = set()
            for point in all_points:
                if hasattr(point, 'vector') and vector_name in point.vector:
                    # Extract source file path from payload
                    source = point.payload.get('source', '')
                    if source:
                        # Convert to relative path format used in processed_files.json
                        # Source format could be from root_path or default "scripts/data/pdfs/filename.pdf"
                        # We need to normalize it to match the format in processed_files.json
                        if source.startswith('scripts/data/pdfs/'):
                            relative_path = source
                        else:
                            # Handle other path formats (including root_path)
                            relative_path = source.replace('\\', '/')
                        
                        files_to_remove.add(relative_path)
            
            return files_to_remove
            
        except Exception as e:
            self._log(f"⚠️ Warning: Could not get files for vector '{vector_name}': {str(e)}")
            return set()
    
    def _update_processed_files_after_clear(self, files_to_remove: set):
        """Update processed_files.json to remove entries that were cleared from the vector database."""
        try:
            # Load current processed files data
            processed_files_data = load_from_json()
            
            # Remove entries from processed_files.json
            removed_count = 0
            for file_path in files_to_remove:
                if file_path in processed_files_data:
                    del processed_files_data[file_path]
                    removed_count += 1
                    self._log(f"📝 Removed from processed list: {file_path}")
            
            # Save updated processed files data
            if removed_count > 0:
                save_to_json(processed_files_data)
                self._log(f"📝 Updated processed files list: removed {removed_count} entries")
            else:
                self._log(f"📝 No processed file entries needed to be removed")
                
        except Exception as e:
            self._log(f"⚠️ Warning: Could not update processed files list: {str(e)}")
    
    def _reset_processing_state(self):
        """Reset the processing state."""
        self.process_btn.configure(text="🚀 Process PDFs", state="normal")
        self.clear_btn.configure(state="normal")
        self.find_pdfs_btn.configure(state="normal")
    
    def _reset_clearing_state(self):
        """Reset the clearing state."""
        self.clear_btn.configure(text="🗑️ Clear Vector", state="normal")
        self.process_btn.configure(state="normal")
        self.find_pdfs_btn.configure(state="normal")
    
    def _log(self, message: str):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Update log on main thread
        self.after(0, self._update_log, log_message)
    
    def _update_log(self, message: str):
        """Update the log text area."""
        self.log_text.insert("end", message)
        self.log_text.see("end")
        
        # Update progress label
        if "Processing:" in message:
            self.progress_label.configure(text=message.strip())
        elif "Processing complete" in message:
            self.progress_label.configure(text="✅ Processing complete!")
        elif "Processing failed" in message:
            self.progress_label.configure(text="❌ Processing failed")
