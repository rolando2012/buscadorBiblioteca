from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import unicodedata
import spacy
import nltk
from nltk.corpus import stopwords
import string

DBPEDIA_ENDPOINT = "http://dbpedia.org/sparql"
app = Flask(__name__)

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_sm")

#nltk.download('stopwords')
stop_words = set(stopwords.words('spanish'))

# Cargar el archivo JSON
with open('./ontologia/bibliotecaDigital.jsonld', 'r', encoding='utf-8') as f:
    ontology_data = json.load(f)

@app.route('/')
def start():
    return render_template('start.html')


@app.route('/index', methods=['GET'])
def search_page():
    return render_template('index.html')
    

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']

    if query.find("?")>-1:
        res = procesarPregunta(query)
        query = res[0]

    results = buscar_resultado(query, ontology_data)
    results_dbpedia = search_dbpedia(query)

    # Combinar resultados locales y JSON
    combined_results = {
        "local": results,
        "dbpedia": results_dbpedia
    }

    return render_template('results.html', results=combined_results,query=query)

@app.route('/details/<instance>')
def details(instance):
    # Buscar la instancia correspondiente
    matching_instance = None
    for entry in ontology_data:
        # Extraer el identificador de la instancia desde "@id"
        instance_id = entry["@id"].split("/")[-1]
        if instance_id == instance:
            matching_instance = entry
            break

     # Si no se encuentra, buscar por el rdfs:label
    if not matching_instance:
        for entry in ontology_data:
            labels = entry.get("http://www.w3.org/2000/01/rdf-schema#label", [])
            for label in labels:
                if label.get("@value") == instance:
                    matching_instance = entry
                    break
            if matching_instance:
                break

    # Manejar caso donde no se encuentra la instancia
    if not matching_instance:
        return f"No se encontró la instancia: {instance}", 404

    # Simplificar los detalles de la instancia
    simplified_results = []
    for predicate, values in matching_instance.items():
        if isinstance(values, list) and "@value" in values[0]:
            label = predicate.split("/")[-1]  # Obtener la última parte del URI como etiqueta
            value = values[0]["@value"]  # Obtener el valor
            simplified_results.append((label, value))
    return render_template('details.html', instance=instance, results=simplified_results)

@app.route('/dbpedia_details/<title>')
def dbpedia_details(title):
    book_details = get_book_details(title)
    if book_details:
        return render_template('dbpedia_details.html', details=book_details, title=title)
    else:
        return "No se encontraron detalles para este libro."


#funcion buscar en json
def buscar_resultado(query, data):
    query = query.lower()
    results = []

    # Diccionario para asociar URIs con etiquetas descriptivas
    property_labels = {
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneColaborador": "Colaborador",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneNombre": "Nombre",

        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneCarnet": "Carnet",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAreaColaboracion": "Área de colaboracion",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAñoIngreso": "Año de Ingreso",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneCodigoSis": "Código SIS",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneEmail": "Email",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAñoIngresoDocente": "Año de ingreso docente",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneDepartamento": "Departamento",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneCargo": "Cargo",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaTieneCategoría": "Categoria",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAreaEstudio": "Area de estudio",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAutor": "Autor",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneInstitucion": "Institucion",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneUbicación": "Ubicacion",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneCapacidad": "Capacidad",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatienePalabraClave": "Palabra Clave",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneCantidadVisualizaciones": "Visualizaciones",

        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneResumen": "Resumen",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTamañoArchivo": "Tamaño de archivo",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo": "Titulo",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneFormato": "Formato",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneFechaPublicacion": "Fecha de publicacion",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneIdioma": "Idioma",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneEstado": "Estado",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneInstitucion": "Institucion",
    }

    for instance in data:
        # Obtener el label de la instancia o extraer desde @id si no existe
        instance_label = instance.get("http://www.w3.org/2000/01/rdf-schema#label", [{"@value": ""}])[0]["@value"]
        if not instance_label:
            instance_id = instance.get("@id", "")
            instance_label = instance_id.split("/")[-1]

        # Inicializar variables para título y otros valores descriptivos
        title = None
        additional_info = []

        # Recorrer propiedades para buscar coincidencias y más información
        for property, values in instance.items():
            if not isinstance(values, list):
                continue

            for value in values:
                if "@value" in value and query in value["@value"].lower():
                    context = property_labels.get(property, "Relacionado")
                    title = f"{value['@value']} - {context}"
                    
                    # Agregar valores adicionales con etiquetas descriptivas
                elif property in property_labels:
                    label = property_labels[property]
                    descriptive_value = f"{label}: {value['@value']}"
                    if descriptive_value not in additional_info and len(additional_info) < 5:
                        additional_info.append(descriptive_value)

        if title:
            results.append({
                "Titulo": title,  # El valor que coincide con la búsqueda
                "Instancia": instance_label,  # El label o ID relacionado con la instancia
                "MasInformacion": additional_info  # Valores con etiquetas descriptivas
            })

    return results

