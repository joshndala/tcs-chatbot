"""
ChromaDB vector store manager for policy document embeddings.
Handles PDF ingestion, embedding generation, and similarity search.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types
from config.settings import settings


class GoogleGenAIEmbeddingFunction:
    """Custom embedding function using the new google-genai SDK."""
    
    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def name(self) -> str:
        """Returns the name of the embedding function."""
        return "google_genai_embedding"

    def embed_query(self, text: str = None, input: str = None) -> List[float]:
        """LangChain compatibility: Embed a single query."""
        val = input if input is not None else text
        if val is None:
            raise ValueError("Must provide 'text' or 'input'")
        return self([val]) # Return List[List[float]] to appease Chroma?

    def embed_documents(self, texts: List[str] = None, input: List[str] = None) -> List[List[float]]:
        """LangChain compatibility: Embed multiple documents."""
        val = input if input is not None else texts
        if val is None:
            raise ValueError("Must provide 'texts' or 'input'")
        return self(val)

    def __call__(self, input: List[str]) -> List[List[float]]:
        # Batch embedding is supported by the new SDK
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=input,
            config=types.EmbedContentConfig(
                 task_type="RETRIEVAL_DOCUMENT" # Optimize for storage
            )
        )
        # Verify response structure (it returns a list of embedding objects)
        return [e.values for e in response.embeddings]


class VectorStore:
    """Manages ChromaDB vector store for policy documents."""
    
    def __init__(self, collection_name: str = "policy_documents"):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create custom embedding function
        self.embedding_function = GoogleGenAIEmbeddingFunction(
            api_key=settings.google_api_key,
            model_name=settings.embedding_model
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Policy document embeddings"}
        )
    
    def add_documents(self, documents, metadatas=None, ids=None):
        """Add documents to vector store in batches."""
        if ids is None:
            count = self.collection.count()
            ids = [f"doc_{count + i}" for i in range(len(documents))]
    
        batch_size = 40 
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch_num = i // batch_size + 1
            batch_docs = documents[i : i + batch_size]
            batch_metas = metadatas[i : i + batch_size] if metadatas else None
            batch_ids = ids[i : i + batch_size]
            
            print(f"   Uploading batch {batch_num}/{total_batches} ({len(batch_docs)} chunks)...")
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
    
    def search(
        self,
        query: str,
        n_results: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with 'documents', 'metadatas', 'distances', and 'ids'
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        # Flatten results (query returns list of lists)
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
    
    def delete_by_metadata(self, where: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filter.
        
        Args:
            where: Metadata filter dictionary
        """
        self.collection.delete(where=where)
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the collection."""
        return self.collection.count()
    
    def get_all_documents(self) -> Dict[str, Any]:
        """
        Retrieve all documents from the collection.
        
        Returns:
            Dictionary with all documents and their metadata
        """
        count = self.collection.count()
        if count == 0:
            return {'documents': [], 'metadatas': [], 'ids': []}
        
        results = self.collection.get()
        return results
    
    def reset_collection(self) -> None:
        """Delete all documents from the collection."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            embedding_function=self.embedding_function,
            metadata={"description": "Policy document embeddings"}
        )
    
    def add_pdf_chunks(
        self,
        chunks: List[str],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add PDF document chunks to the vector store.
        
        Args:
            chunks: List of text chunks from the PDF
            filename: Name of the PDF file
            metadata: Optional additional metadata
        """
        print(f"\n📄 Processing {filename}...")
        print(f"   Total chunks to process: {len(chunks)}")
        
        # Create metadata for each chunk
        metadatas = []
        ids = []
        
        base_id = filename.replace('.pdf', '').replace(' ', '_').lower()
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                'filename': filename,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source': 'pdf'
            }
            
            # Add any additional metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            metadatas.append(chunk_metadata)
            ids.append(f"{base_id}_chunk_{i}")
        
        print(f"   Generating embeddings (this may take a while)...")
        
        try:
            # Add to collection
            self.add_documents(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"   ✅ Successfully added {len(chunks)} chunks to vector store")
        except Exception as e:
            print(f"   ❌ Error adding chunks: {e}")
            raise
    
    def search_by_filename(
        self,
        query: str,
        filename: str,
        n_results: int = 3
    ) -> Dict[str, Any]:
        """
        Search within a specific PDF file.
        
        Args:
            query: Search query text
            filename: PDF filename to search within
            n_results: Number of results to return
            
        Returns:
            Search results filtered by filename
        """
        return self.search(
            query=query,
            n_results=n_results,
            where={'filename': filename}
        )


# Global vector store instance
vector_store = VectorStore()
