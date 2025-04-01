#!/usr/bin/env python3
"""
Local runner for the S3/RAG Kubeflow pipeline.
Executes pipeline components locally for testing purposes without deploying to a cluster.
"""
import os
import sys
import json
import argparse
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path so we can import from components
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def run_local_pipeline(
    # S3/MinIO parameters
    bucket_name="local-test-bucket",
    minio_endpoint="http://localhost:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin",
    file_prefix="",
    file_extensions=[".pdf"],
    max_files=10,
    download_dir=None,
    
    # RAG parameters
    llama_stack_url="http://localhost:8321",
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimension=384,
    provider_id="pgvector",
    vector_db_id="test-vector-db",
    
    # Test options
    use_local_files=False,
    local_files_dir=None,
    cleanup=True
):
    """
    Run the S3 RAG pipeline locally for testing purposes.
    
    Args:
        bucket_name: S3/MinIO bucket name
        minio_endpoint: MinIO/S3 endpoint URL
        minio_access_key: MinIO/S3 access key
        minio_secret_key: MinIO/S3 secret key
        file_prefix: File prefix for filtering
        file_extensions: List of file extensions to process
        max_files: Maximum number of files to process
        download_dir: Directory to download files to (default: temp directory)
        llama_stack_url: URL for the Llama Stack API
        embedding_model: Model to use for embeddings
        embedding_dimension: Dimension size for embeddings
        provider_id: Provider ID for vector database
        vector_db_id: ID for the vector database
        use_local_files: Use local files instead of fetching from S3/MinIO
        local_files_dir: Directory containing local files to process
        cleanup: Whether to clean up temporary files after execution
    """
    print("=" * 80)
    print("LOCAL PIPELINE RUNNER")
    print("=" * 80)
    
    # Create temporary directories for component execution
    temp_dir = tempfile.mkdtemp(prefix="rag_pipeline_")
    if download_dir is None:
        download_dir = os.path.join(temp_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Step 1: Document Provider (S3 or Local Files)
        document_provider_output = os.path.join(temp_dir, "document_provider_output.json")
        
        if use_local_files:
            print("\n=== Using Local Files ===")
            if not local_files_dir:
                raise ValueError("local_files_dir must be provided when use_local_files=True")
                
            local_files = []
            for ext in file_extensions:
                local_files.extend(list(Path(local_files_dir).glob(f"*{ext}")))
            
            document_paths = [str(file_path) for file_path in local_files]
            result = {
                "document_paths": document_paths,
                "metadata": {
                    "source": "local_files",
                    "file_count": len(document_paths),
                    "directory": local_files_dir
                }
            }
            
            with open(document_provider_output, 'w') as f:
                json.dump(result, f, indent=2)
                
            print(f"Found {len(document_paths)} local files in {local_files_dir}")
            for path in document_paths:
                print(f"  - {path}")
                
        else:
            print("\n=== Fetching Documents from S3/MinIO ===")
            # Import the s3_document_provider module
            from components import s3_document_provider
            
            # Execute the underlying function of the S3 document provider
            # In KFP v2, we need to directly call the function inside the component
            s3_provider_fn = s3_document_provider.s3_document_provider.python_func
            
            # We need to manually create the input/output paths that KFP would normally handle
            s3_provider_fn(
                output_path=document_provider_output,
                bucket_name=bucket_name,
                minio_endpoint=minio_endpoint,
                minio_access_key=minio_access_key,
                minio_secret_key=minio_secret_key,
                file_prefix=file_prefix,
                file_extensions=file_extensions,
                max_files=max_files,
                download_dir=download_dir
            )
            
            # Load the result to display info
            with open(document_provider_output, 'r') as f:
                result = json.load(f)
                
            print(f"Downloaded {len(result.get('document_paths', []))} documents from S3/MinIO")
        
        # Step 2: RAG Docling Component
        print("\n=== Processing Documents with RAG Docling Component ===")
        # Import the rag_docling_component module
        from components import rag_docling_component
        
        metrics_output = os.path.join(temp_dir, "metrics.json")
        
        # Execute the RAG docling component
        # Access the underlying function directly in KFP v2
        rag_fn = rag_docling_component.rag_docling_component.python_func
        
        rag_fn(
            document_path=document_provider_output,
            metrics_path=metrics_output,
            llama_stack_url=llama_stack_url,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            provider_id=provider_id,
            vector_db_id=vector_db_id
        )
        
        # Display metrics
        print("\n=== RAG Processing Results ===")
        with open(metrics_output, 'r') as f:
            metrics = json.load(f)
            
        print(f"Document count: {metrics.get('document_count', 0)}")
        print(f"Total chunks: {metrics.get('total_chunks', 0)}")
        print(f"Vector DB registration: {metrics.get('vector_db_registration', 'unknown')}")
        print(f"Vector DB insertion: {metrics.get('vector_db_insertion', 'unknown')}")
        
        if metrics.get('failed_documents'):
            print(f"\nFailed documents ({len(metrics['failed_documents'])}):")
            for doc in metrics['failed_documents']:
                print(f"  - {doc['file']}: {doc['error']}")
                
        print("\n=== Pipeline completed successfully ===")
        return metrics
        
    finally:
        if cleanup:
            print(f"\nCleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
        else:
            print(f"\nTemporary directory preserved at: {temp_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the S3/RAG pipeline locally")
    
    # S3/MinIO options
    parser.add_argument("--bucket-name", default="local-test-bucket", help="S3/MinIO bucket name")
    parser.add_argument("--minio-endpoint", default="http://localhost:9000", help="MinIO/S3 endpoint URL")
    parser.add_argument("--minio-access-key", default="minioadmin", help="MinIO/S3 access key")
    parser.add_argument("--minio-secret-key", default="minioadmin", help="MinIO/S3 secret key")
    parser.add_argument("--file-prefix", default="", help="File prefix for filtering")
    parser.add_argument("--file-extensions", default=".pdf,.docx,.txt", help="Comma-separated list of file extensions")
    parser.add_argument("--max-files", type=int, default=10, help="Maximum number of files to process")
    parser.add_argument("--download-dir", help="Directory to download files to")
    
    # RAG options
    parser.add_argument("--llama-stack-url", default="http://localhost:8321", help="URL for the Llama Stack API")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2", help="Model to use for embeddings")
    parser.add_argument("--embedding-dimension", type=int, default=384, help="Dimension size for embeddings")
    parser.add_argument("--provider-id", default="pgvector", help="Provider ID for vector database")
    parser.add_argument("--vector-db-id", default="test-vector-db", help="ID for the vector database")
    
    # Test options
    parser.add_argument("--use-local-files", action="store_true", help="Use local files instead of S3/MinIO")
    parser.add_argument("--local-files-dir", help="Directory containing local files to process")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean up temporary files after execution")
    
    args = parser.parse_args()
    
    run_local_pipeline(
        # S3/MinIO parameters
        bucket_name=args.bucket_name,
        minio_endpoint=args.minio_endpoint,
        minio_access_key=args.minio_access_key,
        minio_secret_key=args.minio_secret_key,
        file_prefix=args.file_prefix,
        file_extensions=args.file_extensions.split(","),
        max_files=args.max_files,
        download_dir=args.download_dir,
        
        # RAG parameters
        llama_stack_url=args.llama_stack_url,
        embedding_model=args.embedding_model,
        embedding_dimension=args.embedding_dimension,
        provider_id=args.provider_id,
        vector_db_id=args.vector_db_id,
        
        # Test options
        use_local_files=args.use_local_files,
        local_files_dir=args.local_files_dir,
        cleanup=not args.no_cleanup
    ) 