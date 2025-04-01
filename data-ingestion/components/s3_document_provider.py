#!/usr/bin/env python3
"""
S3/MinIO document provider component for RAG pipeline.
Fetches documents from S3/MinIO buckets and prepares them for processing.
"""
from kfp import dsl
from kfp.dsl import Output, OutputPath, component
import json
import os

@component(
    base_image="python:3.9",
    packages_to_install=["boto3", "botocore"]
)
def s3_document_provider(
    output_path: OutputPath(),
    bucket_name: str,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    file_prefix: str = "",
    file_extensions: list = [".pdf"],
    max_files: int = 100,
    download_dir: str = "/tmp/documents"
):
    """
    Fetches documents from an S3/MinIO bucket and prepares them for RAG processing.
    
    Args:
        output_path: Path to write the list of downloaded document paths
        bucket_name: Name of the S3/MinIO bucket
        minio_endpoint: MinIO/S3 endpoint URL
        minio_access_key: MinIO/S3 access key
        minio_secret_key: MinIO/S3 secret key
        file_prefix: Only fetch files with this prefix (optional)
        file_extensions: List of file extensions to fetch (default: [".pdf"])
        max_files: Maximum number of files to fetch (default: 100)
        download_dir: Directory to download files to (default: "/tmp/documents")
    """
    import boto3
    from botocore.client import Config
    
    # Create output directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    
    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version='s3v4')
    )
    
    print(f"Fetching documents from bucket: {bucket_name} with prefix: {file_prefix}")
    
    # List objects in the bucket
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=file_prefix)
    
    # Track downloaded files
    downloaded_files = []
    file_count = 0
    
    # Process each object
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            
            # Skip if it doesn't have one of the specified extensions
            if not any(key.lower().endswith(ext.lower()) for ext in file_extensions):
                continue
                
            # Download the file
            local_file_path = os.path.join(download_dir, os.path.basename(key))
            
            print(f"Downloading {key} to {local_file_path}")
            try:
                s3.download_file(bucket_name, key, local_file_path)
                downloaded_files.append({
                    "file_path": local_file_path,
                    "key": key,
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat()
                })
                file_count += 1
                
                if file_count >= max_files:
                    print(f"Reached max files limit ({max_files})")
                    break
                    
            except Exception as e:
                print(f"Error downloading {key}: {str(e)}")
                
        if file_count >= max_files:
            break
    
    # Write the list of downloaded files to the output path
    result = {
        "document_paths": [doc["file_path"] for doc in downloaded_files],
        "metadata": {
            "bucket": bucket_name,
            "endpoint": minio_endpoint,
            "file_count": len(downloaded_files),
            "details": downloaded_files
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    print(f"Downloaded {len(downloaded_files)} documents to {download_dir}")
    print(f"Document paths written to {output_path}")
    
    return result


# Example pipeline usage
if __name__ == "__main__":
    from kfp import compiler
    import os
    import sys
    
    # Get the root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Create components yaml directory if it doesn't exist
    components_yaml_dir = os.path.join(parent_dir, "yaml", "components")
    os.makedirs(components_yaml_dir, exist_ok=True)
    
    # Set output path for the component
    component_yaml_path = os.path.join(components_yaml_dir, "s3_document_provider.yaml")
    
    # Compile the component
    compiler.Compiler().compile(s3_document_provider, package_path=component_yaml_path)
    print(f"Component YAML saved to {component_yaml_path}") 