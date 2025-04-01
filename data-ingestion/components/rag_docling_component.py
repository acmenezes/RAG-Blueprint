from kfp import dsl
from kfp.dsl import component, Input, InputPath, Output, OutputPath
import uuid
import os
import json
from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Document as LlamaStackDocument

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.labels import DocItemLabel


@component(
    base_image="python:3.9",
    packages_to_install=[
        "llama-stack-client==0.1.9",
        "docling",
        "docling-core"
    ]
)
def rag_docling_component(
    document_path: InputPath(),
    metrics_path: OutputPath(),
    llama_stack_url: str = "http://localhost:8321",
    embedding_model: str = "all-MiniLM-L6-v2",
    embedding_dimension: int = 384,
    provider_id: str = "pgvector",
    vector_db_id: str = "pgvector"
) -> int:
    """
    Process documents, convert them to chunks, and store in a vector database.
    
    Args:
        document_path (InputPath): Path to the document or a JSON file containing document paths
        metrics_path (OutputPath): Path to write processing metrics
        llama_stack_url (str): URL for the Llama Stack API
        embedding_model (str): Model to use for embeddings
        embedding_dimension (int): Dimension size for embeddings
        provider_id (str): Provider ID for vector database
        vector_db_id (str): ID for the vector database
        
    Returns:
        int: Number of documents processed
    """
    # === Step 1: Configure Llama Stack client ===
    client = LlamaStackClient(base_url=llama_stack_url)  # Assumes LLAMA_STACK_API_KEY is set in env

    # === Step 2: Process document path ===
    # The document_path could be a single file or a JSON file with multiple document paths
    documents = []
    if os.path.isfile(document_path):
        # Check if this is a JSON file with a list of document paths
        if document_path.endswith('.json'):
            try:
                with open(document_path, 'r') as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        documents = file_data
                    elif isinstance(file_data, dict) and 'document_paths' in file_data:
                        documents = file_data['document_paths']
                    elif isinstance(file_data, dict) and 'documents' in file_data:
                        documents = file_data['documents']
                    else:
                        documents = [document_path]
            except json.JSONDecodeError:
                documents = [document_path]
        else:
            documents = [document_path]

    # === Step 3: Convert, Chunk, and Prepare Documents ===
    # converter format option for the pictures on pdf to be generated as base64
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    converter = DocumentConverter(
                format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
    )
    chunker = HybridChunker()
    llama_documents: list[LlamaStackDocument] = []
    i = 0
    processing_metrics = {
        "document_count": len(documents),
        "processed_documents": [],
        "failed_documents": []
    }

    for file_path in documents:
        print(f"Processing {file_path}...")
        try:
            docling_doc = converter.convert(source=file_path).document
            chunks = chunker.chunk(docling_doc)
            chunk_count = 0

            for chunk in chunks:
                if any(
                    c.label in [DocItemLabel.TEXT, DocItemLabel.PARAGRAPH]
                    for c in chunk.meta.doc_items
                ):
                    i += 1
                    chunk_count += 1
                    llama_documents.append(
                        LlamaStackDocument(
                            document_id=f"doc-{i}",
                            content=chunk.text,
                            mime_type="text/plain",
                            metadata={"source": file_path},
                        )
                    )
            
            processing_metrics["processed_documents"].append({
                "file": file_path,
                "chunks": chunk_count
            })
        except Exception as e:
            error_message = str(e)
            print(f"Error processing {file_path}: {error_message}")
            processing_metrics["failed_documents"].append({
                "file": file_path,
                "error": error_message
            })

    total_chunks = len(llama_documents)
    processing_metrics["total_chunks"] = total_chunks
    print(f"Total valid documents prepared: {total_chunks}")

    # === Step 4: Create Vector DB ===
    try:
        client.vector_dbs.register(
            vector_db_id=vector_db_id,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            provider_id=provider_id,
        )
        print(f"Vector DB registered successfully: {vector_db_id}")
        processing_metrics["vector_db_registration"] = "success"

    except Exception as e:
        error_message = str(e)
        print(f"Failed to register vector DB '{vector_db_id}': {error_message}")
        processing_metrics["vector_db_registration"] = {
            "status": "failed",
            "error": error_message
        }

    # === Step 5: Insert into Vector DB ===
    try:
        client.tool_runtime.rag_tool.insert(
            documents=llama_documents,
            vector_db_id=vector_db_id,
            chunk_size_in_tokens=512,
        )
        print("Documents successfully inserted into the vector DB.")
        processing_metrics["vector_db_insertion"] = "success"

    except Exception as e:
        error_message = str(e)
        print(f"Error inserting documents into RAG tool: {error_message}")
        processing_metrics["vector_db_insertion"] = {
            "status": "failed",
            "error": error_message
        }
    
    # Write metrics to output
    with open(metrics_path, 'w') as f:
        json.dump(processing_metrics, f, indent=2)

    return total_chunks


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
    component_yaml_path = os.path.join(components_yaml_dir, "rag_docling_component.yaml")
    
    # Save the RAG component
    compiler.Compiler().compile(rag_docling_component, package_path=component_yaml_path)
    print(f"RAG component YAML saved to {component_yaml_path}") 