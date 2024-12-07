from flask import Flask, request, render_template
from rdflib import Graph

app = Flask(__name__)

# Cargar la ontología desde un archivo .owl
g = Graph()
g.parse("ontologia/biblioteca.owl", format="xml")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    sparql_query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?subject ?predicate ?object
    WHERE {{
        ?subject ?predicate ?object .
        FILTER (regex(str(?subject), "{query}", "i") || regex(str(?object), "{query}", "i"))
    }}
    LIMIT 10
    """
    results = g.query(sparql_query)
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
