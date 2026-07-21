import re
from pathlib import Path


def parse_file(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    content = path.read_text(encoding="utf-8", errors="replace")
    name = extract_title(content) or path.stem
    steps = extract_steps(content)

    return {"name": name, "path": str(path.resolve()), "steps": steps}


def extract_title(content: str) -> str:
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_steps(content: str) -> list[dict]:
    steps = []
    step_index = 0
    in_code_block = False

    last_h2_index = None
    last_heading_index = None
    list_stack = []

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        h2 = re.match(r"^##\s+(.+)$", stripped)
        if h2:
            steps.append({
                "step_index": step_index,
                "title": h2.group(1).strip(),
                "level": "h2",
                "parent_index": None,
            })
            last_h2_index = step_index
            last_heading_index = step_index
            list_stack = []
            step_index += 1
            continue

        h3 = re.match(r"^###\s+(.+)$", stripped)
        if h3:
            steps.append({
                "step_index": step_index,
                "title": h3.group(1).strip(),
                "level": "h3",
                "parent_index": last_h2_index,
            })
            last_heading_index = step_index
            list_stack = []
            step_index += 1
            continue

        bullet = re.match(r"^(\s*)([-*+])\s+(.+)$", line)
        if bullet:
            indent = len(bullet.group(1))
            text = bullet.group(3).strip()
            if len(text) > 2:
                while list_stack and list_stack[-1][0] >= indent:
                    list_stack.pop()

                parent = None
                if list_stack:
                    parent = list_stack[-1][1]
                elif last_heading_index is not None:
                    parent = last_heading_index

                steps.append({
                    "step_index": step_index,
                    "title": text,
                    "level": "list",
                    "parent_index": parent,
                })
                list_stack.append((indent, step_index))
                step_index += 1
                continue

        numbered = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if numbered:
            indent = len(numbered.group(1))
            text = numbered.group(2).strip()
            if len(text) > 2:
                while list_stack and list_stack[-1][0] >= indent:
                    list_stack.pop()

                parent = None
                if list_stack:
                    parent = list_stack[-1][1]
                elif last_heading_index is not None:
                    parent = last_heading_index

                steps.append({
                    "step_index": step_index,
                    "title": text,
                    "level": "list",
                    "parent_index": parent,
                })
                list_stack.append((indent, step_index))
                step_index += 1

    return steps
