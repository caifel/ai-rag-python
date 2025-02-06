from flask import Flask, request
from flask_cors import CORS
from flasgger import Swagger
from db import Database
from dotenv import load_dotenv
# from openai import OpenAI

import os
import json
import google.generativeai as genai

from utils import parse_llm_response, get_db_query, get_llm_prompt, llm_base_prompt

# Load environment variables from .env file
load_dotenv()
# Initialize the Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app)  

# client = OpenAI(
#     api_key=os.getenv(os.environ['QWEN_API_KEY']),
#     base_url=os.getenv('QWEN_BASE_URL'),
# )

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel(os.environ['GEMINI_MODEL'])

# Basic Swagger configuration
app.config['SWAGGER'] = {
    'title': 'My Flask API',
    'version': '1.0',
    'description': 'A simple API documentation using flasgger',
}

# Initialize Swagger
swagger = Swagger(app)

def do_search(query):
    try:
        llm_response = model.generate_content(get_llm_prompt(query))
        # print(f"API KEy: {os.getenv('QWEN_API_KEY')}")
        
        # response = client.chat.completions.create(
        #     model=os.getenv('QWEN_MODEL'),
        #     messages=[
        #         {'role': 'system', 'content': llm_base_prompt},
        #         {'role': 'user', 'content': query}
        #     ],
        # )
        # llm_response = response.choices[0].message.content
        
        print(f"Response: {llm_response}")
    except Exception as e:
        print(f"Error generating content: {e}")
        return {"error": "Failed on generation"}

    json_filters = parse_llm_response(llm_response.text)
    db_query, db_params = get_db_query(json_filters)
    
    with Database() as db:
        results = db.execute(db_query, db_params)
        
    print(f"Filters: {json_filters}")
    
    return results, json_filters

@app.route('/')
def home():
    query = "Busco casa en venta en Achumai en cbba por 280k con jardin. Para pareja."
    results, filters = do_search(query)
    
    return json.dumps(
        {
            "count": len(results),
            "results": [dict(row) for row in results],
            "filters": filters # For debugging
        },
        indent=4,
        ensure_ascii=True 
    )

@app.route('/data', methods=['GET'])
def get_data():
   return "Hello, World!"

@app.route('/search', methods=['POST'])
def search_data():
    request_data = request.get_json()
    query = request_data.get('query')
    results, filters = do_search(query)
    
    return json.dumps(
        {
            "count": len(results),
            "results": [dict(row) for row in results],
            "filters": filters # For debugging
        },
        indent=4,
        ensure_ascii=True # To keep accents and special characters
    )

# Run the Flask app
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)

# Agregar negaciones y soportar mas parametros de busqueda
