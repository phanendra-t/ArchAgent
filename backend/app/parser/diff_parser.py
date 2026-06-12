"""Parser for unified diff format."""
from __future__ import annotations
from dataclasses import dataclass, field
from unidiff import PatchSet


@dataclass
class ChangedFile:
    """Represents a single file changed in a PR."""
    path: str
    is_new: bool = False
    is_deleted: bool = False
    added_lines: list[tuple[int, str]] = field(default_factory=list)  # (line_num, content)
    removed_lines: list[tuple[int, str]] = field(default_factory=list)
    full_diff: str = ""


@dataclass
class ParsedDiff:
    """Complete parsed diff with all changed files."""
    files: list[ChangedFile] = field(default_factory=list)
    raw_diff: str = ""

    @property
    def file_paths(self) -> list[str]:
        return [f.path for f in self.files]

    @property
    def added_imports(self) -> list[dict]:
        """Extract newly added import/require/from statements."""
        imports = []
        for file in self.files:
            for line_num, line in file.added_lines:
                import_info = _detect_import(line, file.path)
                if import_info:
                    imports.append({
                        "file": file.path,
                        "line": line_num,
                        "statement": line.strip(),
                        **import_info,
                    })
        return imports


def parse_diff(diff_text: str) -> ParsedDiff:
    """Parse a unified diff string into structured data."""
    patch = PatchSet(diff_text)
    files = []

    for patched_file in patch:
        changed = ChangedFile(
            path=patched_file.path,
            is_new=patched_file.is_added_file,
            is_deleted=patched_file.is_removed_file,
        )

        for hunk in patched_file:
            for line in hunk:
                if line.is_added:
                    changed.added_lines.append((line.target_line_no, line.value))
                elif line.is_removed:
                    changed.removed_lines.append((line.source_line_no, line.value))

        # Store the full diff for this file
        changed.full_diff = str(patched_file)
        files.append(changed)

    return ParsedDiff(files=files, raw_diff=diff_text)


def _detect_import(line: str, file_path: str) -> dict | None:
    """Detect if a line is an import statement (language-agnostic)."""
    import re
    line = line.strip()

    # TypeScript/JavaScript: import X from 'Y' or import { X } from 'Y'
    match = re.match(r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", line)
    if match:
        return {"type": "es_import", "source": match.group(1)}

    # TypeScript/JavaScript: import 'Y' (side-effect)
    match = re.match(r"import\s+['\"]([^'\"]+)['\"]", line)
    if match:
        return {"type": "es_import_side_effect", "source": match.group(1)}

    # CommonJS: require('Y')
    match = re.match(r"(?:const|let|var)\s+.*=\s*require\(['\"]([^'\"]+)['\"]\)", line)
    if match:
        return {"type": "commonjs_require", "source": match.group(1)}

    # Python: from X import Y
    match = re.match(r"from\s+(\S+)\s+import", line)
    if match:
        return {"type": "python_from_import", "source": match.group(1)}

    # Python: import X
    match = re.match(r"import\s+(\S+)", line)
    if match and not line.startswith("import {"):  # Exclude JS destructured imports
        return {"type": "python_import", "source": match.group(1)}

    # Go: import "X"
    match = re.match(r'\s*"([^"]+)"', line)
    if match and file_path.endswith(".go"):
        return {"type": "go_import", "source": match.group(1)}

    # Java/Kotlin: import X.Y.Z
    match = re.match(r"import\s+([\w.]+)", line)
    if match and (file_path.endswith(".java") or file_path.endswith(".kt")):
        return {"type": "java_import", "source": match.group(1)}

    # Rust: use X::Y
    match = re.match(r"use\s+([\w:]+)", line)
    if match:
        return {"type": "rust_use", "source": match.group(1)}

    # C#: using X.Y
    match = re.match(r"using\s+([\w.]+)", line)
    if match:
        return {"type": "csharp_using", "source": match.group(1)}

    return None
