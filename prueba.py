import time
from SPARQLWrapper import SPARQLWrapper, JSON

# Configurar la consulta SPARQL
sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.setQuery("""
    SELECT ?subject ?predicate ?object
    WHERE {
        ?subject ?predicate ?object
    }
    LIMIT 10
""")
sparql.setReturnFormat(JSON)

# Medir el tiempo de ejecución
start_time = time.time()
results = sparql.query().convert()
end_time = time.time()

print(f"Tiempo de ejecución: {end_time - start_time} segundos")
print(results)