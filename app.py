from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import unicodedata
import spacy
from spacy.matcher import Matcher
import socket

DBPEDIA_ENDPOINT = "http://dbpedia.org/sparql"
app = Flask(__name__)

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_sm")

# Cargar el modelo pequeño de spaCy en inglés
nlp2 = spacy.load("en_core_web_sm")

# Cargar el archivo JSONld
# Es un archivo JSON con conceptos de ontología, usa la sintaxis de RFD
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
    langSel = request.form['lang']

    aux = len(query.split(" "))

    if aux > 4:
        if langSel == "Español":
            res = procesarPregunta(query)
            query = res[0]
        else:
            res = procesarPreguntaIngles(query)
            query = res[0]

    results = buscar_resultado(query, ontology_data, langSel)
    if hay_conexion():
        results_dbpedia = search_dbpedia(query, langSel)
        offline = ""
    else:
        results_dbpedia = []
        offline = "No se pudo conectar a DBpedia. Verifique su conexión a Internet."
    # Combinar resultados locales y JSON
    combined_results = {
        "local": results,
        "dbpedia": results_dbpedia
    }

    return render_template('results.html', results=combined_results, query=query, lang=langSel, offline=offline, property_labels=property_labels)

@app.route('/details/<instance>')
def details(instance):
    lang = request.args.get('lang')
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
    return render_template('details.html', instance=instance, results=simplified_results, lang=lang)

@app.route('/dbpedia_details/<title>')
def dbpedia_details(title):
    lang = request.args.get('lang')
    book_details = get_book_details(title, lang)
    if book_details:
        return render_template('dbpedia_details.html', details=book_details, title=title,lang=lang)
    else:
        return "No se encontraron detalles para este libro."


# funcion buscar en json
def buscar_resultado(query, data, langSel):
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
        idiomas = instance.get("http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneIdioma", [])
        idioma_instancia = idiomas[0]["@value"].lower() if idiomas else None
        if langSel and idioma_instancia != langSel.lower():
            continue 

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

