# RAG Document Ingestion Pipeline

This repository contains pipeline components for implementing a complete RAG (Retrieval Augmented Generation) document ingestion workflow in OpenShift AI / RHOAI.

## Components Overview

The pipeline consists of two main components:

1. **S3/MinIO Document Provider** - Fetches documents from S3 or MinIO storage
2. **RAG Docling Component** - Processes documents, chunks them, and stores them in a vector database

## Prerequisites

- OpenShift AI (RHOAI) or Kubeflow Pipelines environment
- Python 3.9+
- Access to a Llama Stack API instance
- Access to S3/MinIO storage (optional)

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Component 1: S3/MinIO Document Provider

This component fetches documents from an S3 or MinIO bucket and prepares them for processing.

### Features

- Fetches multiple documents from S3/MinIO buckets
- Supports filtering by file prefix and extension
- Configurable maximum number of files to download
- Provides detailed metadata about the downloaded files

### Component Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `bucket_name` | str | Name of the S3/MinIO bucket | Required |
| `minio_endpoint` | str | MinIO/S3 endpoint URL | Required |
| `minio_access_key` | str | MinIO/S3 access key | Required |
| `minio_secret_key` | str | MinIO/S3 secret key | Required |
| `file_prefix` | str | Only fetch files with this prefix | `""` (empty) |
| `file_extensions` | list | List of file extensions to fetch | `[".pdf"]` |
| `max_files` | int | Maximum number of files to fetch | `100` |
| `download_dir` | str | Directory to download files to | `"/tmp/documents"` |

### Output Format

The component writes a JSON file with the following structure:

```json
{
  "document_paths": [
    "/tmp/documents/document1.pdf",
    "/tmp/documents/document2.pdf",
    "..."
  ],
  "metadata": {
    "bucket": "my-bucket",
    "endpoint": "http://minio-service:9000",
    "file_count": 2,
    "details": [
      {
        "file_path": "/tmp/documents/document1.pdf",
        "key": "documents/document1.pdf",
        "size": 123456,
        "last_modified": "2023-01-01T12:00:00.000000+00:00"
      },
      {
        "file_path": "/tmp/documents/document2.pdf",
        "key": "documents/document2.pdf",
        "size": 234567,
        "last_modified": "2023-01-02T12:00:00.000000+00:00"
      }
    ]
  }
}
```

### Generating the Component

```bash
python s3_document_provider.py
```

This will create `s3_document_provider_component.yaml` and `s3_document_provider_pipeline.yaml`.

## Component 2: RAG Docling Component

This component processes documents using docling, chunks them, and stores them in a vector database.

### Features

- Processes documents from file paths
- Chunks documents using a hybrid chunking approach
- Embeds chunks using the specified embedding model
- Stores vectors in a vector database (pgvector)

### Component Parameters

- `document_path` (InputPath): Path to the document or a JSON file with document paths
- `metrics_path` (OutputPath): Path to write processing metrics
- `llama_stack_url` (str): URL for the Llama Stack API
- `embedding_model` (str): Model to use for embeddings
- `embedding_dimension` (int): Dimension size for embeddings
- `provider_id` (str): Provider ID for vector database
- `vector_db_id` (str): ID for the vector database

### Input Format

The component expects one of the following at the `document_path`:

1. A direct path to a PDF document
2. A JSON file containing a list of document paths
3. A JSON file with a "documents" key that contains an array of document paths

### Metrics Output

The component generates a JSON metrics file with information about the processing:

```json
{
  "document_count": 2,
  "processed_documents": [
    {
      "file": "path/to/doc1.pdf",
      "chunks": 15
    },
    {
      "file": "path/to/doc2.pdf",
      "chunks": 8
    }
  ],
  "failed_documents": [],
  "total_chunks": 23,
  "vector_db_registration": "success",
  "vector_db_insertion": "success"
}
```

### Generating the Component

```bash
python rag_docling_component.py
```

This will create `rag_docling_component.yaml` and `rag_pipeline.yaml`.

## Complete S3-to-Vector Database Pipeline

A complete pipeline that integrates both components is available. This pipeline:
1. Fetches documents from S3/MinIO
2. Processes them with the RAG docling component
3. Stores them in a vector database

### Generating the Complete Pipeline

```bash
python s3_rag_pipeline.py
```

