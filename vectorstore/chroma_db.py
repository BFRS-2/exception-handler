import chromadb
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import json
import pandas as pd

def get_chroma_db(collection_name="shipment_exceptions"):
    persist_directory = os.path.join(os.path.dirname(__file__), "chroma_store")
    embeddings = OpenAIEmbeddings()
    db = Chroma(collection_name=collection_name, embedding_function=embeddings, persist_directory=persist_directory)
    return db

# New function to load conversations into ChromaDB
def load_conversations_to_chroma(json_path, collection_name="shipment_exceptions"):
    db = get_chroma_db(collection_name)
    with open(json_path, "r") as f:
        conversations = json.load(f)
    docs = []
    metadatas = []
    for conv in conversations:
        shipment_id = conv["shipment_id"]
        # Flatten conversation history into a single string
        conversation_text = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in conv["conversation"]
        ])
        docs.append(conversation_text)
        metadatas.append({"shipment_id": shipment_id})
    db.add_texts(docs, metadatas=metadatas)
    return db

# Retrieve top k similar conversations with score > min_score
def get_top_similar_conversations(query, k=3, min_score=0.75, collection_name="shipment_exceptions"):
    db = get_chroma_db(collection_name)
    # similarity_search_with_score returns (Document, score)
    results = db.similarity_search_with_score(query, k=k*2)  # get more, filter by score
    filtered = [doc for doc, score in results if score >= min_score]
    return filtered[:k]

# Load corrections from corrections.csv into ChromaDB
def load_corrections_to_chroma(csv_path, collection_name="corrections"):
    db = get_chroma_db(collection_name)
    if not os.path.exists(csv_path):
        return db
    df = pd.read_csv(csv_path)
    docs = []
    metadatas = []
    for _, row in df.iterrows():
        doc = (
            f"Issue: {row['issue_description']}\n"
            f"Shipment ID: {row['shipment_id']}\n"
            f"Prompt: {row['prompt']}\n"
            f"LLM Response: {row['response']}\n"
            f"User Feedback: {row['feedback']}\n"
            f"Admin Correction: {row['corrected']}"
        )
        docs.append(doc)
        metadatas.append({"shipment_id": row['shipment_id']})
    db.add_texts(docs, metadatas=metadatas)
    return db

# Retrieve top k similar corrections with score > min_score
def get_top_similar_corrections(query, k=2, min_score=0.75, collection_name="corrections"):
    db = get_chroma_db(collection_name)
    results = db.similarity_search_with_score(query, k=k*2)
    filtered = [doc for doc, score in results if score >= min_score]
    return filtered[:k] 