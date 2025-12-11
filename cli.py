import argparse
import json
from pathlib import Path

from src.summarizer import summarize_project


def main():
    parser = argparse.ArgumentParser(
        description="Codebase summarizer using Gemini"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the project root to summarize",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="code_summary.json",
        help="Output JSON file for summaries",
    )

    args = parser.parse_args()
    root_path = Path(args.path).resolve()

    if not root_path.exists():
        raise SystemExit(f"Path does not exist: {root_path}")

    print(f"Scanning and summarizing: {root_path}")
    result = summarize_project(str(root_path))

    out_path = Path(args.out).resolve()
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Summary written to {out_path}")


if __name__ == "__main__":
    main()
