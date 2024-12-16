from flask import Flask, request, render_template
from rdflib import Graph
from owlready2 import *
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import time
import json

app = Flask(__name__)

# Cargar la ontología con OWLready2
onto_path.append("ontologia/biblioteca")
onto = get_ontology("ontologia/biblioteca.owl").load()
# Convertir la ontología a un grafo RDFlib
graph = default_world.as_rdflib_graph()

# Cargar el archivo JSON
with open('./ontologia/ontologia.jsonld', 'r', encoding='utf-8') as f:
    ontology_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']  # Obtener consulta del formulario
    results = buscar_resultado(query, ontology_data)
    return render_template('results.html', query=query, results=results)

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


if __name__ == '__main__':
    app.run(debug=True)
