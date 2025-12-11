import os
from typing import Dict, List
from .llm_client import summarize_text_chunks

MAX_FOLDER_SUMMARY_CHARS = 4000


def _chunk_text(text: str, max_chars: int = MAX_FOLDER_SUMMARY_CHARS) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def aggregate_folder_summaries(
    root_path: str,
    file_summaries: Dict[str, str],
) -> Dict[str, str]:
    """
    Build folder-level summaries from child file summaries.

    file_summaries keys are relative paths like:
      "src/api/routes.py"

    Returns:
      { "": "...root description...",
        "src": "...",
        "src/api": "..." }
    """
    folders: Dict[str, List[str]] = {}

    for rel_path, summary in file_summaries.items():
        folder = os.path.dirname(rel_path)  # "" or "src" or "src/api"
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(f"{rel_path}: {summary}")

    folder_summaries: Dict[str, str] = {}

    for folder, items in folders.items():
        combined = "\n\n".join(items)
        chunks = _chunk_text(combined)

        system_instruction = (
            "You are an AI assistant that summarizes folders in a codebase. "
            "You are given descriptions of files directly inside this folder "
            "and in its subfolders. Describe what this folder represents in "
            "the project, its main responsibilities, and how it fits into the "
            "overall codebase. Do not invent behavior that is not supported "
            "by the file summaries."
        )

        metadata_text = f"Folder path (relative to project root): '{folder or '/'}'"

        summary = summarize_text_chunks(
            chunks,
            system_instruction,
            filename=folder or "ROOT_FOLDER",
            metadata_text=metadata_text,
        )

        folder_summaries[folder] = summary

    return folder_summaries
