import spacy
from nltk.corpus import stopwords
import string

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_sm")

# Descargar stopwords de NLTK
import nltk
#nltk.download('stopwords')
stop_words = set(stopwords.words('spanish'))

# Función para preprocesar texto
def preprocess_text(text):
    # Tokenización y análisis con spaCy
    doc = nlp(text.lower())

    # Eliminar puntuación y stopwords
    tokens = [token.text for token in doc if token.text not in string.punctuation and token.text not in stop_words]

    return " ".join(tokens)

# Función para extraer frases clave y entidades nombradas
def extract_phrases_and_entities(text):
    # Procesar el texto con spaCy
    doc = nlp(text)

    # Extraer entidades nombradas (NER)
    entities = [ent.text.lower() for ent in doc.ents]

    # Extraer palabras clave basadas en el análisis sintáctico
    keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"] and token.text not in string.punctuation]

    # Combinar entidades y palabras clave
    all_keywords = list(set(entities + keywords))

    return all_keywords

# Ejemplo de pregunta en español
pregunta = '¿Qué libros cubren la teoría de la computación?'

sinRevelancia = ['libros','practica','recurso', 'tema', 'trabajos']

# Preprocesar la pregunta
pregunta_procesada = preprocess_text(pregunta)
print("Pregunta procesada:", pregunta_procesada)
# Extraer frases clave y entidades
palabras_clave = extract_phrases_and_entities(pregunta)
res = palabras_clave[0]
if palabras_clave[0].find("¿")==0:
    palabras_clave = palabras_clave[:-1]
    res = palabras_clave[0]
else:
    for palabra in sinRevelancia:
        if palabra == palabras_clave[0]:
            if(palabras_clave[1].find("¿")==0):
                res = palabras_clave[2]
            else:
                res = palabras_clave[1]
            break

print("Palabras clave extraídas:", palabras_clave)
print("res: ", res)

"""
1. cuando tenga un signo de puntuacion invertir
2. si es libro, recurso, practica, tesis, etc, siguiente
"""