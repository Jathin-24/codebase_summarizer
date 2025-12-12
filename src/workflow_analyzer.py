import os
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
import ast  # Python AST parsing

# Common entry points by language
ENTRYPOINT_PATTERNS = {
    ".py": ["main.py", "app.py", "server.py", "run.py", "manage.py"],
    ".js": ["index.js", "server.js", "app.js", "main.js"],
    ".ts": ["index.ts", "server.ts", "app.ts", "main.ts"],
    ".java": ["Main.java", "App.java"],
    ".go": ["main.go"],
    ".rs": ["main.rs", "lib.rs"],
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
    basename_to_path = {}
    
    for path in file_paths:
        basename = os.path.basename(path).lower()
        basename_to_path[basename] = path
    
    for ext, patterns in ENTRYPOINT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in basename_to_path:
                entrypoints.append(basename_to_path[pattern.lower()])
    
    return entrypoints

def detect_important_modules(file_paths: List[str]) -> Dict[str, float]:
    """Score files by importance based on filename patterns and position."""
    scores = defaultdict(float)
    
    for path in file_paths:
        basename = os.path.basename(path).lower()
        rel_path = path
        
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

def parse_python_imports(content: str) -> List[str]:
    """Parse ACTUAL Python imports using AST."""
    try:
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module.split('.')[0] if node.module else 'local')
        return list(set(imports))
    except:
        return []

def parse_js_imports(content: str) -> List[str]:
    """Parse JavaScript imports."""
    imports = re.findall(r'(?:import|from)\s+["\']([^"\']+)["\']', content)
    return [imp.split('/')[0] for imp in imports if imp]

def build_real_dependency_graph(file_paths: List[str], file_contents: Dict[str, str]) -> Dict:
    """Build ACTUAL dependency graph from import statements."""
    nodes = []
    edges = []
    
    # Build nodes
    for path in file_paths:
        basename = os.path.basename(path)
        ext = os.path.splitext(path)[1]
        nodes.append({
            "id": path,
            "label": basename,
            "group": ext[1:],  # color by language
            "size": 15
        })
    
    # Build REAL edges from imports
    for path, content in file_contents.items():
        ext = os.path.splitext(path)[1]
        
        if ext == '.py':
            imports = parse_python_imports(content)
        elif ext in {'.js', '.ts'}:
            imports = parse_js_imports(content)
        else:
            imports = []
        
        # Find matching files
        for imp in imports[:5]:  # limit per file
            for candidate in file_paths:
                if imp.lower() in os.path.basename(candidate).lower():
                    edges.append({
                        "from": path,
                        "to": candidate,
                        "label": "imports",
                        "value": 1
                    })
                    break
    
    return {"nodes": nodes, "edges": edges[:50]}  # limit edges

def security_scan(file_contents: Dict[str, str]) -> Dict:
    """Scan for security risks and secrets."""
    risks = []
    
    for path, content in file_contents.items():
        issues = []
        
        # Secrets scan
        secrets_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{20,40}["\']',
            r'password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
            r'AKIA[0-9A-Z]{16}',  # AWS keys
            r'ghp_[0-9a-zA-Z]{36}'  # GitHub tokens
        ]
        for pattern in secrets_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("🔴 Potential secret found")
        
        # Security risks
        if "exec(" in content or "eval(" in content:
            issues.append("⚠️ Dangerous eval/exec detected")
        if "subprocess" in content and "shell=True" in content:
            issues.append("⚠️ Shell injection risk")
            
        if issues:
            risks.append({"file": path, "issues": issues})
    
    return {"risks": risks[:10], "total_files_scanned": len(file_contents)}

def predict_api_cost(num_files: int, avg_file_size_kb: float = 20) -> Dict[str, Any]:
    """Predict Gemini API cost before running."""
    tokens_per_kb = 250
    total_input_tokens = int(num_files * avg_file_size_kb * tokens_per_kb * 1.5)
    total_output_tokens = int(total_input_tokens * 0.3)
    
    cost_per_1m_input = 0.075 / 1000000
    cost_per_1m_output = 0.3 / 1000000
    
    total_cost = (total_input_tokens * cost_per_1m_input + 
                  total_output_tokens * cost_per_1m_output)
    
    return {
        "estimated_cost_usd": round(total_cost, 4),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "files": num_files
    }
