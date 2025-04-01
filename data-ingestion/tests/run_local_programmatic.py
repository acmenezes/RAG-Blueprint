#!/usr/bin/env python3
"""
Example of how to use the local pipeline runner programmatically.
"""
import os
import sys

# Add the current directory to path so we can import local_pipeline_runner
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_pipeline_runner import run_local_pipeline

def main():
    # Path to local PDF files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_documents")
    
    # Ensure the directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Data directory: {data_dir}")
    
    # Option 1: Run with local files
    metrics = run_local_pipeline(
        use_local_files=True,
        local_files_dir=data_dir,
        llama_stack_url="http://localhost:8321",
        vector_db_id="programmatic-test-db",
        cleanup=True  # Set to False for debugging
    )
    
    # Print summary of results
    print("\nProcessing summary:")
    print(f"Processed {metrics.get('document_count', 0)} documents")
    print(f"Generated {metrics.get('total_chunks', 0)} chunks")
    
    # Option 2: Run with MinIO (commented out)
    """
    metrics = run_local_pipeline(
        bucket_name="rag-documents",
        minio_endpoint="http://localhost:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin",
        file_prefix="pdf/",
        file_extensions=[".pdf"],
        max_files=5,
        llama_stack_url="http://localhost:8321",
        vector_db_id="minio-test-db",
        cleanup=True
    )
    """
    
    return metrics

if __name__ == "__main__":
    main() 