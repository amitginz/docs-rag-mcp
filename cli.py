"""Command-line entry point: index docs, search, or ask a question."""
import argparse
from pathlib import Path

from rag.answer import answer
from rag.store import DocStore

parser = argparse.ArgumentParser(description="Docs RAG")
sub = parser.add_subparsers(dest="cmd", required=True)
idx = sub.add_parser("index"); idx.add_argument("docs", nargs="?", default="docs")
srch = sub.add_parser("search"); srch.add_argument("query"); srch.add_argument("-k", type=int, default=4)
ask = sub.add_parser("ask"); ask.add_argument("question")
args = parser.parse_args()
store = DocStore(Path(".chroma"))
if args.cmd == "index":
    print(f"Indexed {store.index(args.docs)} chunks")
elif args.cmd == "search":
    for h in store.search(args.query, args.k):
        print(f"{h.distance:.3f}  {h.source} - {h.heading}")
else:
    r = answer(store, args.question)
    print(r.text, "\nSources:", ", ".join(r.sources) or "-")
