🧠 Chat-from-Files AI Assistant

A full-stack Streamlit + FastAPI application that lets you upload documents (PDF, DOCX, TXT, CSV, or even URLs) and chat with an AI assistant powered by Google Gemini + LangChain RAG.
Supports contextual Q&A, SQL querying, and persistent chat history — all API-backed.

🚀 Features

✅ Upload and process multiple file types:

📄 PDF, 📝 DOCX, 🗒️ TXT

🌐 URL links

📊 CSV (AI generates SQL queries automatically!)

✅ Powered by LangChain RAG with vector storage (ChromaDB)
✅ Chat interface built in Streamlit
✅ FastAPI backend for model and data processing
✅ Persistent file, vectorstore, and chat management
✅ Modular code with RAG_end.py, utils.py, and API endpoints
✅ Secure — .env file excluded from GitHub via .gitignore

🏗️ Project Structure
chat-file-bot/
│
├── backend/
│   ├── main.py                # FastAPI backend
│   ├── RAG_end.py             # RAG and vectorstore logic
│   ├── utils.py               # File and chat utilities
│   ├── Prompt_template.py     # Custom LangChain prompt
│   ├── requirements.txt       # Backend dependencies
│
├── frontend/
│   ├── streamlit_app.py       # Streamlit frontend (UI)
│
├── data/
│   ├── uploaded_files/        # Stores uploaded files
│   ├── vectorstores/          # Stores embeddings (ChromaDB)
│   ├── chat_history/          # Stores conversation logs
│
├── .env                       # Environment variables (NOT uploaded)
├── .gitignore
├── README.md
└── requirements.txt
