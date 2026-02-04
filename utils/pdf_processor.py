"""
PDF processing utilities for text extraction and chunking.
"""
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text from a PDF file using PyMuPDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    text = ""
    
    print(f"      Reading PDF with PyMuPDF...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"      Total pages: {total_pages}")
    
    for page_num in range(total_pages):
        if page_num % 10 == 0 and page_num > 0:  # Progress every 10 pages
            print(f"      Processing page {page_num + 1}/{total_pages}...")
        
        try:
            page = doc[page_num]
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        except Exception as e:
            print(f"      Warning: Could not extract text from page {page_num + 1}: {e}")
            continue
    
    doc.close()
    print(f"      ✓ Extracted {len(text)} characters from {total_pages} pages")
    return text.strip()


from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(
    text: str,
    chunk_size: int = 1800,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks using LangChain's optimized splitter.
    
    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""],
        length_function=len,
    )
    
    return text_splitter.split_text(text)


def process_pdf(
    pdf_path: Path,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> Dict[str, Any]:
    """
    Process a PDF file: extract text and create chunks.
    
    Args:
        pdf_path: Path to the PDF file
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        
    Returns:
        Dictionary with filename, full_text, and chunks
    """
    # Extract text
    full_text = extract_text_from_pdf(pdf_path)
    
    # Create chunks
    print(f"      Creating chunks...")
    chunks = chunk_text(full_text, chunk_size, chunk_overlap)
    print(f"      ✓ Created {len(chunks)} chunks")
    
    return {
        'filename': pdf_path.name,
        'full_text': full_text,
        'chunks': chunks,
        'num_chunks': len(chunks),
        'total_chars': len(full_text)
    }


def get_pdf_metadata(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with PDF metadata
    """
    metadata = {
        'filename': pdf_path.name,
        'file_size': pdf_path.stat().st_size,
    }
    
    try:
        doc = fitz.open(pdf_path)
        
        metadata['num_pages'] = len(doc)
        
        # Extract PDF metadata
        pdf_metadata = doc.metadata
        if pdf_metadata:
            metadata['title'] = pdf_metadata.get('title', '')
            metadata['author'] = pdf_metadata.get('author', '')
            metadata['subject'] = pdf_metadata.get('subject', '')
            metadata['creator'] = pdf_metadata.get('creator', '')
        
        doc.close()
    
    except Exception as e:
        metadata['error'] = str(e)
    
    return metadata
