from .file_scanner import list_code_files
from .llm_client import summarize_text_chunks
from .folder_aggregator import aggregate_folder_summaries
from typing import Dict, List
import os

from .file_scanner import list_code_files
from .llm_client import summarize_text_chunks

MAX_CHARS_PER_CHUNK = 4000  # safe baseline for Gemini context. [web:30][web:32]
MIN_CONTENT_LENGTH = 30      # below this, treat as empty / trivial


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: Could not read file {path}: {e}"


def _chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def _get_file_stats(path: str) -> Dict[str, int]:
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        num_lines = len(lines)
    except Exception:
        num_lines = 0

    return {
        "size_bytes": size,
        "num_lines": num_lines,
    }


def summarize_file(path: str) -> str:
    """
    Summarize a single file with guardrails:
    - If empty / trivial -> deterministic message.
    - Else -> Gemini summary with strict rules.
    """

    content = _read_file(path)
    stats = _get_file_stats(path)

    # Debug (optional)
    # print(f"DEBUG {path}: {stats}, preview={repr(content[:120])}")

    # If file is effectively empty or has no meaningful content
    if (
        stats["num_lines"] == 0
        or not content
        or len(content.strip()) < MIN_CONTENT_LENGTH
    ):
        return (
            f"This file ({os.path.basename(path)}) is effectively empty or contains "
            f"no meaningful code/content yet "
            f"({stats['num_lines']} lines, {stats['size_bytes']} bytes)."
        )

    chunks = _chunk_text(content)

    system_instruction = (
        "You are an AI assistant that explains source code files to developers. "
        "Focus on what is actually implemented in the file."
    )

    metadata_text = (
        f"Lines of code: {stats['num_lines']}\n"
        f"Size (bytes): {stats['size_bytes']}"
    )

    return summarize_text_chunks(
        chunks,
        system_instruction,
        filename=os.path.basename(path),
        metadata_text=metadata_text,
    )


def summarize_project(root_path: str) -> Dict[str, Dict]:
    """
    Summarize all files, folders, and then the overall project.

    Returns:
      {
        "project_summary": "...",
        "files": { "rel/file.py": "..." },
        "folders": { "rel/folder": "..." }
      }
    """

    file_paths = list_code_files(root_path)
    file_summaries: Dict[str, str] = {}

    if not file_paths:
        return {
            "project_summary": "No code files were detected in this project.",
            "files": {},
            "folders": {},
        }

    for abs_path in file_paths:
        rel_path = os.path.relpath(abs_path, root_path)
        print(f"Summarizing {rel_path} ...")
        file_summaries[rel_path] = summarize_file(abs_path)

    # Day 2: folder-level aggregation
    folder_summaries = aggregate_folder_summaries(root_path, file_summaries)

    # Build project summary from both file and folder summaries
    project_context_lines = []

    project_context_lines.append("=== FOLDER SUMMARIES ===")
    for folder, summary in folder_summaries.items():
        label = folder or "<root>"
        project_context_lines.append(f"[Folder: {label}] -> {summary}")

    project_context_lines.append("\n=== FILE SUMMARIES ===")
    for path, summary in file_summaries.items():
        project_context_lines.append(f"[File: {path}] -> {summary}")

    project_text = "\n\n".join(project_context_lines)
    project_chunks = _chunk_text(project_text)

    system_instruction = (
        "You are an AI assistant that summarizes entire codebases. "
        "You are given folder-level and file-level descriptions. "
        "Describe the overall purpose of the project, its main components, "
        "typical workflow (entrypoints and major flows), and any notable "
        "architectural patterns. Stay consistent with the provided summaries."
    )

    project_summary = summarize_text_chunks(
        project_chunks,
        system_instruction,
        filename="PROJECT",
    )

    return {
        "project_summary": project_summary,
        "files": file_summaries,
        "folders": folder_summaries,
    }