# Función para limpiar texto y eliminar caracteres no deseados
def clean_text(text):
    if text is None:
        return "N/A"
    cleaned_text = unicodedata.normalize("NFKC", text)
    return cleaned_text

def search_dbpedia(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql_query = f"""
    SELECT DISTINCT ?title
    WHERE {{
      ?book dbo:wikiPageWikiLink ?topic .
      VALUES ?topic {{ 
        dbr:Software 
        dbr:Networks_Concepts
        dbr:Database 
        dbr:Programming 
        dbr:Algorithm 
        dbr:Artificial_intelligence 
        dbr:Data_mining 
        dbr:Operating_system 
      }}
      ?book rdfs:comment ?abstract .
      FILTER(LANG(?abstract) = 'es')    
      FILTER(CONTAINS(LCASE(?abstract), LCASE("{query}")))

      # Intentar obtener título desde varias fuentes
      
      OPTIONAL {{
        ?book dbo:title ?title .
        FILTER(LANG(?title) = 'es')
      }}
      OPTIONAL {{
        ?book rdfs:label ?title .
        FILTER(LANG(?title) = 'es')
      }}
    }}

    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        dbpedia_results = []

        for result in results["results"]["bindings"]:
            if 'title' in result:
                title = clean_text(result['title']['value'])
                dbpedia_results.append({"title": title})
        
        return dbpedia_results
    except Exception as e:
        print(f"Error al consultar DBpedia: {e}")
        return []


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
                "Libro": result.get("book", {}).get("value", ""),
                "Resumen": result.get("abstract", {}).get("value", ""),
                "Autor": result.get("author", {}).get("value", ""),
                "publisher": result.get("publisher", {}).get("value", ""),
                "Fecha de publicacion": result.get("publicationDate", {}).get("value", ""),
                "isbn": result.get("isbn", {}).get("value", ""),
                "Numero de paginas": result.get("numberOfPages", {}).get("value", ""),
                "Languaje": "Español" if result.get("abstract", {}).get("xml:lang", "") == "es" else "English" if result.get("abstract", {}).get("xml:lang", "") == "en" else "Desconocido",
            }
            # Tomar solo el primer conjunto de resultados
            break
        
        return details
    except Exception as e:
        print(f"Error al consultar detalles de DBpedia: {e}")
        return {}
    

# Función para extraer frases clave y entidades nombradas
def procesarPregunta(text):
    # Procesar el texto con spaCy
    doc = nlp(text)

    # Extraer entidades nombradas (NER)
    entities = [ent.text.lower() for ent in doc.ents]

    # Extraer palabras clave basadas en el análisis sintáctico
    keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"] and token.text not in string.punctuation]

    # Combinar entidades y palabras clave
    all_keywords = list(set(entities + keywords))

    return all_keywords

if __name__ == '__main__':
    app.run(debug=True)
