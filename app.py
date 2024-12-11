from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
from SPARQLWrapper import SPARQLWrapper, JSON

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

    # Consulta SPARQL local
    sparql_query_local = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    
    SELECT DISTINCT ?subject 
    WHERE {{
        ?subject rdf:type <http://www.semanticweb.org/miche/ontologies/2024/8/Libro> .
        ?subject ?predicate ?object .
        FILTER (regex(str(?object), "informática|computación|tecnología", "i"))
    }}
    """
    results_local = graph.query(sparql_query_local)
    local_results = [str(row.subject).split("/")[-1] for row in results_local]

    # Consulta SPARQL en DBpedia
    dbpedia_sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    dbpedia_sparql.setQuery("""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?resource ?label WHERE {
        ?resource rdf:type dbo:Book .
        ?resource rdfs:label ?label .
        FILTER (regex(str(?label), "informática|computing|technology", "i") && lang(?label) = "en")
    }
    """)
    dbpedia_sparql.setReturnFormat(JSON)

    dbpedia_results = []
    try:
        response = dbpedia_sparql.query().convert()
        dbpedia_results = [{"resource": result["resource"]["value"], "label": result["label"]["value"]}
                           for result in response["results"]["bindings"]]
    except Exception as e:
        print("Error al conectarse a DBpedia:", e)

    return render_template('results.html', results=local_results, dbpedia_results=dbpedia_results, query=query)

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
