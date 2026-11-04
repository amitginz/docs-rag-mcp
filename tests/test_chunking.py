from pathlib import Path

from rag.chunking import chunk_file, split_sections, split_words


def test_split_sections_keeps_headings():
    sections = split_sections("# Title\n\nintro\n\n## A\n\nalpha\n\n## B\n\nbeta")
    assert sections == [("Title", "intro"), ("A", "alpha"), ("B", "beta")]


def test_split_words_overlaps():
    pieces = split_words(" ".join(str(i) for i in range(10)), max_words=5, overlap=2)
    assert pieces[0].split()[-2:] == pieces[1].split()[:2]


def test_chunk_file_prefixes_heading(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("## Topic\n\nsome text here")
    chunks = chunk_file(f)
    assert chunks[0].text.startswith("Topic\n") and chunks[0].source == "doc.md"
