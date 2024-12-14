import json

# Cargar el archivo JSON
with open("./ontologia/ontologia.json", "r") as f:
    data = json.load(f)

def buscar_palabra_clave(data, palabra_clave):
    resultados = []
    for instancia in data:
        for clave, valores in instancia.items():
            if isinstance(valores, list):
                for valor in valores:
                    if isinstance(valor, dict) and '@value' in valor:
                        valor_str = str(valor['@value'])  # Asegurarse de que el valor sea una cadena
                        if palabra_clave.lower() in valor_str.lower():
                            titulo = instancia.get("http://www.semanticweb.org/miche/ontologies/2024/8/OntologiaBibliotecatieneTitulo", [{"@value": "Sin título"}])[0]['@value']
                            resultados.append(titulo)
    return resultados

# Buscar la palabra "redes" y mostrar los títulos correspondientes
palabra_clave = "jhosemar"
resultados = buscar_palabra_clave(data, palabra_clave)

for titulo in resultados:
    print(f"Título: {titulo}")
