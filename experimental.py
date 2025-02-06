from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv
from llama_index.core.settings import Settings
from llama_index.llms.gemini import Gemini
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.vector_stores import MetadataFilters, RangeFilter

import google.generativeai as genai
from db import Database
from utils import parse_llm_response, get_db_query, get_llm_prompt, get_results_in_json

import sqlite3
import os

# Load environment variables from .env file
load_dotenv()
# Initialize the Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app)  

genai.configure(api_key="GOOGLE_API_KEY")
model = genai.GenerativeModel("gemini-1.5-pro")
# model = genai.GenerativeModel("text-embedding-004")


# Basic Swagger configuration
app.config['SWAGGER'] = {
    'title': 'My Flask API',
    'version': '1.0',
    'description': 'A simple API documentation using flasgger',
}

# Initialize Swagger
swagger = Swagger(app)

# Set Settings
Settings.llm = Gemini(model="models/gemini-1.5-flash")
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def retrieve_query_engine():
    storage_context = StorageContext.from_defaults(persist_dir="index")
    loaded_index = load_index_from_storage(storage_context)
    # query_engine = loaded_index.as_chat_engine(
    #     chat_mode="context",
    # )
    query_engine = loaded_index.as_query_engine()
    return query_engine

# Define a route for the root URL ("/")
@app.route('/')
def home():
    user_prompt = "Busco casa en venta en Achumai en la paz por 280k con jardin. Para pareja."
    llm_prompt = get_llm_prompt(user_prompt)
    llm_response = model.generate_content(llm_prompt)
    json_filters = parse_llm_response(llm_response.text)
    db_query, db_params = get_db_query(json_filters)
    
    with Database() as db:
        results = db.execute(db_query, db_params)
    
    return get_results_in_json(results, json_filters)

# Create index
@app.route('/create_index', methods=['GET'])
def create_index():
    # ## read data.db using sqlite3
    # conn = sqlite3.connect('data.db')
    # conn.row_factory = sqlite3.Row
    # c = conn.cursor()
    # c.execute("SELECT * FROM records")
    # records = c.fetchall()
    # conn.close()
    # ## create documents
    # documents = []
    # for record in records:
    #     print(record)
    #     # ✅ Solo contexto semántico
    #     embedding_text = (
    #         f"{record['type']} en {record['zone']}, {record['city']}. "
    #         # f"{record['description']}"  
    #     )
    #     metadata = {
    #         "type": record['type'],
    #         "zone": record['zone'],
    #         "city": record['city'],
    #     }

    #     doc = Document(text=embedding_text, metadata=metadata)
    #     documents.append(doc)

    #     print(record)
    # ## create index
    # index = VectorStoreIndex.from_documents(documents, show_progress=True)
    # index.storage_context.persist(persist_dir="index")
    
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    index.storage_context.persist(persist_dir="index")
    
    return "Index created"

# Define a route for a GET request
@app.route('/data', methods=['GET'])
def get_data():
    data = {
        "message": "This is a GET request response",
        "status": "success"
    }
    return jsonify(data)

# Define a route for a POST request
@app.route('/submit', methods=['POST'])
def submit_data():
    # Get JSON data from the request
    request_data = request.get_json()
    query = request_data.get('query')

    response = query_engine.query(query)

    response = {
        "message": response,
        "status": "success"
    }
    return jsonify(response)

# Run the Flask app
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)


# limitar la cantidad de resultados obtenidos del embedding