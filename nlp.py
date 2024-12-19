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
pregunta = '¿Cuál es el libro de programación más usado?'

# Preprocesar la pregunta
pregunta_procesada = preprocess_text(pregunta)
print("Pregunta procesada:", pregunta_procesada)

# Extraer frases clave y entidades
palabras_clave = extract_phrases_and_entities(pregunta)
print("Palabras clave extraídas:", palabras_clave)