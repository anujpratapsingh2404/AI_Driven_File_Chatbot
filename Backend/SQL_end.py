import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash", api_key=google_api_key)


def load_csv_to_sql(file_path: str, db_path: str = "data/data.db", table_name: str = None):
    """
    Load CSV into SQLite database. Overwrites the table if it exists.
    Returns (db_path, table_name).
    """
    df = pd.read_csv(file_path)
    if table_name is None:
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        table_name = table_name.replace("-", "_").replace(" ", "_")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    conn.close()
    return db_path, table_name


def get_table_info(db_path: str = "data/data.db") -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema_text = ""
    for table_name in tables:
        name = table_name[0]
        cursor.execute(f'PRAGMA table_info("{name}")')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        schema_text += f"\nTable: {name}\nColumns: {', '.join(column_names)}\n"
    conn.close()
    return schema_text


def generate_sql(question: str, schema: str) -> str:
    prompt = f"""
You are an expert SQL assistant. Based on the database schema below,
write one correct SQL query that answers the user's question.
Do NOT add explanations — return only the SQL statement.

Schema:
{schema}

Question: {question}
"""
    response = llm.invoke(prompt)
    sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    return sql


def run_query(query: str, db_path: str = "data/data.db"):
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        conn.close()
        return str(e)
