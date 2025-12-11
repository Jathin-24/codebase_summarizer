import os
import re
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

# Common entry points by language
ENTRYPOINT_PATTERNS = {
    ".py": ["main.py", "app.py", "server.py", "run.py"],
    ".js": ["index.js", "server.js", "app.js", "main.js"],
    ".ts": ["index.ts", "server.ts", "app.ts", "main.ts"],
    ".java": ["Main.java", "App.java"],
    ".go": ["main.go"],
}

# Common module patterns (high importance)
MODULE_PATTERNS = {
    "models": r".*model.*",
    "routes": r".*route.*|.*router.*",
    "controllers": r".*controller.*",
    "services": r".*service.*",
    "utils": r".*util.*|.*helper.*",
    "config": r".*config.*|.*setting.*",
    "db": r".*db.*|.*database.*",
}

def detect_entrypoints(file_paths: List[str]) -> List[str]:
    """Detect likely entry points based on filename patterns."""
    entrypoints = []
    basename_to_ext = {}
    
    for path in file_paths:
        basename = os.path.basename(path)
        ext = os.path.splitext(basename)[1]
        basename_to_ext[basename.lower()] = path
    
    for ext, patterns in ENTRYPOINT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in basename_to_ext:
                entrypoints.append(basename_to_ext[pattern.lower()])
    
    return entrypoints

def detect_important_modules(file_paths: List[str]) -> Dict[str, float]:
    """Score files by importance based on filename patterns and position."""
    scores = defaultdict(float)
    
    for path in file_paths:
        basename = os.path.basename(path).lower()
        rel_path = path  # simplified
        
        # Position-based scoring (root files more important)
        depth = rel_path.count(os.sep)
        position_score = max(1.0 - depth * 0.2, 0.1)
        
        # Pattern matching
        pattern_score = 0.0
        for category, regex in MODULE_PATTERNS.items():
            if re.search(regex, basename):
                pattern_score += 0.8
                break
        
        scores[path] = position_score + pattern_score
    
    # Normalize to 0-1 range
    if scores:
        max_score = max(scores.values())
        for path in scores:
            scores[path] /= max_score
    
    return dict(scores)

def extract_imports(content: str, file_ext: str) -> List[str]:
    """Extract import statements (simplified heuristic)."""
    imports = []
    
    if file_ext == ".py":
        # Python imports
        py_imports = re.findall(r'^(?:from|import)\s+[\w\.]+', content, re.MULTILINE)
        imports.extend(py_imports)
    
    elif file_ext in {".js", ".ts"}:
        # JS/TS imports
        js_imports = re.findall(r'^(?:import|from)\s+["\'][^"\']+["\']', content, re.MULTILINE)
        imports.extend(js_imports)
    
    return imports

def build_simple_graph(file_paths: List[str], file_contents: Dict[str, str]) -> Dict:
    """Build a simple dependency graph for visualization."""
    nodes = []
    edges = []
    
    # Create nodes for all files
    for path in file_paths:
        ext = os.path.splitext(path)[1]
        nodes.append({
            "id": path,
            "label": os.path.basename(path),
            "color": "#909090"  # default gray
        })
    
    # Simple edges: assume root files → modules they might import
    # (Day 3 simplified version; Day 4 could parse actual imports)
    root_files = [p for p in file_paths if len(p.split(os.sep)) <= 1]
    for root in root_files:
        for module in file_paths:
            if root != module and "src" in module:
                edges.append({
                    "from": root,
                    "to": module,
                    "label": "uses"
                })
    
    return {"nodes": nodes, "edges": edges}
