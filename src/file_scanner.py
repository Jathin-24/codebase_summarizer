import os
from typing import List

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".kt", ".cpp", ".c", ".cs",
    ".go", ".rs", ".php",".html", ".css"
}

IGNORE_DIRS = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}


def is_code_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in CODE_EXTENSIONS


def list_code_files(root_path: str) -> List[str]:
    code_files: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # prune ignored dirs in-place for efficiency
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for fname in filenames:
            if is_code_file(fname):
                full_path = os.path.join(dirpath, fname)
                code_files.append(full_path)

    return code_files
