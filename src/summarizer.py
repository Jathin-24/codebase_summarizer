from typing import Dict, List, Any
import os

from .file_scanner import list_code_files
from .llm_client import summarize_text_chunks
from .folder_aggregator import aggregate_folder_summaries
from .workflow_analyzer import (
    detect_entrypoints, 
    detect_important_modules, 
    build_real_dependency_graph,
    security_scan
)

MAX_CHARS_PER_CHUNK = 4000
MIN_CONTENT_LENGTH = 30


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
    content = _read_file(path)
    stats = _get_file_stats(path)

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


def summarize_project(root_path: str) -> Dict[str, Any]:
    """
    COMPLETE Day 3 implementation with proper variable ordering.
    """
    file_paths = list_code_files(root_path)
    file_summaries: Dict[str, str] = {}

    if not file_paths:
        return {
            "project_summary": "No code files were detected in this project.",
            "files": {},
            "folders": {},
            "workflow": {"entrypoints": [], "important_modules": {}, "top_modules": [], "graph": {"nodes": [], "edges": []}}
        }

    # Step 1: File summaries (existing)
    print("📁 Scanning files...")
    for abs_path in file_paths:
        rel_path = os.path.relpath(abs_path, root_path)
        print(f"  📄 Summarizing {rel_path} ...")
        file_summaries[rel_path] = summarize_file(abs_path)

    # Step 2: Folder summaries (existing Day 2)
    print("📂 Aggregating folders...")
    folder_summaries = aggregate_folder_summaries(root_path, file_summaries)

    # Step 3: Day 3 Workflow analysis (NEW)
    print("🔍 Analyzing workflow...")
    file_contents = {path: _read_file(path) for path in file_paths}
    
    entrypoints = detect_entrypoints(file_paths)
    module_importance = detect_important_modules(file_paths)
    top_modules = sorted(module_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    graph_data = build_real_dependency_graph(file_paths, file_contents)

    # Step 4: Enhanced project summary with ALL context
    print("🎯 Generating project summary...")
    project_context_lines = []

    # Workflow context FIRST (Day 3)
    project_context_lines.append("=== WORKFLOW ENTRY POINTS ===")
    for ep in entrypoints:
        rel_ep = os.path.relpath(ep, root_path)
        project_context_lines.append(f"Likely entrypoint: {rel_ep}")

    project_context_lines.append("\n=== MOST IMPORTANT MODULES ===")
    for path, score in top_modules:
        rel_path = os.path.relpath(path, root_path)
        project_context_lines.append(f"{rel_path}: importance {score:.1f}")

    # Folder summaries (Day 2)
    project_context_lines.append("\n=== FOLDER SUMMARIES ===")
    for folder, summary in folder_summaries.items():
        label = folder or "<root>"
        project_context_lines.append(f"[Folder: {label}] {summary}")

    # File summaries (top 10 for context)
    project_context_lines.append("\n=== TOP 10 FILE SUMMARIES ===")
    top_files = sorted(file_summaries.items(), key=lambda x: len(x[1]))[:10]
    for path, summary in top_files:
        project_context_lines.append(f"[File: {path}] {summary[:150]}...")

    project_text = "\n\n".join(project_context_lines)
    project_chunks = _chunk_text(project_text)

    system_instruction = (
        "You are an AI assistant that summarizes entire codebases. "
        "You are given entry points, important modules, folder descriptions, "
        "and file summaries. Describe the overall purpose of the project, "
        "its main workflow (entrypoints → modules → data flow), "
        "architecture patterns, and key components. "
        "Stay consistent with all provided information."
    )

    project_summary = summarize_text_chunks(
        project_chunks,
        system_instruction,
        filename="PROJECT_OVERVIEW",
    )

    # Day 3: Security scan (NEW IMPACT FEATURE)
    print("🛡️ Running security scan...")
    security = security_scan(file_contents)

    return {
        "project_summary": project_summary,
        "files": file_summaries,
        "folders": folder_summaries,
        "workflow": {
            "entrypoints": [os.path.relpath(ep, root_path) for ep in entrypoints],
            "important_modules": {os.path.relpath(k, root_path): v for k, v in module_importance.items()},
            "top_modules": [(os.path.relpath(p, root_path), score) for p, score in top_modules],
            "graph": graph_data
        },
        "security": security  # ADD THIS LINE
    }

