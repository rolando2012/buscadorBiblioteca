import spacy
from spacy.matcher import Matcher

# Cargar el modelo pequeño de spaCy
nlp = spacy.load("es_core_news_sm")

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

# Pregunta del usuario
pregunta = '¿Qué libros hay para el área de estudio de la Informática ?'
# pregunta = "¿Qué libros están disponibles sobre Java?"

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
# Imprimir los temas detectados
print(temas_ordenados)