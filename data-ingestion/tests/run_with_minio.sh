#!/bin/bash
# Example script for running the RAG pipeline with MinIO

# MinIO connection details
MINIO_ENDPOINT="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
BUCKET_NAME="rag-documents"

# Execute the local pipeline runner with MinIO
python local_pipeline_runner.py \
  --minio-endpoint=$MINIO_ENDPOINT \
  --minio-access-key=$MINIO_ACCESS_KEY \
  --minio-secret-key=$MINIO_SECRET_KEY \
  --bucket-name=$BUCKET_NAME \
  --file-prefix="pdf/" \
  --file-extensions=".pdf" \
  --max-files=5 \
  --llama-stack-url="http://localhost:8321" \
  --vector-db-id="minio-test-db" 