This will create:
- `s3_document_provider_component.yaml` (if it doesn't exist)
- `rag_docling_component.yaml` (if it doesn't exist)
- `s3_rag_pipeline.yaml` (the complete pipeline)

### Pipeline Parameters

The pipeline accepts parameters for both components:

**S3/MinIO Parameters:**
- `bucket_name`: S3/MinIO bucket name
- `minio_endpoint`: S3/MinIO endpoint URL
- `minio_access_key`: S3/MinIO access key
- `minio_secret_key`: S3/MinIO secret key
- `file_prefix`: File prefix for filtering
- `file_extensions`: List of file extensions to process
- `max_files`: Maximum number of files to process

**RAG Parameters:**
- `llama_stack_url`: URL for the Llama Stack API
- `embedding_model`: Model to use for embeddings
- `embedding_dimension`: Dimension size for embeddings
- `provider_id`: Provider ID for vector database
- `vector_db_id`: ID for the vector database

### Example Pipeline Code

```python
from kfp import dsl
from kfp.compiler import Compiler
from kfp.components import load_component_from_file

# Load components
s3_provider_op = load_component_from_file('s3_document_provider_component.yaml')
rag_docling_op = load_component_from_file('rag_docling_component.yaml')

@dsl.pipeline(
    name="S3 RAG Pipeline",
    description="Pipeline that fetches documents from S3/MinIO and processes them for RAG"
)
def s3_rag_pipeline():
    # Fetch documents
    s3_task = s3_provider_op(
        bucket_name="my-bucket",
        minio_endpoint="http://minio-service:9000",
        minio_access_key="minio",
        minio_secret_key="minio123",
        file_prefix="documents/",
        file_extensions=[".pdf", ".docx", ".txt"],
        max_files=50
    )
    
    # Process documents
    rag_task = rag_docling_op(
        document_path=s3_task.outputs['output'],
        llama_stack_url="http://llama-stack-service:8321",
        vector_db_id="my-vector-db"
    )
```

## Local Pipeline Runner

If you want to test the pipeline without deploying it to OpenShift AI/RHOAI, you can use the local pipeline runner provided in this repository.

### Features

- Runs the pipeline components locally without requiring a Kubeflow environment
- Supports both S3/MinIO and local file sources
- Configurable via command line arguments or programmatic API
- Provides detailed metrics and logs

### Using the Local Runner

#### 1. Command Line Usage

```bash
python local_pipeline_runner.py --help
```

Example with local files:

```bash
python local_pipeline_runner.py \
  --use-local-files \
  --local-files-dir=./my-documents \
  --llama-stack-url="http://localhost:8321" \
  --vector-db-id="local-test-db"
```

Example with MinIO:

```bash
python local_pipeline_runner.py \
  --minio-endpoint="http://localhost:9000" \
  --minio-access-key="minioadmin" \
  --minio-secret-key="minioadmin" \
  --bucket-name="rag-documents" \
  --file-prefix="pdf/" \
  --llama-stack-url="http://localhost:8321" \
  --vector-db-id="minio-test-db"
```

#### 2. Programmatic Usage

```python
from local_pipeline_runner import run_local_pipeline

# Run with local files
metrics = run_local_pipeline(
    use_local_files=True,
    local_files_dir="./my-documents",
    llama_stack_url="http://localhost:8321",
    vector_db_id="programmatic-test-db"
)

# Process results
print(f"Processed {metrics['document_count']} documents")
print(f"Generated {metrics['total_chunks']} chunks")
```

### Example Scripts

The `examples` directory contains sample scripts for using the local runner:

- `run_with_local_files.sh` - Example of running with local PDF files
- `run_with_minio.sh` - Example of fetching documents from MinIO
- `run_local_programmatic.py` - Example of using the runner programmatically

See the [examples README](examples/README.md) for more details.

## Running in OpenShift AI

1. Generate the pipeline YAML:
   ```bash
   python s3_rag_pipeline.py
   ```

2. Upload the generated YAML to OpenShift AI:
   - Go to the Pipelines section in the OpenShift AI web interface
   - Click "Create Pipeline" and upload `s3_rag_pipeline.yaml`

3. Create a pipeline run:
   - Click "Create Run" on the uploaded pipeline
   - Configure the parameters (S3 credentials, bucket, etc.)
   - Start the run

## Security Considerations

- Store the MinIO/S3 credentials securely, preferably as Kubernetes secrets
- Configure appropriate access permissions for the downloaded files
- Consider implementing additional security measures for sensitive documents

## Creating Your Own Document Provider

If you need a different document provider, you can create your own:

```python
from kfp.components import create_component_from_func, OutputPath

def your_document_provider(output_path: OutputPath()):
    """Provides document paths to the RAG component."""
    import json
    
    # Get documents from your storage 
    document_paths = ["path/to/doc1.pdf", "path/to/doc2.pdf"]
    
    with open(output_path, 'w') as f:
        json.dump({"document_paths": document_paths}, f)

document_provider = create_component_from_func(func=your_document_provider)
``` 