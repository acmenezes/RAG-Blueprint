# RAG Pipeline Local Runner Examples

This directory contains examples of how to use the local pipeline runner for testing purposes.

## Prerequisites

Before running these examples, ensure you have:

1. Installed all required dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. For MinIO testing:
   - A local MinIO server running (default: http://localhost:9000)
   - A bucket created with some PDF documents
   - Credentials (default: minioadmin/minioadmin)

3. For local file testing:
   - Some PDF files in the `sample_documents` directory (or specify a different directory)

4. For Llama Stack:
   - A local Llama Stack instance running (default: http://localhost:8321)
   - PGVector database configured and accessible

## Examples

### 1. Run with Local Files

This example demonstrates how to process local PDF files:

```bash
./run_with_local_files.sh
```

You can modify the script to change:
- The local files directory
- The Llama Stack URL
- The vector database ID

### 2. Run with MinIO

This example demonstrates how to fetch documents from MinIO:

```bash
./run_with_minio.sh
```

You can modify the script to change:
- MinIO connection details
- Bucket name and file prefix
- File extensions to process
- Maximum number of files to process

## Customizing the Runner

You can run the local pipeline runner directly with custom options:

```bash
python ../local_pipeline_runner.py --help
```

This will show all available options:

```
usage: local_pipeline_runner.py [-h] [--bucket-name BUCKET_NAME]
                               [--minio-endpoint MINIO_ENDPOINT]
                               [--minio-access-key MINIO_ACCESS_KEY]
                               [--minio-secret-key MINIO_SECRET_KEY]
                               [--file-prefix FILE_PREFIX]
                               [--file-extensions FILE_EXTENSIONS]
                               [--max-files MAX_FILES]
                               [--download-dir DOWNLOAD_DIR]
                               [--llama-stack-url LLAMA_STACK_URL]
                               [--embedding-model EMBEDDING_MODEL]
                               [--embedding-dimension EMBEDDING_DIMENSION]
                               [--provider-id PROVIDER_ID]
                               [--vector-db-id VECTOR_DB_ID]
                               [--use-local-files] [--local-files-dir LOCAL_FILES_DIR]
                               [--no-cleanup]
```

## Debugging

If you need to debug the pipeline:

1. Use the `--no-cleanup` flag to preserve temporary files
2. Examine the JSON files in the temporary directory for input/output data
3. Check the metrics output for information about processing results 