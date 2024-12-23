import spacy
from spacy.matcher import Matcher

# Comando para descargar el modelo en inglés de spaCy
# Ejecuta este comando en tu terminal antes de usar el código:
# python -m spacy download en_core_web_sm

# Cargar el modelo pequeño de spaCy en inglés
nlp2 = spacy.load("en_core_web_sm")

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

# Pregunta del usuario en inglés
pregunta = 'What books are available for the study area of Informatics?'
# pregunta = "What books are available about Java?"

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

# Imprimir los temas detectados
print(temas_ordenados)