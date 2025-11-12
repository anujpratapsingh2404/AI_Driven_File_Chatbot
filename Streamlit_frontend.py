import streamlit as st
import requests
from io import BytesIO
from urllib.parse import urlparse  # ✅ For clean URL naming

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Chat from API-backed files", layout="wide")

left, right = st.columns([1, 3])

with left:
    st.header("Files")

    file_type = st.selectbox("Select file type", ["PDF", "DOCX", "TXT", "URL", "CSV"])
    uploaded = st.file_uploader("Upload file", type=None, key="uploader")
    url_input = None

    if file_type == "URL":
        url_input = st.text_input("Enter URL", key="url_input")

    if st.button("Upload"):
        if file_type == "URL":
            if not url_input:
                st.warning("Enter a URL first")
            else:
                if not url_input.startswith(("http://", "https://")):
                    url_input = "https://" + url_input

                parsed = urlparse(url_input)
                safe_name = parsed.netloc or "remote"
                if not safe_name.endswith(".url"):
                    safe_name += ".url"

                b = url_input.encode("utf-8")
                files = {"file": (safe_name, BytesIO(b), "text/plain")}
                data = {"file_type": "url"}

                resp = requests.post(f"{API_BASE}/upload", files=files, data=data)
                if resp.status_code == 200:
                    st.success(f"✅ URL '{safe_name}' uploaded successfully.")
                else:
                    st.error(resp.text)

        else:
            if not uploaded:
                st.warning("Upload a file")
            else:
                files = {
                    "file": (uploaded.name, uploaded.getbuffer(), uploaded.type or "application/octet-stream")
                }
                data = {"file_type": file_type.lower()}
                resp = requests.post(f"{API_BASE}/upload", files=files, data=data)
                if resp.status_code == 200:
                    st.success("✅ File uploaded successfully.")
                else:
                    st.error(resp.text)

    st.markdown("---")
    st.subheader("Saved collections")

    try:
        resp = requests.get(f"{API_BASE}/collections")
        if resp.status_code == 200:
            cols = resp.json().get("collections", [])
        else:
            cols = []
    except Exception:
        cols = []

    selection = st.selectbox("Choose", ["(none)"] + cols, key="saved_select")

    if st.button("Activate selected"):
        if selection == "(none)":
            st.warning("Choose a collection")
        else:
            resp = requests.post(f"{API_BASE}/activate", data={"saved_name": selection})
            if resp.status_code == 200:
                st.success("✅ File activated successfully.")
            else:
                st.error(resp.text)

    if st.button("Delete selected"):
        if selection == "(none)":
            st.warning("Choose a collection")
        else:
            resp = requests.delete(f"{API_BASE}/collections/{selection}")
            if resp.status_code == 200:
                st.success("✅ File deleted successfully.")
            else:
                st.error(resp.text)

    if st.button("Clear chat"):
        if selection == "(none)":
            st.warning("Choose a collection")
        else:
            resp = requests.post(f"{API_BASE}/clear_chat", data={"saved_name": selection})
            if resp.status_code == 200:
                st.success("✅ Chat cleared.")
            else:
                st.error(resp.text)

with right:
    st.title("Chat")

    if "active" not in st.session_state:
        st.session_state.active = None

    if selection != "(none)" and selection != st.session_state.active:
        st.session_state.active = selection

    if not st.session_state.active:
        st.info("Select or upload a collection.")
        st.stop()

    st.markdown(f"**Active:** `{st.session_state.active}`")
    st.markdown("---")

    q = st.text_input("Ask a question:", key="question_input")

    if st.button("Send"):
        if not q.strip():
            st.warning("Type a question first.")
        else:
            data = {"saved_name": st.session_state.active, "question": q}

            with st.spinner("🤔 Thinking... please wait while I process your question..."):
                try:
                    resp = requests.post(f"{API_BASE}/ask", data=data)
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    st.stop()

            if resp.status_code == 200:
                out = resp.json()
                if out.get("mode") == "csv":
                    st.success("✅ SQL query executed successfully.")
                    st.write("**SQL Query:**")
                    st.code(out.get("sql") or "N/A", language="sql")

                    results = out.get("result", [])
                    if results:
                        st.dataframe(results)

                    st.markdown(f"**🤖 Assistant:** {out.get('assistant')}")
                elif out.get("mode") == "rag":
                    st.markdown(f"**🤖 Assistant:** {out.get('answer') or out.get('assistant')}")
                else:
                    st.write(out)
            else:
                st.error(f"❌ {resp.text}")

    st.markdown("---")
    st.subheader("Conversation")

    try:
        c = requests.get(f"{API_BASE}/chat/{st.session_state.active}")
        if c.status_code == 200:
            chat = c.json().get("chat", [])
            for msg in chat:
                role = msg.get("role")
                text = msg.get("text")
                if role == "user":
                    st.markdown(f"**🧑 You:** {text}")
                else:
                    tstr = (text or "").strip()
                    if tstr.upper().startswith("SELECT"):
                        st.code(tstr, language="sql")
                    else:
                        st.markdown(f"**🤖 Bot:** {text}")
        else:
            st.error("Failed to load chat history.")
    except Exception as e:
        st.error(f"Error loading chat: {e}")
