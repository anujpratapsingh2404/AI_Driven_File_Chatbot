import os
from typing import Optional
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model

from backend.Prompt_template import prompt

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

llm = init_chat_model("google_genai:gemini-2.0-flash", api_key=google_api_key)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def create_vectorstore(docs, persist_directory: str, collection_name: str = "default_collection"):
    """
    Create or update a Chroma vectorstore without duplication.
    Compatible with LangChain's Chroma wrapper.
    """
    os.makedirs(persist_directory, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    texts = splitter.split_documents(docs)

    vectordb = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    collection = vectordb._collection

    ids = [f"{collection_name}_{i}" for i in range(1, len(texts) + 1)]

    existing_data = collection.get(ids=ids)
    existing_ids = set(existing_data.get("ids", []))

    update_ids = [id for id in ids if id in existing_ids]
    add_ids = [id for id in ids if id not in existing_ids]

    if update_ids:
        collection.update(
            ids=update_ids,
            documents=[texts[ids.index(id)].page_content for id in update_ids],
            embeddings=[embeddings.embed_query(texts[ids.index(id)].page_content) for id in update_ids]
        )
        print(f"✅ Updated {len(update_ids)} existing documents in '{collection_name}'")

    if add_ids:
        collection.add(
            ids=add_ids,
            documents=[texts[ids.index(id)].page_content for id in add_ids],
            embeddings=[embeddings.embed_query(texts[ids.index(id)].page_content) for id in add_ids]
        )
        print(f"🆕 Added {len(add_ids)} new documents to '{collection_name}'")

    vectordb.persist()
    print(f"💾 Vectorstore saved successfully in {persist_directory}")

    return vectordb


def load_vectorstore_if_exists(persist_directory: str, collection_name: str = "default_collection") -> Optional[Chroma]:
    if os.path.exists(persist_directory):
        return Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
    return None


def get_conversational_chain(vectordb):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
    )
    return qa_chain
