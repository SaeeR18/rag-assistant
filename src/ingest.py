import argparse
import shutil
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src import config


def load_pdfs():
    """Read every PDF in data/docs and return the files and all their pages."""
    pdf_files = sorted(config.DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDFs found in {config.DOCS_DIR}")

    pages = []
    for pdf in pdf_files:
        try:
            loaded = PyPDFLoader(str(pdf)).load()
        except Exception as error:
            print(f"  Skipping {pdf.name}: {error}")
            continue
        for page in loaded:
            # Remember where each piece of text came from
            page.metadata["file_name"] = pdf.name
            page.metadata["page_number"] = page.metadata.get("page", 0) + 1
            pages.append(page)
    return pdf_files, pages


def reset_database():
    """Delete the old saved database so we start clean."""
    if config.CHROMA_DIR.exists() and config.CHROMA_DIR.name == "chroma_db":
        shutil.rmtree(config.CHROMA_DIR)
        print("Old database deleted.")


def main():
    parser = argparse.ArgumentParser(description="Build the vector database.")
    parser.add_argument("--chunk-size", type=int, default=config.CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=config.CHUNK_OVERLAP)
    args = parser.parse_args()

    start = time.time()

    print("Step 1: loading PDFs...")
    pdf_files, pages = load_pdfs()
    print(f"  Files: {len(pdf_files)}")
    print(f"  Total pages: {len(pages)}")

    print("Step 2: splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
    )
    chunks = splitter.split_documents(pages)
    chunks = [c for c in chunks if c.page_content.strip()]
    average = sum(len(c.page_content) for c in chunks) // max(len(chunks), 1)
    print(f"  Chunk size: {args.chunk_size}, overlap: {args.overlap}")
    print(f"  Total chunks: {len(chunks)} (average {average} characters)")

    print("Step 3: creating embeddings and saving to Chroma...")
    reset_database()
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.CHROMA_DIR),
    )

    print(f"Done in {time.time() - start:.0f} seconds.")
    print("\nSample chunk:")
    print("  File:", chunks[0].metadata["file_name"], "| Page:", chunks[0].metadata["page_number"])
    print("  Text:", chunks[0].page_content[:200].replace("\n", " "), "...")


if __name__ == "__main__":
    main()