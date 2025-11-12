from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.utiils import (
    save_file_bytes,
    list_collections,
    collection_path,
    vectorstore_dir_for,
    load_chat_history,
    save_chat_history,
    append_to_chat,
    delete_collection,
)
from backend.RAG_end import create_vectorstore, load_vectorstore_if_exists, get_conversational_chain, embeddings
from backend.SQL_end import load_csv_to_sql, get_table_info, generate_sql, run_query
from backend.loaders import load_docs_by_ext

app = FastAPI(title="File-RAG / CSV-SQL API")

origins = [
    "http://localhost",
    "http://localhost:8501",
    "http://127.0.0.1",
    "http://127.0.0.1:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "API is running"}


@app.post("/upload")
def upload_file(file: UploadFile = File(...), file_type: str = Form(...)):
    try:
        content = file.file.read()
        saved_name = save_file_bytes(file.filename, content)
        display_name = file.filename

        ext = file_type.lower()
        response = {"saved_name": saved_name, "filename": file.filename, "ext": ext}

        full_path = collection_path(saved_name)

        if ext == "csv":
            db_dir = os.path.join("data", "csv_dbs")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, f"{saved_name}.db")
            db_path, table_name = load_csv_to_sql(full_path, db_path=db_path)
            schema = get_table_info(db_path)
            response.update({"mode": "csv", "db_path": db_path, "table_name": table_name, "schema": schema})
            return JSONResponse(status_code=200, content=response)
        else:
            docs = load_docs_by_ext(ext, full_path)
            vect_dir = vectorstore_dir_for(saved_name)
            create_vectorstore(docs, persist_directory=vect_dir)
            response.update({"mode": "rag", "vect_dir": vect_dir})
            return JSONResponse(status_code=200, content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/collections")
def api_list_collections():
    try:
        cols = list_collections()
        return {"collections": cols}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/activate")
def activate_collection(saved_name: str = Form(...)):
    try:
        ext = saved_name.split(".")[-1].lower()
        full_path = collection_path(saved_name)
        if ext == "csv":
            db_dir = os.path.join("data", "csv_dbs")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, f"{saved_name}.db")
            if not os.path.exists(db_path):
                db_path, table_name = load_csv_to_sql(full_path, db_path=db_path)
            schema = get_table_info(db_path)
            return {"mode": "csv", "db_path": db_path, "schema": schema, "table_name": os.path.splitext(os.path.basename(full_path))[0]}
        else:
            ext = ext
            vect_dir = vectorstore_dir_for(saved_name)
            if not os.path.exists(vect_dir):
                docs = load_docs_by_ext(ext, full_path)
                create_vectorstore(docs, persist_directory=vect_dir)
            return {"mode": "rag", "vect_dir": vect_dir}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/collections/{saved_name}")
def api_delete_collection(saved_name: str):
    try:
        ok = delete_collection(saved_name)
        return {"deleted": ok}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/clear_chat")
def api_clear_chat(saved_name: str = Form(...)):
    try:
        save_chat_history(saved_name, [])
        return {"cleared": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/ask")
def ask(saved_name: str = Form(...), question: str = Form(...)):
    try:
        ext = saved_name.split(".")[-1].lower()
        full_path = collection_path(saved_name)

        if ext == "csv":
            db_dir = os.path.join("data", "csv_dbs")
            db_path = os.path.join(db_dir, f"{saved_name}.db")
            if not os.path.exists(db_path):
                db_path, _ = load_csv_to_sql(full_path, db_path=db_path)
            schema = get_table_info(db_path)
            sql_query = generate_sql(question, schema)
            res = run_query(sql_query, db_path)
            append_to_chat(saved_name, "user", question)
            if isinstance(res, str):
                assistant = f"❌ SQL Error: {res}"
                append_to_chat(saved_name, "assistant", assistant)
                return {"mode": "csv", "sql": sql_query, "result": [], "assistant": assistant}
            else:
                if len(res.columns) == 1 and len(res) == 1:
                    val = res.iloc[0, 0]
                    assistant = f"The answer is **{val}**."
                else:
                    assistant = f"Returned {len(res)} rows. (Showing top 10)"
                append_to_chat(saved_name, "assistant", assistant)
                return {"mode": "csv", "sql": sql_query, "result": res.head(10).to_dict(orient="records"), "assistant": assistant}

        else:
            vect_dir = vectorstore_dir_for(saved_name)
            vect = load_vectorstore_if_exists(vect_dir)
            if vect is None:
                ext = saved_name.split(".")[-1].lower()
                docs = load_docs_by_ext(ext, full_path)
                vect = create_vectorstore(docs, persist_directory=vect_dir)
            chain = get_conversational_chain(vect)
            resp = chain({"question": question})
            answer = resp.get("answer") if isinstance(resp, dict) else str(resp)
            append_to_chat(saved_name, "user", question)
            append_to_chat(saved_name, "assistant", answer)
            return {"mode": "rag", "answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/chat/{saved_name}")
def get_chat(saved_name: str):
    try:
        lst = load_chat_history(saved_name)
        return {"chat": [{"role": r, "text": t} for (r, t) in lst]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
