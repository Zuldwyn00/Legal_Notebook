import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from typing import List, Dict, Any
import uuid
import json

from utils import load_config, setup_logger

# ─── LOGGER & CONFIG ────────────────────────────────────────────────────────────────
config = load_config()
logger = setup_logger(__name__, config)
load_dotenv("./.env")


class QdrantManager:
    def __init__(self):
        self.config = config
        self.client = self._initialize_client()
        self.vector_config = {
            "chunk": models.VectorParams(size=3072, distance=models.Distance.COSINE),
            # TODO: add a vector for images as well for a hybrid search in the future.
        }

    def _initialize_client(self):
        qclient = QdrantClient(
            url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY")
        )
        return qclient

    def create_collection(
        self, collection_name: str, vector_config: dict = None
    ) -> bool:
        """
        Creates a new vector collection in the database.

        Args:
            collection_name (str): Name of the collection to create.
            vector_config (dict, optional): Vector configuration. Uses default if None.

        Returns:
            bool: True if collection created successfully, False otherwise.
        """
        if not vector_config:
            vector_config = self.vector_config
        try:
            self.client.create_collection(
                collection_name=collection_name, vectors_config=vector_config
            )
            return True

        except Exception as e:
            print(f"Error creating collection: {e}")
        return False

    def add_embedding(
        self,
        collection_name: str,
        embedding: List[float],
        metadata: dict,
        vector_name: str = "chunk",
    ):
        """
        Adds a single embedding to the collection.

        Args:
            collection_name (str): Name of the collection.
            embedding (List[float]): The embedding vector to add.
            vector_name (str): Name of the vector field. Defaults to "chunk".
            metadata (dict): Optional metadata to store with the embedding.
        """
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector={vector_name: embedding},
            payload=metadata or {},
        )
        self.client.upsert(collection_name=collection_name, points=[point])

    def add_embeddings_batch(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        metadatas: List[dict],
        vector_name: str = "chunk",
        max_batch_size: int = 100,
    ):
        """
        Adds a batch of embeddings to the collection with automatic sub-batching for large datasets.

        Args:
            collection_name (str): Name of the collection.
            embeddings (List[List[float]]): A list of embedding vectors to add.
            metadatas (List[dict]): A list of metadata dictionaries.
            vector_name (str): Name of the vector field. Defaults to "chunk".
            max_batch_size (int): Maximum number of points per sub-batch. Defaults to 100.
        """
        total_points = len(embeddings)
        logger.info(
            f"Uploading batch of {total_points} chunks to collection '{collection_name}' "
            f"(max sub-batch size: {max_batch_size})"
        )
        
        # Process in sub-batches to handle large datasets efficiently
        for batch_start in range(0, total_points, max_batch_size):
            batch_end = min(batch_start + max_batch_size, total_points)
            batch_embeddings = embeddings[batch_start:batch_end]
            batch_metadatas = metadatas[batch_start:batch_end]
            
            logger.debug(f"Processing sub-batch {batch_start//max_batch_size + 1}/{(total_points + max_batch_size - 1)//max_batch_size}")
            
            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={vector_name: embedding},
                    payload=metadata or {},
                )
                for embedding, metadata in zip(batch_embeddings, batch_metadatas)
            ]
            
            # Retry logic for each sub-batch
            for attempt in range(3):  # Increased to 3 attempts for better reliability
                try:
                    self.client.upsert(collection_name=collection_name, points=points)
                    logger.debug(f"Successfully uploaded sub-batch of {len(points)} chunks")
                    break  # Success, move to next sub-batch
                    
                except ResponseHandlingException as e:
                    if attempt < 2:  # Not the last attempt
                        logger.warning(
                            f"Error uploading sub-batch to '{collection_name}' (attempt {attempt + 1}/3), retrying... Error: {e}"
                        )
                    else:  # Last attempt failed
                        logger.error(
                            f"Failed to upload sub-batch to '{collection_name}' after 3 attempts. Error: {e}"
                        )
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error uploading to '{collection_name}': {e}")
                    raise
        
        logger.info(f"Successfully uploaded all {total_points} chunks to collection '{collection_name}'")

    def clear_vector(self, collection_name: str, vector_name: str) -> bool:
        """
        Deletes all elements from the specified collection that share the given vector name.

        Args:
            collection_name (str): Name of the collection to clear vectors from.
            vector_name (str): Name of the vector field to clear.

        Returns:
            bool: True if vectors were cleared successfully, False otherwise.
        """
        try:
            # First, check if the collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                logger.warning(f"Collection '{collection_name}' does not exist")
                return False
            
            # Get collection info to verify vector name exists
            collection_info = self.client.get_collection(collection_name)
            available_vectors = list(collection_info.config.params.vectors.keys())
            
            if vector_name not in available_vectors:
                logger.warning(f"Vector name '{vector_name}' does not exist in collection '{collection_name}'")
                return False
            
            # Get all points from the collection
            # We need to retrieve all points first to identify which ones have the specific vector name
            all_points = self.client.scroll(
                collection_name=collection_name,
                limit=10000,  # Adjust based on your collection size
                with_payload=True,
                with_vectors=True
            )[0]  # scroll returns (points, next_page_offset)
            
            # Filter points that have the specified vector name
            points_to_delete = []
            for point in all_points:
                if hasattr(point, 'vector') and vector_name in point.vector:
                    points_to_delete.append(point.id)
            
            if not points_to_delete:
                logger.info(f"No points found with vector name '{vector_name}' in collection '{collection_name}'")
                return True
            
            # Delete the identified points
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=points_to_delete)
            )
            
            logger.info(f"Successfully cleared {len(points_to_delete)} vectors with name '{vector_name}' from collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vectors from collection '{collection_name}': {e}")
            return False


    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        vector_name: str = "chunk",
        limit: int = 10,
    ) -> list:
        """
        Searches for similar vectors in the collection.

        Args:
            collection_name (str): Name of the collection.
            query_vector (List[float]): The vector to search with.
            vector_name (str, optional): The name of the vector to search against. Can be a string or list of strings. Defaults to "chunk".
            limit (int, optional): The maximum number of results to return.

        Returns:
            list: A list of search results.
        """
        try:
            # Handle single vector name
            if isinstance(vector_name, str):
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=(vector_name, query_vector),
                    limit=limit,
                )
                return search_result
            
            # Handle list of vector names
            elif isinstance(vector_name, list):
                all_results = []
                
                for v_name in vector_name:
                    try:
                        results = self.client.search(
                            collection_name=collection_name,
                            query_vector=(v_name, query_vector),
                            limit=limit,
                        )
                        all_results.extend(results)
                    except Exception as e:
                        logger.warning(f"Failed to search vector '{v_name}': {e}")
                        continue
                
                # Sort all results by score and return top results
                all_results.sort(key=lambda x: x.score, reverse=True)
                return all_results[:limit]
            
            else:
                raise ValueError("vector_name must be a string or list of strings")
                
        except Exception as e:
            raise Exception(f"Error searching vectors: {e}")

    def get_vector_names(self, collection_name: str) -> List[str]:
        """
        Get all available vector names from the collection.
        
        Args:
            collection_name (str): Name of the collection.
            
        Returns:
            List[str]: List of available vector names.
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            vector_names = list(collection_info.config.params.vectors.keys())
            return sorted(vector_names)
        except Exception as e:
            logger.error(f"Error getting vector names: {e}")
            return []

    def count_vectors(self, collection_name: str, vector_name: str) -> int:
        """
        Count the number of elements that exist for a specified vector name in the collection.
        
        Args:
            collection_name (str): Name of the collection.
            vector_name (str): Name of the vector field to count.
            
        Returns:
            int: Number of elements with the specified vector name, or -1 if error occurred.
        """
        try:
            
            # Get all points from the collection
            all_points = self.client.scroll(
                collection_name=collection_name,
                limit=10000,  # Adjust based on your collection size
                with_payload=True,
                with_vectors=True
            )[0]  # scroll returns (points, next_page_offset)
            
            # Count points that have the specified vector name
            count = 0
            for point in all_points:
                if hasattr(point, 'vector') and vector_name in point.vector:
                    count += 1
            
            logger.info(f"Found {count} elements with vector name '{vector_name}' in collection '{collection_name}'")
            return count
            
        except Exception as e:
            logger.error(f"Error counting vectors in collection '{collection_name}': {e}")
            return -1




