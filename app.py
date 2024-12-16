from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
from SPARQLWrapper import SPARQLWrapper, JSON
import json

DBPEDIA_ENDPOINT = "http://dbpedia.org/sparql"
app = Flask(__name__)


# Cargar la ontología con OWLready2 
onto_path.append("ontologia/biblioteca") 
onto = get_ontology("ontologia/biblioteca.owl").load()
# Convertir la ontología a un grafo RDFlib 
graph = default_world.as_rdflib_graph()

@app.route('/')
def start():
    return render_template('start.html')


@app.route('/index', methods=['GET'])
def search_page():
    return render_template('index.html')
    


@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    sparql_query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ontologies: <http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaDigital#>

    SELECT ?identifier
    WHERE {{
      ?individual ?property ?value .
      OPTIONAL {{ ?individual rdfs:label ?label }}
      BIND(COALESCE(?label, STR(?individual)) AS ?identifier)
      FILTER(CONTAINS(LCASE(STR(?value)), LCASE("{query}")))
    }}
    """
    results_local = graph.query(sparql_query)

    # Extraer identificador de las URLs
    resultado_simplificado = []
    for row in results_local:
        identifier = str(row.identifier)
        if identifier.startswith("http://www.semanticweb.org/miche/ontologies/2024/8/"):
            # Extraer la parte final del IRI
            suffix = identifier.split("/")[-1]
            # Concatenar con "OntologiaBiblioteca"
            resultado_simplificado.append(f"{suffix}")
        else:
            # Procesar casos que no sean URL (e.g., estLector001)
            literal_value = identifier.split("'")[0]  # Ajusta si cambia el patrón
            resultado_simplificado.append(f"{literal_value}")
    
    # Consulta a DBpedia
    sparql_query_dbpedia = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?resource ?label
    WHERE {{
      ?resource rdfs:label ?label .
      FILTER(LANG(?label) = "es")  # Etiquetas en español
      FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{query}")))
    }}
    LIMIT 10
    """
    sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
    sparql.setQuery(sparql_query_dbpedia)
    sparql.setReturnFormat(JSON)
    results_dbpedia = sparql.query().convert()

    # Consulta al archivo JSON (DBpedia)
    json_file = "./ontologia/dbpedia_books.json"  # Archivo JSON local

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            books = data["results"]["bindings"]
    except (FileNotFoundError, json.JSONDecodeError):
        books = []

    # Realizar búsqueda en JSON local
    results_dbpedia_processed = set()
    query_lower = query.lower()
    for book in books:
        title = book.get("name", {}).get("value", "").lower()
        author = book.get("author", {}).get("value", "").lower()
        abstract = book.get("abstract", {}).get("value", "").lower()

        if query_lower in title or query_lower in author or query_lower in abstract:
            results_dbpedia_processed.add(title)

    results_dbpedia = sorted(results_dbpedia_processed)

    # Combinar resultados locales y JSON
    combined_results = {
        "local": resultado_simplificado,
        "dbpedia": results_dbpedia
    }

    return render_template('results.html', results=combined_results,query=query)

@app.route('/details/<instance>') 
def details(instance): 
    sparql_query = f""" 
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    PREFIX owl: <http://www.w3.org/2002/07/owl#> 
    
    SELECT ?predicate ?object 
    WHERE {{ 
        ?subject ?predicate ?object . 
        OPTIONAL {{ ?subject rdfs:label ?label }} 
        FILTER (str(?subject) = "http://www.semanticweb.org/miche/ontologies/2024/8/{instance}" || str(?label)="{instance}") 
    }} 
    """ 
    results = graph.query(sparql_query) 
    simplified_results = [(str(row.predicate).split("/")[-1], row.object) for row in results]
    return render_template('details.html', instance=instance, results=simplified_results)

if __name__ == '__main__':
    app.run(debug=True)
