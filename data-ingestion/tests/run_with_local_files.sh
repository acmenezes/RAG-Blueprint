#!/bin/bash
# Example script for running the RAG pipeline with local files

# Path to your local PDF files directory
LOCAL_FILES_DIR="../data/sample_documents"

# Create the sample directory if it doesn't exist
mkdir -p $LOCAL_FILES_DIR

# Execute the local pipeline runner with local files
python local_pipeline_runner.py \
  --use-local-files \
  --local-files-dir=$LOCAL_FILES_DIR \
  --llama-stack-url="http://localhost:8321" \
  --vector-db-id="pgvector" \
  --provider-id="pgvector" \
  --no-cleanup 