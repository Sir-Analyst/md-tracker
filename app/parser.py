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
            })
            step_index += 1
            continue

        h3 = re.match(r"^###\s+(.+)$", stripped)
        if h3:
            steps.append({
                "step_index": step_index,
                "title": h3.group(1).strip(),
                "level": "h3",
            })
            step_index += 1
            continue

        listItem = re.match(r"^\d+\.\s+(.+)$", stripped)
        if listItem:
            text = listItem.group(1).strip()
            if len(text) > 5 and not text.startswith("```"):
                steps.append({
                    "step_index": step_index,
                    "title": text,
                    "level": "list",
                })
                step_index += 1

    return steps
