import glob
import json
import os
from pathlib import Path

from src.chunking.token_counter import TokenCounter
from src.chunking.chunker import HybridChunker


DOCUMENT_DIR = "./data/documents"
CHUNK_DIR = "./data/chunked"


def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)

    counter = TokenCounter()
    chunker = HybridChunker(token_counter=counter)

    paths = glob.glob(f"{DOCUMENT_DIR}/*.json")

    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        chunks = chunker.chunk_document(doc)

        # Lấy tên file document
        doc_name = Path(path).stem
        output_path = os.path.join(CHUNK_DIR, f"{doc_name}_chunks.jsonl")

        # overwrite file cũ
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                chunk["source_file"] = f"{doc_name}.json"
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        print(f"{doc_name}: {len(chunks)} chunks → {output_path}")


if __name__ == "__main__":
    main()