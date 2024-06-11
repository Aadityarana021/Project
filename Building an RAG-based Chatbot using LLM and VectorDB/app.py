import streamlit as st
from PyPDF2 import PdfReader
import os
import re
import google.generativeai as genai
import chromadb
from chromadb.config import Settings
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("Gemini API Key not provided. Please provide a valid GEMINI_API_KEY.")

genai.configure(api_key=gemini_api_key)

# Configure ChromaDB settings
chroma_settings = Settings(persist_directory="chroma_db")

# Function to load PDF and extract text
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

# Function to split text into chunks of appropriate size
def split_text(text, max_chunk_size=500):
    words = text.split()
    chunks = []
    chunk = []
    chunk_size = 0

    for word in words:
        if chunk_size + len(word) + 1 > max_chunk_size:
            chunks.append(" ".join(chunk))
            chunk = []
            chunk_size = 0
        chunk.append(word)
        chunk_size += len(word) + 1

    if chunk:
        chunks.append(" ".join(chunk))

    return chunks

# Define a custom embedding function using Gemini API
class GeminiEmbeddingFunction:
    def __call__(self, input: List[str]):
        embeddings = []
        for text in input:
            embedding = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document",
                title="Custom query"
            )["embedding"]
            embeddings.append(embedding)
        return embeddings

# Function to create a new ChromaDB collection
def create_chroma_db(documents: List[str], db_name: str):
    chroma_client = chromadb.PersistentClient(path=chroma_settings.persist_directory)
    try:
        chroma_client.delete_collection(name=db_name)
    except Exception as e:
        pass  # Ignore if collection does not exist
    db = chroma_client.create_collection(name=db_name, embedding_function=GeminiEmbeddingFunction())
    for i, doc in enumerate(documents):
        db.add(documents=[doc], ids=[str(i)])
    return db

# Function to load an existing Chroma collection
def load_chroma_collection(db_name: str):
    chroma_client = chromadb.PersistentClient(path=chroma_settings.persist_directory)
    return chroma_client.get_collection(name=db_name, embedding_function=GeminiEmbeddingFunction())

# Function to retrieve the most relevant passages based on the query
def get_relevant_passage(query: str, db, n_results: int):
    results = db.query(query_texts=[query], n_results=n_results)
    return [doc[0] for doc in results['documents']]

# Function to construct a prompt for the generation model
def make_rag_prompt(query: str, relevant_passage: str):
    escaped_passage = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
    prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passage included below.
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.
However, you are talking to a non-technical audience, so be sure to break down complicated concepts and
strike a friendly and conversational tone.
QUESTION: '{query}'
PASSAGE: '{escaped_passage}'

ANSWER:
"""
    return prompt

# Function to generate an answer using the Gemini Pro API
def generate_answer(prompt: str):
    model = genai.GenerativeModel('gemini-pro')
    result = model.generate_content(prompt)
    return result.text

# Streamlit application
def main():
    st.set_page_config("Chat PDF")
    st.header("Chat with PDF using Gemini💁")

    db_name = "rag_experiment"

    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        db = load_chroma_collection(db_name)
        relevant_text = get_relevant_passage(user_question, db, n_results=1)
        if relevant_text:
            final_prompt = make_rag_prompt(user_question, "".join(relevant_text))
            answer = generate_answer(final_prompt)
            st.write("Reply: ", answer)
        else:
            st.write("No relevant information found for the given query.")

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            if pdf_docs:
                with st.spinner("Processing..."):
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = split_text(raw_text)
                    create_chroma_db(text_chunks, db_name)
                    st.success("Done")
            else:
                st.error("Please upload at least one PDF file.")

if __name__ == "__main__":
    main()
