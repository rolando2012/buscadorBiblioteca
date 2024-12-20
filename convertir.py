from SPARQLWrapper import SPARQLWrapper, JSON

def get_book_details(title):
    # Inicializar el wrapper de SPARQL para DBpedia
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    
    # Consulta SPARQL adaptada
    sparql_query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX dct: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?book ?abstract ?author ?publisher ?publicationDate ?isbn ?numberOfPages ?language
    WHERE {{
      ?book rdfs:label "{title}"@es .
      OPTIONAL {{ ?book rdfs:comment ?abstract . FILTER(LANG(?abstract) = 'es') }}
      OPTIONAL {{ ?book dbo:author ?author . }}
      OPTIONAL {{ ?book dbo:publisher ?publisher . }}
      OPTIONAL {{ ?book dbo:publicationDate ?publicationDate . }}
      OPTIONAL {{ ?book dbp:isbn ?isbn . }}
      OPTIONAL {{ ?book dbo:numberOfPages ?numberOfPages . }}
      OPTIONAL {{ ?book dct:language ?language . FILTER(LANG(?language) = 'es') }}
    }}
    """
    
    # Configurar la consulta y el formato de respuesta
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    
    try:
        # Ejecutar la consulta
        results = sparql.query().convert()
        details = {}
        
        # Procesar los resultados
        for result in results["results"]["bindings"]:
            details = {
                "book": result.get("book", {}).get("value", ""),
                "abstract": result.get("abstract", {}).get("value", ""),
                "author": result.get("author", {}).get("value", ""),
                "publisher": result.get("publisher", {}).get("value", ""),
                "publicationDate": result.get("publicationDate", {}).get("value", ""),
                "isbn": result.get("isbn", {}).get("value", ""),
                "numberOfPages": result.get("numberOfPages", {}).get("value", ""),
                "language": result.get("language", {}).get("value", ""),
            }
            # Tomar solo el primer conjunto de resultados
            break
        
        return details
    except Exception as e:
        print(f"Error al consultar detalles de DBpedia: {e}")
        return {}

# Ejemplo de uso
book_title = "Colobot"  # Título del libro en español
book_details = get_book_details(book_title)
print(book_details)