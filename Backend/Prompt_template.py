from langchain.prompts import PromptTemplate

CUSTOM_PROMPT = """
You are an expert assistant. Answer the user's question using only the provided context.
If the answer is not in the context, respond with "I don't know".

Context:
{context}

Question:
{question}

Answer:
"""

prompt = PromptTemplate(
    template=CUSTOM_PROMPT,
    input_variables=["context", "question"]
)
