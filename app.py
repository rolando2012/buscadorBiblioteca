from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import time

DBPEDIA_ENDPOINT = "http://dbpedia.org/sparql"
app = Flask(__name__)

# Cargar la ontología con OWLready2
onto_path.append("ontologia/biblioteca")
onto = get_ontology("ontologia/biblioteca.owl").load()
# Convertir la ontología a un grafo RDFlib
graph = default_world.as_rdflib_graph()

# Cargar la lista de libros desde el archivo CSV
libros_csv_path = "csv/books.csv"

def cargar_libros_csv():
    libros_df = pd.read_csv(libros_csv_path)
    return libros_df

libros_df = cargar_libros_csv()

@app.route('/')
def start():
    return render_template('start.html')


@app.route('/index', methods=['GET'])
def search_page():
    return render_template('index.html')
    


@app.route('/search', methods=['POST'])
def search():
    query = request.form['query'].lower()
    results = []

    # Buscar coincidencias en la ontología
    for cls in onto.classes():
        if query in cls.name.lower():
            results.append(cls.name)

    # Si no hay resultados en la ontología, buscar en el CSV
    if not results:
        results = libros_df[libros_df['title'].str.lower().str.contains(query, na=False)]['title'].tolist()

    # Si no se encuentran resultados en ninguna parte
    if not results:
        results.append("No se encontraron resultados.")

    # Si se encuentran resultados, consulta en DBpedia para obtener más detalles
    if results[0] != "No se encontraron resultados.":
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery(f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?subject 
        WHERE {{
            ?subject ?predicate ?object .
            FILTER (regex(str(?subject), "{query}", "i") || regex(str(?object), "{query}", "i"))
        }}
        LIMIT 10
        """)
        sparql.setReturnFormat(JSON)
        start_time = time.time()
        dbpedia_results = sparql.query().convert()
        end_time = time.time()
        print(f"Tiempo de ejecución en DBpedia: {end_time - start_time} segundos")

        for result in dbpedia_results["results"]["bindings"]:
            results.append(result["subject"]["value"].split("/")[-1])

    return render_template('results.html', results=results, query=query)

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
