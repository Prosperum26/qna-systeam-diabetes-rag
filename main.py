"""
Entry point - chạy crawl, build index, hoặc Q&A.
Usage:
  python main.py crawl      # Crawl web -> lưu raw
  python main.py index      # Process + embed + build vectorstore
  python main.py ask        # Chạy Q&A interactive
Chạy các pipelines từ src/pipelines

"""
import sys

# TODO: Implement CLI
# - crawl: gọi crawler, lưu vào data/raw
# - index: load raw -> chunk -> embed -> add to vectorstore
# - ask: load RAG pipeline, loop input question


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands: crawl | index | ask")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "crawl":
        # TODO: run crawler
        print("TODO: Implement crawl")
    elif cmd == "index":
        # TODO: run index pipeline
        print("TODO: Implement index")
    elif cmd == "ask":
        # TODO: run Q&A loop
        print("TODO: Implement ask")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
