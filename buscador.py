import json

def load_books(json_file):
    """
    Carga los datos de libros desde un archivo JSON.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            books = data["results"]["bindings"]
            return books
    except FileNotFoundError:
        print("El archivo JSON no fue encontrado.")
        return []
    except json.JSONDecodeError:
        print("Error al decodificar el archivo JSON.")
        return []


def search_books(books, keyword):
    """
    Busca libros que contengan la palabra clave en el título, autor o resumen.
    Evita títulos repetidos utilizando un conjunto (set).
    """
    keyword = keyword.lower()
    results = set()  # Usamos un conjunto para evitar duplicados

    for book in books:
        title = book.get("name", {}).get("value", "").lower()
        author = book.get("author", {}).get("value", "").lower()
        abstract = book.get("abstract", {}).get("value", "").lower()

        if keyword in title or keyword in author or keyword in abstract:
            results.add(title)  # Se añade el título al conjunto
    
    return sorted(results)  # Devolver los resultados en orden alfabético


def main():
    # Carga los datos desde el archivo JSON generado previamente
    json_file = "./csv/dbpedia_books.json"
    books = load_books(json_file)
    
    if not books:
        print("No hay libros para buscar.")
        return

    # Solicita al usuario una palabra clave
    print("Motor de búsqueda de libros\n")
    keyword = "java"

    # Realiza la búsqueda
    results = search_books(books, keyword)

    # Muestra los resultados
    if results:
        print("\nResultados encontrados:")
        for idx, title in enumerate(results, start=1):
            print(f"{idx}. {title}")
    else:
        print("\nNo se encontraron resultados para esa palabra clave.")


if __name__ == "__main__":
    main()
