import uuid
from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Document as LlamaStackDocument

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.labels import DocItemLabel


def process_documents_to_vectordb(
    llama_stack_url="http://localhost:8321",
    documents=["docling.pdf"],
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimension=384,
    provider_id="pgvector",
    vector_db_id="pgvector"
):
    """
    Process documents, convert them to chunks, and store in a vector database.
    
    Args:
        llama_stack_url (str): URL for the Llama Stack API
        documents (list): List of document file paths to process
        embedding_model (str): Model to use for embeddings
        embedding_dimension (int): Dimension size for embeddings
        provider_id (str): Provider ID for vector database
        vector_db_id (str): ID for the vector database
        
    Returns:
        int: Number of documents processed
    """
    # === Step 1: Configure Llama Stack client ===
    client = LlamaStackClient(base_url=llama_stack_url)  # Assumes LLAMA_STACK_API_KEY is set in env

    # === Step 2: Convert, Chunk, and Prepare Documents ===
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

    for file_path in documents:
        print(f"Processing {file_path}...")
        try:
            docling_doc = converter.convert(source=file_path).document
            chunks = chunker.chunk(docling_doc)

            for chunk in chunks:
                if any(
                    c.label in [DocItemLabel.TEXT, DocItemLabel.PARAGRAPH]
                    for c in chunk.meta.doc_items
                ):
                    i += 1
                    llama_documents.append(
                        LlamaStackDocument(
                            document_id=f"doc-{i}",
                            content=chunk.text,
                            mime_type="text/plain",
                            metadata={"source": file_path},
                        )
                    )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"Total valid documents prepared: {len(llama_documents)}")

    # === Step 3: Create Vector DB ===
    try:
        client.vector_dbs.register(
            vector_db_id=vector_db_id,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
            provider_id=provider_id,
        )
        print(f"Vector DB registered successfully: {vector_db_id}")

    except Exception as e:
        print(f"Failed to register vector DB '{vector_db_id}': {e}")

    # === Step 4: Insert into Vector DB ===
    try:
        client.tool_runtime.rag_tool.insert(
            documents=llama_documents,
            vector_db_id=vector_db_id,
            chunk_size_in_tokens=512,
        )
        print("Documents successfully inserted into the vector DB.")

    except Exception as e:
        print(f"Error inserting documents into RAG tool: {e}")

    return len(llama_documents)


# Example usage
if __name__ == "__main__":
    process_documents_to_vectordb(
        documents=["docling.pdf"],
        vector_db_id="pgvector"
    )
