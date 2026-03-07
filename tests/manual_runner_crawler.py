"""
Manual test runner for project modules.

Usage examples (from project root):

  # Chạy crawler tiểu đường với 5 bài
  python -m tests.manual_runner_crawler --max-articles 5

"""
import argparse
import logging

from src.crawler import run_diabetes_crawler


def run_crawler(args: argparse.Namespace) -> None:
    """Run the Diabetes crawler with CLI-provided options."""
    # Logging cấu hình cơ bản cho test thủ công
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    run_diabetes_crawler(max_articles=args.max_articles, base_dir=args.base_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manual test runner for qna-systeam-diabetes-rag modules.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Crawler runner
    crawler_parser = subparsers.add_parser(
        "crawler",
        help="Run Diabetes crawler (yhoccongdong.com/tieu-duong).",
    )
    crawler_parser.add_argument(
        "--max-articles",
        type=int,
        default=5,
        help="Số lượng bài viết cần crawl (mặc định: 5).",
    )
    crawler_parser.add_argument(
        "--base-dir",
        type=str,
        default="data",
        help="Thư mục gốc để lưu raw HTML và documents (mặc định: data).",
    )
    crawler_parser.set_defaults(func=run_crawler)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Mỗi subcommand có 1 hàm run riêng, chỉ chạy đúng module tương ứng.
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return

    func(args)


if __name__ == "__main__":
    main()

