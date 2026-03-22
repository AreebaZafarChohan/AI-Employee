import re
from typing import Any


def parse_markdown(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content. Returns (metadata, body)."""
    match = re.match(r"^---\n([\s\S]*?)\n---", content)
    if not match:
        return {}, content

    metadata: dict[str, Any] = {}
    for line in match.group(1).split("\n"):
        idx = line.find(":")
        if idx > -1:
            key = line[:idx].strip()
            value = line[idx + 1:].strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            metadata[key] = value

    body = content.replace(match.group(0), "").strip()
    return metadata, body
