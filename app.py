import os
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage, HumanMessage
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

VECTOR_STORE_PATH = "faiss_index"

def scrape_and_store(url):
    if os.path.exists(VECTOR_STORE_PATH):
        logger.info("Loading existing FAISS index...")
        return FAISS.load_local(VECTOR_STORE_PATH, OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=OPENAI_API_KEY),allow_dangerous_deserialization=True)

    logger.info("Scraping and generating embeddings...")
    loader = WebBaseLoader(url)
    try:
        docs = loader.load()
        if not docs:
            logger.error("No documents found on the page!")
            return None
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        return None

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(docs, embeddings)
    vector_store.save_local(VECTOR_STORE_PATH)
    
    return vector_store

def get_retriever(vector_store):
    return vector_store.as_retriever() if vector_store else None

def generate_response(query, retriever):
    if not retriever:
        return "No retriever available. Check if scraping was successful."

    llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    system_prompt = "You are an AI assistant that provides concise and helpful responses about AI courses.Keep answers short but complete."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]

    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)

    try:
        return qa_chain.run(query)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error generating response: {e}"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    response = generate_response(query, retriever)
    return jsonify({"response": response})

if __name__ == "__main__":
    url = "https://brainlox.com/courses/category/technical"
    vector_store = scrape_and_store(url)
    retriever = get_retriever(vector_store)
    
    if not vector_store:
        logger.error("Failed to create vector store. Exiting...")
        exit()

    app.run(host='0.0.0.0', port=5000)
