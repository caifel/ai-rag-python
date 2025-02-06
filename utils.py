import json
import re

llm_base_prompt = """
Analiza el siguiente query de búsqueda inmobiliaria y extrae estos parámetros: 
    - price (number)
    - zone (array of strings) # achumani, centro, sopocachi. Autocorregir si es necesario.
    - city (array of strings) # la paz, cochabamba, santa cruz, oruro, potosi, tarija, pando, beni, chuquisaca. Autocorregir si es necesario.
    - people_capacity (number)
    - garden (booleano)
    - garage (booleano)
    - property_type (string) # casa, departamento, oficina, terreno, local
    - operation_type (string) # venta, alquiler, anticretico

Reglas estrictas:
    - Si un parámetro no se menciona, usa `null`.
    - Respuesta **SOLO el JSON**, sin ```json, ```, ni texto adicional.
    - Strings en minúsculas.
    - Si incluyes delimitadores, la respuesta será inválida

Ejemplo de respuesta para "Casa en Sevilla centro por 250k con jardín. Para persona sola.":

{
    "price": 250000,
    "zone": ["centro"],
    "city": ["sevilla"],
    "people_capacity": 1,
    "garden": true,
    "garage": null,
    "property_type": "casa",
    "operation_type": null
}
"""

def get_llm_prompt(query: str) -> str:
    llm_prompt =  f"{llm_base_prompt}\n\nquery = {query}"
    
    return llm_prompt

def parse_llm_response(response: str) -> dict:
    # Eliminar delimitadores y espacios con regex
    cleaned = re.sub(r'^```json|```$', '', response, flags=re.MULTILINE)
    
    # Limpiar saltos de línea y espacios extra
    cleaned = cleaned.strip().replace('\n', '')
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Intentar extraer JSON entre llaves como último recurso
        json_match = re.search(r'{.*}', cleaned, flags=re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise

def get_db_query(filters: dict) -> str:
    conditions = []
    params = []

    # 1. Filtro de precio
    if 'price' in filters and filters['price'] is not None:
        conditions.append("price <= ?")
        params.append(filters['price'])

    # 2. Filtro de ciudades (array vacío = todas)
    if 'city' in filters and len(filters['city']) > 0:
        placeholders = ','.join(['?'] * len(filters['city']))
        conditions.append(f"LOWER(city) IN ({placeholders})")
        params.extend([city.lower() for city in filters['city']])

    # 3. Filtro de zonas (array vacío = todas)
    if 'zone' in filters and len(filters['zone']) > 0:
        placeholders = ','.join(['?'] * len(filters['zone']))
        conditions.append(f"LOWER(zone) IN ({placeholders})")
        params.extend([zone.lower() for zone in filters['zone']])

    # 4. Capacidad de personas
    if 'people_capacity' in filters and filters['people_capacity'] is not None:
        conditions.append("people_capacity >= ?")
        params.append(filters['people_capacity'])

    # 5. Características booleanas
    bool_mapping = {True: 1, False: 0, None: None}
    
    if 'garden' in filters and filters['garden'] is not None:
        conditions.append("garden = ?")
        params.append(bool_mapping[filters['garden']])

    if 'garage' in filters and filters['garage'] is not None:
        conditions.append("garage = ?")
        params.append(bool_mapping[filters['garage']])

    if 'property_type' in filters and filters['property_type'] is not None:
        conditions.append("LOWER(property_type) = ?")
        params.append(filters['property_type'].lower())

    # 7. Tipo de operación
    if 'operation_type' in filters and filters['operation_type'] is not None:
        conditions.append("LOWER(operation_type) = ?")
        params.append(filters['operation_type'].lower())

    # Construir consulta final
    query = "SELECT * FROM records"
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    return query, params
        