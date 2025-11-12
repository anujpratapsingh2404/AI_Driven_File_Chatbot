import os
import shutil
import time

UPLOAD_DIR = os.path.join("data", "uploaded_files")
VECTORS_ROOT = os.path.join("data", "vectorstores")
CHAT_ROOT = os.path.join("data", "chat_history")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTORS_ROOT, exist_ok=True)
os.makedirs(CHAT_ROOT, exist_ok=True)


def clean_filename(filename: str) -> str:
    """Clean filename: lowercase, replace spaces & invalid characters."""
    base, ext = os.path.splitext(filename)
    base = base.strip().replace(" ", "_")
    return f"{base}{ext}"


def save_file_bytes(filename: str, content: bytes) -> str:
    """
    Save file contents safely; auto-renames if same name already exists.
    Example: 'report.pdf' -> 'report_1.pdf'
    """
    safe_name = clean_filename(filename)
    path = os.path.join(UPLOAD_DIR, safe_name)

    if os.path.exists(path):
        base, ext = os.path.splitext(safe_name)
        safe_name = f"{base}_{int(time.time())}{ext}"
        path = os.path.join(UPLOAD_DIR, safe_name)

    with open(path, "wb") as f:
        f.write(content)

    return safe_name

def list_collections():
    """Return saved filenames sorted."""
    if not os.path.exists(UPLOAD_DIR):
        return []
    return sorted(os.listdir(UPLOAD_DIR))


def collection_path(saved_name: str) -> str:
    return os.path.join(UPLOAD_DIR, saved_name)


def vectorstore_dir_for(saved_name: str) -> str:
    """Return path for Chroma vectorstore directory."""
    name = os.path.splitext(saved_name)[0]
    return os.path.join(VECTORS_ROOT, name)


def chat_file_for(saved_name: str) -> str:
    safe = saved_name.replace("/", "_")
    return os.path.join(CHAT_ROOT, f"{safe}.md")


def save_chat_history(saved_name: str, chat_list):
    path = chat_file_for(saved_name)
    with open(path, "w", encoding="utf-8") as f:
        for role, text in chat_list:
            f.write(f"**{role.capitalize()}:** {text}\n\n")


def load_chat_history(saved_name: str):
    path = chat_file_for(saved_name)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines:
        if "**User:**" in line:
            out.append(("user", line.replace("**User:**", "").strip()))
        elif "**Assistant:**" in line:
            out.append(("assistant", line.replace("**Assistant:**", "").strip()))
    return out


def append_to_chat(saved_name: str, role: str, text: str):
    lst = load_chat_history(saved_name)
    lst.append((role, text))
    save_chat_history(saved_name, lst)


def delete_collection(saved_name: str) -> bool:
    """Delete uploaded file, its vectorstore, and chat history."""
    try:
        fpath = collection_path(saved_name)
        if os.path.exists(fpath):
            os.remove(fpath)

        vectdir = vectorstore_dir_for(saved_name)
        if os.path.exists(vectdir):
            shutil.rmtree(vectdir)

        chatf = chat_file_for(saved_name)
        if os.path.exists(chatf):
            os.remove(chatf)

        return True
    except Exception:
        return False
