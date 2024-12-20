from SPARQLWrapper import SPARQLWrapper, JSON
import unicodedata

# Función para limpiar texto y eliminar caracteres no deseados
def clean_text(text):
    if text is None:
        return "N/A"
    # Eliminar caracteres no deseados como \u200b
    cleaned_text = unicodedata.normalize("NFKC", text)
    return cleaned_text

# Definir el endpoint de DBpedia
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

# Definir la consulta SPARQL
query = """
SELECT DISTINCT ?title
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
  ?book rdfs:comment ?abstract .
 OPTIONAL { ?book dbp:title ?title . }
 OPTIONAL { ?book dbo:title ?title . }
 OPTIONAL { ?book rdfs:label ?title . }


  # Filtro por idioma español
  FILTER ( LANG(?abstract) = 'es' )

  # Búsqueda en título y abstract
  FILTER (
    CONTAINS(LCASE(?abstract), LCASE("QUERY"))
  )
}
"""

# Reemplazar "QUERY" con el texto de búsqueda
search_query = "IndexedDB"  # Cambia esto por tu consulta
query = query.replace('"QUERY"', f'"{search_query}"')

# Configurar la consulta
sparql.setQuery(query)
sparql.setReturnFormat(JSON)

# Ejecutar la consulta
results = sparql.query().convert()

# Imprimir solo los títulos
for result in results["results"]["bindings"]:
    title = clean_text(result.get('title', {}).get('value', 'N/A'))
    print(f"Title: {title}")