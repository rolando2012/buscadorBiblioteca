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
    # Crear una nueva instancia para cada libro
    nueva_instancia = {
        "@id": f"http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaDigital/{libro.get('name', {}).get('value', '').replace(' ', '_')}",
        "@type": ["http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecaDigital"],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo": [{"@value": libro.get("name", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneAutor": [{"@value": libro.get("author", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneResumen": [{"@value": libro.get("abstract", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneISBN": [{"@value": libro.get("isbn", {}).get("value", "")}],
        "http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneIdioma": [{"@value": libro.get("language", {}).get("value", "").split('/')[-1]}],
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