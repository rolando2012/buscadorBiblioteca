from rdflib import Graph
import json

# Carga la ontología desde un archivo local
g = Graph()
g.parse("./ontologia/biblioteca.owl", format="xml")

# Convierte la ontología a una serialización JSON-LD
json_ld = g.serialize(format="json-ld")

# Guarda la serialización JSON-LD en un archivo
with open("./ontologia/ontologia.json", "w") as f:
    f.write(json_ld)

# Opcional: Cargar la ontología JSON para verificar
with open("./ontologia/ontologia.json", "r") as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))
