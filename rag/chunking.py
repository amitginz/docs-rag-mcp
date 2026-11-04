"""Split markdown documents into overlapping, heading-aware chunks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    heading: str
    text: str


def split_sections(markdown: str) -> list[tuple[str, str]]:
    """Return (heading, body) pairs. Text before the first heading gets an empty heading."""
    sections: list[tuple[str, str]] = []
    heading, lines = "", []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.*)", line)
        if match:
            if "".join(lines).strip():
                sections.append((heading, "\n".join(lines).strip()))
            heading, lines = match.group(2).strip(), []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((heading, "\n".join(lines).strip()))
    return sections


def split_words(text: str, max_words: int, overlap: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    step = max(1, max_words - overlap)
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), step)]


def chunk_file(path: Path, max_words: int = 120, overlap: int = 20) -> list[Chunk]:
    chunks: list[Chunk] = []
    for s_index, (heading, body) in enumerate(split_sections(path.read_text(encoding="utf-8"))):
        for c_index, piece in enumerate(split_words(body, max_words, overlap)):
            text = f"{heading}\n{piece}" if heading else piece
            chunks.append(Chunk(f"{path.name}:{s_index}:{c_index}", path.name, heading, text))
    return chunks


def chunk_directory(directory: Path, **kwargs) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("**/*.md")):
        chunks.extend(chunk_file(path, **kwargs))
    return chunks
