#!/usr/bin/env python3
"""
Complete RAG ingestion pipeline that fetches documents from S3/MinIO
and processes them using the RAG docling component.
"""
from kfp import dsl, compiler
import os
import sys
import importlib

# Add parent directory to path so we can import from components
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def compile_s3_rag_pipeline():
    """
    Compiles a pipeline that fetches documents from S3/MinIO and
    processes them with the RAG docling component.
    """
    # Import component modules
    # This will load the components with their @component decorators
    from components import s3_document_provider
    from components import rag_docling_component
    
    # Access the components directly from the modules
    s3_provider = s3_document_provider.s3_document_provider
    rag_docling = rag_docling_component.rag_docling_component
    
    # Define the pipeline
    @dsl.pipeline(
        name="S3 RAG Document Ingestion Pipeline",
        description="Pipeline that fetches documents from S3/MinIO and processes them for RAG"
    )
    def s3_rag_pipeline(
        # S3/MinIO parameters
        bucket_name: str = "llama",
        minio_endpoint: str = "http://minio-service:9000",
        minio_access_key: str = "minio",
        minio_secret_key: str = "minio123",
        file_prefix: str = "",
        file_extensions: list = [".pdf"],
        max_files: int = 50,
        
        # RAG parameters
        llama_stack_url: str = "http://localhost:8321",
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        provider_id: str = "pgvector",
        vector_db_id: str = "pgvector"
    ):
        # Step 1: Fetch documents from S3/MinIO
        s3_task = s3_provider(
            bucket_name=bucket_name,
            minio_endpoint=minio_endpoint,
            minio_access_key=minio_access_key,
            minio_secret_key=minio_secret_key,
            file_prefix=file_prefix,
            file_extensions=file_extensions,
            max_files=max_files
        )
        
        # Step 2: Process documents with RAG docling component
        rag_task = rag_docling(
            document_path=s3_task.output,
            llama_stack_url=llama_stack_url,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            provider_id=provider_id,
            vector_db_id=vector_db_id
        )
    
    # Create directory if it doesn't exist
    pipelines_yaml_dir = os.path.join(parent_dir, "yaml", "pipelines")
    os.makedirs(pipelines_yaml_dir, exist_ok=True)
    
    # Compile the pipeline to the pipelines directory
    output_path = os.path.join(pipelines_yaml_dir, "s3_rag_pipeline.yaml")
    compiler.Compiler().compile(
        pipeline_func=s3_rag_pipeline,
        package_path=output_path
    )
    print(f"Pipeline compiled successfully to {output_path}")

# Run the compilation if this script is executed directly
if __name__ == "__main__":
    compile_s3_rag_pipeline() 