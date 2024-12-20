import requests
import json

# Endpoint SPARQL de DBpedia
SPARQL_ENDPOINT = "http://dbpedia.org/sparql"

# Consulta SPARQL
query = """
SELECT DISTINCT ?book ?number ?abstract ?name ?author ?title ?publisher ?publicationDate ?edition ?isbn ?numberOfPages ?genre ?language ?url
WHERE
{
  ?book dbo:wikiPageWikiLink ?topic .
  VALUES ?topic { 
    dbr:Software 
    dbr:Networks_Concepts
    dbr:Database 
    dbr:Programming 
    dbr:Algorithm 
    dbr:Artificial_intelligence 
    dbr:Data_mining 
    dbr:Operating_system 
  }
  
  # Información básica
  ?book dbo:wikiPageID ?number .
  ?book rdfs:comment ?abstract .
  ?book dbp:name ?name .
  OPTIONAL { ?book dbp:author ?author . }
  
  # Información adicional
  OPTIONAL { ?book dbp:title ?title . }
  OPTIONAL { ?book dbo:publisher ?publisher . }
  OPTIONAL { ?book dbo:publicationDate ?publicationDate . }
  OPTIONAL { ?book dbp:edition ?edition . }
  OPTIONAL { ?book dbo:isbn ?isbn . }
  OPTIONAL { ?book dbo:numberOfPages ?numberOfPages . }
  OPTIONAL { ?book dbo:literaryGenre ?genre . }
  OPTIONAL { ?book dbo:language ?language . }
  
  # Metadatos
  OPTIONAL { ?book foaf:isPrimaryTopicOf ?url . }

  # Filtro por idioma español
  FILTER ( LANG(?abstract) = 'es' )
}
LIMIT 100
"""

# Encabezados de la solicitud
headers = {
    "Accept": "application/sparql-results+json"  # Formato aceptado por el servidor
}

# Parámetros para la solicitud GET
params = {
    "query": query,
    "format": "json"  # Formato deseado para los datos
}

# Enviar la solicitud al endpoint SPARQL
response = requests.get(SPARQL_ENDPOINT, headers=headers, params=params)

# Verificar que la solicitud fue exitosa
if response.status_code == 200:
    # Convertir la respuesta a JSON
    data = response.json()

    # Guardar los resultados en un archivo JSON
    with open("./csv/dbpedia_books.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print("Consulta exitosa. Los resultados se han guardado en 'dbpedia_books.json'.")
else:
    print(f"Error en la consulta: {response.status_code}")
    print(response.text)