def search_dbpedia(query, lang):
    langSel = 'es' if lang == "Español" else 'en'
    
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
      FILTER(LANG(?abstract) = '{langSel}')    
      FILTER(CONTAINS(LCASE(?abstract), LCASE("{query}")))

      # Intentar obtener título desde varias fuentes
      OPTIONAL {{
        ?book dbo:title ?title .
        FILTER(LANG(?title) = '{langSel}')
      }}
      OPTIONAL {{
        ?book rdfs:label ?title .
        FILTER(LANG(?title) = '{langSel}')
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


def get_book_details(title, lang):
    langSel = 'es' if lang == "Español" else 'en'

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
      ?book rdfs:label "{title}"@{langSel} .
      OPTIONAL {{ ?book rdfs:comment ?abstract . FILTER(LANG(?abstract) = '{langSel}') }}
      OPTIONAL {{ ?book dbo:author ?author . }}
      OPTIONAL {{ ?book dbo:publisher ?publisher . }}
      OPTIONAL {{ ?book dbo:publicationDate ?publicationDate . }}
      OPTIONAL {{ ?book dbp:isbn ?isbn . }}
      OPTIONAL {{ ?book dbo:numberOfPages ?numberOfPages . }}
      OPTIONAL {{ ?book dct:language ?language . FILTER(LANG(?language) = '{langSel}') }}
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
                ("Libro" if lang == "Español" else "Book"): result.get("book", {}).get("value", ""),
                ("Resumen" if lang == "Español" else "Abstract"): result.get("abstract", {}).get("value", ""),
                ("Autor" if lang == "Español" else "Author"): result.get("author", {}).get("value", ""),
                ("Editorial" if lang == "Español" else "Publisher"): result.get("publisher", {}).get("value", ""),
                ("Fecha de publicación" if lang == "Español" else "Publication Date"): result.get("publicationDate", {}).get("value", ""),
                "ISBN": result.get("isbn", {}).get("value", ""),
                ("Número de páginas" if lang == "Español" else "Number of Pages"): result.get("numberOfPages", {}).get("value", ""),
                ("Idioma" if lang == "Español" else "Language"): (
                    "Español" if result.get("abstract", {}).get("xml:lang", "") == "es" 
                    else "English" if result.get("abstract", {}).get("xml:lang", "") == "en" 
                    else "Desconocido"
                ),
            }
            # Tomar solo el primer conjunto de resultados
            break
        
        return details
    except Exception as e:
        print(f"Error al consultar detalles de DBpedia: {e}")
        return {}
    

def hay_conexion():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False
    
def procesarPregunta(pregunta):    
    # Crear un Matcher
    matcher = Matcher(nlp.vocab)
    # Definir patrones para entidades clave
    patrones = [
        [{"LOWER": "sistemas"}, {"LOWER": "operativos"}],  # Detectar "sistemas operativos"
        [{"LOWER": "colaborador"}],  
        [{"LOWER": "redes"}],  # Detectar "redes"
        [{"LOWER": "robótica"}],  # Detectar "Robótica"
        [{"LOWER": "inteligencia"}, {"LOWER": "artificial"}],  # Detectar "Inteligencia Artificial"
        [{"LOWER": "programación"}],  # Detectar "programación"
        [{"LOWER": "base"}, {"LOWER": "de"}, {"LOWER": "datos"}],  # Detectar "base de datos"
        [{"LOWER": "ingeniería"}, {"LOWER": "de"}, {"LOWER": "software"}],
        [{"LOWER": "simulación"}],  # Detectar "simulación"
        [{"LOWER": "sistema"}], 
        [{"LOWER": "libros"}],  # Detectar "libros"
        [{"LOWER": "tesis"}],  
        [{"LOWER": "introducción"}, {"LOWER": "a"}, {"LOWER": "la"}, {"LOWER": "programación"}], 
        [{"LOWER": "anónimo"}],
        [{"LOWER": "investigación"}],
        [{"LOWER": "computación"}],
        [{"LOWER": "ingles"}],
        [{"LOWER": "algoritmos"}],
        [{"LOWER": "ciberseguridad"}],  # Detectar "ciberseguridad"
        [{"LOWER": "ágiles"}],
        [{"LOWER": "web"}],
        [{"LOWER": "informática"}],

    ]
    matcher.add("EntidadesClave", patrones)

    # Procesar la pregunta
    doc = nlp(pregunta)

    # Encontrar coincidencias con el Matcher
    matches = matcher(doc)

    # Extraer entidades clave del Matcher
    temas = [doc[start:end].text for match_id, start, end in matches]

    # Si no hay coincidencias con el Matcher, realizar una búsqueda manual
    if len(temas) == 0:
        # Definir una lista de lenguajes de programación y otros temas
        temas_clave = [
            "java", "python", "c++", "javascript", "ruby", "php", "go", "rust", "swift", "kotlin", "scala",
        ]
        
        # Procesar la pregunta en minúsculas
        doc_lower = nlp(pregunta.lower())
        
        # Extraer entidades clave manualmente
        for token in doc_lower:
            if token.text in temas_clave:
                temas.append(token.text)
            elif token.text + " " + doc_lower[token.i + 1].text in temas_clave:  # Detectar frases compuestas
                temas.append(token.text + " " + doc_lower[token.i + 1].text)

    # Ordenar los temas: priorizar "ciberseguridad" sobre "investigación" y colocar "libros" al final
    temas_ordenados = [tema for tema in temas if tema.lower() == "ciberseguridad"] + \
                    [tema for tema in temas if tema.lower() != "ciberseguridad" and tema.lower() != "libros"] + \
                    [tema for tema in temas if tema.lower() == "libros"]
    
    return temas_ordenados

def procesarPreguntaIngles(pregunta):
    # Crear un Matcher
    matcher = Matcher(nlp2.vocab)

    # Definir patrones para entidades clave en inglés
    patrones = [
        [{"LOWER": "operating"}, {"LOWER": "systems"}],  # Detectar "operating systems"
        [{"LOWER": "collaborator"}],  
        [{"LOWER": "networks"}],  # Detectar "networks"
        [{"LOWER": "robotics"}],  # Detectar "robotics"
        [{"LOWER": "artificial"}, {"LOWER": "intelligence"}],  # Detectar "artificial intelligence"
        [{"LOWER": "programming"}],  # Detectar "programming"
        [{"LOWER": "database"}],  # Detectar "database"
        [{"LOWER": "software"}, {"LOWER": "engineering"}],  # Detectar "software engineering"
        [{"LOWER": "simulation"}],  # Detectar "simulation"
        [{"LOWER": "system"}], 
        [{"LOWER": "books"}],  # Detectar "books"
        [{"LOWER": "thesis"}],  
        [{"LOWER": "introduction"}, {"LOWER": "to"}, {"LOWER": "programming"}],  # Detectar "introduction to programming"
        [{"LOWER": "anonymous"}],
        [{"LOWER": "research"}],
        [{"LOWER": "computer"}, {"LOWER": "science"}],  # Detectar "computer science"
        [{"LOWER": "english"}],
        [{"LOWER": "algorithms"}],
        [{"LOWER": "cybersecurity"}],  # Detectar "cybersecurity"
        [{"LOWER": "agile"}],
        [{"LOWER": "web"}],
        [{"LOWER": "informatics"}],  # Detectar "informatics"
    ]
    matcher.add("EntidadesClave", patrones)

    # Procesar la pregunta
    doc = nlp2(pregunta)

    # Encontrar coincidencias con el Matcher
    matches = matcher(doc)

    # Extraer entidades clave del Matcher
    temas = [doc[start:end].text for match_id, start, end in matches]

    # Si no hay coincidencias con el Matcher, realizar una búsqueda manual
    if len(temas) == 0:
        # Definir una lista de lenguajes de programación y otros temas en inglés
        temas_clave = [
            "java", "python", "c++", "javascript", "ruby", "php", "go", "rust", "swift", "kotlin", "scala",
        ]
        
        # Procesar la pregunta en minúsculas
        doc_lower = nlp2(pregunta.lower())
        
        # Extraer entidades clave manualmente
        for token in doc_lower:
            if token.text in temas_clave:
                temas.append(token.text)
            elif token.text + " " + doc_lower[token.i + 1].text in temas_clave:  # Detectar frases compuestas
                temas.append(token.text + " " + doc_lower[token.i + 1].text)

    # Ordenar los temas: priorizar "cybersecurity" sobre "research" y colocar "books" al final
    temas_ordenados = [tema for tema in temas if tema.lower() == "cybersecurity"] + \
                    [tema for tema in temas if tema.lower() != "cybersecurity" and tema.lower() != "books"] + \
                    [tema for tema in temas if tema.lower() == "books"]

    return temas_ordenados

property_labels = {
    "Colaborador": {
        "Español": "Colaborador",
        "English": "Collaborator"
    },
    "Instancia": {
        "Español": "Instancia",
        "English": "Instance"
    },
    "Nombre": {
        "Español": "Nombre",
        "English": "Name"
    },
    "Carnet": {
        "Español": "Carnet",
        "English": "Card"
    },
    "Área de colaboracion": {
        "Español": "Área de colaboración",
        "English": "Collaboration Area"
    },
    "Año de Ingreso": {
        "Español": "Año de Ingreso",
        "English": "Year of Admission"
    },
    "Código SIS": {
        "Español": "Código SIS",
        "English": "SIS Code"
    },
    "Email": {
        "Español": "Email",
        "English": "Email"
    },
    "Año de ingreso docente": {
        "Español": "Año de ingreso docente",
        "English": "Year of Faculty Admission"
    },
    "Departamento": {
        "Español": "Departamento",
        "English": "Department"
    },
    "Cargo": {
        "Español": "Cargo",
        "English": "Position"
    },
    "Categoria": {
        "Español": "Categoría",
        "English": "Category"
    },
    "Area de estudio": {
        "Español": "Área de estudio",
        "English": "Field of Study"
    },
    "Autor": {
        "Español": "Autor",
        "English": "Author"
    },
    "Institucion": {
        "Español": "Institución",
        "English": "Institution"
    },
    "Ubicacion": {
        "Español": "Ubicación",
        "English": "Location"
    },
    "Capacidad": {
        "Español": "Capacidad",
        "English": "Capacity"
    },
    "Palabra Clave": {
        "Español": "Palabra Clave",
        "English": "Keyword"
    },
    "Visualizaciones": {
        "Español": "Visualizaciones",
        "English": "Views"
    },
    "Resumen": {
        "Español": "Resumen",
        "English": "Summary"
    },
    "Tamaño de archivo": {
        "Español": "Tamaño de archivo",
        "English": "File Size"
    },
    "Titulo": {
        "Español": "Título",
        "English": "Title"
    },
    "Formato": {
        "Español": "Formato",
        "English": "Format"
    },
    "Fecha de publicacion": {
        "Español": "Fecha de publicación",
        "English": "Publication Date"
    },
    "Idioma": {
        "Español": "Idioma",
        "English": "Language"
    },
    "Estado": {
        "Español": "Estado",
        "English": "Status"
    },
    'No se encontraron resultados.': {
        'Español': 'No se encontraron resultados locales.',
        'English': 'No local results found.'
    },
    'No se encontraron resultados DBpedia': {
        'Español': 'No se encontraron resultados en DBpedia.',
        'English': 'No DBpedia results found.'
    }
}

if __name__ == '__main__':
    app.run(debug=True)
