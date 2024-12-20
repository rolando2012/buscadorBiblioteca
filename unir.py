import json

# Cargar ontología original y libros de DBpedia
with open('./ontologia/ontologia_prueba.jsonld', 'r', encoding='utf-8') as file:
    ontologia = json.load(file)

with open('./csv/dbpedia_books_en.json', 'r', encoding='utf-8') as file:
    dbpedia_books = json.load(file)

# Extraer libros de DBpedia
libros_dbpedia = dbpedia_books['results']['bindings']

# Crear nuevas instancias basadas en los libros de DBpedia
nuevas_instancias = []

for libro in libros_dbpedia:
    # Determinar el idioma basado en el campo "abstract"
    abstract = libro.get("abstract", {}).get("xml:lang", "")
    if abstract == "es":
        idioma = "Español"
    elif abstract == "en":
        idioma = "English"
    else:
        idioma = "Desconocido"

    # Crear una nueva instancia para cada libro
    nueva_instancia = {
        "@id": f"http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaDigital/{libro.get('name', {}).get('value', '').replace(' ', '_')}",
        "@type": ["http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaDigital"],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo": [{"@value": libro.get("name", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAutor": [{"@value": libro.get("author", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneResumen": [{"@value": libro.get("abstract", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneISBN": [{"@value": libro.get("isbn", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneIdioma": [{"@value": idioma}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneEnlaceAcceso": [{"@value": libro.get("url", {}).get("value", "")}]
    }

    # Evitar instancias incompletas
    if nueva_instancia["http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo"][0]["@value"]:
        nuevas_instancias.append(nueva_instancia)

# Unir nuevas instancias a la ontología
ontologia.extend(nuevas_instancias)

# Guardar el resultado en un nuevo archivo JSON-LD
output_path = './ontologia/ontologia_actualizada.jsonld'
with open(output_path, 'w', encoding='utf-8') as file:
    json.dump(ontologia, file, indent=4, ensure_ascii=False)

print(f"Ontología actualizada guardada en {output_path}")

# Función para buscar en los datos de DBpedia

def buscar_resultado_dbpedia(query, data):
    query = query.lower()
    results = []

    # Diccionario para asociar URIs con etiquetas descriptivas
    property_labels = {
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo": "Titulo",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAutor": "Autor",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneResumen": "Resumen",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneISBN": "ISBN",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneIdioma": "Idioma",
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneEnlaceAcceso": "Enlace de Acceso"
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
