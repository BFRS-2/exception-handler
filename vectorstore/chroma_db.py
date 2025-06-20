import chromadb
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import json

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