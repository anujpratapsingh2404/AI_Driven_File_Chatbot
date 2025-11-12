from langchain_community.document_loaders import (
    PyMuPDFLoader as PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader,
)


def load_pdf(path: str):
    loader = PyPDFLoader(path)
    return loader.load()


def load_docx(path: str):
    loader = Docx2txtLoader(path)
    return loader.load()


def load_text(path: str):
    loader = TextLoader(path, encoding="utf-8")
    return loader.load()


def load_url_file(path: str):
    """
    `path` is expected to be a file in uploaded_files containing the URL text.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            url = f.read().strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("Invalid URL format")
        loader = WebBaseLoader(url)
        return loader.load()
    except Exception as e:
        raise RuntimeError(f"URL Loader Error: {e}")


def load_docs_by_ext(ext: str, path: str):
    ext = ext.lower()
    if ext == "pdf":
        return load_pdf(path)
    if ext == "docx":
        return load_docx(path)
    if ext in ("txt", "text"):
        return load_text(path)
    if ext == "url":
        return load_url_file(path)
    # fallback to text loader
    return load_text(path)
