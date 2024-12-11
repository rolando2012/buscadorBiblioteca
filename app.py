from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *

app = Flask(__name__)


# Cargar la ontología con OWLready2 
onto_path.append("ontologia/biblioteca") 
onto = get_ontology("ontologia/biblioteca.owl").load()
# Convertir la ontología a un grafo RDFlib 
graph = default_world.as_rdflib_graph()

@app.route('/')
def index():
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
    results = graph.query(sparql_query)

    # Extraer identificador de las URLs
    resultado_simplificado = []
    for row in results:
        identifier = str(row.identifier)
        if identifier.startswith("http://www.semanticweb.org/miche/ontologies/2024/8/"):
            # Extraer la parte final del IRI
            suffix = identifier.split("/")[-1]
            # Concatenar con "OntologiaBiblioteca"
            resultado_simplificado.append(f"{suffix}")
        else:
            # Procesar casos que no sean URL (e.g., estLector001)
            literal_value = identifier.split("'")[0]  # Ajusta si cambia el patrón
            resultado_simplificado.append(f"OntologiaBiblioteca{literal_value}")

    return render_template('results.html', results=resultado_simplificado,query=query)

@app.route('/details/<instance>') 
def details(instance): 
    sparql_query = f""" 
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    PREFIX owl: <http://www.w3.org/2002/07/owl#> 
    
    SELECT ?predicate ?object 
    WHERE {{ 
        ?subject ?predicate ?object . 
        FILTER (str(?subject) = "http://www.semanticweb.org/miche/ontologies/2024/8/{instance}") 
    }} 
    """ 
    results = graph.query(sparql_query) 
    simplified_results = [(str(row.predicate).split("/")[-1], row.object) for row in results]
    return render_template('details.html', instance=instance, results=simplified_results)

if __name__ == '__main__':
    app.run(debug=True)
