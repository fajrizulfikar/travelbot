import json
import tempfile
import os
from pathlib import Path


def parse_pdf(file_bytes: bytes) -> str:
    from langchain_community.document_loaders import PyPDFLoader
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name
    try:
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
        return "\n".join(p.page_content for p in pages)
    finally:
        os.unlink(tmp_path)


def parse_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8")


def parse_faq_json(file_bytes: bytes) -> str:
    data = json.loads(file_bytes.decode("utf-8"))
    lines = []
    if isinstance(data, list):
        for item in data:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                lines.append(f"Q: {q}\nA: {a}")
            elif q:
                lines.append(f"Q: {q}")
            elif a:
                lines.append(f"A: {a}")
    return "\n\n".join(lines)


def parse(filename: str, file_bytes: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_bytes)
    elif ext == ".txt":
        return parse_txt(file_bytes)
    elif ext == ".json":
        return parse_faq_json(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")
